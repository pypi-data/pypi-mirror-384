// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use super::qubit::LogicalQubit;
use crate::{
    decompose::{
        self,
        network::network,
        u2::su2_rewrite_hadamard,
        x::{single_aux, v_chain::v_chain, CXMode},
        Algorithm, AuxMode, DepthMode, Schema,
    },
    execution::U4Gate,
};
use num::Complex;
use serde::{Deserialize, Serialize};
use std::f64::consts::{FRAC_1_SQRT_2, FRAC_PI_2, FRAC_PI_4, FRAC_PI_8, PI};

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum Param {
    Value(f64),
    Ref {
        index: usize,
        value: f64,
        multiplier: f64,
    },
}

impl From<f64> for Param {
    fn from(value: f64) -> Self {
        Self::Value(value)
    }
}

impl Param {
    pub fn new_ref(index: usize, multiplier: f64) -> Self {
        Self::Ref {
            index,
            value: 0.0,
            multiplier,
        }
    }

    pub fn new_value(value: f64) -> Self {
        value.into()
    }

    pub(crate) fn update_ref(&mut self, new_value: f64) {
        if let Param::Ref { value, .. } = self {
            *value = new_value;
        } else {
            panic!()
        }
    }

    pub(crate) fn index(&self) -> usize {
        if let Param::Ref { index, .. } = self {
            *index
        } else {
            panic!()
        }
    }

    pub(crate) fn value(&self) -> f64 {
        match self {
            Param::Value(value) => *value,
            Param::Ref {
                value, multiplier, ..
            } => value * multiplier,
        }
    }

