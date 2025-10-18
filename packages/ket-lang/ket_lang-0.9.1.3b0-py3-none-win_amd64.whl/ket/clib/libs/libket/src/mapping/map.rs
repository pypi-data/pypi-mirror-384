// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use std::collections::HashMap;

use crate::{
    circuit::Circuit,
    execution::U4Gate,
    graph::GraphMatrix,
    ir::{
        instructions::Instruction,
        qubit::{LogicalQubit, PhysicalQubit, Qubit},
    },
};
use indexmap::IndexMap;
use itertools::Itertools;
use log::info;

use super::{allocation::Mapping, mcpe::max_consecutive_positive_effect};

pub(super) fn map_circuit(
    mapping: &mut Mapping,
    coupling_graph: &GraphMatrix<PhysicalQubit>,
    logical_circuit: &Circuit<LogicalQubit>,
    u4_gate: U4Gate,
) -> (Circuit<PhysicalQubit>, i32) {
    let mut front: HashMap<LogicalQubit, usize> = HashMap::new();
    let mut active: Vec<usize> = Vec::new();
    let mut frozen: HashMap<LogicalQubit, bool> = HashMap::new();

    let mut head_gates: IndexMap<_, _> = mapping
        .left_values()
        .sorted()
        .map(|qubit| (*qubit, 0))
        .collect();
    let mut final_circuit = Circuit::<PhysicalQubit>::default();

    let mut swap_count = 0;

    while !head_gates.is_empty() {
        let mut remove_qubits: Vec<LogicalQubit> = Vec::new();
        for (qubit, head) in head_gates.iter_mut() {
            if !*frozen.entry(*qubit).or_insert(false) {
                let line = logical_circuit.lines.get(qubit);
                loop {
                    let gate_index = line.and_then(|gate_line| gate_line.get(*head));
                    if let Some(gate_index) = gate_index {
                        let instruction = &logical_circuit.instruction(*gate_index);

                        if matches!(instruction, Instruction::Identity) {
                            *head += 1;
                            continue;
                        }

                        if instruction.affect_one_qubit() {
                            *head += 1;
                            final_circuit.add_instruction(instruction.map_qubits(mapping));
                            continue;
                        }

                        front.insert(*qubit, *gate_index);

                        if instruction
                            .qubits()
                            .all(|qubit| front.get(qubit).is_some_and(|gate| *gate == *gate_index))
                        {
                            for qubit in instruction.qubits() {
                                front.remove(qubit);
                            }
                            active.push(*gate_index);
                        }

                        frozen.insert(*qubit, true);
                        break;
                    } else {
                        remove_qubits.push(*qubit);
                        break;
                    }
                }
            }
        }

        for qubit in remove_qubits.drain(..) {
            head_gates.shift_remove(&qubit);
        }

        active.retain(|gate_index| {
            let instruction = logical_circuit.instruction(*gate_index);
            if let Instruction::Gate {
                target, control, ..
            } = instruction
            {
                let control = control[0];

                if coupling_graph
                    .edge(
                        *mapping.get_by_left(target).unwrap(),
                        *mapping.get_by_left(&control).unwrap(),
                    )
                    .is_some()
                {
                    head_gates.entry(*target).and_modify(|index| *index += 1);
                    head_gates.entry(control).and_modify(|index| *index += 1);
                    final_circuit.add_instruction(instruction.map_qubits(mapping));

                    frozen.insert(*target, false);
                    frozen.insert(control, false);
                    false
                } else {
                    true
                }
            } else {
                for qubit in instruction.qubits() {
                    head_gates.entry(*qubit).and_modify(|index| *index += 1);
                    frozen.insert(*qubit, false);
                }
                final_circuit.add_instruction(instruction.map_qubits(mapping));
                false
            }
        });

        if active.is_empty() {
            continue;
        }

        let active_qubits: Vec<_> = active
            .iter()
            .flat_map(|gate_index| logical_circuit.instruction(*gate_index).qubits())
            .collect();

        let swap_candidates: Vec<_> = active_qubits
            .iter()
            .map(|qubit| *mapping.get_by_left(qubit).unwrap())
            .flat_map(|qubit| {
                let neighbors = coupling_graph.neighbors(qubit);
                neighbors
                    .iter()
                    .map(|(neighbor, _)| (qubit, *neighbor))
                    .collect::<Vec<_>>()
            })
            .unique_by(|(a, b)| {
                if a.index() < b.index() {
                    (*a, *b)
                } else {
                    (*b, *a)
                }
            })
            .collect();

        let swap_candidates: Vec<_> = swap_candidates
            .iter()
            .map(|swap| {
                let mcpe = max_consecutive_positive_effect(
                    *swap,
                    mapping,
                    coupling_graph,
                    logical_circuit,
                    &head_gates,
                );
                (*swap, mcpe)
            })
            .collect();

        let (swap, _) = swap_candidates
            .iter()
            .max_by_key(|(_, mcpe)| *mcpe)
            .unwrap();

        let (physical_a, physical_b) = *swap;
        for (gate, target, control) in u4_gate.swap(physical_a, physical_b) {
            final_circuit.gate(gate, target, &control.map_or(vec![], |c| vec![c]));
        }

        let logical_a = mapping.remove_by_right(&physical_a);
        let logical_b = mapping.remove_by_right(&physical_b);

        if let Some((logical_a, _)) = logical_a {
            mapping.insert(logical_a, physical_b);
        }

        if let Some((logical_b, _)) = logical_b {
            mapping.insert(logical_b, physical_a);
        }
        swap_count += 1;
    }

    info!("SWAP Added: {swap_count}");

    (final_circuit, swap_count)
}
