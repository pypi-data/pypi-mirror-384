// SPDX-FileCopyrightText: 2025 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use std::collections::{HashMap, HashSet};

use itertools::Itertools;

use crate::{
    error::{KetError, Result},
    ir::qubit::{LogicalQubit, Qubit},
    prelude::QuantumGate,
    process::Process,
};

#[derive(Debug, Default)]
pub(super) struct AuxQubit {
    /// Number of auxiliary allocated
    pub count: usize,

    /// Number of auxiliary group allocated
    id_count: usize,

    /// Number of aux group allocate and not free
    pub open_alloc: usize,

    pub open_clean_alloc: usize,

    /// Top stack (Next to be free, Can execute gate until)
    pub alloc_stack: Vec<(usize, usize)>,

    /// Number of qubits allocated and not free
    pub being_used: usize,

    /// Map group id into (aux, interaction group)
    pub registry: HashMap<usize, (Vec<LogicalQubit>, Option<Vec<LogicalQubit>>)>,

    /// Map qubit to its group id
    registry_rev: HashMap<LogicalQubit, usize>,

    /// Main qubits being used as aux
    pub using: HashSet<LogicalQubit>,

    pub state: Vec<AuxState>,
    pub blocked_qubits: Vec<HashSet<LogicalQubit>>,
    pub blocked_qubits_undo: Vec<HashSet<LogicalQubit>>,

    pub is_permutation: usize,
    pub is_diagonal: usize,
}

#[derive(Debug, Clone, Copy, Default)]
pub(super) enum AuxState {
    #[default]
    Begin,
    Mid,
    Undo,
}

impl AuxQubit {
    pub fn register_alloc(
        &mut self,
        aux_qubits: Vec<LogicalQubit>,
        interacting_qubits: Option<Vec<LogicalQubit>>,
        next_gate_queue: usize,
    ) -> usize {
        let id = self.id_count;
        self.open_alloc += 1;
        if interacting_qubits.is_none() {
            self.open_clean_alloc += 1;
        }
        self.id_count += 1;

        self.count += aux_qubits.len();
        self.being_used += aux_qubits.len();

        for a in &aux_qubits {
            self.registry_rev.insert(*a, id);
        }

        self.registry.insert(id, (aux_qubits, interacting_qubits));

        self.alloc_stack.push((id, next_gate_queue));

        id
    }

    pub fn register_free(
        &mut self,
        aux_qubits: Vec<LogicalQubit>,
        is_clean: bool,
        main_qubits: HashSet<LogicalQubit>,
    ) {
        if is_clean {
            self.open_clean_alloc -= 1;
        }
        self.being_used -= aux_qubits.len();
        for a in &aux_qubits {
            self.registry_rev.remove(a);
        }
        self.open_alloc -= 1;
        if self.open_alloc == 0 {
            self.using.clear();
        } else {
            self.using.extend(main_qubits);
        }
    }

    pub fn is_dirty(&self, qubit: &LogicalQubit) -> bool {
        self.registry_rev
            .get(qubit)
            .is_some_and(|id| self.registry.get(id).unwrap().1.is_some())
    }

    pub fn validate_gate(
        &mut self,
        gate: &QuantumGate,
        target: &LogicalQubit,
        ctrl: &[LogicalQubit],
    ) -> Result<()> {
        if let Some(aux_state) = self.state.last() {
            match aux_state {
                AuxState::Begin => {
                    if self.is_permutation == 0 && !gate.is_permutation() {
                        return Err(KetError::UncomputeFaill);
                    }
                }
                AuxState::Mid => {
                    if target.is_aux() && !self.is_dirty(target) && !gate.is_diagonal() {
                        return Err(KetError::UncomputeFaill);
                    } else if !gate.is_diagonal() {
                        self.blocked_qubits.last_mut().unwrap().insert(*target);
                    }
                }
                AuxState::Undo => {
                    if self.is_permutation == 0 && !gate.is_permutation() {
                        return Err(KetError::UncomputeFaill);
                    }
                    if ctrl
                        .iter()
                        .chain([target])
                        .any(|q| self.blocked_qubits.last().unwrap().contains(q))
                    {
                        return Err(KetError::UncomputeFaill);
                    }

                    if !gate.is_diagonal() {
                        self.blocked_qubits_undo.last_mut().unwrap().insert(*target);
                    }
                }
            }
        }

        Ok(())
    }
}

