use pyo3::prelude::*;

mod core;
mod bindings;

#[pymodule]
fn suma_ulsa_native(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    bindings::register_modules(m)?;
    Ok(())
}
