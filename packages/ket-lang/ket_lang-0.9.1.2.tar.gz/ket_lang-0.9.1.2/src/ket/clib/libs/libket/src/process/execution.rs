// SPDX-FileCopyrightText: 2025 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use crate::{
    circuit::Circuit,
    error::{KetError, Result},
    execution::{BatchExecution, ExpValueStrategy, Gradient, QuantumExecution, ResultData},
    ir::{
        hamiltonian,
        qubit::{LogicalQubit, PhysicalQubit, Qubit},
    },
    mapping,
    prelude::{Pauli, PauliTerm, QuantumGate, U2Gates},
    process::ExecutionStrategy,
};
use itertools::Itertools;
use rand::{
    distr::{weighted::WeightedIndex, Distribution},
    rng,
};

use std::{collections::HashMap, hash::Hash};

use super::{ExecutionProtocol, Process};

fn submit_execution(
    execution_strategy: &ExecutionStrategy,
    execution: &mut Box<dyn BatchExecution>,
    logical_circuit: &Circuit<LogicalQubit>,
    physical_circuit: Option<&Circuit<PhysicalQubit>>,
    u2_gates: Option<U2Gates>,
    parameters: &[f64],
) -> ResultData {
    match execution_strategy {
        ExecutionStrategy::ManagedByTarget => {
            let circuit = if let Some(physical_circuit) = physical_circuit {
                let mut circuit = physical_circuit.clone();
                circuit.gate_map(u2_gates.unwrap(), parameters);
                circuit.final_instructions()
            } else {
                logical_circuit.final_instructions()
            };

            execution.submit_execution(&circuit, parameters);
            let result = execution.get_results();
            execution.clear();
            result
        }
        ExecutionStrategy::DirectSample(shots) => {
            let mut result = vec![0.0; logical_circuit.exp_value_size()];

            let circuits: Vec<_> = if let Some(physical_circuit) = physical_circuit {
                direct_sample(physical_circuit, *shots)
                    .drain(..)
                    .map(|(mut c, s, i)| {
                        c.gate_map(u2_gates.unwrap(), parameters);
                        (c.final_instructions(), s, i)
                    })
                    .collect()
            } else {
                direct_sample(logical_circuit, *shots)
                    .drain(..)
                    .map(|(c, s, i)| (c.final_instructions(), s, i))
                    .collect()
            };

            for (circuit, coef, index) in circuits {
                execution.submit_execution(&circuit, parameters);
                let data = execution.get_results();

                execution.clear();

                result[index] +=
                    from_sample_to_exp_value(&data.samples[0].0, &data.samples[0].1, *shots) * coef;
            }

            ResultData {
                measurements: vec![],
                exp_values: result,
                samples: vec![],
                dumps: vec![],
                gradients: None,
            }
        }
        ExecutionStrategy::ClassicalShadows {
            bias,
            samples,
            shots,
        } => {
            let result: Vec<f64> = if let Some(physical_circuit) = physical_circuit {
                let hamiltonian = physical_circuit.get_hamiltonian();
                let qubits = hamiltonian
                    .iter()
                    .flat_map(|h| h.0.qubits().cloned())
                    .unique()
                    .collect_vec();

                let rounds = randomized_classical_shadow(qubits.len(), *samples, bias);

                let mut circuits =
                    classical_shadow_circuits(physical_circuit, &qubits, &rounds, *shots);
                let measures = circuits
                    .drain(..)
                    .flat_map(|mut c| {
                        c.gate_map(u2_gates.unwrap(), parameters);
                        execution.submit_execution(&c.final_instructions(), parameters);
                        let data = execution.get_results();
                        execution.clear();

                        data.samples
                    })
                    .collect::<Vec<_>>();

                physical_circuit
                    .get_hamiltonian()
                    .iter()
                    .map(|(h, index)| {
                        (
                            h.products
                                .iter()
                                .zip(&h.coefficients)
                                .map(|(obs, coef)| {
                                    classical_shadow_processing(obs, &measures, *shots, &rounds)
                                        * coef
                                })
                                .sum(),
                            *index,
                        )
                    })
                    .sorted_by_key(|(_, index)| *index)
                    .map(|(exp_value, _)| exp_value)
                    .collect()
            } else {
                let hamiltonian = logical_circuit.get_hamiltonian();
                let qubits = hamiltonian
                    .iter()
                    .flat_map(|h| h.0.qubits().cloned())
                    .unique()
                    .collect_vec();

                let rounds = randomized_classical_shadow(qubits.len(), *samples, bias);

                let mut circuits =
                    classical_shadow_circuits(logical_circuit, &qubits, &rounds, *shots);
                let measures = circuits
                    .drain(..)
                    .flat_map(|c| {
                        execution.submit_execution(&c.final_instructions(), parameters);
                        let data = execution.get_results();
                        execution.clear();
                        data.samples
                    })
                    .collect::<Vec<_>>();

                logical_circuit
                    .get_hamiltonian()
                    .iter()
                    .map(|(h, index)| {
                        (
                            h.products
                                .iter()
                                .zip(&h.coefficients)
                                .map(|(obs, coef)| {
                                    classical_shadow_processing(obs, &measures, *shots, &rounds)
                                        * coef
                                })
                                .sum(),
                            *index,
                        )
                    })
                    .sorted_by_key(|(_, index)| *index)
                    .map(|(exp_value, _)| exp_value)
                    .collect()
            };

            ResultData {
                measurements: vec![],
                exp_values: result,
                samples: vec![],
                dumps: vec![],
                gradients: None,
            }
        }
        ExecutionStrategy::MeasureFromSample(shots) => {
            let (data, measures, qubit_map) = if let Some(physical_circuit) = physical_circuit {
                let measures = physical_circuit.get_measures();
                let qubits = measures
                    .iter()
                    .flat_map(|(q, _)| q)
                    .cloned()
                    .unique()
                    .collect_vec();
                let qubit_map: HashMap<_, _> = qubits
                    .iter()
                    .enumerate()
                    .map(|(i, q)| (q.index(), i))
                    .collect();
                let measures = measures
                    .iter()
                    .map(|(qubits, index)| (qubits.iter().map(Qubit::index).collect_vec(), *index))
                    .collect_vec();

                let mut circuit = physical_circuit.clone();
                circuit.clear_measure();
                circuit.sample(&qubits, *shots, 0);

                circuit.gate_map(u2_gates.unwrap(), parameters);

                execution.submit_execution(&circuit.final_instructions(), parameters);

                (execution.get_results(), measures, qubit_map)
            } else {
                let measures = logical_circuit.get_measures();
                let qubits = measures
                    .iter()
                    .flat_map(|(q, _)| q)
                    .cloned()
                    .unique()
                    .collect_vec();
                let qubit_map: HashMap<_, _> = qubits
                    .iter()
                    .enumerate()
                    .map(|(i, q)| (q.index(), i))
                    .collect();
                let measures = measures
                    .iter()
                    .map(|(qubits, index)| (qubits.iter().map(Qubit::index).collect_vec(), *index))
                    .collect_vec();

                let mut circuit = logical_circuit.clone();
                circuit.clear_measure();
                circuit.sample(&qubits, *shots, 0);

                execution.submit_execution(&circuit.final_instructions(), parameters);

                (execution.get_results(), measures, qubit_map)
            };

            let data = &data.samples[0];
            let data = *data
                .0
                .iter()
                .zip(&data.1)
                .max_by_key(|(_, count)| *count)
                .unwrap()
                .0;

            let results: Vec<_> = measures
                .iter()
                .map(|(qs, index)| {
                    (
                        qs.iter()
                            .enumerate()
                            .map(|(i, q)| {
                                let data_index = qubit_map[q];
                                let bit = (data >> data_index) & 1;
                                bit << i
                            })
                            .reduce(|a, b| a | b)
                            .unwrap_or(0),
                        index,
                    )
                })
                .sorted_by_key(|(_, i)| *i)
                .map(|(r, _)| r)
                .collect();

            ResultData {
                measurements: results,
                exp_values: vec![],
                samples: vec![],
                dumps: vec![],
                gradients: None,
            }
        }
    }
}

