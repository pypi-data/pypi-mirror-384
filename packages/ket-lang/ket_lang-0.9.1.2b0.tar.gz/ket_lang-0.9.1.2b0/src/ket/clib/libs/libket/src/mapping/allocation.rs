// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use itertools::Itertools;

use crate::{
    graph::GraphMatrix,
    ir::qubit::{LogicalQubit, PhysicalQubit},
};

pub(crate) type Mapping = bimap::BiMap<LogicalQubit, PhysicalQubit>;

pub fn initial(
    interaction_graph: &GraphMatrix<LogicalQubit>,
    coupling_graph: &GraphMatrix<PhysicalQubit>,
) -> Mapping {
    let center_logical_qubit = interaction_graph.get_center();
    let center_physical_qubit = coupling_graph.get_center();

    let mut mapping = Mapping::new();
    mapping.insert(center_logical_qubit, center_physical_qubit);

    let mut queue = interaction_graph.breadth_first_search(center_logical_qubit);
    queue.pop_front();

    while let Some(next_logical_qubit) = queue.pop_front() {
        let reference_locations =
            reference_locations(next_logical_qubit, &mapping, interaction_graph);

        let candidate_locations =
            candidate_locations(&reference_locations, &mapping, coupling_graph);

        let next_physical_qubit = next_physical_qubit(
            next_logical_qubit,
            &candidate_locations,
            interaction_graph,
            coupling_graph,
        );

        mapping.insert(next_logical_qubit, next_physical_qubit);
    }

    mapping
}

fn reference_locations(
    qubit: LogicalQubit,
    mapping: &Mapping,
    interaction_graph: &GraphMatrix<LogicalQubit>,
) -> Vec<PhysicalQubit> {
    let mut reference_locations: Vec<_> = interaction_graph
        .neighbors(qubit)
        .into_iter()
        .filter(|(node, _)| mapping.contains_left(node))
        .collect();

    reference_locations.sort_by_key(|(_, value)| *value);
    reference_locations
        .into_iter()
        .map(|(node, _)| *mapping.get_by_left(&node).unwrap())
        .collect()
}

fn candidate_locations(
    reference_locations: &[PhysicalQubit],
    mapping: &Mapping,
    coupling_graph: &GraphMatrix<PhysicalQubit>,
) -> Vec<PhysicalQubit> {
    let mut neighbors_locations: Vec<_> = coupling_graph
        .neighbors(reference_locations[0])
        .into_iter()
        .map(|(node, _)| node)
        .collect();

    let mut candidate_locations: Vec<_>;

    loop {
        assert!(!neighbors_locations.is_empty());

        candidate_locations = neighbors_locations
            .iter()
            .filter(|node| !mapping.contains_right(node))
            .cloned()
            .collect();

        if !candidate_locations.is_empty() {
            break;
        }

        neighbors_locations = neighbors_locations
            .into_iter()
            .flat_map(|qubit| {
                coupling_graph
                    .neighbors(qubit)
                    .into_iter()
                    .map(|(node, _)| node)
                    .collect::<Vec<_>>()
            })
            .unique()
            .collect();
    }

    for reference in &reference_locations[1..] {
        let mut candidate_locations_dist: Vec<_> = candidate_locations
            .iter()
            .map(|candidate| (*candidate, coupling_graph.dist(*candidate, *reference)))
            .collect();

        candidate_locations_dist.sort_by_key(|(_, dist)| *dist);

        let min_dist = candidate_locations_dist[0].1;
        candidate_locations = candidate_locations_dist
            .into_iter()
            .filter_map(|(node, dist)| if dist <= min_dist { Some(node) } else { None })
            .collect();

        if candidate_locations.len() == 1 {
            break;
        }
    }

    candidate_locations
}

fn next_physical_qubit(
    next_logical_qubit: LogicalQubit,
    candidate_locations: &[PhysicalQubit],
    interaction_graph: &GraphMatrix<LogicalQubit>,
    coupling_graph: &GraphMatrix<PhysicalQubit>,
) -> PhysicalQubit {
    if candidate_locations.len() > 1 {
        let interaction_degree = interaction_graph.degree(next_logical_qubit);

        let mut candidate_degree: Vec<_> = candidate_locations
            .iter()
            .map(|node| {
                (
                    node,
                    coupling_graph.degree(*node).abs_diff(interaction_degree),
                )
            })
            .collect();

        candidate_degree.sort_by_key(|(_, degree)| *degree);

        *candidate_degree[0].0
    } else {
        candidate_locations[0]
    }
}
