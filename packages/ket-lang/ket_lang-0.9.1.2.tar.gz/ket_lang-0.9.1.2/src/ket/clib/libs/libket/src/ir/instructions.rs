// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use super::{
    gate::{Matrix, QuantumGate},
    hamiltonian::Hamiltonian,
    qubit::{LogicalQubit, PhysicalQubit, Qubit},
};
use crate::mapping::allocation::Mapping;
use serde::{Deserialize, Serialize};
use std::hash::Hash;

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub enum Instruction<Q> {
    Gate {
        gate: QuantumGate,
        target: Q,
        control: Vec<Q>,
    },
    #[default]
    Identity,
    Measure {
        qubits: Vec<Q>,
        index: usize,
    },
    Sample {
        qubits: Vec<Q>,
        index: usize,
        shots: usize,
    },
    Dump {
        qubits: Vec<Q>,
        index: usize,
    },
    ExpValue {
        hamiltonian: Hamiltonian<Q>,
        index: usize,
    },
    U2Gates {
        gates: Vec<QuantumGate>,
        qubit: Q,
    },
}

impl<Q> Instruction<Q>
where
    Q: Qubit + Eq + Hash + Clone + Copy,
{
    pub(crate) fn qubits(&self) -> impl Iterator<Item = &Q> {
        use genawaiter::{rc::gen, yield_};
        gen!({
            match self {
                Instruction::Gate {
                    target, control, ..
                } => {
                    yield_!(target);
                    for qubit in control {
                        yield_!(qubit);
                    }
                }
                Instruction::Measure { qubits, .. }
                | Instruction::Sample { qubits, .. }
                | Instruction::Dump { qubits, .. } => {
                    for qubit in qubits {
                        yield_!(qubit);
                    }
                }
                Instruction::ExpValue { hamiltonian, .. } => {
                    for qubit in hamiltonian.qubits() {
                        yield_!(qubit);
                    }
                }
                _ => {}
            }
        })
        .into_iter()
    }

    pub(crate) fn is_ctrl_gate(&self) -> bool {
        match self {
            Instruction::Gate { control, .. } => !control.is_empty(),
            _ => false,
        }
    }
    pub(crate) fn affect_one_qubit(&self) -> bool {
        match self {
            Instruction::Gate { control, .. } => control.is_empty(),
            Instruction::Measure { qubits, .. }
            | Instruction::Sample { qubits, .. }
            | Instruction::Dump { qubits, .. } => qubits.len() == 1,
            Instruction::Identity => true,
            Instruction::ExpValue { hamiltonian, .. } => {
                let mut qubits = hamiltonian.qubits();
                qubits.next().is_some() && qubits.next().is_none()
            }
            Instruction::U2Gates { .. } => panic!("this instructions is restrict"),
        }
    }

    pub(crate) fn one_qubit_gate(&self) -> bool {
        match self {
            Instruction::Gate { control, .. } => control.is_empty(),
            Instruction::Identity => true,
            _ => false,
        }
    }

    pub(crate) fn matrix(&self) -> Matrix {
        match self {
            Instruction::Gate { gate, .. } => gate.matrix(),
            Instruction::Identity => QuantumGate::Phase(0.0.into()).matrix(),
            _ => panic!("matrix available only for gate instruction"),
        }
    }

    pub(crate) fn to_usize_qubit(&self) -> Instruction<usize> {
        match self {
            Instruction::Gate {
                gate,
                target,
                control,
            } => Instruction::Gate {
                gate: *gate,
                target: target.index(),
                control: control.iter().map(|c| c.index()).collect(),
            },
            Instruction::Identity => Instruction::Identity,
            Instruction::Measure { qubits, index } => Instruction::Measure {
                qubits: qubits.iter().map(|q| q.index()).collect(),
                index: *index,
            },
            Instruction::Sample {
                qubits,
                index,
                shots,
            } => Instruction::Sample {
                qubits: qubits.iter().map(|q| q.index()).collect(),
                index: *index,
                shots: *shots,
            },
            Instruction::Dump { qubits, index } => Instruction::Dump {
                qubits: qubits.iter().map(|q| q.index()).collect(),
                index: *index,
            },
            Instruction::ExpValue { hamiltonian, index } => Instruction::ExpValue {
                hamiltonian: hamiltonian.to_usize_qubit(),
                index: *index,
            },
            Instruction::U2Gates { .. } => {
                panic!("U2Gates instruction should not be present at this point.")
            }
        }
    }
}

impl Instruction<LogicalQubit> {
    pub(crate) fn map_qubits(&self, mapping: &Mapping) -> Instruction<PhysicalQubit> {
        match self {
            Instruction::Gate {
                gate,
                target,
                control,
            } => Instruction::Gate {
                gate: *gate,
                target: *mapping.get_by_left(target).unwrap(),
                control: control
                    .iter()
                    .map(|qubit| *mapping.get_by_left(qubit).unwrap())
                    .collect(),
            },
            Instruction::Measure { qubits, index } => Instruction::Measure {
                qubits: qubits
                    .iter()
                    .map(|qubit| *mapping.get_by_left(qubit).unwrap())
                    .collect(),
                index: *index,
            },
            Instruction::Sample {
                qubits,
                index,
                shots,
            } => Instruction::Sample {
                qubits: qubits
                    .iter()
                    .map(|qubit| *mapping.get_by_left(qubit).unwrap())
                    .collect(),
                index: *index,
                shots: *shots,
            },
            Instruction::Dump { qubits, index } => Instruction::Dump {
                qubits: qubits
                    .iter()
                    .map(|qubit| *mapping.get_by_left(qubit).unwrap())
                    .collect(),
                index: *index,
            },
            Instruction::ExpValue { hamiltonian, index } => Instruction::ExpValue {
                hamiltonian: hamiltonian.map_qubits(mapping),
                index: *index,
            },
            _ => Default::default(),
        }
    }

    pub(crate) fn replace_qubit(&mut self, old: LogicalQubit, new: LogicalQubit) {
        match self {
            Instruction::Gate {
                target, control, ..
            } => {
                if *target == old {
                    *target = new;
                }
                for qubit in control {
                    if *qubit == old {
                        *qubit = new;
                        break;
                    }
                }
            }
            Instruction::Identity => {}
            _ => {
                panic!("Qubit replace should only happens in gate instruction")
            }
        }
    }
}