type CSRound = Vec<Pauli>;

fn randomized_classical_shadow(
    number_of_qubits: usize,
    samples: usize,
    bias: &(u8, u8, u8),
) -> Vec<CSRound> {
    let mut rng = rng();
    let dist = WeightedIndex::new([bias.0, bias.1, bias.2]).unwrap();
    (0..samples)
        .map(|_| {
            (0..number_of_qubits)
                .map(|_| match dist.sample(&mut rng) {
                    0 => Pauli::PauliX,
                    1 => Pauli::PauliY,
                    2 => Pauli::PauliZ,
                    _ => unreachable!(),
                })
                .collect::<CSRound>()
        })
        .collect()
}

fn classical_shadow_circuits<Q>(
    circuit: &Circuit<Q>,
    qubits: &[Q],
    rounds: &[CSRound],
    shots: usize,
) -> Vec<Circuit<Q>>
where
    Q: Qubit + Eq + Hash + Copy + From<usize> + Sync,
{
    rounds
        .iter()
        .map(|round| {
            let mut circuit = circuit.clone();
            circuit.clear_exp_value();
            for (i, measure) in round.iter().enumerate() {
                match measure {
                    Pauli::PauliX => {
                        circuit.gate(QuantumGate::Hadamard, qubits[i], &[]);
                    }
                    Pauli::PauliY => {
                        circuit.gate(QuantumGate::sd(), qubits[i], &[]);
                        circuit.gate(QuantumGate::Hadamard, qubits[i], &[]);
                    }
                    Pauli::PauliZ => {}
                }
            }
            circuit.sample(qubits, shots, 0);
            circuit
        })
        .collect()
}

