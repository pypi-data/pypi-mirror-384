// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

#[derive(thiserror::Error, Debug, Clone, Copy)]
#[repr(i32)]
pub enum KetError {
    #[error("No error occurred")]
    Success,

    #[error("The maximum number of qubits has been reached")]
    MaxQubitsReached,

    #[error("Cannot append instruction to a terminated process")]
    TerminatedProcess,

    #[error("Cannot append non-gate instructions within an inverse scope")]
    InverseScope,

    #[error("Cannot append non-gate instructions within a controlled scope")]
    ControlledScope,

    #[error("Qubit is not available for measurement or gate application")]
    QubitUnavailable,

    #[error("A qubit cannot be both control and target in the same instruction")]
    ControlTargetOverlap,

    #[error("A qubit cannot be used as a control qubit more than once")]
    ControlTwice,

    #[error("A measurement feature (measure, sample, exp_value, or dump) is disabled")]
    MeasurementDisabled,

    #[error("No qubits are available in the current control stack to pop")]
    ControlStackEmpty,

    #[error("No inverse scope is available to end")]
    InverseScopeEmpty,

    #[error("The provided data does not match the expected number of results")]
    ResultDataMismatch,

    #[error("Ending a non-empty control stack is not allowed")]
    ControlStackNotEmpty,

    #[error("Cannot end the primary control stack")]
    ControlStackRemovePrimary,

    #[error("No auxiliary qubit available to free")]
    AuxQubitNotAvailable,

    #[error("Operation not allowed in auxiliary qubits")]
    AuxQubitNotAllowed,

    #[error("Gradient calculation is not enabled in the process")]
    GradientDisabled,

    #[error("Cannot add control qubits to a gate with gradient calculation")]
    ControlledParameter,

    #[error("Fail to uncompute auxiliary qubit")]
    UncomputeFaill,

    #[error("The qubit is not part of the interaction group of the auxiliary qubit")]
    NoInInteractionGroup,
}

pub type Result<T> = std::result::Result<T, KetError>;

impl KetError {
    pub fn error_code(&self) -> i32 {
        *self as i32
    }

    /// # Safety
    pub unsafe fn from_error_code(error_code: i32) -> KetError {
        unsafe { std::mem::transmute(error_code) }
    }
}

#[cfg(test)]
mod tests {
    use super::KetError;

    #[test]
    fn success_is_zero() {
        assert!(KetError::Success.error_code() == 0)
    }
}
