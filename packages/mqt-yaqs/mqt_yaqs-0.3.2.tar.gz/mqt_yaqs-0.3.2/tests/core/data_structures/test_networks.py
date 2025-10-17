# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Tests for network classes.

This module provides unit tests for the Matrix Product State (MPS) class and its associated methods.
It verifies correct initialization, custom tensor assignment, bond dimension computation, network flipping,
orthogonality center shifting, normalization, observable measurement, and overall validity of MPS objects.
These tests ensure that the MPS class functions as expected in various simulation scenarios.
"""

# ignore non-lowercase variable names for physics notation
# ruff: noqa: N806

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

import numpy as np
import opt_einsum as oe
import pytest
from qiskit.circuit import QuantumCircuit
from scipy.stats import unitary_group

from mqt.yaqs import simulator
from mqt.yaqs.core.data_structures.simulation_parameters import AnalogSimParams, StrongSimParams

if TYPE_CHECKING:
    from numpy.typing import NDArray

from mqt.yaqs.core.data_structures.networks import MPO, MPS
from mqt.yaqs.core.data_structures.simulation_parameters import Observable
from mqt.yaqs.core.libraries.gate_library import GateLibrary, Id, X, Y, Z


def untranspose_block(mpo_tensor: NDArray[np.complex128]) -> NDArray[np.complex128]:
    """Reverse the transposition of an MPO tensor.

    MPO tensors are stored in the order (sigma, sigma', row, col). This function transposes
    the tensor to the order (row, col, sigma, sigma') so that the first two indices can be interpreted
    as a block matrix of operators.

    Args:
        mpo_tensor (NDArray[np.complex128]): The MPO tensor in (sigma, sigma', row, col) order.

    Returns:
        NDArray[np.complex128]: The MPO tensor in (row, col, sigma, sigma') order.
    """
    return np.transpose(mpo_tensor, (2, 3, 0, 1))


def crandn(
    size: int | tuple[int, ...], *args: int, seed: np.random.Generator | int | None = None
) -> NDArray[np.complex128]:
    """Draw random samples from the standard complex normal distribution.

    Args:
        size: The size/shape of the output array.
        args: Additional dimensions for the output array.
        seed: The seed for the random number generator.

    Returns:
        The array of random complex numbers.
    """
    if isinstance(size, int) and len(args) > 0:
        size = (size, *list(args))
    elif isinstance(size, int):
        size = (size,)
    rng = np.random.default_rng(seed)
    # 1 / sqrt(2) is a normalization factor
    return np.asarray((rng.standard_normal(size) + 1j * rng.standard_normal(size)) / np.sqrt(2), dtype=np.complex128)


def random_mps(shapes: list[tuple[int, int, int]], *, normalize: bool = True) -> MPS:
    """Create a random MPS with the given shapes.

    Args:
        shapes (List[Tuple[int, int, int]]): The shapes of the tensors in the
            MPS.
        normalize (bool): Whether to normalize the MPS.

    Returns:
        MPS: The random MPS.
    """
    tensors = [crandn(shape) for shape in shapes]
    mps = MPS(len(shapes), tensors=tensors)
    if normalize:
        mps.normalize()
    return mps


rng = np.random.default_rng()

##############################################################################
# Tests for the MPO class
##############################################################################


def test_init_ising() -> None:
    """Test that init_ising creates the correct MPO for the Ising model.

    This test initializes an Ising MPO with a given length, coupling constant (J), and transverse field (g).
    It verifies that:
      - The MPO has the expected length and physical dimension.
      - The left boundary tensor, inner tensors, and right boundary tensor have the correct shapes.
      - The operator blocks (after untransposing) match the expected values: identity, -J*Z, and -g*X.
    """
    mpo = MPO()
    length = 4
    J = 1.0
    g = 0.5

    mpo.init_ising(length, J, g)

    assert mpo.length == length
    assert mpo.physical_dimension == 2
    assert len(mpo.tensors) == length

    minus_J = -J  # -1.0
    minus_g = -g  # -0.5

    # Check left boundary: shape (2,2,1,3) -> untransposed to (1,3,2,2)
    left_block = untranspose_block(mpo.tensors[0])
    assert left_block.shape == (1, 3, 2, 2)

    block_I = left_block[0, 0]
    block_JZ = left_block[0, 1]
    block_gX = left_block[0, 2]

    assert np.allclose(block_I, Id().matrix)
    assert np.allclose(block_JZ, minus_J * Z().matrix)
    assert np.allclose(block_gX, minus_g * X().matrix)

    # Check an inner tensor (if length > 2): shape (2,2,3,3) -> untransposed to (3,3,2,2)
    if length > 2:
        inner_block = untranspose_block(mpo.tensors[1])
        assert inner_block.shape == (3, 3, 2, 2)
        assert np.allclose(inner_block[0, 0], Id().matrix)
        assert np.allclose(inner_block[0, 1], minus_J * Z().matrix)
        assert np.allclose(inner_block[0, 2], minus_g * X().matrix)
        assert np.allclose(inner_block[1, 2], Z().matrix)
        assert np.allclose(inner_block[2, 2], Id().matrix)

    # Check right boundary: shape (2,2,3,1) -> untransposed to (3,1,2,2)
    right_block = untranspose_block(mpo.tensors[-1])
    assert right_block.shape == (3, 1, 2, 2)

    block_gX = right_block[0, 0]
    block_Z = right_block[1, 0]
    block_I = right_block[2, 0]

    assert np.allclose(block_gX, minus_g * X().matrix)
    assert np.allclose(block_Z, Z().matrix)
    assert np.allclose(block_I, Id().matrix)


def test_init_heisenberg() -> None:
    """Test that init_heisenberg creates the correct MPO for the Heisenberg model.

    This test initializes a Heisenberg MPO with given coupling constants (Jx, Jy, Jz) and field h.
    It verifies that:
      - The MPO has the expected length and physical dimension.
      - The left boundary tensor (after untransposition) has the correct shape and
        contains the expected operators: [I, -Jx*X, -Jy*Y, -Jz*Z, -h*Z].
      - Inner and right boundary tensors have the expected shapes.
    """
    mpo = MPO()
    length = 5
    Jx, Jy, Jz, h = 1.0, 0.5, 0.3, 0.2

    mpo.init_heisenberg(length, Jx, Jy, Jz, h)

    assert mpo.length == length
    assert mpo.physical_dimension == 2
    assert len(mpo.tensors) == length

    left_block = untranspose_block(mpo.tensors[0])
    assert left_block.shape == (1, 5, 2, 2)

    block_I = left_block[0, 0]
    block_JxX = left_block[0, 1]
    block_JyY = left_block[0, 2]
    block_JzZ = left_block[0, 3]
    block_hZ = left_block[0, 4]

    minus_Jx = -Jx
    minus_Jy = -Jy
    minus_Jz = -Jz
    minus_h = -h

    assert np.allclose(block_I, Id().matrix)
    assert np.allclose(block_JxX, minus_Jx * X().matrix)
    assert np.allclose(block_JyY, minus_Jy * Y().matrix)
    assert block_JyY.shape == (2, 2)
    assert np.allclose(block_JzZ, minus_Jz * Z().matrix)
    assert np.allclose(block_hZ, minus_h * Z().matrix)

    for i, tensor in enumerate(mpo.tensors):
        if i == 0:
            assert tensor.shape == (2, 2, 1, 5)
        elif i == length - 1:
            assert tensor.shape == (2, 2, 5, 1)
        else:
            assert tensor.shape == (2, 2, 5, 5)


def test_init_identity() -> None:
    """Test that init_identity initializes an identity MPO correctly.

    This test checks that an identity MPO has the correct length, physical dimension,
    and that each tensor corresponds to the identity operator.
    """
    mpo = MPO()
    length = 3
    pdim = 2

    mpo.init_identity(length, physical_dimension=pdim)

    assert mpo.length == length
    assert mpo.physical_dimension == pdim
    assert len(mpo.tensors) == length

    for tensor in mpo.tensors:
        assert tensor.shape == (2, 2, 1, 1)
        assert np.allclose(np.squeeze(tensor), Id().matrix)


def test_init_custom_hamiltonian() -> None:
    """Test initializing a custom Hamiltonian MPO using user-provided boundary and inner tensors.

    This test creates random tensors for the left boundary, inner sites, and right boundary,
    initializes the MPO with these using init_custom_hamiltonian, and verifies that the tensors
    have the expected shapes and values (after appropriate transposition).
    """
    length = 4
    pdim = 2

    left_bound = rng.random(size=(1, 2, pdim, pdim)).astype(np.complex128)
    inner = rng.random(size=(2, 2, pdim, pdim)).astype(np.complex128)
    right_bound = rng.random(size=(2, 1, pdim, pdim)).astype(np.complex128)

    mpo = MPO()
    mpo.init_custom_hamiltonian(length, left_bound, inner, right_bound)

    assert mpo.length == length
    assert len(mpo.tensors) == length

    assert mpo.tensors[0].shape == (pdim, pdim, 1, 2)
    for i in range(1, length - 1):
        assert mpo.tensors[i].shape == (pdim, pdim, 2, 2)
    assert mpo.tensors[-1].shape == (pdim, pdim, 2, 1)

    assert np.allclose(mpo.tensors[0], np.transpose(left_bound, (2, 3, 0, 1)))
    for i in range(1, length - 1):
        assert np.allclose(mpo.tensors[i], np.transpose(inner, (2, 3, 0, 1)))
    assert np.allclose(mpo.tensors[-1], np.transpose(right_bound, (2, 3, 0, 1)))


def test_init_custom() -> None:
    """Test that init_custom correctly sets up an MPO from a user-provided list of tensors.

    This test provides a list of tensors for the left boundary, middle, and right boundary,
    initializes the MPO, and checks that the shapes and values of the MPO tensors match the inputs.
    """
    length = 3
    pdim = 2
    tensors = [
        rng.random(size=(1, 2, pdim, pdim)).astype(np.complex128),
        rng.random(size=(2, 2, pdim, pdim)).astype(np.complex128),
        rng.random(size=(2, 1, pdim, pdim)).astype(np.complex128),
    ]

    mpo = MPO()
    mpo.init_custom(tensors)

    assert mpo.length == length
    assert mpo.physical_dimension == pdim
    assert len(mpo.tensors) == length

    for original, created in zip(tensors, mpo.tensors, strict=False):
        assert original.shape == created.shape
        assert np.allclose(original, created)


def test_to_mps() -> None:
    """Test converting an MPO to an MPS.

    This test initializes an MPO using init_ising, converts it to an MPS via to_mps,
    and verifies that the resulting MPS has the correct length and that each tensor has been reshaped
    to the expected dimensions.
    """
    mpo = MPO()
    length = 3
    J, g = 1.0, 0.5

    mpo.init_ising(length, J, g)
    mps = mpo.to_mps()

    assert isinstance(mps, MPS)
    assert mps.length == length

    for i, tensor in enumerate(mps.tensors):
        original_mpo_tensor = mpo.tensors[i]
        pdim2 = original_mpo_tensor.shape[0] * original_mpo_tensor.shape[1]
        bond_in = original_mpo_tensor.shape[2]
        bond_out = original_mpo_tensor.shape[3]
        assert tensor.shape == (pdim2, bond_in, bond_out)


def test_check_if_valid_mpo() -> None:
    """Test that a valid MPO passes the check_if_valid_mpo method without raising errors.

    This test initializes an Ising MPO and calls check_if_valid_mpo, which should validate the MPO.
    """
    mpo = MPO()
    length = 4
    J, g = 1.0, 0.5

    mpo.init_ising(length, J, g)
    mpo.check_if_valid_mpo()


def test_rotate() -> None:
    """Test the rotate method for an MPO.

    This test checks that rotating an MPO (without conjugation) transposes each tensor as expected,
    and that rotating back with conjugation returns tensors with the original physical dimensions.
    """
    mpo = MPO()
    length = 3
    J, g = 1.0, 0.5

    mpo.init_ising(length, J, g)
    original_tensors = [t.copy() for t in mpo.tensors]

    mpo.rotate(conjugate=False)
    for orig, rotated in zip(original_tensors, mpo.tensors, strict=False):
        assert rotated.shape == (orig.shape[1], orig.shape[0], orig.shape[2], orig.shape[3])
        np.testing.assert_allclose(rotated, np.transpose(orig, (1, 0, 2, 3)))

    mpo.rotate(conjugate=True)
    for tensor in mpo.tensors:
        assert tensor.shape[0:2] == (2, 2)


def test_check_if_identity() -> None:
    """Test that an identity MPO is recognized as identity by check_if_identity.

    This test initializes an identity MPO and verifies that check_if_identity returns True
    when a fidelity threshold is provided.
    """
    mpo = MPO()
    length = 3
    pdim = 2

    mpo.init_identity(length, pdim)
    fidelity_threshold = 0.9
    assert mpo.check_if_identity(fidelity_threshold) is True


##############################################################################
# Tests for the MPS class
##############################################################################


@pytest.mark.parametrize("state", ["zeros", "ones", "x+", "x-", "y+", "y-", "Neel", "wall", "basis"])
def test_mps_initialization(state: str) -> None:
    """Test that MPS initializes with the correct chain length, physical dimensions, and tensor shapes.

    This test creates an MPS with 4 sites using a specified default state and verifies that each tensor
    is of rank 3 and has dimensions corresponding to the physical dimension and default bond dimensions.

    Args:
        state (str): The default state to initialize (e.g., "zeros", "ones", "x+", etc.).
    """
    length = 4
    pdim = 2
    basis_string = "1001"

    if state == "basis":
        mps = MPS(length=length, physical_dimensions=[pdim] * length, state=state, basis_string=basis_string)
    else:
        mps = MPS(length=length, physical_dimensions=[pdim] * length, state=state)

    assert mps.length == length
    assert len(mps.tensors) == length
    assert all(d == pdim for d in mps.physical_dimensions)

    for i, tensor in enumerate(mps.tensors):
        # Check tensor shape
        assert tensor.ndim == 3
        assert tensor.shape == (pdim, 1, 1)

        # Validate state-specific behavior
        vec = tensor[:, 0, 0]
        if state == "zeros":
            expected = np.array([1, 0], dtype=complex)
            np.testing.assert_allclose(vec, expected)
        elif state == "ones":
            expected = np.array([0, 1], dtype=complex)
            np.testing.assert_allclose(vec, expected)
        elif state == "x+":
            expected = np.array([1, 1], dtype=complex) / np.sqrt(2)
            np.testing.assert_allclose(vec, expected)
        elif state == "x-":
            expected = np.array([1, -1], dtype=complex) / np.sqrt(2)
            np.testing.assert_allclose(vec, expected)
        elif state == "y+":
            expected = np.array([1, 1j], dtype=complex) / np.sqrt(2)
            np.testing.assert_allclose(vec, expected)
        elif state == "y-":
            expected = np.array([1, -1j], dtype=complex) / np.sqrt(2)
            np.testing.assert_allclose(vec, expected)
        elif state == "Neel":
            expected = np.array([1, 0], dtype=complex) if i % 2 else np.array([0, 1], dtype=complex)
            np.testing.assert_allclose(vec, expected)
        elif state == "wall":
            expected = np.array([1, 0], dtype=complex) if i < length // 2 else np.array([0, 1], dtype=complex)
            np.testing.assert_allclose(vec, expected)
        elif state == "basis":
            bit = int(basis_string[i])
            expected = np.zeros(pdim, dtype=complex)
            expected[bit] = 1
            np.testing.assert_allclose(vec, expected)


def test_mps_custom_tensors() -> None:
    """Test that an MPS can be initialized with custom tensors.

    This test provides a list of custom rank-3 tensors for an MPS and verifies that the MPS
    retains these tensors correctly.
    """
    length = 3
    pdim = 2
    t1 = rng.random(size=(pdim, 1, 2)).astype(np.complex128)
    t2 = rng.random(size=(pdim, 2, 2)).astype(np.complex128)
    t3 = rng.random(size=(pdim, 2, 2)).astype(np.complex128)
    tensors = [t1, t2, t3]

    mps = MPS(length=length, tensors=tensors, physical_dimensions=[pdim] * length)
    assert mps.length == length
    assert len(mps.tensors) == length
    for i, tensor in enumerate(mps.tensors):
        assert np.allclose(tensor, tensors[i])


def test_flip_network() -> None:
    """Test the flip_network method of MPS.

    This test reverses the order of the MPS tensors and transposes each tensor's bond dimensions.
    Flipping the network twice should restore the original order and tensor values.
    """
    length = 3
    pdim = 2
    t1 = rng.random(size=(pdim, 1, 2)).astype(np.complex128)
    t2 = rng.random(size=(pdim, 2, 2)).astype(np.complex128)
    t3 = rng.random(size=(pdim, 2, 1)).astype(np.complex128)
    original_tensors = [t1, t2, t3]
    mps = MPS(length, tensors=copy.deepcopy(original_tensors), physical_dimensions=[pdim] * length)

    mps.flip_network()
    flipped_tensors = mps.tensors
    assert len(flipped_tensors) == length
    assert flipped_tensors[0].shape == (pdim, original_tensors[2].shape[2], original_tensors[2].shape[1])
    mps.flip_network()
    for orig, now in zip(original_tensors, mps.tensors, strict=False):
        assert np.allclose(orig, now)


def test_shift_orthogonality_center_right() -> None:
    """Test shifting the orthogonality center to the right in an MPS.

    This test verifies that shifting the orthogonality center does not change the rank of the tensors.
    """
    pdim = 2
    shapes = [(pdim, 1, 2), (pdim, 2, 3), (pdim, 3, 3), (pdim, 3, 1)]
    mps = random_mps(shapes)
    mps.set_canonical_form(0)
    assert mps.check_canonical_form() == [0]
    mps.shift_orthogonality_center_right(current_orthogonality_center=0)
    assert mps.check_canonical_form() == [1]
    mps.shift_orthogonality_center_right(current_orthogonality_center=1)
    assert mps.check_canonical_form() == [2]
    mps.shift_orthogonality_center_right(current_orthogonality_center=2)
    assert mps.check_canonical_form() == [3]


def test_shift_orthogonality_center_left() -> None:
    """Test shifting the orthogonality center to the left in an MPS.

    This test ensures that the left shift operation does not alter the rank (3) of the MPS tensors.
    """
    pdim = 2
    shapes = [(pdim, 1, 2), (pdim, 2, 3), (pdim, 3, 3), (pdim, 3, 1)]
    mps = random_mps(shapes)
    mps.set_canonical_form(3)
    assert mps.check_canonical_form() == [3]
    mps.shift_orthogonality_center_left(current_orthogonality_center=3)
    assert mps.check_canonical_form() == [2]
    mps.shift_orthogonality_center_left(current_orthogonality_center=2)
    assert mps.check_canonical_form() == [1]
    mps.shift_orthogonality_center_left(current_orthogonality_center=1)
    assert mps.check_canonical_form() == [0]


@pytest.mark.parametrize("desired_center", [0, 1, 2, 3])
def test_set_canonical_form(desired_center: int) -> None:
    """Test that set_canonical_form correctly sets the MPS into a canonical form without altering tensor shapes.

    This test initializes an MPS with a default state, applies the canonical form procedure, and checks the
    orthogonality.
    """
    pdim = 2
    shapes = [(pdim, 1, 2), (pdim, 2, 4), (pdim, 4, 3), (pdim, 3, 1)]
    mps = random_mps(shapes)
    mps.set_canonical_form(desired_center)
    assert [desired_center] == mps.check_canonical_form()


def test_normalize() -> None:
    """Test that normalize brings an MPS to unit norm without changing tensor ranks.

    This test normalizes an MPS (using 'B' normalization) and verifies that the overall norm is 1 and
    that all tensors remain rank-3.
    """
    length = 4
    pdim = 2
    t1 = rng.random(size=(pdim, 1, 2)).astype(np.complex128)
    t2 = rng.random(size=(pdim, 2, 3)).astype(np.complex128)
    t3 = rng.random(size=(pdim, 3, 3)).astype(np.complex128)
    t4 = rng.random(size=(pdim, 3, 1)).astype(np.complex128)
    mps = MPS(length, [t1, t2, t3, t4], [pdim] * length)

    mps.normalize(form="B")
    assert np.isclose(mps.norm(), 1)
    for tensor in mps.tensors:
        assert tensor.ndim == 3


def test_scalar_product_same_state() -> None:
    """Test that the scalar product of a normalized state with itself equals 1.

    For a normalized product state (here constructed as an MPS in 'random' state), the inner product
    <psi|psi> should be 1.
    """
    psi_mps = MPS(length=3, state="random")
    val = psi_mps.scalar_product(psi_mps)
    np.testing.assert_allclose(val, 1.0, atol=1e-12)


def test_scalar_product_orthogonal_states() -> None:
    """Test that the scalar product between orthogonal product states is 0.

    This test creates two MPS objects initialized in orthogonal states ("zeros" and "ones")
    and verifies that their inner product is 0.
    """
    psi_mps_0 = MPS(length=3, state="zeros")
    psi_mps_1 = MPS(length=3, state="ones")
    val = psi_mps_0.scalar_product(psi_mps_1)
    np.testing.assert_allclose(val, 0.0, atol=1e-12)


def test_scalar_product_partial_site() -> None:
    """Test the scalar product function when specifying a single site.

    For a given site (here site 0 of a 3-site MPS), the scalar product computed by
    scalar_product should equal the direct contraction of the tensor at that site,
    which for a normalized state is 1.
    """
    psi_mps = MPS(length=3, state="x+")
    site = 0
    partial_val = psi_mps.scalar_product(psi_mps, sites=site)
    np.testing.assert_allclose(partial_val, 1.0, atol=1e-12)


def test_local_expect_z_on_zero_state() -> None:
    """Test the local expectation value of the Z observable on a |0> state.

    For the computational basis state |0>, the expectation value of Z is +1.
    This test verifies that local_expect returns +1 for site 0 and site 1 of a 2-qubit MPS
    initialized in the "zeros" state.
    """
    # Pauli-Z in computational basis.
    z = Observable(Z(), 0)

    psi_mps = MPS(length=2, state="zeros")
    val = psi_mps.local_expect(z, sites=0)
    np.testing.assert_allclose(val, 1.0, atol=1e-12)

    z = Observable(Z(), 1)
    val_site1 = psi_mps.local_expect(z, sites=1)
    np.testing.assert_allclose(val_site1, 1.0, atol=1e-12)


def test_local_expect_x_on_plus_state() -> None:
    """Test the local expectation value of the X observable on a |+> state.

    For the |+> state, defined as 1/√2 (|0> + |1>), the expectation value of the X observable is +1.
    This test verifies that local_expect returns +1 for a single-qubit MPS initialized in the "x+" state.
    """
    x = Observable(X(), 0)
    psi_mps = MPS(length=3, state="x+")
    val = psi_mps.local_expect(x, sites=0)
    np.testing.assert_allclose(val, 1.0, atol=1e-12)


def test_measure() -> None:
    """Test that the measure method of an MPS returns the expected observable value.

    This test creates an MPS initialized in the 'x+' state, measures the X observable on site 0,
    and verifies that the measured value is close to 1.
    """
    length = 2
    pdim = 2
    mps = MPS(length=length, physical_dimensions=[pdim] * length, state="x+")
    obs = Observable(X(), 0)
    val = mps.expect(obs)
    assert np.isclose(val, 1)


def test_single_shot() -> None:
    """Test measure_single_shot on an MPS initialized in the |0> state.

    For an MPS representing the state |0> on all qubits, a single-shot measurement should yield 0.
    """
    psi_mps = MPS(length=3, state="zeros")
    val = psi_mps.measure_single_shot()
    np.testing.assert_allclose(val, 0, atol=1e-12)


def test_multi_shot() -> None:
    """Test measure over multiple shots on an MPS initialized in the |1> state.

    This test performs 10 measurement shots on an MPS in the "ones" state and verifies that
    the measurement result for the corresponding basis state (here, 7) is present, while an unexpected
    key (e.g., 0) should not be present.
    """
    psi_mps = MPS(length=3, state="ones")
    shots_dict = psi_mps.measure_shots(shots=10)
    # Assuming that in the "ones" state the measurement outcome is encoded as 7.
    assert shots_dict[7]
    with pytest.raises(KeyError):
        _ = shots_dict[0]


def test_norm() -> None:
    """Test that the norm of an MPS initialized in the 'zeros' state is 1.

    This test checks the norm method of an MPS.
    """
    length = 3
    pdim = 2
    mps = MPS(length=length, physical_dimensions=[pdim] * length, state="zeros")
    val = mps.norm()
    assert val == 1


def test_check_if_valid_mps() -> None:
    """Test that an MPS with consistent bond dimensions passes the validity check.

    This test creates an MPS with carefully constructed tensors and verifies that check_if_valid_mps
    does not raise an exception.
    """
    length = 3
    pdim = 2
    t1 = rng.random(size=(pdim, 1, 2)).astype(np.complex128)
    t2 = rng.random(size=(pdim, 2, 3)).astype(np.complex128)
    t3 = rng.random(size=(pdim, 3, 1)).astype(np.complex128)
    mps = MPS(length, tensors=[t1, t2, t3], physical_dimensions=[pdim] * length)
    mps.check_if_valid_mps()


def test_check_canonical_form_none() -> None:
    """Tests that no canonical form is detected for an MPS in a non-canonical state."""
    mps = random_mps([(2, 1, 2), (2, 2, 3), (2, 3, 1)], normalize=False)
    res = mps.check_canonical_form()
    assert res == []


def test_check_canonical_form_left() -> None:
    """Test that the left canonical form is detected correctly."""
    unitary_mid = unitary_group.rvs(6).reshape((6, 2, 3)).transpose(1, 0, 2)
    unitary_right = unitary_group.rvs(3).reshape(3, 3, 1)
    tensors = [crandn(2, 1, 6), unitary_mid, unitary_right]
    mps = MPS(length=3, tensors=tensors)
    res = mps.check_canonical_form()
    assert 0 in res


def test_check_canonical_form_right() -> None:
    """Test that the right canonical form is detected correctly."""
    unitary_left = unitary_group.rvs(3).astype(np.complex128).reshape(3, 1, 3)
    unitary_mid = unitary_group.rvs(6).astype(np.complex128).reshape((2, 3, 6))
    tensors = [unitary_left, unitary_mid, crandn(2, 6, 1)]
    mps = MPS(length=3, tensors=tensors)
    res = mps.check_canonical_form()
    assert 2 in res


def test_check_canonical_form_middle() -> None:
    """Test that a site canonical form is detected correctly."""
    unitary_left = unitary_group.rvs(3).astype(np.complex128).reshape(3, 1, 3)
    unitary_right = unitary_group.rvs(3).astype(np.complex128).reshape(3, 3, 1)
    tensors = [unitary_left, crandn(2, 3, 3), unitary_right]
    mps = MPS(length=3, tensors=tensors)
    res = mps.check_canonical_form()
    assert 1 in res


def test_check_canonical_form_full() -> None:
    """Test the very special case that all canonical forms are true."""
    delta_left = np.eye(2, dtype=np.complex128).reshape(2, 1, 2)
    delta_right = np.eye(2, dtype=np.complex128).reshape(2, 2, 1)
    delta_mid = np.zeros((2, 2, 2), dtype=np.complex128)
    delta_mid[0, 0, 0] = np.array(1, dtype=np.complex128)
    delta_mid[1, 1, 1] = np.array(1, dtype=np.complex128)
    tensors = [delta_left, delta_mid, delta_right]
    mps = MPS(length=3, tensors=tensors)
    res = mps.check_canonical_form()
    assert res == [0, 1, 2]


def test_convert_to_vector() -> None:
    """Test convert to vector.

    Tests the MPS_to_vector function for various initial states.
    For each state, the expected full state vector is computed as the tensor
    product of the corresponding local state vectors.
    """
    test_states = ["zeros", "ones", "x+", "x-", "y+", "y-"]
    Length = 4  # Use a small number of sites for testing.
    tol = 1e-12

    for state_str in test_states:
        if state_str == "zeros":
            local_state = np.array([1, 0], dtype=complex)
        if state_str == "ones":
            local_state = np.array([0, 1], dtype=complex)
        if state_str == "x+":
            local_state = np.array([1 / np.sqrt(2), 1 / np.sqrt(2)], dtype=complex)
        if state_str == "x-":
            local_state = np.array([1 / np.sqrt(2), -1 / np.sqrt(2)], dtype=complex)
        if state_str == "y+":
            local_state = np.array([1 / np.sqrt(2), 1j / np.sqrt(2)], dtype=complex)
        if state_str == "y-":
            local_state = np.array([1 / np.sqrt(2), -1j / np.sqrt(2)], dtype=complex)

        # Create an MPS for the given state.
        mps = MPS(length=Length, state=state_str)
        psi = mps.to_vec()

        # Construct the expected state vector as the Kronecker product of local states.
        local_states = [local_state for _ in range(Length)]

        expected = np.array(1, dtype=complex)
        for state in local_states:
            expected = np.kron(expected, state)

        assert np.allclose(psi, expected, atol=tol)


def test_convert_to_vector_fidelity() -> None:
    """Test convert to vector.

    Tests the MPS_to_vector function for a circuit input
    """
    num_qubits = 3
    circ = QuantumCircuit(num_qubits)
    circ.h(0)
    circ.cx(0, 1)
    state_vector = np.array([0.70710678, 0, 0, 0.70710678, 0, 0, 0, 0])
    # Define the initial state
    state = MPS(num_qubits, state="zeros")

    # Define the simulation parameters
    sim_params = StrongSimParams(
        observables=[Observable(Z(), site) for site in range(num_qubits)], get_state=True, show_progress=False
    )
    simulator.run(state, circ, sim_params)
    assert sim_params.output_state is not None
    tdvp_state = sim_params.output_state.to_vec()
    np.testing.assert_allclose(1, np.abs(np.vdot(state_vector, tdvp_state)) ** 2)


def test_convert_to_vector_fidelity_long_range() -> None:
    """Test convert to vector.

    Tests the MPS_to_vector function for a circuit input
    """
    num_qubits = 3
    circ = QuantumCircuit(num_qubits)
    circ.h(0)
    circ.cx(0, 2)
    state_vector = np.array([0.70710678, 0, 0, 0, 0, 0.70710678, 0, 0])

    # Define the initial state
    state = MPS(num_qubits, state="zeros")

    # Define the simulation parameters
    sim_params = StrongSimParams(
        observables=[Observable(Z(), site) for site in range(num_qubits)], get_state=True, show_progress=False
    )
    simulator.run(state, circ, sim_params)
    assert sim_params.output_state is not None
    tdvp_state = sim_params.output_state.to_vec()
    np.testing.assert_allclose(1, np.abs(np.vdot(state_vector, tdvp_state)) ** 2)


@pytest.mark.parametrize(("length", "target"), [(6, 16), (7, 7), (9, 8), (10, 3)])
def test_pad_shapes_and_centre(length: int, target: int) -> None:
    """Test that pad_bond_dimension correctly pads the MPS and preserves invariants.

    * the state's norm is unchanged
    * the orthogonality-centre index is [0]
    * every virtual leg has the expected size
      ( powers-of-two "staircase" capped by target_dim )
    """
    mps = MPS(length=length, state="zeros")  # all bonds = 1
    norm_before = mps.norm()

    mps.pad_bond_dimension(target)

    # invariants
    assert np.isclose(mps.norm(), norm_before, atol=1e-12)
    assert mps.check_canonical_form()[0] == 0

    # expected staircase
    for i, T in enumerate(mps.tensors):
        _, chi_l, chi_r = T.shape

        # left (bond i - 1)
        if i == 0:
            left_expected = 1
        else:
            exp_left = min(i, length - i)
            left_expected = min(target, 2**exp_left)

        # right (bond i)
        if i == length - 1:
            right_expected = 1
        else:
            exp_right = min(i + 1, length - 1 - i)
            right_expected = min(target, 2**exp_right)

        assert chi_l == left_expected, f"site {i}: left {chi_l} vs {left_expected}"
        assert chi_r == right_expected, f"site {i}: right {chi_r} vs {right_expected}"


def test_pad_raises_on_shrink() -> None:
    """Test that pad_bond_dimension raises a ValueError when trying to shrink the bond dimension.

    Calling pad_bond_dimension with a *smaller* target than an existing
    bond must raise a ValueError.
    """
    mps = MPS(length=5, state="zeros")
    mps.pad_bond_dimension(4)  # enlarge first

    with pytest.raises(ValueError, match="Target bond dim must be at least current bond dim"):
        mps.pad_bond_dimension(2)  # would shrink - must fail


@pytest.mark.parametrize("center", [0, 1, 2, 3])
def test_truncate_preserves_orthogonality_center_and_canonicity(center: int) -> None:
    """Test that truncation preserves the orthogonality center and canonicity.

    This test checks that after truncation, the orthogonality center remains unchanged.
    """
    # build a simple MPS of length 4
    shapes = [(2, 1, 4)] + [(2, 4, 4)] * 2 + [(2, 4, 1)]
    mps = random_mps(shapes)
    # set an arbitrary initial center
    mps.set_canonical_form(center)
    # record the full state-vector for fidelity check
    before_vec = mps.to_vec()
    # record the center and canonical-split
    before_center = mps.check_canonical_form()[0]
    assert before_center == center

    # do a "no-real" truncation (tiny threshold, generous max bond)
    mps.truncate(threshold=1e-16, max_bond_dim=100)
    after_center = mps.check_canonical_form()[0]
    assert after_center == center

    # fidelity of state stays unity
    after_vec = mps.to_vec()
    overlap = np.abs(np.vdot(before_vec, after_vec)) ** 2
    assert np.isclose(overlap, 1.0, atol=1e-12)

    # also check left/right canonicity around that center
    L = mps.length
    for i in range(before_center):
        # left-canonical test
        A = mps.tensors[i]
        conjA = np.conj(A)
        gram = oe.contract("ijk, ijl->kl", conjA, A)
        # identity on the i-th right bond
        assert np.allclose(gram, np.eye(gram.shape[0]), atol=1e-12)
    for i in range(before_center + 1, L):
        # right-canonical test
        A = mps.tensors[i]
        conjA = np.conj(A)
        gram = oe.contract("ijk, ilk->jl", A, conjA)
        assert np.allclose(gram, np.eye(gram.shape[0]), atol=1e-12)


def test_truncate_reduces_bond_dimensions_and_truncates() -> None:
    """Test that truncation reduces bond dimensions and truncates the MPS.

    This test creates an MPS with large bond dimensions and then truncates it to a smaller size.
    """
    # build an MPS with initially large bonds
    shapes = [(2, 1, 8)] + [(2, 8, 8)] * 3 + [(2, 8, 1)]
    mps = random_mps(shapes)
    # put it into a known canonical form
    mps.set_canonical_form(2)
    # perform a truncation that will cut back to max_bond=3
    mps.truncate(threshold=1e-12, max_bond_dim=3)

    # check validity and that every bond dim <= 3
    mps.check_if_valid_mps()
    for _tensor in mps.tensors:
        pass
    for T in mps.tensors:
        _, bond_left, bond_right = T.shape
        assert bond_left <= 3
        assert bond_right <= 3


def _bell_pair_mps() -> MPS:
    """Auxiliary function to create a Bell-pair MPS.

    Construct a 2-site MPS for the Bell state (|00> + |11>)/√2.
    Contracting the bond yields θ = diag(1/√2, 1/√2).

    Shapes:
        A: (phys=2, left=1, right=2)
        B: (phys=2, left=2, right=1)

    Returns:
        MPS: The product-state MPS.
    """
    A = np.zeros((2, 1, 2), dtype=complex)
    B = np.zeros((2, 2, 1), dtype=complex)

    # A encodes 1/√2 on |0> with bond 0, and 1/√2 on |1> with bond 1
    A[0, 0, 0] = 1 / np.sqrt(2)
    A[1, 0, 1] = 1 / np.sqrt(2)

    # B routes bond 0 -> |0>, bond 1 -> |1>
    B[0, 0, 0] = 1.0
    B[1, 1, 0] = 1.0

    return MPS(length=2, tensors=[A, B], physical_dimensions=[2, 2])


def _product_state_mps(length: int) -> MPS:
    """Construct a product-state MPS |0…0⟩ with all bonds = 1.

    Returns:
        MPS: The product-state MPS.
    """
    pdim = 2
    tensors = []
    for _ in range(length):
        T = np.zeros((pdim, 1, 1), dtype=complex)
        T[0, 0, 0] = 1.0  # |0>
        tensors.append(T)
    return MPS(length=length, tensors=tensors, physical_dimensions=[pdim] * length)


def test_get_max_bond() -> None:
    """get_max_bond reports max over index-0/2 across tensors."""
    # Shapes chosen so the per-tensor max(phys_dim, right_bond) are 3, 4, 2 → global 4
    t1 = np.zeros((2, 1, 3), dtype=complex)
    t2 = np.zeros((2, 3, 4), dtype=complex)
    t3 = np.zeros((2, 4, 1), dtype=complex)
    mps = MPS(length=3, tensors=[t1, t2, t3], physical_dimensions=[2, 2, 2])

    assert mps.get_max_bond() == 4


def test_get_total_bond() -> None:
    """get_total_bond sums internal left bonds over tensors[1:]."""
    # Left bonds (2nd index) of tensors[1:] are 3 and 4 → total 7
    t1 = np.zeros((2, 1, 3), dtype=complex)
    t2 = np.zeros((2, 3, 4), dtype=complex)
    t3 = np.zeros((2, 4, 1), dtype=complex)
    mps = MPS(length=3, tensors=[t1, t2, t3], physical_dimensions=[2, 2, 2])

    assert mps.get_total_bond() == 7


def test_get_cost() -> None:
    """get_cost sums cubes of internal left bonds over tensors[1:]."""
    # Cubes: 3^3 + 4^3 = 27 + 64 = 91
    t1 = np.zeros((2, 1, 3), dtype=complex)
    t2 = np.zeros((2, 3, 4), dtype=complex)
    t3 = np.zeros((2, 4, 1), dtype=complex)
    mps = MPS(length=3, tensors=[t1, t2, t3], physical_dimensions=[2, 2, 2])

    assert mps.get_cost() == 91


def test_get_entropy_zero_for_product_cut() -> None:
    """get_entropy returns 0 on a product state (bond dim = 1)."""
    mps = _product_state_mps(4)
    ent = mps.get_entropy([1, 2])  # nearest-neighbor cut
    assert isinstance(ent, np.float64)
    assert np.isclose(ent, 0.0, atol=1e-12)


def test_get_entropy_bell_pair_ln2() -> None:
    """get_entropy across the Bell cut equals ln(2)."""
    mps = _bell_pair_mps()
    ent = mps.get_entropy([0, 1])
    assert np.isclose(ent, np.log(2.0), atol=1e-12)


def test_get_entropy_asserts_on_non_adjacent_or_wrong_len() -> None:
    """get_entropy asserts on invalid site lists."""
    mps = _product_state_mps(4)
    with pytest.raises(AssertionError):
        _ = mps.get_entropy([1])  # wrong length
    with pytest.raises(AssertionError):
        _ = mps.get_entropy([1, 3])  # non-adjacent


def test_get_schmidt_spectrum_product_padding() -> None:
    """get_schmidt_spectrum returns [1, nan, …] for product cut; length=500."""
    mps = _product_state_mps(3)
    spec = mps.get_schmidt_spectrum([0, 1])

    assert isinstance(spec, np.ndarray)
    assert spec.dtype == np.float64
    assert spec.shape == (500,)
    assert np.isclose(spec[0], 1.0, atol=1e-12)
    # the remainder must be NaN
    assert np.all(np.isnan(spec[1:]))


def test_get_schmidt_spectrum_bell_pair_values_and_padding() -> None:
    """get_schmidt_spectrum on Bell pair yields two equal singular values then NaNs."""
    mps = _bell_pair_mps()
    spec = mps.get_schmidt_spectrum([0, 1])

    assert spec.shape == (500,)
    # Two non-NaN entries ≈ 1/√2, rest NaN
    non_nan = spec[~np.isnan(spec)]
    assert non_nan.size == 2
    assert np.allclose(non_nan, 1 / np.sqrt(2), atol=1e-12)
    assert np.all(np.isnan(spec[2:]))


def test_get_schmidt_spectrum_asserts_on_invalid_sites() -> None:
    """get_schmidt_spectrum asserts on non-adjacent or wrong-length site lists."""
    mps = _product_state_mps(5)
    with pytest.raises(AssertionError):
        _ = mps.get_schmidt_spectrum([2])  # wrong length
    with pytest.raises(AssertionError):
        _ = mps.get_schmidt_spectrum([1, 3])  # non-adjacent


def test_evaluate_observables_diagnostics_and_meta_then_pvm_separately() -> None:
    """Evaluate diagnostics/meta (no PVM) and PVM in separate calls to satisfy params typing/rules.

    For |0000⟩ product MPS:
      - runtime_cost = Σ_{i≥1} bond_left(i)^3 = 1^3 * 3 = 3
      - total_bond  = Σ_{i≥1} bond_left(i)   = 1   * 3 = 3
      - max_bond    = max over (phys_dim/right_bond) = 2
      - entropy(1,2) = 0
      - schmidt_spectrum(1,2) = length-500 vector with [1, nan, ...]
      - pvm("0000") = 1  (checked in a separate params object to avoid mixing)
    """
    mps = _product_state_mps(4)

    # ---- diagnostics + meta (NO PVM here) ----
    diagnostics_and_meta: list[Observable] = [
        Observable(GateLibrary.runtime_cost(), 0),
        Observable(GateLibrary.max_bond(), 0),
        Observable(GateLibrary.total_bond(), 0),
        Observable(GateLibrary.entropy(), [1, 2]),
        Observable(GateLibrary.schmidt_spectrum(), [1, 2]),
    ]
    sim_diag = AnalogSimParams(diagnostics_and_meta, elapsed_time=0.1, dt=0.1, show_progress=False)

    results_diag = np.empty((len(diagnostics_and_meta), 2), dtype=object)
    mps.evaluate_observables(sim_diag, results_diag, column_index=0)

    # Diagnostics
    # Ordering based on sorted_observables
    assert results_diag[2, 0] == 3  # runtime_cost
    assert results_diag[3, 0] == 2  # max_bond
    assert results_diag[4, 0] == 3  # total_bond

    # Entropy
    assert isinstance(results_diag[0, 0], (float, np.floating))
    assert np.isclose(results_diag[0, 0], 0.0, atol=1e-12)

    # Schmidt spectrum
    spec = results_diag[1, 0]
    assert isinstance(spec, np.ndarray)
    assert spec.shape == (500,)
    assert np.isclose(spec[0], 1.0, atol=1e-12)
    assert np.all(np.isnan(spec[1:]))

    # ---- PVM ONLY (no mixing) ----
    pvm_only = [Observable(GateLibrary.pvm("0000"), 0)]
    sim_pvm = AnalogSimParams(pvm_only, elapsed_time=0.1, dt=0.1, show_progress=False)

    results_pvm = np.empty((len(pvm_only), 1), dtype=object)
    mps.evaluate_observables(sim_pvm, results_pvm, column_index=0)

    assert results_pvm[0, 0] == 1


def test_evaluate_observables_local_ops_and_center_shifts() -> None:
    """Evaluate local observables over increasing sites to exercise rightward shifts.

    For |0000⟩:
      - ⟨Z⟩ at sites 0,1,3 is +1
      - ⟨X⟩ at site 2 is 0
    The observable order [Z(0), Z(1), X(2), Z(3)] forces center shifts 0→1→2→3.
    """
    mps = _product_state_mps(4)

    obs_seq: list[Observable] = [
        Observable(GateLibrary.z(), 0),
        Observable(GateLibrary.z(), 1),
        Observable(GateLibrary.x(), 2),
        Observable(GateLibrary.z(), 3),
    ]
    sim_params = AnalogSimParams(obs_seq, elapsed_time=0.1, dt=0.1, show_progress=False)

    results = np.empty((len(obs_seq), 3), dtype=np.float64)
    mps.evaluate_observables(sim_params, results, column_index=2)

    z0, z1, x2, z3 = (results[i, 2] for i in range(4))
    assert np.isclose(z0, 1.0, atol=1e-12)
    assert np.isclose(z1, 1.0, atol=1e-12)
    assert np.isclose(x2, 0.0, atol=1e-12)
    assert np.isclose(z3, 1.0, atol=1e-12)


def test_evaluate_observables_meta_validation_errors() -> None:
    """Meta-observable input validation: wrong length and non-adjacent sites must assert."""
    mps = _product_state_mps(4)

    # Wrong length (entropy expects exactly two adjacent indices)
    sim_bad_len = AnalogSimParams(
        [Observable(GateLibrary.entropy(), [1])], elapsed_time=0.1, dt=0.1, show_progress=False
    )
    results_len = np.empty((1, 1), dtype=np.float64)
    with pytest.raises(AssertionError):
        mps.evaluate_observables(sim_bad_len, results_len, column_index=0)

    # Non-adjacent Schmidt cut
    sim_non_adj = AnalogSimParams(
        [Observable(GateLibrary.schmidt_spectrum(), [0, 2])], elapsed_time=0.1, dt=0.1, show_progress=False
    )
    results_adj = np.empty((1, 1), dtype=object)
    with pytest.raises(AssertionError):
        mps.evaluate_observables(sim_non_adj, results_adj, column_index=0)
