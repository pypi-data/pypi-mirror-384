// SPDX-FileCopyrightText: 2025 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use std::f64::consts::{FRAC_PI_2, FRAC_PI_4, FRAC_PI_8};

use itertools::chain;

use crate::{
    ir::qubit::LogicalQubit,
    prelude::{QuantumGate, U4Gate},
};

fn c2x(
    control_0: LogicalQubit,
    control_1: LogicalQubit,
    target: LogicalQubit,
    u4_gate: U4Gate,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    chain![
        [(QuantumGate::Hadamard, target, None)],
        u4_gate.cnot(control_1, target),
        [(QuantumGate::td(), target, None)],
        u4_gate.cnot(control_0, target),
        [(QuantumGate::t(), target, None)],
        u4_gate.cnot(control_1, target),
        [(QuantumGate::td(), target, None)],
        u4_gate.cnot(control_0, target),
        [
            (QuantumGate::t(), control_1, None),
            (QuantumGate::t(), target, None),
        ],
        u4_gate.cnot(control_0, control_1),
        [
            (QuantumGate::Hadamard, target, None),
            (QuantumGate::t(), control_0, None),
            (QuantumGate::td(), control_1, None),
        ],
        u4_gate.cnot(control_0, control_1)
    ]
    .collect()
}

fn c3x(
    control_0: LogicalQubit,
    control_1: LogicalQubit,
    control_2: LogicalQubit,
    target: LogicalQubit,
    u4_gate: U4Gate,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    chain![
        [
            (QuantumGate::Hadamard, target, None),
            (QuantumGate::sqrt_t(), control_0, None),
            (QuantumGate::sqrt_t(), control_1, None),
            (QuantumGate::sqrt_t(), control_2, None),
            (QuantumGate::sqrt_t(), target, None),
        ],
        u4_gate.cnot(control_0, control_1),
        [(QuantumGate::sqrt_td(), control_1, None)],
        u4_gate.cnot(control_0, control_1),
        u4_gate.cnot(control_1, control_2),
        [(QuantumGate::sqrt_td(), control_2, None)],
        u4_gate.cnot(control_0, control_2),
        [(QuantumGate::sqrt_t(), control_2, None)],
        u4_gate.cnot(control_1, control_2),
        [(QuantumGate::sqrt_td(), control_2, None)],
        u4_gate.cnot(control_0, control_2),
        u4_gate.cnot(control_2, target),
        [(QuantumGate::sqrt_td(), target, None)],
        u4_gate.cnot(control_1, target),
        [(QuantumGate::sqrt_t(), target, None)],
        u4_gate.cnot(control_2, target),
        [(QuantumGate::sqrt_td(), target, None)],
        u4_gate.cnot(control_0, target),
        [(QuantumGate::sqrt_t(), target, None)],
        u4_gate.cnot(control_2, target),
        [(QuantumGate::sqrt_td(), target, None)],
        u4_gate.cnot(control_1, target),
        [(QuantumGate::sqrt_t(), target, None)],
        u4_gate.cnot(control_2, target),
        [(QuantumGate::sqrt_td(), target, None)],
        u4_gate.cnot(control_0, target),
        [(QuantumGate::Hadamard, target, None)],
    ]
    .collect()
}

fn c4x(
    control_0: LogicalQubit,
    control_1: LogicalQubit,
    control_2: LogicalQubit,
    control_3: LogicalQubit,
    target: LogicalQubit,
    u4_gate: U4Gate,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    chain![
        [(QuantumGate::Hadamard, target, None)],
        cp(FRAC_PI_2, control_3, target, u4_gate),
        [(QuantumGate::Hadamard, target, None)],
        c3x_ap(control_0, control_1, control_2, control_3, u4_gate),
        [(QuantumGate::Hadamard, target, None)],
        cp(-FRAC_PI_2, control_3, target, u4_gate),
        [(QuantumGate::Hadamard, target, None)],
        c3x_ap(control_0, control_1, control_2, control_3, u4_gate)
            .into_iter()
            .rev()
            .map(|(gate, target, control)| (gate.inverse(), target, control))
            .collect::<Vec<_>>(),
        c3sx(control_0, control_1, control_2, target, u4_gate)
    ]
    .collect()
}

pub(crate) fn cp(
    lambda: f64,
    control: LogicalQubit,
    target: LogicalQubit,
    u4_gate: U4Gate,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    chain![
        [(QuantumGate::Phase((lambda / 2.0).into()), control, None)],
        u4_gate.cnot(control, target),
        [(QuantumGate::Phase((-lambda / 2.0).into()), target, None)],
        u4_gate.cnot(control, target),
        [(QuantumGate::Phase((lambda / 2.0).into()), target, None)],
    ]
    .collect()
}

