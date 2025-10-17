// (C) Copyright 2025- ECMWF.
//
// This software is licensed under the terms of the Apache Licence Version 2.0
// which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
// In applying this licence, ECMWF does not waive the privileges and immunities
// granted to it by virtue of its status as an intergovernmental organisation
// nor does it submit to any jurisdiction.

use pyo3::prelude::*;
use rayon::prelude::*;
use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::exceptions::PyValueError;
use std::sync::atomic::{AtomicI64, Ordering};
use fixedbitset::FixedBitSet;

#[pyfunction]
fn compute_topological_labels_rust<'py>(
    py: Python<'py>,
    sources: PyReadonlyArray1<'py, usize>,
    sinks: PyReadonlyArray1<'py, usize>,
    downstream_nodes: PyReadonlyArray1<'py, usize>,
    n_nodes: usize,
) -> PyResult<Py<PyArray1<i64>>> {

    let labels: Vec<AtomicI64> = (0..n_nodes)
        .map(|_| AtomicI64::new(0))
        .collect();

    let mut current = sources.as_slice()?.to_vec();
    let sinks = sinks.as_slice()?;
    let downstream = downstream_nodes.as_slice()?;

    let mut next = Vec::with_capacity(current.len());
    let mut visited = FixedBitSet::with_capacity(n_nodes);

    for &i in &current {
        let d = downstream[i];
        if d != n_nodes {
            next.push(d);
        }
    }
    std::mem::swap(&mut current, &mut next);

    for n in 1..=n_nodes {
        if current.is_empty() {
            sinks.par_iter().for_each(|&i| {
                labels[i].store((n as i64) - 1, Ordering::Relaxed);
            });
            break;
        }

        current.par_iter().for_each(|&i| {
            labels[i].store(n as i64, Ordering::Relaxed);
        });

        next.clear();
        visited.clear();
        for &i in &current {
            let d = downstream[i];
            if d != n_nodes && !visited.contains(d) {
                visited.insert(d);
                next.push(d);
            }
        }

        std::mem::swap(&mut current, &mut next);
    }

    if !current.is_empty() {
        return Err(PyErr::new::<PyValueError, _>("River Network contains a cycle."));
    }

    let result: Vec<i64> = labels.iter()
        .map(|a| a.load(Ordering::Relaxed))
        .collect();
    let array = PyArray1::from_vec(py, result);
    Ok(array.to_owned().into())
}

#[pymodule]
fn _rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compute_topological_labels_rust, m)?)?;
    Ok(())
}
