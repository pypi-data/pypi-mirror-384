// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use crate::{
    decompose,
    ir::{
        gate::{Matrix, QuantumGate},
        hamiltonian::Hamiltonian,
        instructions::Instruction,
        qubit::LogicalQubit,
    },
    process::{DumpData, Sample},
};
use serde::{Deserialize, Serialize};
use std::f64::consts::FRAC_PI_2;

/// Quantum Execution target configuration.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ExecutionTarget {
    /// Number of qubits available.
    pub num_qubits: usize,
    /// QPU architecture. If None, only logical circuit is generated
    pub qpu: Option<QPU>,
    /// How runtime lib will handle the execution.
    pub execution_protocol: ExecutionProtocol,
    /// If gradient will be computed and how.
    pub gradient: Option<Gradient>,
}

/// Quantum Execution target.
#[derive(Debug)]
pub enum QuantumExecution {
    /// Dynamic quantum execution.
    Live(Box<dyn LiveExecution>),
    /// Non-interactive quantum execution.
    Batch(Box<dyn BatchExecution>),
}

/// How the execution will be handled.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ExecutionProtocol {
    /// All measurements are computed by the execution target.
    ManagedByTarget {
        measure: Capability,
        sample: Capability,
        exp_value: Capability,
        dump: Capability,
    },
    /// The measure and expected value are computed by the runtime lib.
    SampleBased(ExpValueStrategy),
}

impl Default for ExecutionProtocol {
    fn default() -> Self {
        Self::ManagedByTarget {
            measure: Default::default(),
            sample: Default::default(),
            exp_value: Default::default(),
            dump: Default::default(),
        }
    }
}

/// How the expected value of an Hamiltonian can be computed.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ExpValueStrategy {
    /// Using a sample for each observable.
    DirectSample(usize),
    /// Using classical shadows.
    ClassicalShadows {
        /// Weights for selecting the random measurement basis (X, Y,Z).
        bias: (u8, u8, u8),
        /// Number of measurement rounds.
        samples: usize,
        /// Number of shorts for each measurement round.
        shots: usize,
    },
}

/// QPU architecture;
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QPU {
    /// Qubit connectivity. If None, no circuit mapping will be performed.
    pub coupling_graph: Option<Vec<(usize, usize)>>,
    /// Single-qubit gates supported by the QPU.
    pub u2_gates: U2Gates,
    /// Two-qubits gates supported by the QPU.
    pub u4_gate: U4Gate,
}

/// Single qubit gate supported by the QPU.
#[derive(Debug, Default, Clone, Copy, Serialize, Deserialize)]
pub enum U2Gates {
    #[default]
    /// All gates supported.
    All,
    /// RZ and RY supported.
    ZYZ,
    /// RZ and SX supported.
    RzSx,
}

/// Two-qubit gates supported by the QPU.
#[derive(Debug, Default, Clone, Copy, Serialize, Deserialize)]
pub enum U4Gate {
    /// CNOT gate supported.
    #[default]
    CX,
    /// Controlled-Z gate supported.
    CZ,
}

/// Execution capability for a measurement operation.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub enum Capability {
    /// Operation not supported by the execution target.
    #[default]
    Unsupported,
    /// Operation supported by the execution target, but limited.
    Basic,
    /// Operation supported by the execution target.
    Advanced,
}

/// How the gradient can be computed.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Gradient {
    /// Compute gradient using the parameter shift rule.
    ParameterShift,
    /// Gradient computed by the execution target.
    NativeSupport,
}

pub trait LiveExecution {
    fn gate(&mut self, gate: QuantumGate, target: LogicalQubit, control: &[LogicalQubit]);
    fn measure(&mut self, qubits: &[LogicalQubit]) -> u64;
    fn exp_value(&mut self, hamiltonian: &Hamiltonian<LogicalQubit>) -> f64;
    fn sample(&mut self, qubits: &[LogicalQubit], shots: usize) -> Sample;
    fn dump(&mut self, qubits: &[LogicalQubit]) -> DumpData;

    fn save(&self) -> Vec<u8>;
    fn load(&mut self, data: &[u8]);
}

pub trait BatchExecution {
    fn submit_execution(&mut self, circuit: &[Instruction<usize>], parameters: &[f64]);
    fn get_results(&mut self) -> ResultData;
    fn clear(&mut self);
}

#[derive(Debug, Clone, Default, Deserialize, Serialize)]
pub struct ResultData {
    pub measurements: Vec<u64>,
    pub exp_values: Vec<f64>,
    pub samples: Vec<Sample>,
    pub dumps: Vec<DumpData>,
    pub gradients: Option<Vec<f64>>,
}

impl U2Gates {
    pub fn decompose(&self, matrix: &Matrix) -> Vec<QuantumGate> {
        match self {
            Self::ZYZ => Self::decompose_zyz(matrix),
            Self::RzSx => Self::decompose_rzsx(matrix),
            Self::All => panic!("decomposition not required"),
        }
    }

    fn decompose_zyz(matrix: &Matrix) -> Vec<QuantumGate> {
        let (_, theta_0, theta_1, theta_2) = decompose::util::zyz(*matrix);
        if theta_1.abs() <= 1e-14 {
            vec![QuantumGate::RotationZ((theta_2 + theta_0).into())]
        } else {
            vec![
                QuantumGate::RotationZ(theta_2.into()),
                QuantumGate::RotationY(theta_1.into()),
                QuantumGate::RotationZ(theta_0.into()),
            ]
        }
    }

    fn decompose_rzsx(matrix: &Matrix) -> Vec<QuantumGate> {
        let (_, theta_0, theta_1, theta_2) = decompose::util::zyz(*matrix);
        if theta_1.abs() <= 1e-14 {
            vec![QuantumGate::RotationZ((theta_2 + theta_0).into())]
        } else {
            vec![
                QuantumGate::RotationZ(theta_2.into()),
                QuantumGate::RotationX(FRAC_PI_2.into()),
                QuantumGate::RotationZ(theta_1.into()),
                QuantumGate::RotationX((-FRAC_PI_2).into()),
                QuantumGate::RotationZ(theta_0.into()),
            ]
        }
    }
}

impl std::fmt::Debug for dyn LiveExecution {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("LiveExecution")
    }
}

impl std::fmt::Debug for dyn BatchExecution {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("BatchExecution")
    }
}

impl U4Gate {
    pub(crate) fn cnot<Q: Copy>(&self, control: Q, target: Q) -> Vec<(QuantumGate, Q, Option<Q>)> {
        match self {
            Self::CX => vec![(QuantumGate::PauliX, target, Some(control))],
            Self::CZ => vec![
                (QuantumGate::Hadamard, target, None),
                (QuantumGate::PauliZ, target, Some(control)),
                (QuantumGate::Hadamard, target, None),
            ],
        }
    }

    pub(crate) fn cz<Q: Copy>(&self, control: Q, target: Q) -> Vec<(QuantumGate, Q, Option<Q>)> {
        match self {
            Self::CX => vec![
                (QuantumGate::Hadamard, target, None),
                (QuantumGate::PauliX, target, Some(control)),
                (QuantumGate::Hadamard, target, None),
            ],
            Self::CZ => vec![(QuantumGate::PauliZ, target, Some(control))],
        }
    }

    pub(crate) fn swap<Q: Copy>(&self, qubit_a: Q, qubit_b: Q) -> Vec<(QuantumGate, Q, Option<Q>)> {
        self.cnot(qubit_a, qubit_b)
            .into_iter()
            .chain(self.cnot(qubit_b, qubit_a))
            .chain(self.cnot(qubit_a, qubit_b))
            .collect()
    }
}
