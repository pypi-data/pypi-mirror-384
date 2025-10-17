// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use std::{collections::HashMap, hash::Hash};

use itertools::chain;

use crate::{
    execution::U2Gates,
    graph::GraphMatrix,
    ir::{
        gate::{matrix_dot, Param, QuantumGate},
        hamiltonian::Hamiltonian,
        instructions::Instruction,
        qubit::{LogicalQubit, PhysicalQubit, Qubit},
    },
};

#[derive(Debug, Clone)]
pub(crate) struct Circuit<Q> {
    pub(crate) instructions: Vec<Instruction<Q>>,
    pub(crate) lines: HashMap<Q, Vec<usize>>,
    pub(crate) gate_count: HashMap<usize, i64>,
    pub(crate) qubit_depth: HashMap<Q, usize>,
    pub(crate) measure_indexes: Vec<usize>,
    pub(crate) exp_value_indexes: Vec<usize>,
    pub(crate) param_gates: Vec<usize>,
}

impl<Q> Circuit<Q>
where
    Q: Qubit + Eq + Hash + Copy + From<usize> + Sync,
{
    fn last_gate_index(&self, qubit: Q) -> Option<usize> {
        if let Some(gate_line) = self.lines.get(&qubit) {
            for index in gate_line.iter().rev() {
                match self.instructions[*index] {
                    Instruction::Gate { gate, .. } => match gate {
                        QuantumGate::RotationX(Param::Ref { .. })
                        | QuantumGate::RotationY(Param::Ref { .. })
                        | QuantumGate::RotationZ(Param::Ref { .. })
                        | QuantumGate::Phase(Param::Ref { .. }) => return None,
                        _ => return Some(*index),
                    },
                    Instruction::Identity => continue,
                    _ => return None,
                }
            }
        }
        None
    }

    fn matches_inverse(&self, index: usize, gate: &QuantumGate, target: Q, control: &[Q]) -> bool {
        if let Instruction::Gate {
            gate: last_gate,
            target: last_target,
            control: last_control,
        } = &self.instructions[index]
        {
            target == *last_target
                && gate.is_inverse(last_gate)
                && control.len() == last_control.len()
                && control.iter().all(|c| last_control.contains(c))
                && control
                    .iter()
                    .all(|qubit| (self.last_gate_index(*qubit) == Some(index)))
        } else {
            panic!("expecting a gate")
        }
    }

    pub fn instruction(&self, index: usize) -> &Instruction<Q> {
        &self.instructions[index]
    }

    pub fn gate(&mut self, gate: QuantumGate, target: Q, control: &[Q]) -> Option<usize> {
        if gate.is_identity() {
            return None;
        }

        let gate_index = self.instructions.len();
        let num_qubits = control.len() + 1;

        if let Some(last_gate_index) = self.last_gate_index(target) {
            if self.matches_inverse(last_gate_index, &gate, target, control) {
                std::mem::take(&mut self.instructions[last_gate_index]);
                *self.gate_count.entry(num_qubits).or_insert(1) -= 1;
                return None;
            }
        }

        for qubit in control.iter().chain([&target]) {
            self.lines.entry(*qubit).or_default().push(gate_index);
        }

        self.update_depth(control, target);

        if matches!(
            gate,
            QuantumGate::RotationX(Param::Ref { .. })
                | QuantumGate::RotationY(Param::Ref { .. })
                | QuantumGate::RotationZ(Param::Ref { .. })
                | QuantumGate::Phase(Param::Ref { .. })
        ) {
            self.param_gates.push(gate_index);
        }

        let index = self.instructions.len();

        self.instructions.push(Instruction::Gate {
            gate,
            target,
            control: control.to_owned(),
        });

        *self.gate_count.entry(num_qubits).or_insert(0) += 1;

        Some(index)
    }

    pub fn sample(&mut self, qubits: &[Q], shots: usize, index: usize) {
        let inst_index = self.instructions.len();
        for qubit in qubits {
            self.lines.entry(*qubit).or_default().push(inst_index);
        }

        self.instructions.push(Instruction::Sample {
            qubits: qubits.to_owned(),
            index,
            shots,
        });
    }

    fn update_depth(&mut self, control: &[Q], target: Q) {
        if !control.is_empty() {
            let max = chain!(
                control
                    .iter()
                    .map(|c| self.qubit_depth.get(c).cloned().unwrap_or(0)),
                [self.qubit_depth.get(&target).cloned().unwrap_or(0)]
            )
            .max()
            .unwrap_or(0)
                + 1;

            for c in control {
                self.qubit_depth.insert(*c, max);
            }
            self.qubit_depth.insert(target, max);
        }
    }

    pub fn depth(&self) -> usize {
        if let Some(value) = self.qubit_depth.values().max() {
            *value
        } else {
            0
        }
    }

    pub(crate) fn reverse_for_mapping(&self) -> Self {
        let mut circuit = Self::default();
        for instruction in self.instructions.iter().rev() {
            if let Instruction::Gate {
                gate,
                target,
                control,
            } = instruction
            {
                circuit.gate(gate.inverse(), *target, control);
            }
        }
        circuit
    }

    pub(crate) fn get_hamiltonian(&self) -> Vec<(Hamiltonian<Q>, usize)> {
        self.exp_value_indexes
            .iter()
            .map(|i| {
                if let Instruction::ExpValue { hamiltonian, index } = &self.instructions[*i] {
                    (hamiltonian.clone(), *index)
                } else {
                    panic!("Expecting a ExpValue instruction")
                }
            })
            .collect()
    }

    pub(crate) fn get_measures(&self) -> Vec<(Vec<Q>, usize)> {
        self.measure_indexes
            .iter()
            .map(|i| {
                if let Instruction::Measure { qubits, index } = &self.instructions[*i] {
                    (qubits.clone(), *index)
                } else {
                    panic!("Expecting a Measure instruction")
                }
            })
            .collect()
    }

    pub(crate) fn exp_value_size(&self) -> usize {
        self.exp_value_indexes.len()
    }

    pub(crate) fn clear_exp_value(&mut self) {
        for index in self.exp_value_indexes.iter() {
            self.instructions[*index] = Instruction::Identity;
        }
        self.exp_value_indexes.clear();
    }

    pub(crate) fn clear_measure(&mut self) {
        for index in self.measure_indexes.iter() {
            self.instructions[*index] = Instruction::Identity;
        }
        self.measure_indexes.clear();
    }

    pub(crate) fn final_instructions(&self) -> Vec<Instruction<usize>> {
        self.instructions
            .iter()
            .map(|i| i.to_usize_qubit())
            .collect()
    }
}

