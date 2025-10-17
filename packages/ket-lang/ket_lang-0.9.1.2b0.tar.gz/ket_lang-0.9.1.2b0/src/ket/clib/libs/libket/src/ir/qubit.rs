// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use std::hash::Hash;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize, Serialize, PartialOrd, Ord, Hash)]
pub enum LogicalQubit {
    Main { index: usize },
    Aux { index: usize },
}

impl Default for LogicalQubit {
    fn default() -> Self {
        LogicalQubit::Main { index: 0 }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Deserialize, Serialize, PartialOrd, Ord)]
pub struct PhysicalQubit {
    index: usize,
}

pub trait Qubit {
    fn index(&self) -> usize;
    fn is_aux(&self) -> bool {
        false
    }
}

impl LogicalQubit {
    pub fn main(index: usize) -> Self {
        if index >= 1 << 32 {
            LogicalQubit::Aux {
                index: (index >> 32) - 1,
            }
        } else {
            LogicalQubit::Main { index }
        }
    }

    pub fn aux(index: usize) -> Self {
        LogicalQubit::Aux { index }
    }

    pub fn is_main(&self) -> bool {
        !self.is_aux()
    }
}

impl Qubit for LogicalQubit {
    fn index(&self) -> usize {
        match self {
            LogicalQubit::Main { index } | LogicalQubit::Aux { index } => *index,
        }
    }

    fn is_aux(&self) -> bool {
        matches!(self, LogicalQubit::Aux { .. })
    }
}

impl Qubit for PhysicalQubit {
    fn index(&self) -> usize {
        self.index
    }
}

impl PhysicalQubit {
    pub fn new(index: usize) -> Self {
        PhysicalQubit { index }
    }
}

impl From<usize> for PhysicalQubit {
    fn from(index: usize) -> Self {
        PhysicalQubit::new(index)
    }
}

impl From<usize> for LogicalQubit {
    fn from(index: usize) -> Self {
        LogicalQubit::main(index)
    }
}
