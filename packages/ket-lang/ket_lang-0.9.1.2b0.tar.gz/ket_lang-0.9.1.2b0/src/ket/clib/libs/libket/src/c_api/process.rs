// SPDX-FileCopyrightText: 2020 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
// SPDX-FileCopyrightText: 2020 Rafael de Santiago <r.santiago@ufsc.br>
//
// SPDX-License-Identifier: Apache-2.0

//! C API for the `Process` struct.

use itertools::Itertools;

use super::error::wrapper;
use crate::{
    execution::QuantumExecution,
    ir::{
        gate::Param,
        qubit::{LogicalQubit, Qubit},
    },
    prelude::*,
};

/// Creates a new `Process` instance with the given process ID.
///
/// # Arguments
///
/// * `config` -  \[in\] A mutable pointer to a `Configuration` instance.
/// * `process` -  \[out\] A mutable pointer to a `Process` pointer.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
///
/// # Safety
///
/// This function is marked as unsafe because it deals with raw pointers.
#[no_mangle]
pub unsafe extern "C" fn ket_process_new(
    config: *mut (ExecutionTarget, Option<QuantumExecution>),
    process: &mut *mut Process,
) -> i32 {
    let (execution_target, execution) = unsafe { *Box::from_raw(config) };
    *process = Box::into_raw(Box::new(Process::new(execution_target, execution)));
    KetError::Success.error_code()
}

/// Deletes the `Process` instance.
///
/// # Arguments
///
/// * `process` -  \[in\] A pointer to the `Process` instance to be deleted.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
///
/// # Safety
///
/// This function is marked as unsafe because it deals with raw pointers.
#[no_mangle]
pub unsafe extern "C" fn ket_process_delete(process: *mut Process) -> i32 {
    unsafe {
        let _ = Box::from_raw(process);
    }
    KetError::Success.error_code()
}

/// Allocates a qubit for the `Process` instance.
///
/// # Arguments
///
/// * `process` -  \[in\] A mutable reference to the `Process` instance.
/// * `qubit` -  \[out\] A mutable pointer to a `usize`.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
#[no_mangle]
pub extern "C" fn ket_process_allocate_qubit(process: &mut Process, qubit: &mut usize) -> i32 {
    match process.alloc() {
        Ok(result) => {
            *qubit = result.index();
            KetError::Success.error_code()
        }
        Err(error) => error.error_code(),
    }
}

/// Applies a quantum gate to the target `Qubit` in the `Process` instance.
///
/// # Arguments
///
/// * `process` -  \[in\] A mutable reference to the `Process` instance.
/// * `gate` -  \[in\] An integer representing the gate type. See the function body for the mapping of gate values to gate types.
/// * `pi_fraction_top` -  \[in\] The numerator of the fraction part of the angle, used by certain gate types.
/// * `pi_fraction_bottom` -  \[in\] The denominator of the fraction part of the angle, used by certain gate types.
/// * `scalar` -  \[in\] A floating-point parameter value used by certain gate types.
/// * `target` -  \[in\] A reference to the target `Qubit` instance.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
#[no_mangle]
pub extern "C" fn ket_process_apply_gate(
    process: &mut Process,
    gate: i32,
    angle: f64,
    use_param: bool,
    param_index: usize,
    target: usize,
) -> i32 {
    let gate = match gate {
        1 => QuantumGate::PauliX,
        2 => QuantumGate::PauliY,
        3 => QuantumGate::PauliZ,
        10 => QuantumGate::RotationX(if use_param {
            Param::new_ref(param_index, angle)
        } else {
            angle.into()
        }),
        20 => QuantumGate::RotationY(if use_param {
            Param::new_ref(param_index, angle)
        } else {
            angle.into()
        }),
        30 => QuantumGate::RotationZ(if use_param {
            Param::new_ref(param_index, angle)
        } else {
            angle.into()
        }),
        31 => QuantumGate::Phase(if use_param {
            Param::new_ref(param_index, angle)
        } else {
            angle.into()
        }),
        0 => QuantumGate::Hadamard,
        _ => panic!("Undefined Pauli index. Use 0 for H, 1 for X, 2 for Y, and 3 for Z"),
    };

    wrapper(process.gate(gate, LogicalQubit::main(target)))
}

