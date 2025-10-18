// SPDX-FileCopyrightText: 2024 Evandro Chagas Ribeiro da Rosa <evandro@quantuloop.com>
//
// SPDX-License-Identifier: Apache-2.0

use env_logger::Builder;
use log::LevelFilter;

use crate::{error::Result, ir::qubit::LogicalQubit, prelude::QuantumGate, process::Process};

#[cfg(feature = "plot")]
use crate::process::{DumpData, Sample};
#[cfg(feature = "plot")]
use plotly::Plot;

pub fn ajd<F>(process: &mut Process, mut f: F) -> Result<()>
where
    F: FnMut(&mut Process) -> Result<()>,
{
    process.adj_begin()?;
    f(process)?;
    process.adj_end()
}

pub fn ctrl<F>(process: &mut Process, control: &[LogicalQubit], mut f: F) -> Result<()>
where
    F: FnMut(&mut Process) -> Result<()>,
{
    process.ctrl_push(control)?;
    f(process)?;
    process.ctrl_pop()
}

pub fn c1gate(
    process: &mut Process,
    gate: QuantumGate,
    control: LogicalQubit,
    target: LogicalQubit,
) -> Result<()> {
    ctrl(process, &[control], |process| process.gate(gate, target))
}

pub fn cnot(process: &mut Process, control: LogicalQubit, target: LogicalQubit) -> Result<()> {
    c1gate(process, QuantumGate::PauliX, control, target)
}

pub fn swap(process: &mut Process, qubit1: LogicalQubit, qubit2: LogicalQubit) -> Result<()> {
    cnot(process, qubit1, qubit2)?;
    cnot(process, qubit2, qubit1)?;
    cnot(process, qubit1, qubit2)
}

pub fn around<O, I>(process: &mut Process, mut outer: O, mut inner: I) -> Result<()>
where
    I: FnMut(&mut Process) -> Result<()>,
    O: FnMut(&mut Process) -> Result<()>,
{
    outer(process)?;
    inner(process)?;
    ajd(process, outer)
}

pub fn set_log_level(level: u32) {
    let level = match level {
        0 => LevelFilter::Off,
        1 => LevelFilter::Error,
        2 => LevelFilter::Warn,
        3 => LevelFilter::Info,
        4 => LevelFilter::Debug,
        5 => LevelFilter::Trace,
        _ => LevelFilter::max(),
    };

    Builder::new().filter_level(level).init();
}

#[cfg(feature = "plot")]
pub fn plot_sample(data: &Sample) -> Plot {
    use plotly::{layout::Axis, Bar, Layout};

    let trace = Bar::new(data.0.clone(), data.1.clone());
    let layout = Layout::new()
        .x_axis(Axis::new().title("Measurement Results"))
        .y_axis(Axis::new().title("Measurement Count"));
    let mut plot = Plot::new();
    plot.add_trace(trace);
    plot.set_layout(layout);

    plot
}

#[cfg(feature = "plot")]
pub fn plot_dump(data: &DumpData) -> Plot {
    use plotly::{common::Marker, layout::Axis, Bar, Layout};
    use std::f64::consts::PI;

    use crate::ir::gate::Cf64;

    let amp: Vec<_> = data
        .amplitudes_real
        .iter()
        .zip(data.amplitudes_imag.iter())
        .map(|(re, im)| Cf64::new(*re, *im))
        .collect();

    let prob: Vec<_> = amp.iter().map(|x| x.norm_sqr()).collect();
    let phase: Vec<_> = amp.iter().map(|x| x.arg()).collect();
    let base: Vec<_> = data.basis_states.iter().map(|x| x[0]).collect();

    let trace = Bar::new(base, prob).marker(
        Marker::new()
            .color_array(phase)
            .cmin(-PI)
            .cmax(PI)
            .show_scale(true),
    );

    let layout = Layout::new()
        .x_axis(Axis::new().title("Basis State"))
        .y_axis(
            Axis::new()
                .title("Measurement Probability (%)")
                .range(vec![0.0, 1.0]),
        );

    let mut plot = Plot::new();
    plot.add_trace(trace);
    plot.set_layout(layout);

    plot
}
