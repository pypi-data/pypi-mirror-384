// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use crate::ir::qubit::Qubit;
use std::{collections::VecDeque, marker::PhantomData};

#[derive(Debug, Clone, Default)]
pub(crate) struct GraphMatrix<Q> {
    graph: Vec<Vec<Option<i64>>>,
    n: usize,
    distance: Option<Vec<Vec<i64>>>,

    qubit_type: PhantomData<Q>,
}

impl<Q> GraphMatrix<Q>
where
    Q: Qubit + From<usize> + Clone + Copy + Sync + PartialEq,
{
    pub fn new(n: usize) -> Self {
        let mut graph = vec![];
        for i in 1..n {
            graph.push(vec![None; i]);
        }
        Self {
            graph,
            n,
            distance: None,
            qubit_type: PhantomData,
        }
    }

    fn add_node(&mut self) {
        if self.n != 0 {
            self.graph.push(vec![None; self.n]);
        }
        self.n += 1;
    }

    pub fn edge(&self, i: Q, j: Q) -> Option<i64> {
        let (i, j) = (i.index(), j.index());

        if self.n <= i || self.n <= j {
            return None;
        }

        if i == j {
            return Some(0);
        }

        let (i, j) = if i > j { (i, j) } else { (j, i) };
        let i = i - 1;
        self.graph[i][j]
    }

    pub fn neighbors(&self, node: Q) -> Vec<(Q, i64)> {
        let node = node.index();
        (0..self.n)
            .filter_map(|j| {
                if node != j {
                    self.edge(node.into(), j.into())
                        .map(|value| (j.into(), value))
                } else {
                    None
                }
            })
            .collect()
    }

    pub fn set_edge(&mut self, i: Q, j: Q, value: i64) {
        let (i, j) = (i.index(), j.index());

        while self.n <= i || self.n <= j {
            self.add_node();
        }

        if i == j {
            return;
        }

        let (i, j) = if i > j { (i, j) } else { (j, i) };
        let i = i - 1;
        self.graph[i][j] = Some(value);
    }

    pub fn dist(&self, i: Q, j: Q) -> i64 {
        let (i, j) = (i.index(), j.index());

        if let Some(distance) = &self.distance {
            if i == j {
                return 0;
            }

            let (i, j) = if i > j { (i, j) } else { (j, i) };
            let i = i - 1;
            distance[i][j]
        } else {
            panic!("Calculate distance before")
        }
    }

    fn set_dist_min(&mut self, i: Q, j: Q, value: i64) {
        let (i, j) = (i.index(), j.index());

        if self.distance.is_none() {
            panic!("Cannot set distance without distance matrix");
        }
        if i == j {
            return;
        }

        let (i, j) = if i > j { (i, j) } else { (j, i) };
        let i = i - 1;
        let value = std::cmp::min(self.distance.as_ref().unwrap()[i][j], value);
        self.distance.as_mut().unwrap()[i][j] = value;
    }

    pub fn calculate_distance(&mut self) {
        if self.distance.is_some() {
            return;
        }

        self.distance = Some(
            self.graph
                .iter()
                .map(|row| {
                    row.iter()
                        .map(|value| if value.is_some() { 1 } else { u32::MAX as i64 })
                        .collect::<Vec<i64>>()
                })
                .collect(),
        );

        for k in 0..self.n {
            for i in 0..self.n {
                for j in i..self.n {
                    let dist = self.dist(i.into(), k.into()) + self.dist(k.into(), j.into());
                    self.set_dist_min(i.into(), j.into(), dist);
                }
            }
        }
    }

    pub fn get_center(&self) -> Q {
        let max_distance: Vec<i64> = (0..self.n)
            .map(|i| {
                (0..self.n)
                    .map(|j| self.dist(i.into(), j.into()))
                    .max()
                    .unwrap()
            })
            .collect();

        let min = max_distance.iter().min().unwrap();

        let mut center_list: Vec<(usize, i64)> = max_distance
            .iter()
            .enumerate()
            .filter_map(|(node, value)| {
                if value <= min {
                    Some((
                        node,
                        (0..self.n)
                            .map(|other| self.dist(node.into(), other.into()))
                            .sum(),
                    ))
                } else {
                    None
                }
            })
            .collect();

        center_list.sort_by_key(|(_, dist)| *dist);

        center_list[0].0.into()
    }

    pub fn breadth_first_search(&self, start: Q) -> VecDeque<Q> {
        let mut visited: Vec<Q> = vec![];
        let mut queue = VecDeque::from([start]);

        while let Some(front) = queue.pop_front() {
            visited.push(front);
            let neighbors = self.neighbors(front);
            let mut neighbors: Vec<_> = neighbors
                .iter()
                .filter_map(|(index, value)| {
                    if !visited.contains(index) && !queue.contains(index) {
                        Some((*index, *value))
                    } else {
                        None
                    }
                })
                .collect();

            neighbors.sort_by_key(|(_, value)| *value);

            for (next, _) in neighbors {
                queue.push_back(next);
            }
        }

        VecDeque::from(visited)
    }

    pub fn degree(&self, node: Q) -> usize {
        self.neighbors(node).len()
    }
}
