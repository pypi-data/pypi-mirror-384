use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

// Asumiendo que tienes estas definiciones en tu crate
use crate::core::NumberConverter;

#[pyclass(name = "NumberConverter")]
struct PyNumberConverter {
    inner: NumberConverter,
}

#[pymethods]
impl PyNumberConverter {
    #[new]
    fn new(value: i64) -> Self {
        PyNumberConverter {
            inner: NumberConverter::new(value),
        }
    }

    /// Convierte a binario
    pub fn to_binary(&mut self) -> String {
        self.inner.to_binary()
    }

    /// Convierte a hexadecimal
    pub fn to_hex(&mut self) -> String {
        self.inner.to_hex()
    }

    /// Convierte a letras (A=1, B=2, ...)
    pub fn to_letters(&mut self) -> String {
        self.inner.to_letters()
    }

    /// Obtiene el historial de conversiones
    pub fn get_history(&self) -> Vec<String> {
        self.inner.get_history().to_vec()
    }

    /// Obtiene el valor decimal actual
    #[getter]
    pub fn value(&self) -> i64 {
        self.inner.value
    }

    /// Establece un nuevo valor decimal
    #[setter]
    pub fn set_value(&mut self, value: i64) {
        self.inner.value = value;
        // Opcional: agregar al historial
        self.inner.history.push(format!("decimal={}", value));
    }

    /// Representación en string
    fn __repr__(&self) -> String {
        format!("NumberConverter(value={})", self.inner.value)
    }

    /// Representación en string (más legible)
    fn __str__(&self) -> String {
        format!("NumberConverter(value={})", self.inner.value)
    }
}

#[pyfunction]
fn binary_to_decimal(s: &str) -> PyResult<i64> {
    i64::from_str_radix(s, 2)
        .map_err(|e| PyValueError::new_err(format!("Error convirtiendo binario a decimal: {}", e)))
}

#[pyfunction]
fn decimal_to_binary(n: i64) -> String {
    format!("{:b}", n)
}

#[pyfunction]
fn decimal_to_hex(n: i64) -> String {
    format!("{:X}", n)
}

#[pyfunction]
fn decimal_to_letters(n: i64) -> PyResult<String> {
    if n <= 0 {
        return Err(PyValueError::new_err("El número debe ser positivo"));
    }
    let mut letters = String::new();
    let mut num = n;
    
    while num > 0 {
        let rem = ((num - 1) % 26) as u8;
        letters.insert(0, (b'A' + rem) as char);
        num = (num - 1) / 26;
    }
    Ok(letters)
}

#[pyfunction]
fn binary_to_hex(s: &str) -> PyResult<String> {
    let decimal = binary_to_decimal(s)?;
    Ok(format!("{:X}", decimal))
}

#[pyfunction]
fn hex_to_decimal(s: &str) -> PyResult<i64> {
    i64::from_str_radix(s, 16)
        .map_err(|e| PyValueError::new_err(format!("Error convirtiendo hexadecimal a decimal: {}", e)))
}

#[pyfunction]
fn hex_to_binary(s: &str) -> PyResult<String> {
    let decimal = hex_to_decimal(s)?;
    Ok(format!("{:b}", decimal))
}

#[pyfunction]
fn letters_to_decimal(s: &str) -> PyResult<i64> {
    if s.is_empty() {
        return Err(PyValueError::new_err("La cadena no puede estar vacía"));
    }
    
    let mut result = 0;
    for (i, c) in s.chars().rev().enumerate() {
        if !c.is_ascii_uppercase() {
            return Err(PyValueError::new_err("Solo se permiten letras mayúsculas A-Z"));
        }
        
        let value = (c as u8 - b'A' + 1) as i64;
        result += value * 26_i64.pow(i as u32);
    }
    
    Ok(result)
}

/// Función de conversión general entre formatos
#[pyfunction]
fn convert_number(value: &str, from_format: &str, to_format: &str) -> PyResult<String> {
    let decimal = match from_format.to_lowercase().as_str() {
        "decimal" => value.parse::<i64>()
            .map_err(|e| PyValueError::new_err(format!("Error parseando decimal: {}", e)))?,
        "binary" => binary_to_decimal(value)?,
        "hex" | "hexadecimal" => hex_to_decimal(value)?,
        "letters" => letters_to_decimal(value)?,
        _ => return Err(PyValueError::new_err(format!("Formato de origen no soportado: {}", from_format)))
    };
    
    match to_format.to_lowercase().as_str() {
        "decimal" => Ok(decimal.to_string()),
        "binary" => Ok(decimal_to_binary(decimal)),
        "hex" | "hexadecimal" => Ok(decimal_to_hex(decimal)),
        "letters" => decimal_to_letters(decimal),
        _ => Err(PyValueError::new_err(format!("Formato de destino no soportado: {}", to_format)))
    }
}

/// Registra el módulo de conversiones
pub fn register(parent: &Bound<'_, PyModule>) -> PyResult<()> {
    let submodule = PyModule::new(parent.py(), "conversions")?;
    
    // Agregar la clase
    submodule.add_class::<PyNumberConverter>()?;
    
    // Agregar todas las funciones
    submodule.add_function(wrap_pyfunction!(binary_to_decimal, &submodule)?)?;
    submodule.add_function(wrap_pyfunction!(decimal_to_binary, &submodule)?)?;
    submodule.add_function(wrap_pyfunction!(decimal_to_hex, &submodule)?)?;
    submodule.add_function(wrap_pyfunction!(decimal_to_letters, &submodule)?)?;
    submodule.add_function(wrap_pyfunction!(binary_to_hex, &submodule)?)?;
    submodule.add_function(wrap_pyfunction!(hex_to_decimal, &submodule)?)?;
    submodule.add_function(wrap_pyfunction!(hex_to_binary, &submodule)?)?;
    submodule.add_function(wrap_pyfunction!(letters_to_decimal, &submodule)?)?;
    submodule.add_function(wrap_pyfunction!(convert_number, &submodule)?)?;
    
    // Agregar constantes útiles
    submodule.add("SUPPORTED_FORMATS", vec!["decimal", "binary", "hex", "letters"])?;

    parent.add_submodule(&submodule)?;
    parent.py().import("sys")?
        .getattr("modules")?
        .set_item(&format!("suma_ulsa.conversions"), submodule)?;

    Ok(())
}