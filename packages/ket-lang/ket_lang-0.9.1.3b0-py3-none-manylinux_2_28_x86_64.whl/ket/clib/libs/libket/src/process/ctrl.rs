// SPDX-FileCopyrightText: 2025 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use crate::error::{KetError, Result};
use crate::ir::qubit::LogicalQubit;
use crate::process::Process;

#[derive(Debug)]
pub(super) struct CtrlEngine {
    /// Control qubits stack.
    pub stack: Vec<Vec<Vec<LogicalQubit>>>,
    /// List of control qubits.
    list: Vec<LogicalQubit>,
    /// If the list of control qubits are up to date.
    is_list_valid: bool,
}

impl Default for CtrlEngine {
    fn default() -> Self {
        Self {
            stack: vec![Vec::new()],
            list: Default::default(),
            is_list_valid: Default::default(),
        }
    }
}

impl CtrlEngine {
    /// Get control qubit list
    pub fn get_list(&mut self) -> &[LogicalQubit] {
        if !self.is_list_valid {
            self.list = self
                .stack
                .last()
                .unwrap()
                .clone()
                .into_iter()
                .flatten()
                .collect();
            self.is_list_valid = true;
        }
        &self.list
    }

    /// Add qubits to control qubit list
    pub fn push(&mut self, qubits: &[LogicalQubit]) -> Result<()> {
        if qubits.iter().any(|qubit| self.get_list().contains(qubit)) {
            return Err(KetError::ControlTwice);
        }

        self.stack.last_mut().unwrap().push(qubits.to_owned());
        self.is_list_valid = false;

        Ok(())
    }

    /// Remover qubits from the control qubit list
    pub fn pop(&mut self) -> Result<()> {
        self.is_list_valid = false;

        if self.stack.last_mut().unwrap().pop().is_none() {
            Err(KetError::ControlStackEmpty)
        } else {
            Ok(())
        }
    }

    /// Start a new control qubit list
    pub fn begin(&mut self) -> Result<()> {
        self.stack.push(vec![]);
        self.is_list_valid = false;
        Ok(())
    }

    /// End the control qubit list
    pub fn end(&mut self) -> Result<()> {
        match self.stack.pop() {
            Some(stack) => {
                if !stack.is_empty() {
                    Err(KetError::ControlStackNotEmpty)
                } else {
                    self.is_list_valid = false;
                    if self.stack.is_empty() {
                        Err(KetError::ControlStackRemovePrimary)
                    } else {
                        Ok(())
                    }
                }
            }
            None => Err(KetError::ControlStackRemovePrimary),
        }
    }
}

impl Process {
    pub fn ctrl_push(&mut self, qubits: &[LogicalQubit]) -> Result<()> {
        self.adj_ctrl_checks(Some(qubits))?;
        self.ctrl.push(qubits)
    }

    pub fn ctrl_pop(&mut self) -> Result<()> {
        self.ctrl.pop()
    }

    pub fn adj_begin(&mut self) -> Result<()> {
        self.adj_ctrl_checks(None)?;
        self.adj_stack.push(vec![]);
        Ok(())
    }

    pub fn adj_end(&mut self) -> Result<()> {
        if let Some(mut gates) = self.adj_stack.pop() {
            while let Some(gate) = gates.pop() {
                self.push_gate(gate.inverse());
            }
            Ok(())
        } else {
            Err(KetError::InverseScopeEmpty)
        }
    }

    pub fn ctrl_begin(&mut self) -> Result<()> {
        self.adj_ctrl_checks(None)?;
        self.ctrl.begin()
    }

    pub fn ctrl_end(&mut self) -> Result<()> {
        self.adj_ctrl_checks(None)?;
        self.ctrl.end()
    }
}