impl Circuit<PhysicalQubit> {
    pub(crate) fn add_instruction(&mut self, instruction: Instruction<PhysicalQubit>) {
        let index = self.instructions.len();
        for qubit in instruction.qubits() {
            self.lines.entry(*qubit).or_default().push(index);
        }

        match &instruction {
            Instruction::Gate {
                target, control, ..
            } => {
                *self.gate_count.entry(control.len() + 1).or_insert(0) += 1;
                self.update_depth(control, *target);
            }
            Instruction::Measure { .. } => {
                self.measure_indexes.push(index);
            }
            Instruction::ExpValue { .. } => {
                self.exp_value_indexes.push(index);
            }
            _ => {}
        }

        self.instructions.push(instruction);
    }

    pub(crate) fn gate_map(&mut self, u2_gates: U2Gates, parameters: &[f64]) {
        for (index, param) in self.param_gates.iter().zip(parameters.iter()) {
            if let Instruction::Gate {
                gate:
                    QuantumGate::RotationX(Param::Ref { value, .. })
                    | QuantumGate::RotationY(Param::Ref { value, .. })
                    | QuantumGate::RotationZ(Param::Ref { value, .. })
                    | QuantumGate::Phase(Param::Ref { value, .. }),
                ..
            } = &mut self.instructions[*index]
            {
                *value = *param;
            } else {
                panic!("Expecting a param gate instruction")
            }
        }

        if matches!(u2_gates, U2Gates::All) {
            return;
        }

        for (qubit, line) in self.lines.iter() {
            let mut gates = line.iter();
            while let Some(index) = gates.next() {
                let instruction = self.instruction(*index);
                if !instruction.one_qubit_gate() {
                    continue;
                }
                let mut matrix = instruction.matrix();

                for next_index in gates.by_ref() {
                    let next_gate = self.instruction(*next_index);
                    if next_gate.one_qubit_gate() {
                        matrix = matrix_dot(&next_gate.matrix(), &matrix);
                        std::mem::take(&mut self.instructions[*next_index]);
                    } else {
                        break;
                    }
                }
                self.instructions[*index] = Instruction::U2Gates {
                    gates: u2_gates.decompose(&matrix),
                    qubit: *qubit,
                };
            }
        }

        let mut new_circuit = Self::default();
        for instruction in self.instructions.iter() {
            match instruction {
                Instruction::Identity => {}
                Instruction::U2Gates { gates, qubit } => {
                    for gate in gates {
                        if gate.is_identity() {
                            continue;
                        }
                        new_circuit.add_instruction(Instruction::Gate {
                            gate: *gate,
                            target: *qubit,
                            control: vec![],
                        });
                    }
                }
                _ => {
                    new_circuit.add_instruction(instruction.clone());
                }
            }
        }

        *self = new_circuit;
    }
}