fn c3sx(
    control_0: LogicalQubit,
    control_1: LogicalQubit,
    control_2: LogicalQubit,
    target: LogicalQubit,
    u4_gate: U4Gate,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    chain![
        [(QuantumGate::Hadamard, target, None)],
        cp(FRAC_PI_8, control_0, target, u4_gate),
        [(QuantumGate::Hadamard, target, None)],
        u4_gate.cnot(control_0, control_1),
        [(QuantumGate::Hadamard, target, None)],
        cp(-FRAC_PI_8, control_1, target, u4_gate),
        [(QuantumGate::Hadamard, target, None)],
        u4_gate.cnot(control_0, control_1),
        [(QuantumGate::Hadamard, target, None)],
        cp(FRAC_PI_8, control_1, target, u4_gate),
        [(QuantumGate::Hadamard, target, None)],
        u4_gate.cnot(control_1, control_2),
        [(QuantumGate::Hadamard, target, None)],
        cp(-FRAC_PI_8, control_2, target, u4_gate),
        [(QuantumGate::Hadamard, target, None)],
        u4_gate.cnot(control_0, control_2),
        [(QuantumGate::Hadamard, target, None)],
        cp(FRAC_PI_8, control_2, target, u4_gate),
        [(QuantumGate::Hadamard, target, None)],
        u4_gate.cnot(control_1, control_2),
        [(QuantumGate::Hadamard, target, None)],
        cp(-FRAC_PI_8, control_2, target, u4_gate),
        [(QuantumGate::Hadamard, target, None)],
        u4_gate.cnot(control_0, control_2),
        [(QuantumGate::Hadamard, target, None)],
        cp(FRAC_PI_8, control_2, target, u4_gate),
        [(QuantumGate::Hadamard, target, None)],
    ]
    .collect()
}

fn c3x_ap(
    control_0: LogicalQubit,
    control_1: LogicalQubit,
    control_2: LogicalQubit,
    target: LogicalQubit,
    u4_gate: U4Gate,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    chain![
        [
            (QuantumGate::Hadamard, target, None),
            (QuantumGate::t(), target, None),
        ],
        u4_gate.cnot(control_2, target),
        [
            (QuantumGate::td(), target, None),
            (QuantumGate::Hadamard, target, None),
        ],
        u4_gate.cnot(control_0, target),
        [(QuantumGate::t(), target, None)],
        u4_gate.cnot(control_1, target),
        [(QuantumGate::td(), target, None)],
        u4_gate.cnot(control_0, target),
        [(QuantumGate::t(), target, None)],
        u4_gate.cnot(control_1, target),
        [
            (QuantumGate::td(), target, None),
            (QuantumGate::Hadamard, target, None),
            (QuantumGate::t(), target, None),
        ],
        u4_gate.cnot(control_2, target),
        [
            (QuantumGate::td(), target, None),
            (QuantumGate::Hadamard, target, None),
        ]
    ]
    .collect()
}

fn c2x_ap(
    control_0: LogicalQubit,
    control_1: LogicalQubit,
    target: LogicalQubit,
    u4_gate: U4Gate,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    [(QuantumGate::RotationY((-FRAC_PI_4).into()), target, None)]
        .into_iter()
        .chain(u4_gate.cnot(control_0, target))
        .chain([(QuantumGate::RotationY((-FRAC_PI_4).into()), target, None)])
        .chain(u4_gate.cnot(control_1, target))
        .chain([(QuantumGate::RotationY(FRAC_PI_4.into()), target, None)])
        .chain(u4_gate.cnot(control_0, target))
        .chain([(QuantumGate::RotationY(FRAC_PI_4.into()), target, None)])
        .collect()
}

pub(crate) fn c1to4x(
    control: &[LogicalQubit],
    target: LogicalQubit,
    u4_gate: U4Gate,
    approximated: bool,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    match control.len() {
        1 => u4_gate.cnot(control[0], target),
        2 => {
            if approximated {
                c2x_ap(control[0], control[1], target, u4_gate)
            } else {
                c2x(control[0], control[1], target, u4_gate)
            }
        }
        3 => {
            if approximated {
                c3x_ap(control[0], control[1], control[2], target, u4_gate)
            } else {
                c3x(control[0], control[1], control[2], target, u4_gate)
            }
        }
        4 => c4x(
            control[0], control[1], control[2], control[3], target, u4_gate,
        ),
        n => panic!("C{n}X not supported"),
    }
}
