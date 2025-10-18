// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use allocation::Mapping;

use crate::{
    circuit::Circuit,
    graph::GraphMatrix,
    ir::qubit::{LogicalQubit, PhysicalQubit},
    prelude::U4Gate,
};

pub mod allocation;
pub mod map;
mod mcpe;

pub fn map_circuit(
    mut mapping: Mapping,
    coupling_graph: &GraphMatrix<PhysicalQubit>,
    logical_circuit: &Circuit<LogicalQubit>,
    u4_gate: U4Gate,
    iterations: usize,
) -> Circuit<PhysicalQubit> {
    let reverse_circuit = logical_circuit.reverse_for_mapping();

    let (mut physical_circuit, mut min_swap) =
        map::map_circuit(&mut mapping, coupling_graph, logical_circuit, u4_gate);

    for _ in 0..iterations {
        map::map_circuit(&mut mapping, coupling_graph, &reverse_circuit, u4_gate);
        let (circuit, swap_count) =
            map::map_circuit(&mut mapping, coupling_graph, logical_circuit, u4_gate);
        if swap_count < min_swap {
            physical_circuit = circuit;
            min_swap = swap_count;
        }
    }

    physical_circuit
}