    fn inverse(&self) -> Self {
        match self {
            Param::Value(value) => Param::Value(-value),
            Param::Ref {
                index,
                value,
                multiplier,
            } => Param::Ref {
                index: *index,
                value: *value,
                multiplier: -multiplier,
            },
        }
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum QuantumGate {
    PauliX,
    PauliY,
    PauliZ,
    RotationX(Param),
    RotationY(Param),
    RotationZ(Param),
    Phase(Param),
    Hadamard,
}

pub type Cf64 = Complex<f64>;
pub type Matrix = [[Cf64; 2]; 2];

impl QuantumGate {
    pub fn s() -> Self {
        Self::Phase(FRAC_PI_2.into())
    }

    pub fn sd() -> Self {
        Self::Phase((-FRAC_PI_2).into())
    }

    pub fn t() -> Self {
        Self::Phase(FRAC_PI_4.into())
    }

    pub fn td() -> Self {
        Self::Phase((-FRAC_PI_4).into())
    }

    pub fn sqrt_t() -> Self {
        Self::Phase(FRAC_PI_8.into())
    }

    pub fn sqrt_td() -> Self {
        Self::Phase((-FRAC_PI_8).into())
    }

    pub fn is_permutation(&self) -> bool {
        match self {
            QuantumGate::RotationX(param) | QuantumGate::RotationY(param) => {
                if let Param::Value(value) = param {
                    (value.abs() - PI).abs() <= 1e-10 || (value.abs() - 2.0 * PI).abs() <= 1e-10
                } else {
                    false
                }
            }
            QuantumGate::Hadamard => false,
            _ => true,
        }
    }

    pub fn is_diagonal(&self) -> bool {
        matches!(
            self,
            QuantumGate::PauliZ | QuantumGate::RotationZ(_) | QuantumGate::Phase(_)
        )
    }

    pub(crate) fn is_identity(&self) -> bool {
        let (angle, n) = match self {
            QuantumGate::RotationX(angle) => (angle, 4.0),
            QuantumGate::RotationY(angle) => (angle, 4.0),
            QuantumGate::RotationZ(angle) => (angle, 4.0),
            QuantumGate::Phase(angle) => (angle, 2.0),
            _ => return false,
        };
        if let Param::Value(angle) = angle {
            (angle % (n * PI)).abs() < 1e-14
        } else {
            false
        }
    }

    pub(crate) fn is_inverse(&self, other: &Self) -> bool {
        match self {
            QuantumGate::PauliX => matches!(other, QuantumGate::PauliX),
            QuantumGate::PauliY => matches!(other, QuantumGate::PauliY),
            QuantumGate::PauliZ => matches!(other, QuantumGate::PauliZ),
            QuantumGate::RotationX(angle) => {
                if let QuantumGate::RotationX(Param::Value(other)) = other {
                    if let Param::Value(angle) = angle {
                        QuantumGate::RotationX((angle + other).into()).is_identity()
                    } else {
                        false
                    }
                } else {
                    false
                }
            }
            QuantumGate::RotationY(angle) => {
                if let QuantumGate::RotationY(Param::Value(other)) = other {
                    if let Param::Value(angle) = angle {
                        QuantumGate::RotationY((angle + other).into()).is_identity()
                    } else {
                        false
                    }
                } else {
                    false
                }
            }
            QuantumGate::RotationZ(angle) => {
                if let QuantumGate::RotationZ(Param::Value(other)) = other {
                    if let Param::Value(angle) = angle {
                        QuantumGate::RotationZ((angle + other).into()).is_identity()
                    } else {
                        false
                    }
                } else {
                    false
                }
            }
            QuantumGate::Phase(angle) => {
                if let QuantumGate::Phase(Param::Value(other)) = other {
                    if let Param::Value(angle) = angle {
                        QuantumGate::Phase((angle + other).into()).is_identity()
                    } else {
                        false
                    }
                } else {
                    false
                }
            }
            QuantumGate::Hadamard => matches!(other, QuantumGate::Hadamard),
        }
    }

    pub(crate) fn matrix(&self) -> Matrix {
        match self {
            QuantumGate::PauliX => [[0.0.into(), 1.0.into()], [1.0.into(), 0.0.into()]],
            QuantumGate::PauliY => [[0.0.into(), -Cf64::i()], [Cf64::i(), 0.0.into()]],
            QuantumGate::PauliZ => [[1.0.into(), 0.0.into()], [0.0.into(), (-1.0).into()]],
            QuantumGate::RotationX(angle) => {
                let angle = angle.value();
                [
                    [(angle / 2.0).cos().into(), -Cf64::i() * (angle / 2.0).sin()],
                    [-Cf64::i() * (angle / 2.0).sin(), (angle / 2.0).cos().into()],
                ]
            }
            QuantumGate::RotationY(angle) => {
                let angle = angle.value();
                [
                    [(angle / 2.0).cos().into(), (-(angle / 2.0).sin()).into()],
                    [(angle / 2.0).sin().into(), (angle / 2.0).cos().into()],
                ]
            }
            QuantumGate::RotationZ(angle) => {
                let angle = angle.value();
                [
                    [(-Cf64::i() * (angle / 2.0)).exp(), 0.0.into()],
                    [0.0.into(), (Cf64::i() * (angle / 2.0)).exp()],
                ]
            }
            QuantumGate::Phase(angle) => [
                [1.0.into(), 0.0.into()],
                [0.0.into(), (Cf64::i() * angle.value()).exp()],
            ],
            QuantumGate::Hadamard => [
                [(1.0 / 2.0f64.sqrt()).into(), (1.0 / 2.0f64.sqrt()).into()],
                [(1.0 / 2.0f64.sqrt()).into(), (-1.0 / 2.0f64.sqrt()).into()],
            ],
        }
    }

    pub(crate) fn su2_matrix(&self) -> Matrix {
        match self {
            QuantumGate::PauliX => QuantumGate::RotationX(PI.into()).matrix(),
            QuantumGate::PauliY => QuantumGate::RotationY(PI.into()).matrix(),
            QuantumGate::PauliZ => QuantumGate::RotationZ(PI.into()).matrix(),
            QuantumGate::Phase(angle) => QuantumGate::RotationZ(*angle).matrix(),
            QuantumGate::Hadamard => [
                [-Cf64::i() * FRAC_1_SQRT_2, -Cf64::i() * FRAC_1_SQRT_2],
                [-Cf64::i() * FRAC_1_SQRT_2, Cf64::i() * FRAC_1_SQRT_2],
            ],
            _ => self.matrix(),
        }
    }

    pub(crate) fn inverse(&self) -> Self {
        match self {
            QuantumGate::PauliX => QuantumGate::PauliX,
            QuantumGate::PauliY => QuantumGate::PauliY,
            QuantumGate::PauliZ => QuantumGate::PauliZ,
            QuantumGate::RotationX(angle) => QuantumGate::RotationX(angle.inverse()),
            QuantumGate::RotationY(angle) => QuantumGate::RotationY(angle.inverse()),
            QuantumGate::RotationZ(angle) => QuantumGate::RotationZ(angle.inverse()),
            QuantumGate::Phase(angle) => QuantumGate::Phase(angle.inverse()),
            QuantumGate::Hadamard => QuantumGate::Hadamard,
        }
    }

    pub(crate) fn decomposition_list(&self, control_size: usize) -> Vec<Algorithm> {
        if std::env::var("KET_FORCE_DECOMPOSE_ALGORITHM").unwrap_or("0".to_string()) == "1" {
            let algorithm = match std::env::var("KET_DECOMPOSE_ALGORITHM")
                .unwrap_or_default()
                .as_str()
            {
                "VChainC2XClean" => Algorithm::VChain(CXMode::C2X, AuxMode::Clean),
                "VChainC3XClean" => Algorithm::VChain(CXMode::C3X, AuxMode::Clean),
                "VChainC2XDirty" => Algorithm::VChain(CXMode::C2X, AuxMode::Dirty),
                "VChainC3XDirty" => Algorithm::VChain(CXMode::C3X, AuxMode::Dirty),
                "NetworkU2C2X" => Algorithm::NetworkU2(CXMode::C2X),
                "NetworkU2C3X" => Algorithm::NetworkU2(CXMode::C3X),
                "NetworkPauliC2X" => Algorithm::NetworkPauli(CXMode::C2X),
                "NetworkPauliC3X" => Algorithm::NetworkPauli(CXMode::C3X),
                "SingleAuxLinearClean" => Algorithm::SingleAux(DepthMode::Linear, AuxMode::Clean),
                "SingleAuxLinearDirty" => Algorithm::SingleAux(DepthMode::Linear, AuxMode::Dirty),
                "SingleAuxLogClean" => Algorithm::SingleAux(DepthMode::Log, AuxMode::Clean),
                "SingleAuxLogDirty" => Algorithm::SingleAux(DepthMode::Log, AuxMode::Dirty),
                "SingleAuxU2" => Algorithm::SingleAuxU2,
                "LinearDepth" => Algorithm::LinearDepth,
                "SU2Linear" => Algorithm::SU2(DepthMode::Linear),
                "SU2Log" => Algorithm::SU2(DepthMode::Log),
                "SU2Rewrite" => Algorithm::SU2Rewrite,
                "AdjustableDepth" => Algorithm::AdjustableDepth,
                other => panic!("undefined decomposition algorithm: {other}. Are you sure that you want to use this configuration?"),
            };
            return match self {
                QuantumGate::PauliX | QuantumGate::PauliY | QuantumGate::PauliZ => {
                    assert!(
                        control_size <= 3
                            || matches!(
                                algorithm,
                                Algorithm::NetworkPauli(_)
                                    | Algorithm::VChain(_, _)
                                    | Algorithm::AdjustableDepth
                                    | Algorithm::SingleAux(_, _)
                                    | Algorithm::LinearDepth
                            )
                    );
                    if control_size <= 3 {
                        vec![Algorithm::NoAuxCX]
                    } else if control_size == 4 {
                        vec![algorithm, Algorithm::NoAuxCX]
                    } else {
                        vec![algorithm, Algorithm::LinearDepth]
                    }
                }
                QuantumGate::RotationX(_)
                | QuantumGate::RotationY(_)
                | QuantumGate::RotationZ(_) => {
                    assert!(
                        control_size <= 1
                            || matches!(
                                algorithm,
                                Algorithm::NetworkU2(_)
                                    | Algorithm::SU2(_)
                                    | Algorithm::LinearDepth
                            )
                    );
                    if control_size > 1 {
                        vec![algorithm, Algorithm::LinearDepth]
                    } else {
                        vec![Algorithm::CU2]
                    }
                }
                QuantumGate::Phase(_) | QuantumGate::Hadamard => {
                    assert!(
                        control_size <= 1
                            || matches!(
                                algorithm,
                                Algorithm::NetworkU2(_)
                                    | Algorithm::SingleAuxU2
                                    | Algorithm::SU2Rewrite
                                    | Algorithm::LinearDepth
                            )
                    );
                    if control_size > 1 {
                        vec![algorithm, Algorithm::LinearDepth]
                    } else {
                        vec![Algorithm::CU2]
                    }
                }
            };
        }

        match self {
            QuantumGate::PauliX | QuantumGate::PauliY | QuantumGate::PauliZ => {
                if control_size <= 3 {
                    vec![Algorithm::NoAuxCX]
                } else if control_size == 4 {
                    vec![
                        Algorithm::NetworkPauli(CXMode::C2X),
                        Algorithm::NetworkPauli(CXMode::C3X),
                        Algorithm::VChain(CXMode::C3X, AuxMode::Clean),
                        Algorithm::VChain(CXMode::C2X, AuxMode::Dirty),
                        Algorithm::NoAuxCX,
                    ]
                } else {
                    vec![
                        Algorithm::NetworkPauli(CXMode::C2X),
                        Algorithm::NetworkPauli(CXMode::C3X),
                        Algorithm::VChain(CXMode::C3X, AuxMode::Clean),
                        Algorithm::VChain(CXMode::C2X, AuxMode::Dirty),
                        Algorithm::SingleAux(DepthMode::Linear, AuxMode::Dirty),
                        Algorithm::LinearDepth,
                    ]
                }
            }
            QuantumGate::RotationX(_) | QuantumGate::RotationY(_) | QuantumGate::RotationZ(_) => {
                if control_size > 1 {
                    vec![
                        Algorithm::NetworkU2(CXMode::C3X),
                        Algorithm::SU2(DepthMode::Linear),
                    ]
                } else {
                    vec![Algorithm::CU2]
                }
            }
            QuantumGate::Phase(_) | QuantumGate::Hadamard => {
                if control_size > 1 {
                    vec![
                        Algorithm::NetworkU2(CXMode::C3X),
                        Algorithm::SU2Rewrite,
                        Algorithm::LinearDepth,
                    ]
                } else {
                    vec![Algorithm::CU2]
                }
            }
        }
    }

    pub(crate) fn decompose(
        &self,
        target: LogicalQubit,
        control: &[LogicalQubit],
        schema: Schema,
        u4_gate: U4Gate,
    ) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
        match self {
            QuantumGate::PauliX => Self::decompose_x(target, control, schema, u4_gate),
            QuantumGate::PauliY => Self::decompose_y(target, control, schema, u4_gate),
            QuantumGate::PauliZ => Self::decompose_z(target, control, schema, u4_gate),
            QuantumGate::RotationX(_) | QuantumGate::RotationY(_) | QuantumGate::RotationZ(_) => {
                self.decompose_r(target, control, schema, u4_gate)
            }
            QuantumGate::Phase(angle) => {
                Self::decompose_phase(angle.value(), target, control, schema, u4_gate)
            }
            QuantumGate::Hadamard => Self::decompose_hadamard(target, control, schema, u4_gate),
        }
    }

    fn decompose_r(
        &self,
        target: LogicalQubit,
        control: &[LogicalQubit],
        schema: Schema,
        u4_gate: U4Gate,
    ) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
        match &schema.algorithm {
            Algorithm::LinearDepth => decompose::u2::linear_depth(*self, control, target, u4_gate),

            Algorithm::NetworkU2(cx_mode) => decompose::network::network(
                *self,
                control,
                &schema.aux_qubits.unwrap().1,
                target,
                u4_gate,
                *cx_mode,
                schema.approximated,
            ),
            Algorithm::SU2(depth_mode) => decompose::su2::decompose(
                *self,
                control,
                target,
                u4_gate,
                *depth_mode,
                schema.approximated,
            ),
            Algorithm::CU2 => decompose::u2::cu2(self.matrix(), control[0], target, u4_gate),
            _ => panic!("Invalid Decomposition for Rotation Gate"),
        }
    }

