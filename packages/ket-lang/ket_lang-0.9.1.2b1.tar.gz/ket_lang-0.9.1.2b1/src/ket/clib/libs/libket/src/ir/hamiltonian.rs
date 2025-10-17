// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use std::hash::Hash;

use itertools::Itertools;
use serde::{Deserialize, Serialize};

use crate::mapping::allocation::Mapping;

use super::qubit::{LogicalQubit, PhysicalQubit, Qubit};

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub enum Pauli {
    PauliX,
    PauliY,
    PauliZ,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PauliTerm<Q> {
    pub pauli: Pauli,
    pub qubit: Q,
}

pub type PauliProduct<Q> = Vec<PauliTerm<Q>>;

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Hamiltonian<Q> {
    pub products: Vec<PauliProduct<Q>>,
    pub coefficients: Vec<f64>,
}

impl<Q> Hamiltonian<Q>
where
    Q: Qubit + Eq + Hash + Clone + Copy,
{
    pub(crate) fn qubits(&self) -> impl Iterator<Item = &Q> {
        use genawaiter::{rc::gen, yield_};
        gen!({
            for qubit in self
                .products
                .iter()
                .flat_map(|product| product.iter().map(|term| &term.qubit))
                .unique()
            {
                yield_!(qubit)
            }
        })
        .into_iter()
    }

    pub fn to_usize_qubit(&self) -> Hamiltonian<usize> {
        Hamiltonian {
            products: self
                .products
                .iter()
                .map(|product| {
                    product
                        .iter()
                        .map(|term| PauliTerm {
                            pauli: term.pauli,
                            qubit: term.qubit.index(),
                        })
                        .collect::<Vec<_>>()
                })
                .collect(),
            coefficients: self.coefficients.clone(),
        }
    }
}

impl Hamiltonian<LogicalQubit> {
    pub(crate) fn map_qubits(&self, mapping: &Mapping) -> Hamiltonian<PhysicalQubit> {
        Hamiltonian {
            products: self
                .products
                .iter()
                .map(|product| {
                    product
                        .iter()
                        .map(|term| PauliTerm {
                            pauli: term.pauli,
                            qubit: *mapping.get_by_left(&term.qubit).unwrap(),
                        })
                        .collect::<Vec<_>>()
                })
                .collect(),
            coefficients: self.coefficients.clone(),
        }
    }
}
