// SPDX-FileCopyrightText: 2025 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use std::f64::consts::PI;

use itertools::chain;
use num::integer::Roots;

use crate::{
    decompose::{su2, AuxMode, DepthMode},
    ir::qubit::LogicalQubit,
    prelude::{QuantumGate, U4Gate},
};

use super::{c2to4x, v_chain::v_chain, CXMode};

fn linear(
    control: &[LogicalQubit],
    aux_qubit: LogicalQubit,
    target: LogicalQubit,
    u4_gate: U4Gate,
    approximated: bool,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    chain![
        [(QuantumGate::Hadamard, target, None)],
        su2::decompose(
            QuantumGate::RotationX((2.0 * PI).into()),
            chain![control.iter().cloned(), [target]]
                .collect::<Vec<_>>()
                .as_ref(),
            aux_qubit,
            u4_gate,
            DepthMode::Linear,
            approximated
        ),
        [(QuantumGate::Hadamard, target, None)],
    ]
    .collect()
}

pub(super) fn log3_registers(
    control: &[LogicalQubit],
) -> (Vec<&[LogicalQubit]>, &[LogicalQubit], &[LogicalQubit]) {
    let n = control.len();
    let p = n.sqrt();
    let r0 = &control[..2 * p];
    let mut registers = vec![r0];
    for i in 1..p + 1 {
        let begin = (1 + i) * p;
        let end = (2 + i) * p;
        if end < n {
            registers.push(&control[begin..end]);
        } else {
            registers.push(&control[begin..]);
            assert!(!registers.last().unwrap().is_empty());
            break;
        }
    }
    let b = registers.len() - 1;
    let r0star = &r0[..b];
    let r0b = &r0[b..];

    (registers, r0star, r0b)
}

pub(super) fn log(
    control: &[LogicalQubit],
    aux_qubit: LogicalQubit,
    more_aux: Option<LogicalQubit>,
    target: LogicalQubit,
    u4_gate: U4Gate,
    aux_mode: AuxMode,
    approximated: bool,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    let n = control.len();
    if n == 4 {
        return if let Some(more_aux) = more_aux {
            v_chain(
                control,
                &[aux_qubit, more_aux],
                target,
                u4_gate,
                AuxMode::Dirty,
                CXMode::C2X,
                approximated,
            )
        } else {
            return c2to4x::c1to4x(control, target, u4_gate, approximated);
        };
    } else if n <= 3 {
        return c2to4x::c1to4x(control, target, u4_gate, approximated);
    }

    let (registers, r0star, r0b) = log3_registers(control);
    let b = r0star.len();

    let c_r0_a = log(
        registers[0],
        target,
        Some(registers[1][0]),
        aux_qubit,
        u4_gate,
        AuxMode::Dirty,
        true,
    );

    let mut prod_i = Vec::new();
    for i in 1..b + 1 {
        prod_i.extend(log(
            registers[i],
            r0b[i - 1],
            None,
            r0star[i - 1],
            u4_gate,
            AuxMode::Dirty,
            true,
        ));
    }

    let x_r0star: Vec<_> = r0star
        .iter()
        .cloned()
        .map(|qubit| (QuantumGate::PauliX, qubit, None))
        .collect();

    let r0star_aux: Vec<_> = r0star.iter().copied().chain([aux_qubit]).collect();

    let c_r0star_aux_t = log(
        &r0star_aux,
        r0b[0],
        Some(registers[1][0]),
        target,
        u4_gate,
        aux_mode,
        false,
    );

    let clean_aux_gates = chain![
        c_r0_a.clone(),
        prod_i.clone(),
        x_r0star.clone(),
        c_r0star_aux_t.clone(),
        x_r0star.clone(),
        prod_i.clone(),
        c_r0_a.clone(),
    ];

    match aux_mode {
        AuxMode::Clean => clean_aux_gates.collect(),
        AuxMode::Dirty => chain![
            clean_aux_gates,
            prod_i.clone(),
            x_r0star.clone(),
            c_r0star_aux_t,
            x_r0star,
            prod_i,
        ]
        .collect(),
    }
}

pub(crate) fn decompose(
    control: &[LogicalQubit],
    aux_qubit: LogicalQubit,
    target: LogicalQubit,
    u4_gate: U4Gate,
    aux_mode: AuxMode,
    depth_mode: DepthMode,
    approximated: bool,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    match depth_mode {
        DepthMode::Log => log(
            control,
            aux_qubit,
            None,
            target,
            u4_gate,
            aux_mode,
            approximated,
        ),
        DepthMode::Linear => linear(control, aux_qubit, target, u4_gate, approximated),
    }
}