/// Applies a global phase.
///
/// # Arguments
///
/// * `process` -  \[in\] A mutable reference to the `Process` instance.
/// * `pi_fraction_top` -  \[in\] The numerator of the fraction part of the angle.
/// * `pi_fraction_bottom` -  \[in\] The denominator of the fraction part of the angle.
/// * `scalar` -  \[in\] A floating-point parameter value.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
#[no_mangle]
pub extern "C" fn ket_process_apply_global_phase(process: &mut Process, angle: f64) -> i32 {
    wrapper(process.global_phase(angle))
}

/// Measures the specified qubits in the `Process` instance.
///
/// # Arguments
///
/// * `process` -  \[in\] A mutable reference to the `Process` instance.
/// * `qubits` -  \[in\] A mutable pointer to an array of mutable references to `Qubit` instances.
/// * `qubits_size` -  \[in\] The size of the `qubits` array.
/// * `result` -  \[out\] A mutable pointer to a `usize` where the measurement result will be stored.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
///
/// # Safety
///
/// This function is marked as unsafe due to the use of raw pointers.
#[no_mangle]
pub unsafe extern "C" fn ket_process_measure(
    process: &mut Process,
    qubits: *const usize,
    qubits_size: usize,
    result: &mut usize,
) -> i32 {
    let qubits = unsafe { std::slice::from_raw_parts(qubits, qubits_size) };
    let qubits = qubits
        .iter()
        .map(|index| LogicalQubit::main(*index))
        .collect::<Vec<_>>();

    match process.measure(&qubits) {
        Ok(result_id) => {
            *result = result_id;
            KetError::Success.error_code()
        }
        Err(error) => error.error_code(),
    }
}

/// Creates a new `PauliHamiltonian` instance.
///
/// # Arguments
///
/// * `hamiltonian` -  \[out\] A mutable pointer to a `PauliHamiltonian` pointer.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
#[no_mangle]
pub extern "C" fn ket_hamiltonian_new(hamiltonian: &mut *mut Hamiltonian<LogicalQubit>) -> i32 {
    *hamiltonian = Box::into_raw(Box::default());

    KetError::Success.error_code()
}

/// Adds a term to the `PauliHamiltonian`.
///
/// # Arguments
///
/// * `hamiltonian` -  \[in\] A mutable reference to the `PauliHamiltonian` instance.
/// * `pauli` -  \[in\] A pointer to an array of integers representing the Pauli operators (1 for X, 2 for Y, 3 for Z).
/// * `pauli_size` -  \[in\] The size of the `pauli` array.
/// * `qubits` -  \[in\] A pointer to an array of integers representing the qubit indices for each Pauli operator.
/// * `qubits_size` -  \[in\] The size of the `qubits` array.
/// * `coefficients` -  \[in\] The coefficient for the term.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
///
/// # Safety
///
/// This function is marked as unsafe due to the use of raw pointers.
#[no_mangle]
pub unsafe extern "C" fn ket_hamiltonian_add(
    hamiltonian: &mut Hamiltonian<LogicalQubit>,
    pauli: *const i32,
    pauli_size: usize,
    qubits: *const usize,
    qubits_size: usize,
    coefficients: f64,
) -> i32 {
    assert_eq!(pauli_size, qubits_size);

    let pauli = unsafe { std::slice::from_raw_parts(pauli, pauli_size) };
    let qubits = unsafe { std::slice::from_raw_parts(qubits, qubits_size) };
    let qubits = qubits
        .iter()
        .map(|index| LogicalQubit::main(*index))
        .collect::<Vec<_>>();

    let pauli_product: PauliProduct<_> = pauli
        .iter()
        .zip(qubits.iter())
        .map(|(pauli, qubit)| {
            let pauli = match pauli {
                1 => Pauli::PauliX,
                2 => Pauli::PauliY,
                3 => Pauli::PauliZ,
                _ => panic!("Undefined Pauli index. Use 1 for X, 2 for Y, and 3 for Z"),
            };

            PauliTerm {
                pauli,
                qubit: *qubit,
            }
        })
        .collect();

    hamiltonian.products.push(pauli_product);
    hamiltonian.coefficients.push(coefficients);

    KetError::Success.error_code()
}