impl Circuit<LogicalQubit> {
    pub fn measure(&mut self, qubits: &[LogicalQubit], index: usize) {
        let inst_index = self.instructions.len();
        for qubit in qubits {
            self.lines.entry(*qubit).or_default().push(inst_index);
        }

        self.measure_indexes.push(inst_index);

        self.instructions.push(Instruction::Measure {
            qubits: qubits.to_owned(),
            index,
        });
    }

    pub fn exp_value(&mut self, hamiltonian: Hamiltonian<LogicalQubit>, index: usize) {
        let inst_index = self.instructions.len();
        for qubit in hamiltonian.qubits() {
            self.lines.entry(*qubit).or_default().push(inst_index);
        }

        self.exp_value_indexes.push(inst_index);

        self.instructions
            .push(Instruction::ExpValue { hamiltonian, index });
    }

    pub fn dump(&mut self, qubits: &[LogicalQubit], index: usize) {
        let inst_index = self.instructions.len();
        for qubit in qubits {
            self.lines.entry(*qubit).or_default().push(inst_index);
        }

        self.instructions.push(Instruction::Dump {
            qubits: qubits.to_owned(),
            index,
        });
    }

    pub fn alloc_aux_qubit(&mut self, aux_qubit: LogicalQubit, main_qubit: LogicalQubit) {
        assert!(aux_qubit.is_aux());
        assert!(main_qubit.is_main());
        let aux_line = self.lines.remove(&aux_qubit);
        if let Some(line) = aux_line {
            for index in line {
                self.instructions
                    .get_mut(index)
                    .unwrap()
                    .replace_qubit(aux_qubit, main_qubit);
                self.lines.entry(main_qubit).or_default().push(index);
            }
        }
    }

    pub fn interaction_graph(&self) -> GraphMatrix<LogicalQubit> {
        let mut graph = GraphMatrix::new(self.lines.len());
        for (index, instruction) in self.instructions.iter().enumerate() {
            if instruction.is_ctrl_gate() {
                let mut qubits = instruction.qubits();
                let i = *qubits.next().unwrap();
                let j = *qubits.next().unwrap();
                if graph.edge(i, j).is_none() {
                    graph.set_edge(i, j, index as i64);
                }
            }
        }
        for i in self.lines.keys() {
            for j in self.lines.keys() {
                if i != j && graph.edge(*i, *j).is_none() {
                    graph.set_edge(*i, *j, self.instructions.len() as i64);
                }
            }
        }
        graph.calculate_distance();
        graph
    }
}

impl<Q> Default for Circuit<Q> {
    fn default() -> Self {
        Self {
            instructions: Default::default(),
            lines: Default::default(),
            gate_count: Default::default(),
            qubit_depth: Default::default(),
            measure_indexes: Default::default(),
            exp_value_indexes: Default::default(),
            param_gates: Default::default(),
        }
    }
}
