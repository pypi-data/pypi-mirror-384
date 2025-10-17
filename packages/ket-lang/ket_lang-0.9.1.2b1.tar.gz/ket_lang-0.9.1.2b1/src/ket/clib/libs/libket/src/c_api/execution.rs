// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
// SPDX-FileCopyrightText: 2024 2024 Otávio Augusto de Santana Jatobá <otavio.jatoba@grad.ufsc.br>
//
// SPDX-License-Identifier: Apache-2.0

use itertools::Itertools;

use crate::{
    execution::*,
    ir::{
        instructions::Instruction,
        qubit::{LogicalQubit, Qubit},
    },
    prelude::{Hamiltonian, QuantumGate},
    process::{DumpData, Sample},
};

#[repr(C)]
#[derive(Debug, Clone)]
pub struct BatchCExecution {
    submit_execution: fn(*const u8, usize, *const f64, usize),
    get_results: fn(data: &mut *const u8, len: &mut usize),
    clear: fn(),
}

impl BatchExecution for BatchCExecution {
    fn submit_execution(&mut self, circuit: &[Instruction<usize>], parameters: &[f64]) {
        let circuit = serde_json::to_vec(circuit).unwrap();
        (self.submit_execution)(
            circuit.as_ptr(),
            circuit.len(),
            parameters.as_ptr(),
            parameters.len(),
        );
    }

    fn get_results(&mut self) -> ResultData {
        let mut buffer = std::ptr::null();
        let mut len: usize = 0;
        (self.get_results)(&mut buffer, &mut len);
        let buffer = unsafe { std::slice::from_raw_parts(buffer, len) };
        serde_json::from_slice(buffer).unwrap()
    }

    fn clear(&mut self) {
        (self.clear)();
    }
}

#[repr(C)]
#[derive(Debug, Clone)]
pub struct LiveCExecution {
    gate: fn(*const u8, usize, usize, *const usize, usize),
    measure: fn(*const usize, usize) -> u64,
    exp_value: fn(*const u8, usize) -> f64,
    sample: fn(*const usize, usize, usize, &mut *const u8, &mut usize),
    dump: fn(*const usize, usize, &mut *const u8, &mut usize),
    save: fn(&mut *const u8, &mut usize),
    load: fn(*const u8, usize),
}

impl LiveExecution for LiveCExecution {
    fn gate(&mut self, gate: QuantumGate, target: LogicalQubit, control: &[LogicalQubit]) {
        assert!(target.is_main());
        assert!(!control.iter().any(Qubit::is_aux));
        let gate = serde_json::to_vec(&gate).unwrap();
        let control = control.iter().map(Qubit::index).collect_vec();
        (self.gate)(
            gate.as_ptr(),
            gate.len(),
            target.index(),
            control.as_ptr(),
            control.len(),
        );
    }

    fn measure(&mut self, qubits: &[LogicalQubit]) -> u64 {
        assert!(!qubits.iter().any(Qubit::is_aux));
        let qubits = qubits.iter().map(Qubit::index).collect_vec();

        (self.measure)(qubits.as_ptr(), qubits.len())
    }

    fn exp_value(&mut self, hamiltonian: &Hamiltonian<LogicalQubit>) -> f64 {
        let hamiltonian = serde_json::to_vec(&hamiltonian.to_usize_qubit()).unwrap();

        (self.exp_value)(hamiltonian.as_ptr(), hamiltonian.len())
    }

    fn sample(&mut self, qubits: &[LogicalQubit], shots: usize) -> Sample {
        assert!(!qubits.iter().any(Qubit::is_aux));
        let qubits = qubits.iter().map(Qubit::index).collect_vec();

        let mut result = std::ptr::null();
        let mut size = 0;
        (self.sample)(qubits.as_ptr(), qubits.len(), shots, &mut result, &mut size);

        serde_json::from_slice(unsafe { std::slice::from_raw_parts(result, size) }).unwrap()
    }

    fn dump(&mut self, qubits: &[LogicalQubit]) -> DumpData {
        assert!(!qubits.iter().any(Qubit::is_aux));
        let qubits = qubits.iter().map(Qubit::index).collect_vec();

        let mut result = std::ptr::null();
        let mut size = 0;
        (self.dump)(qubits.as_ptr(), qubits.len(), &mut result, &mut size);

        serde_json::from_slice(unsafe { std::slice::from_raw_parts(result, size) }).unwrap()
    }

    fn save(&self) -> Vec<u8> {
        let mut result = std::ptr::null();
        let mut size = 0;
        (self.save)(&mut result, &mut size);

        unsafe { std::slice::from_raw_parts(result, size).to_vec() }
    }

    fn load(&mut self, data: &[u8]) {
        (self.load)(data.as_ptr(), data.len())
    }
}

#[no_mangle]
/// # Safety
pub unsafe extern "C" fn ket_make_configuration(
    execution_target_json: *const u8,
    execution_target_size: usize,
    batch_execution: *const BatchCExecution,
    live_execution: *const LiveCExecution,
    result: &mut *mut (ExecutionTarget, Option<QuantumExecution>),
) -> i32 {
    let execution: Option<QuantumExecution> = if !batch_execution.is_null() {
        Some(QuantumExecution::Batch(Box::new(unsafe {
            (*batch_execution).clone()
        })))
    } else if !live_execution.is_null() {
        Some(QuantumExecution::Live(Box::new(unsafe {
            (*live_execution).clone()
        })))
    } else {
        None
    };

    let execution_target =
        unsafe { std::slice::from_raw_parts(execution_target_json, execution_target_size) };
    let execution_target = serde_json::from_slice(execution_target).unwrap();

    *result = Box::into_raw(Box::new((execution_target, execution)));

    0
}