/// Calculates the expected value of the `PauliHamiltonian` in the `Process` instance.
///
/// # Arguments
///
/// * `process` -  \[in\] A mutable reference to the `Process` instance.
/// * `hamiltonian` -  \[in\] A mutable pointer to a `PauliHamiltonian`.
/// * `result` -  \[out\] A mutable pointer to a `usize` where the result identifier will be stored.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
///
/// # Safety
///
/// This function is marked as unsafe due to the use of raw pointers.
#[no_mangle]
pub unsafe extern "C" fn ket_process_exp_value(
    process: &mut Process,
    hamiltonian: *mut Hamiltonian<LogicalQubit>,
    result: &mut usize,
) -> i32 {
    let hamiltonian = unsafe { Box::from_raw(hamiltonian) };
    match process.exp_value(*hamiltonian) {
        Ok(result_id) => {
            *result = result_id;

            KetError::Success.error_code()
        }
        Err(error) => error.error_code(),
    }
}

/// Samples the specified qubits in the `Process` instance.
///
/// # Arguments
///
/// * `process` -  \[in\] A mutable reference to the `Process` instance.
/// * `qubits` -  \[in\] A pointer to an array of integers representing the qubit indices to be sampled.
/// * `qubits_size` -  \[in\] The size of the `qubits` array.
/// * `shots` -  \[in\] The number of measurement shots.
/// * `result` -  \[out\] A mutable pointer to a `usize` where the result identifier will be stored.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
///
/// # Safety
///
/// This function is marked as unsafe due to the use of raw pointers.
#[no_mangle]
pub unsafe extern "C" fn ket_process_sample(
    process: &mut Process,
    qubits: *const usize,
    qubits_size: usize,
    shots: usize,
    result: &mut usize,
) -> i32 {
    let qubits = unsafe { std::slice::from_raw_parts(qubits, qubits_size) };
    let qubits = qubits
        .iter()
        .map(|index| LogicalQubit::main(*index))
        .collect::<Vec<_>>();

    match process.sample(&qubits, shots) {
        Ok(result_id) => {
            *result = result_id;

            KetError::Success.error_code()
        }
        Err(error) => error.error_code(),
    }
}

/// Dumps the state of the specified qubits in the `Process` instance.
///
/// # Arguments
///
/// * `process` -  \[in\] A mutable reference to the `Process` instance.
/// * `qubits` -  \[in\] A pointer to an array of qubit indices to be dumped.
/// * `qubits_size` -  \[in\] The size of the `qubits` array.
/// * `result` -  \[out\] A mutable pointer to a `usize` representing the result index of the dump.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
///
/// # Safety
///
/// This function is marked as unsafe due to the use of raw pointers.
#[no_mangle]
pub unsafe extern "C" fn ket_process_dump(
    process: &mut Process,
    qubits: *const usize,
    qubits_size: usize,
    result: &mut usize,
) -> i32 {
    let qubits = unsafe { std::slice::from_raw_parts(qubits, qubits_size) };
    let qubits = qubits
        .iter()
        .map(|index| LogicalQubit::main(*index))
        .collect::<Vec<_>>();

    match process.dump(&qubits) {
        Ok(result_id) => {
            *result = result_id;

            KetError::Success.error_code()
        }
        Err(error) => error.error_code(),
    }
}

