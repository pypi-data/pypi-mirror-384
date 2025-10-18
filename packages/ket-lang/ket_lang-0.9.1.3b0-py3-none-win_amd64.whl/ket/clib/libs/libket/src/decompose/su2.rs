// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use std::{f64::consts::FRAC_PI_4, f64::consts::PI};

use itertools::chain;

use crate::{
    execution::U4Gate,
    ir::{
        gate::{matrix_dot, Matrix, QuantumGate},
        qubit::LogicalQubit,
    },
};

use super::{u2::cu2, util::zyz, x, AuxMode, DepthMode};

fn c2xp(
    a: LogicalQubit,
    b: LogicalQubit,
    c: LogicalQubit,
    u4_gate: U4Gate,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    chain![
        [
            (QuantumGate::Hadamard, b, None),
            (QuantumGate::td(), b, None)
        ],
        u4_gate.cnot(a, b),
        [(QuantumGate::t(), b, None)],
        u4_gate.cnot(c, b),
        [(QuantumGate::td(), b, None)],
        u4_gate.cnot(a, b),
        [
            (QuantumGate::t(), b, None),
            (QuantumGate::Hadamard, b, None),
        ]
    ]
    .collect()
}

fn c2iz(
    a: LogicalQubit,
    b: LogicalQubit,
    c: LogicalQubit,
    u4_gate: U4Gate,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    chain![
        [(QuantumGate::td(), c, None)],
        u4_gate.cnot(a, c),
        [(QuantumGate::t(), c, None)],
        u4_gate.cnot(b, c),
        [(QuantumGate::td(), c, None)],
        u4_gate.cnot(a, c),
        [(QuantumGate::t(), c, None)],
        u4_gate.cnot(b, c),
    ]
    .collect()
}

pub(crate) fn cz_ap(
    control: &[LogicalQubit],
    aux_qubits: &[LogicalQubit],
    target: LogicalQubit,
    u4_gate: U4Gate,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    let n = control.len();
    let a = aux_qubits.len();
    if n == 1 {
        u4_gate.cz(control[0], target)
    } else if n == 2 {
        c2iz(control[0], control[1], target, u4_gate)
    } else {
        chain![
            c2xp(
                *control.last().unwrap(),
                *aux_qubits.last().unwrap(),
                target,
                u4_gate
            ),
            cz_ap(
                &control[..n - 1],
                &aux_qubits[..a - 1],
                *aux_qubits.last().unwrap(),
                u4_gate
            ),
            c2xp(
                *control.last().unwrap(),
                *aux_qubits.last().unwrap(),
                target,
                u4_gate
            )
        ]
        .collect()
    }
}

pub(super) fn linear(
    gate: QuantumGate,
    control: &[LogicalQubit],
    target: LogicalQubit,
    u4_gate: U4Gate,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    let (a4, theta) = match gate {
        QuantumGate::RotationX(theta) => (vec![], theta.value()),
        QuantumGate::RotationY(theta) => {
            (vec![QuantumGate::Hadamard, QuantumGate::s()], theta.value())
        }
        QuantumGate::RotationZ(theta) => (vec![QuantumGate::Hadamard], theta.value()),
        QuantumGate::Hadamard => (vec![QuantumGate::RotationY(FRAC_PI_4.into())], PI),
        _ => panic!("Not an SU2 gate"),
    };

    let a2 = QuantumGate::RotationX((-theta / 4.0).into());
    let a3 = a2.inverse();
    let a1: Vec<_> = chain![[a3], a4.iter().rev().map(|gate| gate.inverse())].collect();

    let n = control.len() / 2;
    let c1 = &control[..n];
    let c2 = &control[n..];

    chain![
        a4.iter().map(|gate| (*gate, target, None)),
        cz_ap(c1, c2, target, u4_gate),
        [(a2, target, None)],
        cz_ap(c2, c1, target, u4_gate),
        [(a3, target, None)],
        cz_ap(c1, c2, target, u4_gate)
            .into_iter()
            .rev()
            .map(|(gate, target, control)| (gate.inverse(), target, control)),
        [(a2, target, None)],
        cz_ap(c2, c1, target, u4_gate)
            .into_iter()
            .rev()
            .map(|(gate, target, control)| (gate.inverse(), target, control)),
        a1.iter().map(|gate| (*gate, target, None)),
    ]
    .collect()
}

fn log(
    matrix: Matrix,
    control: &[LogicalQubit],
    target: LogicalQubit,
    u4_gate: U4Gate,
    approximated: bool,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    let n = control.len();
    let (_, beta, gamma, delta) = zyz(matrix);

    let c = QuantumGate::RotationZ(((delta - beta) / 2.0).into()).matrix();
    let b = matrix_dot(
        &QuantumGate::RotationZ((-(delta + beta) / 2.0).into()).matrix(),
        &QuantumGate::RotationY((-gamma / 2.0).into()).matrix(),
    );
    let a = matrix_dot(
        &QuantumGate::RotationY((gamma / 2.0).into()).matrix(),
        &QuantumGate::RotationZ(beta.into()).matrix(),
    );

    cu2(c, control[n - 1], target, u4_gate)
        .into_iter()
        .chain(x::single_aux::decompose(
            &control[..n - 1],
            control[n - 1],
            target,
            u4_gate,
            AuxMode::Dirty,
            DepthMode::Log,
            approximated,
        ))
        .chain(cu2(b, control[n - 1], target, u4_gate))
        .chain(x::single_aux::decompose(
            &control[..n - 1],
            control[n - 1],
            target,
            u4_gate,
            AuxMode::Dirty,
            DepthMode::Log,
            approximated,
        ))
        .chain(cu2(a, control[n - 1], target, u4_gate))
        .collect()
}

pub(crate) fn decompose(
    gate: QuantumGate,
    control: &[LogicalQubit],
    target: LogicalQubit,
    u4_gate: U4Gate,
    depth_mode: DepthMode,
    approximated: bool,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    match depth_mode {
        DepthMode::Log => log(gate.su2_matrix(), control, target, u4_gate, approximated),
        DepthMode::Linear => linear(gate, control, target, u4_gate),
    }
}
