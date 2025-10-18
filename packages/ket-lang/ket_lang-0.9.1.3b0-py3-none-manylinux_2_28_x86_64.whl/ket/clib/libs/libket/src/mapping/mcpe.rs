// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use indexmap::IndexMap;

use crate::{
    circuit::Circuit,
    graph::GraphMatrix,
    ir::{
        instructions::Instruction,
        qubit::{LogicalQubit, PhysicalQubit},
    },
};

use super::allocation::Mapping;

pub fn max_consecutive_positive_effect(
    swap: (PhysicalQubit, PhysicalQubit),
    mapping: &Mapping,
    coupling_graph: &GraphMatrix<PhysicalQubit>,
    circuit: &Circuit<LogicalQubit>,
    head_gates: &IndexMap<LogicalQubit, usize>,
) -> i64 {
    let (physical_a, physical_b) = swap;

    let effect = |target: LogicalQubit, control: LogicalQubit| {
        let (physical_target, physical_control) = (
            mapping.get_by_left(&target).cloned(),
            mapping.get_by_left(&control).cloned(),
        );
        if let (Some(physical_target), Some(physical_control)) = (physical_target, physical_control)
        {
            let old_dist = coupling_graph.dist(physical_target, physical_control);
            let new_dist = match (
                physical_a == physical_target,
                physical_a == physical_control,
                physical_b == physical_target,
                physical_b == physical_control,
            ) {
                (true, _, _, _) => coupling_graph.dist(physical_b, physical_control),
                (_, true, _, _) => coupling_graph.dist(physical_target, physical_b),
                (_, _, true, _) => coupling_graph.dist(physical_a, physical_control),
                (_, _, _, true) => coupling_graph.dist(physical_target, physical_a),
                _ => panic!("SWAP do not affect the gate or SWAP control and target"),
            };
            old_dist - new_dist
        } else {
            0
        }
    };

    let calculate_mcpe = |qubit: &LogicalQubit| {
        let mut head_gate: usize = match head_gates.get(qubit) {
            Some(head_gate) => *head_gate,
            None => return 0,
        };

        let mut mcpe = 0;

        while let Some(gate_index) = circuit
            .lines
            .get(qubit)
            .and_then(|gate_line| gate_line.get(head_gate))
        {
            let instruction = circuit.instruction(*gate_index);
            if let Instruction::Gate {
                target, control, ..
            } = instruction
            {
                if !control.is_empty() {
                    let swap_effect = effect(*target, control[0]);
                    if swap_effect >= 0 {
                        mcpe += swap_effect;
                    } else {
                        break;
                    }
                }
            }
            head_gate += 1;
        }
        mcpe
    };

    let a = calculate_mcpe(mapping.get_by_right(&physical_a).unwrap());
    let b = mapping.get_by_right(&physical_b).map_or(0, calculate_mcpe);
    if a == 0 {
        -1
    } else {
        a + b
    }
}