/// Pushes control qubits onto the control stack in the `Process` instance.
///
/// # Arguments
///
/// * `process` -  \[in\] A mutable reference to the `Process` instance.
/// * `qubits` -  \[in\] A pointer to an array of qubit indices to be pushed onto the control stack.
/// * `qubits_size` -  \[in\] The size of the `qubits` array.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
///
/// # Safety
///
/// This function is marked as unsafe due to the use of raw pointers.
#[no_mangle]
pub unsafe extern "C" fn ket_process_ctrl_push(
    process: &mut Process,
    qubits: *const usize,
    qubits_size: usize,
) -> i32 {
    let qubits = unsafe { std::slice::from_raw_parts(qubits, qubits_size) };
    let qubits = qubits
        .iter()
        .map(|index| LogicalQubit::main(*index))
        .collect::<Vec<_>>();

    wrapper(process.ctrl_push(&qubits))
}

/// Pops control qubits from the control stack in the `Process` instance.
///
/// # Arguments
///
/// * `process` -  \[in\] A mutable reference to the `Process` instance.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
#[no_mangle]
pub extern "C" fn ket_process_ctrl_pop(process: &mut Process) -> i32 {
    wrapper(process.ctrl_pop())
}

/// Pushes control stack in the `Process` instance.
///
/// # Arguments
///
/// * `process` -  \[in\] A mutable reference to the `Process` instance.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
///
/// # Safety
///
/// This function is marked as unsafe due to the use of raw pointers.
#[no_mangle]
pub unsafe extern "C" fn ket_process_ctrl_stack(process: &mut Process) -> i32 {
    wrapper(process.ctrl_begin())
}

/// Pops control stack from the `Process` instance.
///
/// # Arguments
///
/// * `process` -  \[in\] A mutable reference to the `Process` instance.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
#[no_mangle]
pub extern "C" fn ket_process_ctrl_unstack(process: &mut Process) -> i32 {
    wrapper(process.ctrl_end())
}

/// Begins an adjoint operation in the `Process` instance.
///
/// # Arguments
///
/// * `process` -  \[in\] A mutable reference to the `Process` instance.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
#[no_mangle]
pub extern "C" fn ket_process_adj_begin(process: &mut Process) -> i32 {
    wrapper(process.adj_begin())
}

/// Ends an adjoint operation in the `Process` instance.
///
/// # Arguments
///
/// * `process` -  \[in\] A mutable reference to the `Process` instance.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
#[no_mangle]
pub extern "C" fn ket_process_adj_end(process: &mut Process) -> i32 {
    wrapper(process.adj_end())
}

/// Execute the `Process`.
///
/// # Arguments
///
/// * `process` -  \[in\] A mutable reference to the `Process` instance.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
#[no_mangle]
pub extern "C" fn ket_process_execute(process: &mut Process) -> i32 {
    wrapper(process.execute())
}

/// Prepares the `Process` instance for execution.
///
/// # Arguments
///
/// * `process` -  \[in\] A mutable reference to the `Process` instance.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
#[no_mangle]
pub extern "C" fn ket_process_prepare_for_execution(process: &mut Process) -> i32 {
    wrapper(process.prepare_for_execution())
}

