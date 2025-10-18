// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use std::f64::consts::FRAC_PI_4;

use ket::{
    execution::{Capability, ExecutionProtocol},
    prelude::*,
};

fn main() -> Result<(), KetError> {
    set_log_level(3);

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

    let size = 8;

    let qubits: Vec<_> = (0..size).map(|_| process.alloc().unwrap()).collect();

    for qubit in &qubits {
        process.gate(QuantumGate::Hadamard, *qubit)?;
    }

    let steps = ((FRAC_PI_4) * f64::sqrt((1 << size) as f64)) as i64;

    for _ in 0..steps {
        around(
            &mut process,
            |process| {
                for qubit in &qubits {
                    process.gate(QuantumGate::PauliX, *qubit)?;
                }
                Ok(())
            },
            |process| {
                ctrl(process, &qubits[1..], |process| {
                    process.gate(QuantumGate::PauliZ, qubits[0])
                })
            },
        )?;

        around(
            &mut process,
            |process| {
                for qubit in &qubits {
                    process.gate(QuantumGate::Hadamard, *qubit)?;
                }

                for qubit in &qubits {
                    process.gate(QuantumGate::PauliX, *qubit)?;
                }
                Ok(())
            },
            |process| {
                ctrl(process, &qubits[1..], |process| {
                    process.gate(QuantumGate::PauliZ, qubits[0])
                })
            },
        )?;
    }

    let _ = process.sample(&qubits, 1024)?;

    println!("{:#?}", process.metadata());

    Ok(())
}
