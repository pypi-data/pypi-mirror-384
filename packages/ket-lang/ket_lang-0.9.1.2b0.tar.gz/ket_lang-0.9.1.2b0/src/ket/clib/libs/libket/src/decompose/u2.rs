// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use std::f64::consts::{FRAC_PI_2, FRAC_PI_4, PI};

use itertools::chain;

use crate::{
    decompose::su2::cz_ap,
    execution::U4Gate,
    ir::{
        gate::{Matrix, QuantumGate},
        qubit::LogicalQubit,
    },
};

use super::{
    util::{exp_gate, zyz},
    x, AuxMode, DepthMode,
};

pub(crate) fn cu2(
    matrix: Matrix,
    control: LogicalQubit,
    target: LogicalQubit,
    u4_gate: U4Gate,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    let (alpha, beta, gamma, delta) = zyz(matrix);

    let mut instructions = vec![
        (QuantumGate::Phase(alpha.into()), control, None),
        (
            QuantumGate::RotationZ(((delta - beta) / 2.0).into()),
            target,
            None,
        ),
    ];
    instructions.extend(u4_gate.cnot(control, target));
    instructions.extend([
        (
            QuantumGate::RotationZ((-(delta + beta) / 2.0).into()),
            target,
            None,
        ),
        (QuantumGate::RotationY((-gamma / 2.0).into()), target, None),
    ]);
    instructions.extend(u4_gate.cnot(control, target));
    instructions.extend([
        (QuantumGate::RotationY((gamma / 2.0).into()), target, None),
        (QuantumGate::RotationZ(beta.into()), target, None),
    ]);

    instructions
}

fn mcu2_step(
    matrix: Matrix,
    qubits: &[LogicalQubit],
    first: bool,
    inverse: bool,
    u4_gate: U4Gate,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    let mut instructions = Vec::new();

    let start = if inverse { 1 } else { 0 };

    let mut qubit_pairs: Vec<(usize, usize)> = (0..qubits.len())
        .enumerate()
        .flat_map(|(i, t)| {
            if i > start {
                (start..i).map(|c| (c, t)).collect::<Vec<(usize, usize)>>()
            } else {
                vec![]
            }
        })
        .collect();

    qubit_pairs.sort_by_key(|(c, t)| c + t);
    if !inverse {
        qubit_pairs.reverse();
    }

    for (control, target) in qubit_pairs {
        let exponent: i32 = target as i32 - control as i32;
        let exponent = if control == 0 { exponent - 1 } else { exponent };
        let param = 2.0_f64.powi(exponent);
        let signal = control == 0 && !first;
        let signal = signal ^ inverse;
        if target == qubits.len() - 1 && first {
            let gate = exp_gate(matrix, 1.0 / param, signal);
            instructions.extend(cu2(gate, qubits[control], qubits[target], u4_gate));
        } else {
            instructions.extend(cu2(
                QuantumGate::RotationX(
                    (std::f64::consts::PI * (if signal { -1.0 } else { 1.0 }) / param).into(),
                )
                .matrix(),
                qubits[control],
                qubits[target],
                u4_gate,
            ));
        }
    }

    instructions
}

pub(crate) fn linear_depth(
    gate: QuantumGate,
    control: &[LogicalQubit],
    target: LogicalQubit,
    u4_gate: U4Gate,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    let matrix = gate.matrix();
    let mut control_target = control.to_vec();
    control_target.push(target);

    let mut instruction = Vec::new();

    instruction.extend(mcu2_step(matrix, &control_target, true, false, u4_gate));
    instruction.extend(mcu2_step(matrix, &control_target, true, true, u4_gate));
    instruction.extend(mcu2_step(matrix, control, false, false, u4_gate));
    instruction.extend(mcu2_step(matrix, control, false, true, u4_gate));

    instruction
}

pub(crate) fn single_aux(
    gate: QuantumGate,
    control: &[LogicalQubit],
    aux_qubit: LogicalQubit,
    target: LogicalQubit,
    u4_gate: U4Gate,
    approximated: bool,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    chain![
        x::single_aux::decompose(
            control,
            target,
            aux_qubit,
            u4_gate,
            AuxMode::Dirty,
            DepthMode::Log,
            approximated
        ),
        cu2(gate.matrix(), aux_qubit, target, u4_gate),
        x::single_aux::decompose(
            control,
            target,
            aux_qubit,
            u4_gate,
            AuxMode::Dirty,
            DepthMode::Log,
            approximated
        )
    ]
    .collect()
}

fn czz_ap(
    control: &[LogicalQubit],
    aux_qubits: &[LogicalQubit],
    target1: LogicalQubit,
    target2: LogicalQubit,
    u4_gate: U4Gate,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    chain![
        u4_gate.cnot(target2, target1),
        cz_ap(control, aux_qubits, target1, u4_gate),
        u4_gate.cnot(target2, target1),
    ]
    .collect()
}

pub(crate) fn su2_rewrite_hadamard(
    control: &[LogicalQubit],
    aux_qubit: LogicalQubit,
    target: LogicalQubit,
    u4_gate: U4Gate,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    let a4_1 = QuantumGate::RotationY(FRAC_PI_4.into());
    let a4_2 = QuantumGate::Hadamard;
    let theta1 = PI;
    let theta2 = -2.0 * FRAC_PI_2;

    let a2_1 = QuantumGate::RotationX((-theta1 / 4.0).into());
    let a3_1 = a2_1.inverse();
    let a1_1 = [a3_1, a4_1.inverse()];

    let a2_2 = QuantumGate::RotationX((-theta2 / 4.0).into());
    let a3_2 = a2_2.inverse();
    let a1_2 = [a3_2, a4_2.inverse()];

    let n = control.len() / 2;
    let c1 = &control[..n];
    let c2 = &control[n..];

    chain![
        [(a4_1, target, None), (a4_2, aux_qubit, None)],
        czz_ap(c1, c2, target, aux_qubit, u4_gate),
        [(a2_1, target, None), (a2_2, aux_qubit, None)],
        czz_ap(c2, c1, target, aux_qubit, u4_gate),
        [(a3_1, target, None), (a3_2, aux_qubit, None)],
        czz_ap(c1, c2, target, aux_qubit, u4_gate)
            .into_iter()
            .rev()
            .map(|(gate, target, control)| (gate.inverse(), target, control)),
        [(a2_1, target, None), (a2_2, aux_qubit, None)],
        czz_ap(c2, c1, target, aux_qubit, u4_gate)
            .into_iter()
            .rev()
            .map(|(gate, target, control)| (gate.inverse(), target, control)),
        a1_1.iter().map(|gate| (*gate, target, None)),
        a1_2.iter().map(|gate| (*gate, aux_qubit, None)),
    ]
    .collect()
}
