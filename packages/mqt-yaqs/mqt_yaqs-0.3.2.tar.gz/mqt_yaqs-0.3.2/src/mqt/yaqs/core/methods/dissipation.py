# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Dissipative sweep of the Tensor Jump Method.

This module implements a function to apply dissipation to a quantum state represented as an MPS.
The dissipative operator is computed from a noise model by exponentiating a weighted sum of jump operators,
and is then applied to each tensor in the MPS via tensor contraction. If no noise is present or if all
noise strengths are zero, the MPS is simply shifted to its canonical form.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import opt_einsum as oe
from scipy.linalg import expm

from ..methods.tdvp import merge_mps_tensors, split_mps_tensor

if TYPE_CHECKING:
    from ..data_structures.networks import MPS
    from ..data_structures.noise_model import NoiseModel
    from ..data_structures.simulation_parameters import AnalogSimParams, StrongSimParams, WeakSimParams


def is_adjacent(proc: dict[str, Any]) -> bool:
    """Return True if the two-site process targets nearest neighbors.

    Assumes the process is two-site and checks |i-j| == 1.
    """
    s = proc["sites"]
    return bool(abs(s[1] - s[0]) == 1)


def is_longrange(proc: dict[str, Any]) -> bool:
    """Return True if the two-site process is long-range (non-neighbor)."""
    s = proc["sites"]
    return bool(abs(s[1] - s[0]) > 1)


def is_pauli(proc: dict[str, Any]) -> bool:
    """Return True if the process is a Pauli process."""
    return bool(
        proc["name"]
        in {
            "pauli_x",
            "pauli_y",
            "pauli_z",
            "crosstalk_xx",
            "crosstalk_yy",
            "crosstalk_zz",
            "crosstalk_xy",
            "crosstalk_yx",
            "crosstalk_zy",
            "crosstalk_zx",
            "crosstalk_yz",
            "crosstalk_xz",
        }
    )


def apply_dissipation(
    state: MPS,
    noise_model: NoiseModel | None,
    dt: float,
    sim_params: AnalogSimParams | StrongSimParams | WeakSimParams,
) -> None:
    """Apply dissipation to the system state using a given noise model and time step.

    This function modifies the state tensors of an MPS by applying a dissipative operator
    that is calculated from the noise model's jump operators and strengths. The operator is
    computed by exponentiating a matrix derived from these jump operators, and then applied to
    each tensor in the state using an Einstein summation contraction.

    Args:
        state: The Matrix Product State representing the current state of the system.
        noise_model: The noise model containing jump operators and their
            corresponding strengths. If None or if all strengths are zero, no dissipation is applied.
        dt: The time step for the evolution, used in the exponentiation of the dissipative operator.
        sim_params: Simulation parameters that include settings.

    Notes:
        - If no noise is present (i.e. `noise_model` is None or all noise strengths are zero),
          the function shifts the orthogonality center of the MPS tensors and returns early.
        - The dissipation operator A is calculated as a sum over each jump operator, where each
          term is given by (noise strength) * (conjugate transpose of the jump operator) multiplied
          by the jump operator.
        - The dissipative operator is computed using the matrix exponential `expm(-0.5 * dt * A)`.
        - The operator is then applied to each tensor in the MPS via a contraction using `opt_einsum`.
    """
    if noise_model is None or all(proc["strength"] == 0 for proc in noise_model.processes):
        for i in reversed(range(state.length)):
            state.shift_orthogonality_center_left(current_orthogonality_center=i, decomposition="QR")
        return

    for i in reversed(range(state.length)):
        # 1. Apply all 1-site dissipators on site i
        for process in noise_model.processes:
            if len(process["sites"]) == 1 and process["sites"][0] == i:
                gamma = process["strength"]
                if is_pauli(process):
                    dissipative_factor = np.exp(-0.5 * dt * gamma)
                    state.tensors[i] *= dissipative_factor
                else:
                    jump_op_mat = process["matrix"]
                    mat = np.conj(jump_op_mat).T @ jump_op_mat
                    dissipative_op = expm(-0.5 * dt * gamma * mat)
                    state.tensors[i] = oe.contract("ab, bcd->acd", dissipative_op, state.tensors[i])

            processes_here = [
                process for process in noise_model.processes if len(process["sites"]) == 2 and process["sites"][1] == i
            ]
        # 2. Apply all 2-site dissipators acting on sites (i-1, i)
        if i != 0:
            for process in processes_here:
                gamma = process["strength"]
                if is_pauli(process):
                    dissipative_factor = np.exp(-0.5 * dt * gamma)
                    state.tensors[i] *= dissipative_factor

                elif is_longrange(process):
                    msg = "Non-Pauli Long-range processes are not implemented yet"
                    raise NotImplementedError(msg)
                else:
                    jump_op_mat = process["matrix"]
                    mat = np.conj(jump_op_mat).T @ jump_op_mat
                    dissipative_op = expm(-0.5 * dt * gamma * mat)

                    merged_tensor = merge_mps_tensors(state.tensors[i - 1], state.tensors[i])
                    merged_tensor = oe.contract("ab, bcd->acd", dissipative_op, merged_tensor)

                    # singular values always contracted right
                    # since ortho center is shifted to the left after loop
                    tensor_left, tensor_right = split_mps_tensor(
                        merged_tensor,
                        "right",
                        sim_params,
                        [state.physical_dimensions[i - 1], state.physical_dimensions[i]],
                        dynamic=False,
                    )
                    state.tensors[i - 1], state.tensors[i] = tensor_left, tensor_right

        # Shift orthogonality center
        if i != 0:
            state.shift_orthogonality_center_left(current_orthogonality_center=i, decomposition="SVD")
