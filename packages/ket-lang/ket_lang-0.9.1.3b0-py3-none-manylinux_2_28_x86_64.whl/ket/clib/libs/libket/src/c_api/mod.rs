// SPDX-FileCopyrightText: 2020 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
// SPDX-FileCopyrightText: 2020 Rafael de Santiago <r.santiago@ufsc.br>
//
// SPDX-License-Identifier: Apache-2.0

//! C API Wrapper
//!
//! This module provides a wrapper C for the Rust functions.
//!
//! ## Error Handling
//!
//! The `ket_error_message` function allows retrieving error messages associated with error codes.
//! Given an error code, it returns the corresponding error message string.
//!
//! # Safety
//!
//! Care should be taken when using C functions and data structures.

pub mod error;
pub mod execution;
pub mod objects;
pub mod process;

/// Sets the log level for Libket.
#[no_mangle]
pub extern "C" fn ket_set_log_level(level: u32) -> i32 {
    crate::util::set_log_level(level);
    crate::prelude::KetError::Success.error_code()
}

const BUILD_INFO: &str = build_info::format!("{} v{} [{} {}]", $.crate_info.name, $.crate_info.version, $.compiler, $.target);

#[no_mangle]
pub extern "C" fn ket_build_info(msg: &mut *const u8, size: &mut usize) -> i32 {
    let bytes = BUILD_INFO.as_bytes();
    *size = bytes.len();
    *msg = bytes.as_ptr();
    crate::prelude::KetError::Success.error_code()
}