fn classical_shadow_processing<Q: Qubit>(
    obs: &[PauliTerm<Q>],
    measures: &[(Vec<u64>, Vec<u64>)],
    shots: usize,
    rounds: &[CSRound],
) -> f64 {
    let matching_measures: Vec<_> = rounds
        .iter()
        .enumerate()
        .filter_map(|(index, round)| {
            if obs
                .iter()
                .all(|term| round[term.qubit.index()] == term.pauli)
            {
                Some(index)
            } else {
                None
            }
        })
        .collect();

    matching_measures
        .iter()
        .map(|index| &measures[*index])
        .flat_map(|(states, counts)| {
            states.iter().zip(counts.iter()).map(|(state, count)| {
                obs.iter()
                    .map(|p| from_u64_to_exp_value(*state, p.qubit.index()))
                    .product::<i32>() as f64
                    * *count as f64
            })
        })
        .sum::<f64>()
        / (matching_measures.len() * shots) as f64
}

fn from_u64_to_exp_value(state: u64, qubit: usize) -> i32 {
    if state & (1 << qubit) == 0 {
        1
    } else {
        -1
    }
}

fn from_sample_to_exp_value(state: &[u64], count: &[u64], shots: usize) -> f64 {
    state
        .iter()
        .zip(count)
        .map(|(state, count)| {
            (if state.count_ones() % 2 == 0 {
                1.0
            } else {
                -1.0
            }) * (*count as f64 / shots as f64)
        })
        .sum::<f64>()
}

fn direct_sample<Q>(circuit: &Circuit<Q>, shots: usize) -> Vec<(Circuit<Q>, f64, usize)>
where
    Q: Qubit + Eq + Hash + Copy + From<usize> + Sync,
{
    let hamiltonian = circuit.get_hamiltonian();

    let mut circuits = Vec::new();
    for (h, index) in hamiltonian.iter() {
        for (p, c) in h.products.iter().zip(&h.coefficients) {
            let mut new_circuit = circuit.clone();
            new_circuit.clear_exp_value();

            let mut qubits = Vec::new();
            assert!(!p.is_empty());

            for term in p {
                match term.pauli {
                    hamiltonian::Pauli::PauliX => {
                        new_circuit.gate(QuantumGate::Hadamard, term.qubit, &[]);
                    }
                    hamiltonian::Pauli::PauliY => {
                        new_circuit.gate(QuantumGate::sd(), term.qubit, &[]);
                        new_circuit.gate(QuantumGate::Hadamard, term.qubit, &[]);
                    }
                    hamiltonian::Pauli::PauliZ => {}
                }
                qubits.push(term.qubit);
            }
            assert!(!qubits.is_empty());
            new_circuit.sample(&qubits, shots, 0);
            circuits.push((new_circuit, *c, *index));
        }
    }

    circuits
}

impl Process {
    fn map_circuit(&mut self) {
        if let Some(coupling_graph) = self.coupling_graph.as_ref() {
            let mapping = mapping::allocation::initial(
                &self.logical_circuit.interaction_graph(),
                coupling_graph,
            );
            let physical_circuit = mapping::map_circuit(
                mapping,
                coupling_graph,
                &self.logical_circuit,
                self.execution_target.qpu.as_ref().unwrap().u4_gate,
                4,
            );
            self.physical_circuit = Some(physical_circuit);
        }
    }

