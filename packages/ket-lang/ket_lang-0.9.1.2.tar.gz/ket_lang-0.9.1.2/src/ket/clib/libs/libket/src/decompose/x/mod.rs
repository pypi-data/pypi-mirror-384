// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use serde::Serialize;
use single_aux::{log, log3_registers};
pub(crate) mod c2to4x;
pub(crate) mod single_aux;
pub(crate) mod v_chain;

use crate::{
    execution::U4Gate,
    ir::{gate::QuantumGate, qubit::LogicalQubit},
};

use super::{network::network, AuxMode};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Hash)]
pub(crate) enum CXMode {
    C2X,
    C3X,
}

pub(crate) fn adjustable_depth(
    control: &[LogicalQubit],
    aux_qubits: &[LogicalQubit],
    target: LogicalQubit,
    u4_gate: U4Gate,
    approximated: bool,
) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
    let n = control.len();
    let m = aux_qubits.len();
    let num_registers = m / 2;
    let register_size = n / num_registers;

    let log3_instructions = (0..num_registers - 1)
        .flat_map(|i| {
            log(
                &control[i * register_size..(i + 1) * register_size],
                aux_qubits[num_registers + i],
                None,
                aux_qubits[i],
                u4_gate,
                AuxMode::Clean,
                true,
            )
        })
        .chain({
            let i = num_registers - 1;
            {
                let control: &[LogicalQubit] = &control[i * register_size..];
                let aux_qubit = aux_qubits[num_registers + i];
                let target = aux_qubits[i];
                let aux_mode = AuxMode::Clean;
                let uncompute = true;
                let n = control.len();
                if n == 4 {
                    return if let Some(more_aux) = None {
                        v_chain::v_chain(
                            control,
                            &[aux_qubit, more_aux],
                            target,
                            u4_gate,
                            AuxMode::Dirty,
                            CXMode::C2X,
                            approximated,
                        )
                    } else {
                        return c2to4x::c1to4x(control, target, u4_gate, uncompute);
                    };
                } else if n <= 3 {
                    return c2to4x::c1to4x(control, target, u4_gate, uncompute);
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

                let clean_aux_gates = c_r0_a
                    .iter()
                    .chain(prod_i.iter())
                    .chain(x_r0star.iter())
                    .chain(c_r0star_aux_t.iter())
                    .chain(x_r0star.iter())
                    .chain(prod_i.iter())
                    .chain(c_r0_a.iter());

                match aux_mode {
                    AuxMode::Clean => clean_aux_gates.cloned().collect::<Vec<_>>(),
                    AuxMode::Dirty => clean_aux_gates
                        .chain(prod_i.iter())
                        .chain(x_r0star.iter())
                        .chain(c_r0star_aux_t.iter())
                        .chain(x_r0star.iter())
                        .chain(prod_i.iter())
                        .cloned()
                        .collect::<Vec<_>>(),
                }
            }
        });

    log3_instructions
        .clone()
        .chain(network(
            QuantumGate::PauliX,
            &aux_qubits[..num_registers],
            &aux_qubits[num_registers..],
            target,
            u4_gate,
            CXMode::C2X,
            approximated,
        ))
        .chain(
            log3_instructions
                .rev()
                .map(|(gate, target, control)| (gate.inverse(), target, control)),
        )
        .collect()
}
