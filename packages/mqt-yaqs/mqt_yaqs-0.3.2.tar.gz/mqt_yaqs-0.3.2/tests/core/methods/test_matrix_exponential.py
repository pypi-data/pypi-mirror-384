# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Tests for Krylov subspace methods used for matrix exponential calculations.

This module provides unit tests for the internal functions `lanczos_iteration` and `expm_krylov`,
which are utilized in YAQS for efficient computation of matrix exponentials.

The tests verify that:
- The Lanczos iteration correctly generates orthonormal bases and respects expected shapes.
- Early termination of the Lanczos iteration occurs appropriately when convergence conditions are met.
- Krylov subspace approximations to matrix exponentials match exact computations when the subspace dimension
  equals the full space, and remain within acceptable error bounds for smaller subspace dimensions.

These tests ensure reliable numerical behavior and accuracy of Krylov-based algorithms within YAQS.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy.linalg import norm
from scipy.linalg import expm

from mqt.yaqs.core.methods.matrix_exponential import expm_krylov, lanczos_iteration

if TYPE_CHECKING:
    from numpy.typing import NDArray


def test_lanczos_iteration_small() -> None:
    """Test small Lanczos.

    Check that lanczos_iteration produces correct shapes and orthonormal vectors
    for a small 2x2 Hermitian matrix.
    """
    mat = np.array([[2.0, 1.0], [1.0, 3.0]])

    def matrix_free_operator(x: NDArray[np.complex128]) -> NDArray[np.complex128]:
        return mat @ x

    initial_vec = np.array([1.0, 1.0], dtype=complex)
    lanczos_iterations = 2

    alpha, beta, lanczos_mat = lanczos_iteration(matrix_free_operator, initial_vec, lanczos_iterations)
    # alpha should have shape (2,), beta shape (1,), and V shape (2, 2)
    assert alpha.shape == (2,)
    assert beta.shape == (1,)
    assert lanczos_mat.shape == (2, 2)

    # Check first Lanczos vector is normalized.
    np.testing.assert_allclose(norm(lanczos_mat[:, 0]), 1.0, atol=1e-12)
    # Check second vector is orthogonal to the first.
    dot_01 = np.vdot(lanczos_mat[:, 0], lanczos_mat[:, 1])
    np.testing.assert_allclose(dot_01, 0.0, atol=1e-12)
    np.testing.assert_allclose(norm(lanczos_mat[:, 1]), 1.0, atol=1e-12)


def test_lanczos_early_termination() -> None:
    """Test Lanczos early termination.

    Check that lanczos_iteration terminates early when beta[j] is nearly zero.

    Using a diagonal matrix so that if the starting vector is an eigenvector, the
    iteration can terminate early. In this case, with initial_vec aligned with [1, 0],
    the iteration should stop after one step.
    """
    mat = np.diag([1.0, 2.0])

    def matrix_free_operator(x: NDArray[np.complex128]) -> NDArray[np.complex128]:
        return mat @ x

    initial_vec = np.array([1.0, 0.0], dtype=complex)
    lanczos_iterations = 5

    alpha, beta, lanczos_mat = lanczos_iteration(matrix_free_operator, initial_vec, lanczos_iterations)
    # Expect termination after 1 iteration: alpha shape (1,), beta shape (0,), V shape (2, 1)
    assert alpha.shape == (1,)
    assert beta.shape == (0,)
    assert lanczos_mat.shape == (2, 1), "Should have truncated V to 1 Lanczos vector."


def test_expm_krylov_2x2_exact() -> None:
    """Test exact Krylov matrix exponential.

    For a 2x2 Hermitian matrix, when lanczos_iterations equals the full dimension (2),
    expm_krylov should yield a result that matches the direct matrix exponential exactly.
    """
    mat = np.array([[2.0, 1.0], [1.0, 3.0]])

    def matrix_free_operator(x: NDArray[np.complex128]) -> NDArray[np.complex128]:
        return mat @ x

    v = np.array([1.0, 0.0], dtype=complex)
    dt = 0.1
    lanczos_iterations = 2  # full subspace

    approx = expm_krylov(matrix_free_operator, v, dt, lanczos_iterations)
    direct = expm(-1j * dt * mat) @ v

    np.testing.assert_allclose(
        approx,
        direct,
        atol=1e-12,
        err_msg="Krylov expm approximation should match direct exponential for 2x2, lanczos_iterations=2.",
    )


def test_expm_krylov_smaller_subspace() -> None:
    """Test small subspace Krylov matrix exponential.

    For a 2x2 Hermitian matrix, if lanczos_iterations is less than the full dimension,
    the expm_krylov result will be approximate. For small dt, the approximation
    should be within a tolerance of 1e-1.
    """
    mat = np.array([[2.0, 1.0], [1.0, 3.0]])

    def matrix_free_operator(x: NDArray[np.complex128]) -> NDArray[np.complex128]:
        return mat @ x

    v = np.array([1.0, 1.0], dtype=complex)
    dt = 0.05
    lanczos_iterations = 1  # subspace dimension smaller than the full space

    approx = expm_krylov(matrix_free_operator, v, dt, lanczos_iterations)
    direct = expm(-1j * dt * mat) @ v

    np.testing.assert_allclose(
        approx,
        direct,
        atol=1e-1,
        err_msg="Krylov with subspace < dimension might be approximate, but should be within 1e-1 for small dt.",
    )