    fn parameter_shift_rule(&mut self, execution: &mut Box<dyn BatchExecution>) {
        (0..self.parameters.len())
            .map(|index| {
                let mut parameters = self.parameters.clone();
                parameters[index] += std::f64::consts::FRAC_PI_2;

                let results = submit_execution(
                    self.execution_strategy.as_ref().unwrap(),
                    execution,
                    &self.logical_circuit,
                    self.physical_circuit.as_ref(),
                    self.execution_target.qpu.as_ref().map(|qpu| qpu.u2_gates),
                    &parameters,
                );

                let e_plus = results.exp_values[0];

                parameters[index] = self.parameters[index] - std::f64::consts::FRAC_PI_2;
                let results = submit_execution(
                    self.execution_strategy.as_ref().unwrap(),
                    execution,
                    &self.logical_circuit,
                    self.physical_circuit.as_ref(),
                    self.execution_target.qpu.as_ref().map(|qpu| qpu.u2_gates),
                    &parameters,
                );

                let e_minus = results.exp_values[0];

                (e_plus - e_minus) / 2.0
            })
            .zip(self.gradients.iter_mut())
            .for_each(|(result, gradient)| {
                *gradient = Some(result);
            });
    }

    pub fn prepare_for_execution(&mut self) -> Result<()> {
        if self.execution_strategy.is_none() {
            self.execution_strategy = Some(match &self.execution_target.execution_protocol {
                ExecutionProtocol::ManagedByTarget { .. } => ExecutionStrategy::ManagedByTarget,
                ExecutionProtocol::SampleBased(ExpValueStrategy::ClassicalShadows {
                    bias,
                    samples,
                    shots,
                }) => {
                    if !self.measurements.is_empty() {
                        ExecutionStrategy::MeasureFromSample(*samples * *shots)
                    } else if !self.samples.is_empty() {
                        ExecutionStrategy::ManagedByTarget
                    } else {
                        ExecutionStrategy::ClassicalShadows {
                            bias: *bias,
                            samples: *samples,
                            shots: *shots,
                        }
                    }
                }
                ExecutionProtocol::SampleBased(ExpValueStrategy::DirectSample(shots)) => {
                    if !self.measurements.is_empty() {
                        ExecutionStrategy::MeasureFromSample(*shots)
                    } else if !self.samples.is_empty() {
                        ExecutionStrategy::ManagedByTarget
                    } else {
                        ExecutionStrategy::DirectSample(*shots)
                    }
                }
            });

            self.map_circuit();
        }
        Ok(())
    }

    pub fn execute(&mut self) -> Result<()> {
        self.prepare_for_execution()?;

        let mut results = None;

        if let Some(QuantumExecution::Batch(mut execution)) = self.quantum_execution.take() {
            results = Some(submit_execution(
                self.execution_strategy.as_ref().unwrap(),
                &mut execution,
                &self.logical_circuit,
                self.physical_circuit.as_ref(),
                self.execution_target.qpu.as_ref().map(|qpu| qpu.u2_gates),
                &self.parameters,
            ));

            if !self.parameters.is_empty()
                && matches!(
                    self.execution_target.gradient,
                    Some(Gradient::ParameterShift)
                )
            {
                self.parameter_shift_rule(&mut execution);
            }
        }

        if let Some(mut results) = results {
            if self.measurements.len() != results.measurements.len()
                || self.exp_values.len() != results.exp_values.len()
                || self.samples.len() != results.samples.len()
                || self.dumps.len() != results.dumps.len()
                || (!self.parameters.is_empty()
                    && matches!(
                        self.execution_target.gradient,
                        Some(Gradient::NativeSupport)
                    )
                    && results
                        .gradients
                        .as_ref()
                        .is_none_or(|gradients| self.gradients.len() != gradients.len()))
            {
                return Err(KetError::ResultDataMismatch);
            }

            results
                .measurements
                .drain(..)
                .zip(self.measurements.iter_mut())
                .for_each(|(result, measurement)| {
                    *measurement = Some(result);
                });

            results
                .exp_values
                .drain(..)
                .zip(self.exp_values.iter_mut())
                .for_each(|(result, exp_value)| {
                    *exp_value = Some(result);
                });

            results
                .samples
                .drain(..)
                .zip(self.samples.iter_mut())
                .for_each(|(result, sample)| {
                    assert_eq!(result.0.len(), result.1.len());
                    *sample = Some(result);
                });

            results
                .dumps
                .drain(..)
                .zip(self.dumps.iter_mut())
                .for_each(|(result, dump)| {
                    *dump = Some(result);
                });

            if let Some(result) = results.gradients.as_mut() {
                result
                    .drain(..)
                    .zip(self.gradients.iter_mut())
                    .for_each(|(result, gradient)| {
                        *gradient = Some(result);
                    });
            }
        }
        Ok(())
    }
}
