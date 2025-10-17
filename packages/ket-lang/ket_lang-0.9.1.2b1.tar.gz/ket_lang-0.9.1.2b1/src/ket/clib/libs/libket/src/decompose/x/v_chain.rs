// SPDX-FileCopyrightText: 2025 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use itertools::chain;

use crate::{
    decompose::AuxMode,
    ir::qubit::LogicalQubit,
    prelude::{QuantumGate, U4Gate},
};

use super::{c2to4x, CXMode};

fn v_chain_action(
    control: &[LogicalQubit],
    aux_qubit: &[LogicalQubit],
    target: LogicalQubit,
    u4_gate: U4Gate,
    approximated: u8,
    left_right: (bool, bool),
    cx_mode: CXMode,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    let n = control.len();
    if n <= match cx_mode {
        CXMode::C2X => 2,
        CXMode::C3X => 3,
    } {
        return c2to4x::c1to4x(
            control,
            target,
            u4_gate,
            if matches!(cx_mode, CXMode::C3X) {
                false
            } else {
                approximated == 0
            },
        );
    }

    let a = aux_qubit.len();

    let c_n_index = n - match cx_mode {
        CXMode::C2X => 1,
        CXMode::C3X => 2,
    };

    let edge_ctrl: Vec<LogicalQubit> = control[c_n_index..]
        .iter()
        .cloned()
        .chain([*aux_qubit.last().unwrap()])
        .collect();

    let edge = c2to4x::c1to4x(&edge_ctrl, target, u4_gate, approximated == 0);
    let approximated = if approximated != 0 {
        approximated - 1
    } else {
        0
    };

    match left_right {
        (true, true) => chain![
            edge.clone(),
            v_chain_action(
                &control[..c_n_index],
                &aux_qubit[..a - 1],
                *aux_qubit.last().unwrap(),
                u4_gate,
                approximated,
                left_right,
                cx_mode,
            ),
            edge
        ]
        .collect(),
        (true, false) => chain![
            edge,
            v_chain_action(
                &control[..c_n_index],
                &aux_qubit[..a - 1],
                *aux_qubit.last().unwrap(),
                u4_gate,
                approximated,
                left_right,
                cx_mode,
            ),
        ]
        .collect(),
        (false, true) => chain![
            v_chain_action(
                &control[..c_n_index],
                &aux_qubit[..a - 1],
                *aux_qubit.last().unwrap(),
                u4_gate,
                approximated,
                left_right,
                cx_mode,
            ),
            edge
        ]
        .collect(),
        (false, false) => panic!("invalid parameters for v_chain_c2x_action"),
    }
}

pub(crate) fn v_chain(
    control: &[LogicalQubit],
    aux_qubit: &[LogicalQubit],
    target: LogicalQubit,
    u4_gate: U4Gate,
    aux_mode: AuxMode,
    cx_mode: CXMode,
    approximated: bool,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    let n = control.len();
    if n <= 3 {
        return c2to4x::c1to4x(control, target, u4_gate, approximated);
    }

    let a = aux_qubit.len();
    let (action, reset) = match aux_mode {
        AuxMode::Clean => ((false, true), (true, false)),
        AuxMode::Dirty => ((true, true), (true, true)),
    };

    chain![
        v_chain_action(
            control,
            aux_qubit,
            target,
            u4_gate,
            match cx_mode {
                CXMode::C2X => 1,
                CXMode::C3X => 2,
            },
            action,
            cx_mode,
        ),
        v_chain_action(
            &control[..n - match cx_mode {
                CXMode::C2X => 1,
                CXMode::C3X => 2,
            }],
            &aux_qubit[..a - 1],
            aux_qubit[a - 1],
            u4_gate,
            match cx_mode {
                CXMode::C2X => 0,
                CXMode::C3X => 1,
            },
            reset,
            cx_mode,
        )
    ]
    .collect()
}