    fn decompose_x(
        target: LogicalQubit,
        control: &[LogicalQubit],
        schema: Schema,
        u4_gate: U4Gate,
    ) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
        match &schema.algorithm {
            Algorithm::VChain(cx_mode, aux_mode) => v_chain(
                control,
                &schema.aux_qubits.unwrap().1,
                target,
                u4_gate,
                *aux_mode,
                *cx_mode,
                schema.approximated,
            ),
            Algorithm::SingleAux(depth_mode, aux_mode) => single_aux::decompose(
                control,
                schema.aux_qubits.unwrap().1[0],
                target,
                u4_gate,
                *aux_mode,
                *depth_mode,
                schema.approximated,
            ),
            Algorithm::LinearDepth => {
                decompose::u2::linear_depth(QuantumGate::PauliX, control, target, u4_gate)
            }
            Algorithm::NoAuxCX => {
                decompose::x::c2to4x::c1to4x(control, target, u4_gate, schema.approximated)
            }
            Algorithm::AdjustableDepth => decompose::x::adjustable_depth(
                control,
                &schema.aux_qubits.unwrap().1,
                target,
                u4_gate,
                schema.approximated,
            ),
            Algorithm::NetworkPauli(cx_mode) => network(
                QuantumGate::PauliX,
                control,
                &schema.aux_qubits.unwrap().1,
                target,
                u4_gate,
                *cx_mode,
                schema.approximated,
            ),
            _ => panic!("Invalid Decomposition {schema:?} for Pauli Gate"),
        }
    }

    fn decompose_y(
        target: LogicalQubit,
        control: &[LogicalQubit],
        schema: Schema,
        u4_gate: U4Gate,
    ) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
        [(QuantumGate::sd(), target, None)]
            .into_iter()
            .chain(Self::decompose_x(target, control, schema, u4_gate))
            .chain([(QuantumGate::s(), target, None)])
            .collect()
    }

    fn decompose_z(
        target: LogicalQubit,
        control: &[LogicalQubit],
        schema: Schema,
        u4_gate: U4Gate,
    ) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
        [(QuantumGate::Hadamard, target, None)]
            .into_iter()
            .chain(Self::decompose_x(target, control, schema, u4_gate))
            .chain([(QuantumGate::Hadamard, target, None)])
            .collect()
    }

    fn decompose_phase(
        angle: f64,
        target: LogicalQubit,
        control: &[LogicalQubit],
        schema: Schema,
        u4_gate: U4Gate,
    ) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
        match &schema.algorithm {
            Algorithm::LinearDepth => {
                decompose::u2::linear_depth(Self::Phase(angle.into()), control, target, u4_gate)
            }
            Algorithm::NetworkU2(cx_mode) => network(
                Self::Phase(angle.into()),
                control,
                &schema.aux_qubits.unwrap().1,
                target,
                u4_gate,
                *cx_mode,
                schema.approximated,
            ),
            Algorithm::SU2Rewrite => {
                let control: Vec<_> = control.iter().cloned().chain([target]).collect();
                decompose::su2::decompose(
                    QuantumGate::RotationZ((-2.0 * angle).into()),
                    &control,
                    schema.aux_qubits.unwrap().1[0],
                    u4_gate,
                    DepthMode::Linear,
                    schema.approximated,
                )
            }
            Algorithm::CU2 => decompose::u2::cu2(
                QuantumGate::Phase(angle.into()).matrix(),
                control[0],
                target,
                u4_gate,
            ),
            Algorithm::SingleAuxU2 => decompose::u2::single_aux(
                Self::Phase(angle.into()),
                control,
                schema.aux_qubits.unwrap().1[0],
                target,
                u4_gate,
                schema.approximated,
            ),
            _ => panic!("Invalid Decomposition for Phase Gate"),
        }
    }

    fn decompose_hadamard(
        target: LogicalQubit,
        control: &[LogicalQubit],
        schema: Schema,
        u4_gate: U4Gate,
    ) -> Vec<(QuantumGate, LogicalQubit, Option<LogicalQubit>)> {
        match &schema.algorithm {
            Algorithm::LinearDepth => {
                decompose::u2::linear_depth(Self::Hadamard, control, target, u4_gate)
            }
            Algorithm::NetworkU2(cx_mode) => network(
                Self::Hadamard,
                control,
                &schema.aux_qubits.unwrap().1,
                target,
                u4_gate,
                *cx_mode,
                schema.approximated,
            ),
            Algorithm::SU2Rewrite => {
                su2_rewrite_hadamard(control, schema.aux_qubits.unwrap().1[0], target, u4_gate)
            }
            Algorithm::CU2 => {
                decompose::u2::cu2(QuantumGate::Hadamard.matrix(), control[0], target, u4_gate)
            }
            Algorithm::SingleAuxU2 => decompose::u2::single_aux(
                QuantumGate::Hadamard,
                control,
                schema.aux_qubits.unwrap().1[0],
                target,
                u4_gate,
                schema.approximated,
            ),
            _ => panic!("Invalid Decomposition for Hadamard Gate"),
        }
    }
}

pub(crate) fn matrix_dot(matrix_a: &Matrix, matrix_b: &Matrix) -> Matrix {
    [
        [
            matrix_a[0][0] * matrix_b[0][0] + matrix_a[0][1] * matrix_b[1][0],
            matrix_a[0][0] * matrix_b[0][1] + matrix_a[0][1] * matrix_b[1][1],
        ],
        [
            matrix_a[1][0] * matrix_b[0][0] + matrix_a[1][1] * matrix_b[1][0],
            matrix_a[1][0] * matrix_b[0][1] + matrix_a[1][1] * matrix_b[1][1],
        ],
    ]
}
