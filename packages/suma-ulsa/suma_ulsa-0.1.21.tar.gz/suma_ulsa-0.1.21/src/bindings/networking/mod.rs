pub mod subnet_calculator;
pub mod vlsm_calculator;

use pyo3::prelude::*;
use crate::bindings::networking::subnet_calculator::{create_subnet_calculator, PySubnetCalculator, PySubnetRow};
use crate::bindings::networking::vlsm_calculator::{PyVLSMCalculator};
 
/// Registra el módulo de redes
pub fn register(parent: &Bound<'_, PyModule>) -> PyResult<()> {
    let submodule = PyModule::new(parent.py(), "networking")?;
    
    submodule.add_class::<PySubnetCalculator>()?;
    submodule.add_class::<PyVLSMCalculator>()?;
    submodule.add_class::<PySubnetRow>()?;
    submodule.add_function(wrap_pyfunction!(create_subnet_calculator, &submodule)?)?;
    
    
    parent.add_submodule(&submodule)?;
    
    // Registrar el módulo en sys.modules
    parent.py().import("sys")?
        .getattr("modules")?
        .set_item("suma_ulsa.networking", submodule)?;
    
    Ok(())
}