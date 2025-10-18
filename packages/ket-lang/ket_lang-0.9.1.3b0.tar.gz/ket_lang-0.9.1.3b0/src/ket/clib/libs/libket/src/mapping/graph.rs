// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use std::collections::VecDeque;

use rayon::prelude::*;

#[derive(Debug, Clone)]
pub struct GraphMatrix {
    graph: Vec<Vec<Option<i64>>>,
    n: usize,
    distance: Option<Vec<Vec<i64>>>,
}

impl GraphMatrix {
    pub fn new(n: usize) -> Self {
        let mut graph = vec![];
        for i in 1..n {
            graph.push(vec![None; i]);
        }
        Self {
            graph,
            n,
            distance: None,
        }
    }

    pub fn add_node(&mut self) {
        if self.n != 0 {
            self.graph.push(vec![None; self.n]);
        }
        self.n += 1;
    }

    pub fn get_edge(&self, i: usize, j: usize) -> Option<i64> {
        if i == j {
            return Some(0);
        }

        let (i, j) = if i > j { (i, j) } else { (j, i) };
        let i = i - 1;
        self.graph[i][j]
    }

    pub fn neighbors(&self, node: usize) -> Vec<(usize, i64)> {
        (0..self.n)
            .filter_map(|j| {
                if node != j {
                    self.get_edge(node, j).map(|value| (j, value))
                } else {
                    None
                }
            })
            .collect()
    }

    pub fn set_edge(&mut self, i: usize, j: usize, value: i64) {
        if i == j {
            return;
        }

        let (i, j) = if i > j { (i, j) } else { (j, i) };
        let i = i - 1;
        self.graph[i][j] = Some(value);
    }

    pub fn remove_edge(&mut self, i: usize, j: usize) {
        if i == j {
            return;
        }

        let (i, j) = if i > j { (i, j) } else { (j, i) };
        let i = i - 1;
        self.graph[i][j] = None;
    }

    pub fn set_edge_if_none(&mut self, i: usize, j: usize, value: i64) {
        if i == j {
            return;
        }

        let (i, j) = if i > j { (i, j) } else { (j, i) };
        let i = i - 1;
        if self.graph[i][j].is_none() {
            self.graph[i][j] = Some(value);
        }
    }

    pub fn dist(&self, i: usize, j: usize) -> i64 {
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

    fn set_dist_min(&mut self, i: usize, j: usize, value: i64) {
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
                        .map(|value| {
                            if value.is_some() {
                                1
                            } else {
                                (self.n * self.n) as i64
                            }
                        })
                        .collect::<Vec<i64>>()
                })
                .collect(),
        );

        for k in 0..self.n {
            for i in 0..self.n {
                for j in i..self.n {
                    let dist = self.dist(i, k) + self.dist(k, j);
                    self.set_dist_min(i, j, dist);
                }
            }
        }
    }

    pub fn get_center(&self) -> usize {
        let max_distance: Vec<i64> = (0..self.n)
            .into_par_iter()
            .map(|i| {
                (0..self.n)
                    .into_par_iter()
                    .map(|j| self.dist(i, j))
                    .max()
                    .unwrap()
            })
            .collect();

        let min = max_distance.par_iter().min().unwrap();

        let mut center_list: Vec<(usize, i64)> = max_distance
            .iter()
            .enumerate()
            .filter_map(|(node, value)| {
                if value <= min {
                    Some((
                        node,
                        (0..self.n)
                            .into_par_iter()
                            .map(|other| self.dist(node, other))
                            .sum(),
                    ))
                } else {
                    None
                }
            })
            .collect();

        center_list.sort_by_key(|(_, dist)| *dist);

        center_list[0].0
    }

    pub fn breadth_first_search(&self, start: usize) -> VecDeque<usize> {
        let mut visited = vec![];
        let mut queue = VecDeque::from([start]);

        while let Some(front) = queue.pop_front() {
            visited.push(front);
            let neighbors = self.neighbors(front);
            let mut neighbors: Vec<(usize, i64)> = neighbors
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

    pub fn degree(&self, node: usize) -> usize {
        self.neighbors(node).len()
    }

    pub fn complete_graph(&mut self, mut value: i64) {
        for i in 0..self.n - 1 {
            self.set_edge_if_none(i, i + 1, value);
            value += 1;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::GraphMatrix;

    #[test]
    fn test_floyd_warshall() {
        let mut graph = GraphMatrix::new(5);
        graph.set_edge(0, 2, 1);
        graph.set_edge(1, 2, 1);
        graph.set_edge(3, 2, 1);
        graph.set_edge(4, 2, 1);

        graph.calculate_distance();

        assert!(graph.dist(0, 1) == 2);
        assert!(graph.dist(0, 2) == 1);
        assert!(graph.dist(0, 3) == 2);
        assert!(graph.dist(0, 4) == 2);
        assert!(graph.dist(1, 2) == 1);
        assert!(graph.dist(1, 3) == 2);
        assert!(graph.dist(1, 4) == 2);
        assert!(graph.dist(2, 3) == 1);
        assert!(graph.dist(2, 4) == 1);
        assert!(graph.dist(3, 4) == 2);

        assert!(graph.dist(0, 0) == 0);
        assert!(graph.dist(1, 1) == 0);
        assert!(graph.dist(2, 2) == 0);
        assert!(graph.dist(3, 3) == 0);
        assert!(graph.dist(4, 4) == 0);
    }

    #[test]
    fn test_graph_center() {
        let mut graph = GraphMatrix::new(5);
        graph.set_edge(0, 2, 1);
        graph.set_edge(1, 2, 1);
        graph.set_edge(3, 2, 1);
        graph.set_edge(4, 2, 1);

        graph.calculate_distance();

        let center = graph.get_center();

        println!("{:?}", center);

        assert!(center == 2)
    }

    #[test]
    fn test_breadth_first_search() {
        let mut graph = GraphMatrix::new(4);
        graph.set_edge(0, 2, 0);
        graph.set_edge(0, 1, 1);
        graph.set_edge(1, 2, 3);
        graph.set_edge(2, 3, 5);
        graph.set_edge(0, 3, 6);

        graph.calculate_distance();
        let start = graph.get_center();
        let list = graph.breadth_first_search(start);

        println!("{:?}", list);

        assert!(list[0] == 0);
        assert!(list[1] == 2);
        assert!(list[2] == 1);
        assert!(list[3] == 3);
    }
}