/// Gets the JSON representation of the logical instructions in the `Process` instance.
///
/// # Arguments
///
/// * `process` -  \[in\] A mutable reference to the `Process` instance.
/// * `buffer` -  \[in/out\] A mutable pointer to a buffer to store the JSON representation.
/// * `buffer_size` -  \[in\] The size of the provided buffer.
/// * `write_size` -  \[out\] A mutable pointer to the actual size of the written data.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
///
/// # Safety
///
/// This function is marked as unsafe due to the use of raw pointers.
#[no_mangle]
pub unsafe extern "C" fn ket_process_instructions_json(
    process: &mut Process,
    buffer: *mut u8,
    buffer_size: usize,
    write_size: &mut usize,
) -> i32 {
    let instructions = process.instructions_json();
    let instructions = instructions.as_bytes();
    *write_size = instructions.len();
    if buffer_size >= *write_size {
        let buffer = unsafe { std::slice::from_raw_parts_mut(buffer, buffer_size) };
        buffer[..*write_size].copy_from_slice(instructions);
    }

    KetError::Success.error_code()
}

/// Gets the JSON representation of the physical instructions in the `Process` instance.
///
/// # Arguments
///
/// * `process` -  \[in\] A mutable reference to the `Process` instance.
/// * `buffer` -  \[in/out\] A mutable pointer to a buffer to store the JSON representation.
/// * `buffer_size` -  \[in\] The size of the provided buffer.
/// * `write_size` -  \[out\] A mutable pointer to the actual size of the written data.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
///
/// # Safety
///
/// This function is marked as unsafe due to the use of raw pointers.
#[no_mangle]
pub unsafe extern "C" fn ket_process_isa_instructions_json(
    process: &mut Process,
    buffer: *mut u8,
    buffer_size: usize,
    write_size: &mut usize,
) -> i32 {
    let instructions = process.isa_instructions_json();
    let instructions = instructions.as_bytes();
    *write_size = instructions.len();
    if buffer_size >= *write_size {
        let buffer = unsafe { std::slice::from_raw_parts_mut(buffer, buffer_size) };
        buffer[..*write_size].copy_from_slice(instructions);
    }

    KetError::Success.error_code()
}

/// Gets the JSON representation of the metadata in the `Process` instance.
///
/// # Arguments
///
/// * `process` -  \[in\] A mutable reference to the `Process` instance.
/// * `buffer` -  \[in/out\] A mutable pointer to a buffer to store the JSON representation.
/// * `buffer_size` -  \[in\] The size of the provided buffer.
/// * `write_size` -  \[out\] A mutable pointer to the actual size of the written data.
///
/// # Returns
///
/// An integer representing the error code. `0` indicates success.
///
/// # Safety
///
/// This function is marked as unsafe due to the use of raw pointers.
#[no_mangle]
pub unsafe extern "C" fn ket_process_metadata_json(
    process: &mut Process,
    buffer: *mut u8,
    buffer_size: usize,
    write_size: &mut usize,
) -> i32 {
    let metadata = process.metadata();
    let metadata = serde_json::to_string(&metadata).unwrap();
    let metadata = metadata.as_bytes();
    *write_size = metadata.len();

    if buffer_size >= *write_size {
        let buffer = unsafe { std::slice::from_raw_parts_mut(buffer, buffer_size) };
        buffer[..*write_size].copy_from_slice(metadata);
    }

    KetError::Success.error_code()
}

/// # Safety
#[no_mangle]
pub unsafe extern "C" fn ket_process_set_parameter(
    process: &mut Process,
    param: f64,
    index: &mut usize,
) -> i32 {
    match process.parameter(param) {
        Ok(result) => {
            *index = result;
            KetError::Success.error_code()
        }
        Err(err) => err.error_code(),
    }
}

/// # Safety
#[no_mangle]
pub unsafe extern "C" fn ket_process_get_gradient(
    process: &Process,
    index: usize,
    available: &mut bool,
    gradient: &mut f64,
) -> i32 {
    if let Some(value) = process.gradient(index) {
        *available = true;
        *gradient = value;
    } else {
        *available = false;
    }
    KetError::Success.error_code()
}

