// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use std::f64::consts::PI;

use ket::{
    execution::{Capability, ExecutionProtocol},
    ir::qubit::LogicalQubit,
    prelude::*,
};

fn qft(process: &mut Process, qubits: &[LogicalQubit], do_swap: bool) -> Result<(), KetError> {
    if qubits.len() == 1 {
        return process.gate(QuantumGate::Hadamard, qubits[0]);
    }

    let init = &qubits[..qubits.len() - 1];
    let last = qubits[qubits.len() - 1];
    process.gate(QuantumGate::Hadamard, last)?;
    for (i, c) in init.iter().enumerate() {
        c1gate(
            process,
            QuantumGate::Phase((PI / 2.0_f64.powi(i as i32 + 1)).into()),
            *c,
            last,
        )?;
    }
    qft(process, init, false)?;

    if do_swap {
        for i in 0..qubits.len() / 2 {
            swap(process, qubits[i], qubits[qubits.len() - i - 1])?;
        }
    }

    Ok(())
}

fn main() -> Result<(), KetError> {
    let config = ExecutionTarget {
        num_qubits: 12,
        qpu: Some(QPU {
            coupling_graph: Some(ket::ex_arch::GRID12.to_vec()),
            u2_gates: U2Gates::RzSx,
            u4_gate: U4Gate::CZ,
        }),
        execution_protocol: ExecutionProtocol::ManagedByTarget {
            sample: Capability::Basic,
            measure: Capability::Unsupported,
            exp_value: Capability::Unsupported,
            dump: Capability::Unsupported,
        },
        gradient: None,
    };

    let mut process = Process::new(config, None);

    let size = 12;
    let qubits: Vec<_> = (0..size).map(|_| process.alloc().unwrap()).collect();

    qft(&mut process, &qubits, true)?;

    println!("{:#?}", process.metadata());

    Ok(())
}
