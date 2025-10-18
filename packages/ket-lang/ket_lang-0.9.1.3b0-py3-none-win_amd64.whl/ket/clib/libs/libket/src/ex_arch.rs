// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

// 0--1--2--3
// |  |  |  |
// 4--5--6--7
// |  |  |  |
// 8--9--A--B
pub static GRID12: [(usize, usize); 17] = [
    (0, 4),
    (0, 1),
    (1, 2),
    (1, 5),
    (2, 3),
    (2, 6),
    (3, 7),
    (4, 8),
    (4, 5),
    (5, 9),
    (5, 6),
    (6, 10),
    (6, 7),
    (7, 11),
    (8, 9),
    (9, 10),
    (10, 11),
];

pub fn fully_connected(n: usize) -> Vec<(usize, usize)> {
    let mut edges = Vec::new();
    for i in 0..n {
        for j in i + 1..n {
            edges.push((i, j));
        }
    }
    edges
}