/// # Safety
#[no_mangle]
pub unsafe extern "C" fn ket_process_save_sim_state(
    process: &Process,
    buffer: *mut u8,
    buffer_size: usize,
    write_size: &mut usize,
) -> i32 {
    let state = process.save_sim_state();

    *write_size = state.len();
    if buffer_size >= *write_size {
        let buffer = unsafe { std::slice::from_raw_parts_mut(buffer, buffer_size) };
        buffer[..*write_size].copy_from_slice(&state);
    }

    KetError::Success.error_code()
}

/// # Safety
#[no_mangle]
pub unsafe extern "C" fn ket_process_load_sim_state(
    process: &mut Process,
    data: *const u8,
    size: usize,
) -> i32 {
    let data = unsafe { std::slice::from_raw_parts(data, size) };

    process.load_sim_state(data);

    KetError::Success.error_code()
}

/// # Safety
#[no_mangle]
pub unsafe extern "C" fn ket_process_is_diagonal_begin(process: &mut Process) -> i32 {
    process.is_diagonal_begin();
    KetError::Success.error_code()
}

/// # Safety
#[no_mangle]
pub unsafe extern "C" fn ket_process_is_diagonal_end(process: &mut Process) -> i32 {
    process.is_diagonal_end();
    KetError::Success.error_code()
}

/// # Safety
#[no_mangle]
pub unsafe extern "C" fn ket_process_is_permutation_begin(process: &mut Process) -> i32 {
    process.is_permutation_begin();

    KetError::Success.error_code()
}

/// # Safety
#[no_mangle]
pub unsafe extern "C" fn ket_process_is_permutation_end(process: &mut Process) -> i32 {
    process.is_permutation_end();

    KetError::Success.error_code()
}

/// # Safety
#[no_mangle]
pub unsafe extern "C" fn ket_process_around_begin(process: &mut Process) -> i32 {
    process.around_begin();
    KetError::Success.error_code()
}

/// # Safety
#[no_mangle]
pub unsafe extern "C" fn ket_process_around_mid(process: &mut Process) -> i32 {
    process.around_mid();
    KetError::Success.error_code()
}

/// # Safety
#[no_mangle]
pub unsafe extern "C" fn ket_process_around_undo(process: &mut Process) -> i32 {
    process.around_undo();
    KetError::Success.error_code()
}

/// # Safety
#[no_mangle]
pub unsafe extern "C" fn ket_process_around_end(process: &mut Process) -> i32 {
    process.around_end();
    KetError::Success.error_code()
}

/// # Safety
#[no_mangle]
pub unsafe extern "C" fn ket_process_allocate_aux(
    process: &mut Process,
    size: usize,
    interacting_qubits: *const usize,
    interacting_qubits_size: usize,
    aux_begin: &mut usize,
    aux_id: &mut usize,
) -> i32 {
    let interacting_qubits = if interacting_qubits_size == 0 {
        None
    } else {
        let interacting_qubits =
            std::slice::from_raw_parts(interacting_qubits, interacting_qubits_size);
        Some(
            interacting_qubits
                .iter()
                .cloned()
                .map(LogicalQubit::main)
                .collect_vec(),
        )
    };

    match process.alloc_aux(size, interacting_qubits.as_deref()) {
        Ok((aux, id)) => {
            *aux_begin = aux[0].index();
            *aux_id = id;
            KetError::Success.error_code()
        }
        Err(err) => err.error_code(),
    }
}

/// # Safety
#[no_mangle]
pub unsafe extern "C" fn ket_process_free_aux(process: &mut Process, aux_id: usize) -> i32 {
    process.free_aux(aux_id);

    KetError::Success.error_code()
}

/// # Safety
#[no_mangle]
pub unsafe extern "C" fn ket_process_approximated_decomposition_begin(
    process: &mut Process,
) -> i32 {
    process.approximated_decomposition_begin();

    KetError::Success.error_code()
}

/// # Safety
#[no_mangle]
pub unsafe extern "C" fn ket_process_approximated_decomposition_end(process: &mut Process) -> i32 {
    process.approximated_decomposition_end();

    KetError::Success.error_code()
}
