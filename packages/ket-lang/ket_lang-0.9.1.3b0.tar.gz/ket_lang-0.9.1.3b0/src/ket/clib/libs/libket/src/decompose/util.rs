// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use crate::ir::gate::{Cf64, Matrix};
use num::{complex::ComplexFloat, Complex};

fn extract_phase(matrix: Matrix) -> f64 {
    let [[a, b], [c, d]] = matrix;
    let det = a * d - b * c;
    1.0 / 2.0 * det.im.atan2(det.re)
}

fn is_close(a: f64, b: f64) -> bool {
    (a - b).abs() < 1e-14
}

pub(crate) fn zyz(matrix: Matrix) -> (f64, f64, f64, f64) {
    let phase = extract_phase(matrix);
    let e_phase = (-Complex::<_>::i() * phase).exp();

    let matrix = [
        [matrix[0][0] * e_phase, matrix[0][1] * e_phase],
        [matrix[1][0] * e_phase, matrix[1][1] * e_phase],
    ];

    let matrix_0_1_abs = matrix[0][0].abs().clamp(-1.0, 1.0);

    let theta_1 = if matrix[0][0].abs() >= matrix[0][1].abs() {
        2.0 * matrix_0_1_abs.acos()
    } else {
        2.0 * matrix[0][1].abs().asin()
    };

    let theta_1_2_cos = (theta_1 / 2.0).cos();
    let theta_0_plus_2 = if !is_close(theta_1_2_cos, 0.0) {
        let tmp = matrix[1][1] / theta_1_2_cos;
        2.0 * tmp.im.atan2(tmp.re)
    } else {
        0.0
    };

    let theta_1_2_sin = (theta_1 / 2.0).sin();
    let theta_0_sub_2 = if !is_close(theta_1_2_sin, 0.0) {
        let tmp = matrix[1][0] / theta_1_2_sin;
        2.0 * tmp.im.atan2(tmp.re)
    } else {
        0.0
    };

    let theta_0 = (theta_0_plus_2 + theta_0_sub_2) / 2.0;
    let theta_2 = (theta_0_plus_2 - theta_0_sub_2) / 2.0;

    (phase, theta_0, theta_1, theta_2)
}

type Vector = (Cf64, Cf64);

pub(super) fn eigen(matrix: Matrix) -> ((Complex<f64>, Vector), (Complex<f64>, Vector)) {
    let [[a, b], [c, d]] = matrix;

    let m = (a + d) / 2.0;
    let p = a * d - b * c;

    let lambda_1 = m + (m.powi(2) - p).sqrt();
    let lambda_2 = m - (m.powi(2) - p).sqrt();

    let (v1, v2) = if (lambda_1 - d).abs() < 1e-14 && c.abs() < 1e-14 {
        ((c, lambda_1 - a), (lambda_2 - d, b))
    } else {
        ((lambda_1 - d, c), (b, lambda_2 - a))
    };

    let p1 = (v1.0.abs().powi(2) + v1.1.abs().powi(2)).sqrt();
    let p2 = (v2.0.abs().powi(2) + v2.1.abs().powi(2)).sqrt();

    let v1 = (v1.0 / p1, v1.1 / p1);
    let v2 = (v2.0 / p2, v2.1 / p2);

    ((lambda_1, v1), (lambda_2, v2))
}

pub(super) fn exp_gate(matrix: Matrix, param: f64, inverse: bool) -> Matrix {
    let ((lambda1, v1), (lambda_2, v2)) = eigen(matrix);

    let value_1 = lambda1.powf(param);
    let gate_1 = [
        [value_1 * v1.0 * v1.0.conj(), value_1 * v1.0 * v1.1.conj()],
        [value_1 * v1.1 * v1.0.conj(), value_1 * v1.1 * v1.1.conj()],
    ];

    let value_2 = lambda_2.powf(param);
    let gate_2 = [
        [value_2 * v2.0 * v2.0.conj(), value_2 * v2.0 * v2.1.conj()],
        [value_2 * v2.1 * v2.0.conj(), value_2 * v2.1 * v2.1.conj()],
    ];

    let gate = [
        [gate_1[0][0] + gate_2[0][0], gate_1[0][1] + gate_2[0][1]],
        [gate_1[1][0] + gate_2[1][0], gate_1[1][1] + gate_2[1][1]],
    ];

    if inverse {
        [
            [gate[0][0].conj(), gate[1][0].conj()],
            [gate[0][1].conj(), gate[1][1].conj()],
        ]
    } else {
        gate
    }
}
