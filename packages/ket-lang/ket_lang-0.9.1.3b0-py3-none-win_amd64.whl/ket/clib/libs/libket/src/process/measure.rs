// SPDX-FileCopyrightText: 2025 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use crate::{
    error::Result,
    execution::{Capability, LiveExecution, QuantumExecution},
    ir::qubit::LogicalQubit,
    prelude::Hamiltonian,
};

use super::{ExecutionProtocol, Process};

impl Process {
    fn live_execution_or_none<F, T>(&mut self, call: F) -> Option<T>
    where
        F: Fn(&mut Box<dyn LiveExecution>) -> T,
    {
        if let Some(QuantumExecution::Live(execution)) = self.quantum_execution.as_mut() {
            Some(call(execution))
        } else {
            None
        }
    }

    pub fn measure(&mut self, qubits: &[LogicalQubit]) -> Result<usize> {
        self.non_gate_checks(Some(qubits), self.features.measure)?;
        self.execute_gate_queue(0);

        let index = self.measurements.len();

        self.logical_circuit.measure(qubits, index);

        let result = self.live_execution_or_none(|execution| execution.measure(qubits));
        self.measurements.push(result);

        for qubit in qubits {
            self.valid_qubit.insert(*qubit, true);
        }

        if !matches!(
            self.execution_target.execution_protocol,
            ExecutionProtocol::ManagedByTarget {
                measure: Capability::Advanced,
                ..
            }
        ) {
            for qubit in qubits {
                self.valid_qubit.insert(*qubit, false);
            }
        }
        Ok(index)
    }

    pub fn sample(&mut self, qubits: &[LogicalQubit], shots: usize) -> Result<usize> {
        self.non_gate_checks(Some(qubits), self.features.sample)?;
        self.execute_gate_queue(0);

        let index = self.samples.len();

        self.logical_circuit.sample(qubits, shots, index);

        let result = self.live_execution_or_none(|execution| execution.sample(qubits, shots));
        self.samples.push(result);

        if self.execute_after_sample() {
            self.execute()?
        }

        Ok(index)
    }

    pub fn exp_value(&mut self, hamiltonian: Hamiltonian<LogicalQubit>) -> Result<usize> {
        let qubits = hamiltonian.qubits().cloned().collect::<Vec<_>>();
        self.non_gate_checks(Some(&qubits), self.features.exp_value)?;
        self.execute_gate_queue(0);

        let index = self.exp_values.len();

        let result = self.live_execution_or_none(|execution| execution.exp_value(&hamiltonian));
        self.exp_values.push(result);

        self.logical_circuit.exp_value(hamiltonian, index);

        if self.execute_after_exp_value() {
            self.execute()?;
        }

        Ok(index)
    }

    pub fn dump(&mut self, qubits: &[LogicalQubit]) -> Result<usize> {
        self.non_gate_checks(Some(qubits), self.features.dump)?;
        self.execute_gate_queue(0);

        let index = self.dumps.len();

        self.logical_circuit.dump(qubits, index);

        let result = self.live_execution_or_none(|execution| execution.dump(qubits));
        self.dumps.push(result);

        if self.execute_after_dump() {
            self.execute()?;
        }

        Ok(index)
    }
}