impl Process {
    pub fn alloc_aux(
        &mut self,
        num_qubits: usize,
        interacting_qubits: Option<&[LogicalQubit]>,
    ) -> Result<(Vec<LogicalQubit>, usize)> {
        let num_qubits_needed = if let Some(interacting_qubits) = interacting_qubits {
            interacting_qubits.len()
        } else {
            self.allocated_qubits
        } + num_qubits
            + self.aux.using.len()
            + self.aux.being_used;

        if num_qubits_needed > self.execution_target.num_qubits {
            return Err(KetError::MaxQubitsReached);
        }

        let result: Vec<_> = (0..num_qubits)
            .map(|index| LogicalQubit::aux(index + self.aux.count))
            .collect();

        let id = self.aux.register_alloc(
            result.clone(),
            interacting_qubits.map(|iq| iq.to_owned()),
            self.gate_queue.len(),
        );

        Ok((result, id))
    }

    pub fn free_aux(&mut self, group_id: usize) {
        let gate_until = if let Some((next_id, gate_until)) = self.aux.alloc_stack.pop() {
            assert!(next_id == group_id);
            gate_until
        } else {
            panic!("No aux qubits to free")
        };

        let (aux_qubits, interacting_qubits) = self.aux.registry.remove(&group_id).unwrap();

        let mut allocated = HashSet::new();

        for aux_qubit in &aux_qubits {
            let main_qubit = if let Some(interacting_qubits) = &interacting_qubits {
                let mut main_qubit = None;

                for candidate_qubit in (0..self.execution_target.num_qubits)
                    .map(LogicalQubit::main)
                    .sorted_by_key(|q| self.logical_circuit.qubit_depth.get(q).unwrap_or(&0))
                {
                    if !allocated.contains(&candidate_qubit)
                        && !interacting_qubits.contains(&candidate_qubit)
                        && !self.aux.using.contains(&candidate_qubit)
                    {
                        main_qubit = Some(candidate_qubit);
                        break;
                    }
                }
                main_qubit.unwrap()
            } else {
                let mut main_qubit = None;
                for candidate_qubit in (self.allocated_qubits..self.execution_target.num_qubits)
                    .map(LogicalQubit::main)
                    .sorted_by_key(|q| self.logical_circuit.qubit_depth.get(q).unwrap_or(&0))
                {
                    if !allocated.contains(&candidate_qubit)
                        && !self.aux.using.contains(&candidate_qubit)
                    {
                        main_qubit = Some(candidate_qubit);
                        break;
                    }
                }
                main_qubit.unwrap()
            };

            allocated.insert(main_qubit);
            self.logical_circuit.alloc_aux_qubit(*aux_qubit, main_qubit);
        }

        self.execute_gate_queue(gate_until);
        for q in &aux_qubits {
            self.valid_qubit.insert(*q, false);
        }

        self.aux
            .register_free(aux_qubits, interacting_qubits.is_none(), allocated);
    }

    pub fn is_diagonal_begin(&mut self) {
        self.aux.is_diagonal += 1;
    }

    pub fn is_diagonal_end(&mut self) {
        self.aux.is_diagonal -= 1;
    }

    pub fn is_permutation_begin(&mut self) {
        self.aux.is_permutation += 1;
    }

    pub fn is_permutation_end(&mut self) {
        self.aux.is_permutation -= 1;
    }

    pub fn around_begin(&mut self) {
        if self.aux.open_clean_alloc != 0 {
            self.aux.state.push(AuxState::Begin);
        }
    }

    pub fn around_mid(&mut self) {
        if let Some(state) = self.aux.state.last_mut() {
            *state = match state {
                AuxState::Begin => {
                    self.aux.blocked_qubits.push(Default::default());
                    AuxState::Mid
                }
                state => unreachable!("around_mid: unreachable state={:?}", state),
            };
        }
    }

    pub fn around_undo(&mut self) {
        if let Some(state) = self.aux.state.last_mut() {
            *state = match state {
                AuxState::Mid => {
                    self.aux.blocked_qubits_undo.push(Default::default());
                    AuxState::Undo
                }
                state => unreachable!("around_undo: unreachable state={:?}", state),
            };
        }
    }

    pub fn around_end(&mut self) {
        if let Some(state) = self.aux.state.pop() {
            match state {
                AuxState::Undo => {
                    let blocked_qubits = self.aux.blocked_qubits.pop().unwrap();
                    let blocked_qubits_undo = self.aux.blocked_qubits_undo.pop().unwrap();

                    if let Some(blocked_qubits_last) = self.aux.blocked_qubits.last_mut() {
                        blocked_qubits_last.extend(blocked_qubits);
                        blocked_qubits_last.extend(blocked_qubits_undo);
                    }
                }
                state => unreachable!("around_end: unreachable state={:?}", state),
            };
        }
    }
}
