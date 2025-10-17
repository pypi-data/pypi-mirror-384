// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use num::Integer;
use serde::Serialize;
use x::CXMode;

use crate::ir::qubit::LogicalQubit;

pub(crate) mod network;
pub(crate) mod su2;
pub(crate) mod u2;
pub(crate) mod util;
pub(crate) mod x;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Hash)]
pub enum AuxMode {
    Clean,
    Dirty,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Hash)]
pub enum DepthMode {
    Log,
    Linear,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Default, Hash)]
pub(crate) enum Algorithm {
    VChain(CXMode, AuxMode),
    NetworkU2(CXMode),
    NetworkPauli(CXMode),
    SingleAux(DepthMode, AuxMode),
    SingleAuxU2,
    #[default]
    LinearDepth,
    SU2(DepthMode),
    SU2Rewrite,
    AdjustableDepth,
    NoAuxCX,
    CU2,
}

impl std::fmt::Display for Algorithm {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{self:?}")
    }
}

#[derive(Debug, Clone, Default)]
pub(crate) struct Schema {
    pub algorithm: Algorithm,
    pub aux_qubits: Option<(usize, Vec<LogicalQubit>)>,
    pub approximated: bool,
}

#[derive(Debug, Clone, Default)]
pub(crate) enum State {
    #[default]
    Begin,
    End,
}

#[derive(Debug, Clone, Default)]
pub(crate) struct Registry {
    pub algorithm: Algorithm,
    pub aux_qubits_id: Option<usize>,
    pub state: State,
    pub num_u4: i64,
}

fn num_aux_network_u2(cx_mode: &CXMode, n: usize) -> usize {
    let n_cx = match cx_mode {
        CXMode::C2X => 2,
        CXMode::C3X => 3,
    };

    let (a, rem) = n.div_rem(&n_cx);

    if n == 1 {
        0
    } else if n == 2 && matches!(cx_mode, CXMode::C3X) {
        1
    } else {
        a + num_aux_network_u2(cx_mode, a + rem)
    }
}

fn num_aux_network_pauli(cx_mode: &CXMode, n: usize) -> usize {
    let n_cx = match cx_mode {
        CXMode::C2X => 2,
        CXMode::C3X => 3,
    };

    let (a, rem) = n.div_rem(&n_cx);

    if n <= n_cx {
        0
    } else {
        a + num_aux_network_pauli(cx_mode, a + rem)
    }
}

impl Algorithm {
    pub fn aux_needed(&self, n: usize) -> usize {
        match self {
            Algorithm::VChain(cx_mode, _) => match cx_mode {
                CXMode::C2X => n - 2,
                CXMode::C3X => usize::div_ceil(n - 3, 2),
            },
            Algorithm::NetworkU2(cx_mode) => num_aux_network_u2(cx_mode, n),
            Algorithm::NetworkPauli(cx_mode) => num_aux_network_pauli(cx_mode, n),
            Algorithm::SingleAux(_, _) => 1,
            Algorithm::SingleAuxU2 => 1,
            Algorithm::LinearDepth => 0,
            Algorithm::SU2(_) => 0,
            Algorithm::SU2Rewrite => 1,
            Algorithm::AdjustableDepth => std::cmp::max(
                std::env::var("KET_ADJUSTABLE_DEPTH")
                    .unwrap_or("2".to_string())
                    .parse()
                    .unwrap_or((n as f64 * 0.1) as usize),
                2,
            ),
            Algorithm::NoAuxCX => 0,
            Algorithm::CU2 => 0,
        }
    }

    pub fn aux_mode(&self) -> AuxMode {
        match self {
            Algorithm::VChain(_, aux_mode) => *aux_mode,
            Algorithm::SingleAux(_, aux_mode) => *aux_mode,
            _ => AuxMode::Clean,
        }
    }

    pub fn need_aux(&self) -> bool {
        self.aux_needed(100) > 0
    }
}
