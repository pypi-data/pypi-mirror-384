use pyo3::prelude::*;
use pyo3::types::{PyDict, PyAny};
use pyo3::wrap_pyfunction;
use std::collections::HashMap;

use crate::bindings;
use crate::core::{BooleanExpr, TruthTable};

#[pyclass(name = "TruthTable")]
pub struct PyTruthTable {
    inner: TruthTable,
}

#[pymethods]
impl PyTruthTable {
    #[new]
    pub fn new(
        variables: Vec<String>,
        columns: HashMap<String, Vec<bool>>,
        column_order: Vec<String>,
        combinations: Vec<Vec<bool>>,
    ) -> PyResult<Self> {
        let inner = TruthTable::new(variables, columns, column_order, combinations)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e))?;
        Ok(PyTruthTable { inner })
    }

    pub fn to_pretty_string(&self) -> String {
        if self.inner.variables.is_empty() {
            return "Empty TruthTable".to_string();
        }
        let max_len = self.inner.column_order.iter().map(|k| k.len()).max().unwrap_or(0).max(6);
        let mut output = String::new();
        
        // Header with column names in order
        for name in &self.inner.column_order {
            output.push_str(&format!("│ {:^width$} ", name, width = max_len));
        }
        output.push_str("│\n");
        
        // Separator
        for _ in &self.inner.column_order {
            output.push_str(&format!("├{:─<width$}", "", width = max_len + 2));
        }
        output.push_str("┤\n");
        
        // Rows
        for i in 0..self.inner.combinations.len() {
            for name in &self.inner.column_order {
                let val = self.inner.columns.get(name).unwrap()[i];
                output.push_str(&format!("│ {:^width$} ", val, width = max_len));
            }
            output.push_str("│\n");
        }
        
        // Bottom line
        for _ in &self.inner.column_order {
            output.push_str(&format!("└{:─<width$}", "", width = max_len + 2));
        }
        output.push_str("┘\n");
        
        output
    }

    fn to_polars(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let polars = py.import("polars")?;
        let data_dict = PyDict::new(py);
        
        for name in &self.inner.column_order {
            data_dict.set_item(name, self.inner.columns.get(name).unwrap())?;
        }
        
        if let Ok(from_dict) = polars.getattr("from_dict") {
            return Ok(from_dict.call1((data_dict,))?.into());
        }
        
        let dataframe = polars.getattr("DataFrame")?;
        Ok(dataframe.call1((data_dict,))?.into())
    }

    fn to_lazyframe(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let df = self.to_polars(py)?;
        Python::attach(|py| {
            let df_bound = df.bind(py);
            let lazyframe = df_bound.call_method0("lazy")?;
            Ok(lazyframe.into())
        })
    }

    fn to_list(&self) -> Vec<Vec<bool>> {
        self.inner.combinations.clone()
    }

    fn to_named_rows(&self) -> Vec<HashMap<String, bool>> {
        self.inner.to_named_rows()
    }

    fn to_column_dict(&self) -> HashMap<String, Vec<bool>> {
        self.inner.column_order.iter()
            .map(|name| (name.clone(), self.inner.columns.get(name).unwrap().clone()))
            .collect()
    }

    fn get_row(&self, index: usize) -> Option<HashMap<String, bool>> {
        self.inner.get_row(index)
    }

    fn get_column(&self, variable: String) -> Option<Vec<bool>> {
        self.inner.get_column(&variable)
    }

    #[pyo3(name = "filter_true")]
    fn py_filter_true(&self) -> PyResult<Self> {
        let result_label = self.inner.column_order.last()
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyValueError, _>("No columns found"))?;
        let assignments = self.inner.satisfiable_assignments(true, result_label);
        let combinations: Vec<Vec<bool>> = assignments
            .iter()
            .map(|assignment| {
                self.inner.variables
                    .iter()
                    .map(|var| *assignment.get(var).unwrap())
                    .collect()
            })
            .collect();
        let columns: HashMap<String, Vec<bool>> = self.inner.column_order.iter()
            .map(|name| {
                let values: Vec<bool> = assignments
                    .iter()
                    .map(|assignment| *assignment.get(name).unwrap())
                    .collect();
                (name.clone(), values)
            })
            .collect();
        let new_inner = TruthTable::new(
            self.inner.variables.clone(),
            columns,
            self.inner.column_order.clone(),
            combinations,
        ).map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e))?;
        Ok(PyTruthTable { inner: new_inner })
    }

    #[pyo3(name = "filter_false")]
    fn py_filter_false(&self) -> PyResult<Self> {
        let result_label = self.inner.column_order.last()
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyValueError, _>("No columns found"))?;
        let assignments = self.inner.satisfiable_assignments(false, result_label);
        let combinations: Vec<Vec<bool>> = assignments
            .iter()
            .map(|assignment| {
                self.inner.variables
                    .iter()
                    .map(|var| *assignment.get(var).unwrap())
                    .collect()
            })
            .collect();
        let columns: HashMap<String, Vec<bool>> = self.inner.column_order.iter()
            .map(|name| {
                let values: Vec<bool> = assignments
                    .iter()
                    .map(|assignment| *assignment.get(name).unwrap())
                    .collect();
                (name.clone(), values)
            })
            .collect();
        let new_inner = TruthTable::new(
            self.inner.variables.clone(),
            columns,
            self.inner.column_order.clone(),
            combinations,
        ).map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e))?;
        Ok(PyTruthTable { inner: new_inner })
    }

    fn satisfiable_assignments(&self, value: bool, py: Python<'_>) -> PyResult<Vec<Py<PyDict>>> {
        let result_label = self.inner.column_order.last()
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyValueError, _>("No columns found"))?;
        let assignments = self.inner.satisfiable_assignments(value, result_label);
        let mut result = Vec::new();
        for assignment in assignments {
            let dict = PyDict::new(py);
            for name in &self.inner.column_order {
                dict.set_item(name, assignment.get(name).unwrap())?;
            }
            result.push(dict.into());
        }
        Ok(result)
    }

    fn __str__(&self) -> String {
        self.to_pretty_string()
    }

    fn summary(&self, py: Python<'_>) -> PyResult<Py<PyDict>> {
        Python::attach(|py| {
            let dict = PyDict::new(py);
            let result_label = self.inner.column_order.last()
                .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyValueError, _>("No columns found"))?;
            let true_count = self.inner.columns.get(result_label).unwrap().iter().filter(|&&b| b).count() as f64;
            let total = self.inner.combinations.len() as f64;
            dict.set_item("num_variables", self.inner.variables.len())?;
            dict.set_item("total_combinations", total)?;
            dict.set_item("true_count", true_count)?;
            dict.set_item("false_count", total - true_count)?;
            dict.set_item("true_percentage", (true_count / total) * 100.0)?;
            for var in &self.inner.variables {
                let var_true_count = self.inner.columns.get(var).unwrap().iter().filter(|&&b| b).count() as f64;
                dict.set_item(format!("{}_true_count", var), var_true_count)?;
            }
            Ok(dict.into())
        })
    }
    fn select_columns(&self, columns: Vec<String>) -> PyResult<Self> {
        let columns_ref: Vec<&str> = columns.iter().map(|s| s.as_str()).collect();
        let new_inner = self.inner.select_columns(&columns_ref)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e))?;
        Ok(PyTruthTable { inner: new_inner })
    }

    /// Filters rows based on a Python callable applied to the specified column.
    fn filter(&self, column: String, predicate: &Bound<'_, PyAny>, py: Python<'_>) -> PyResult<Self> {
        if !self.inner.columns.contains_key(&column) {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Column '{}' not found", column)));
        }
        let new_inner = self.inner.filter(&column, |val| {
            predicate.call1((val,)).and_then(|res| res.is_truthy()).unwrap_or(false)
        }).map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e))?;
        Ok(PyTruthTable { inner: new_inner })
    }

    /// Checks if this truth table is equivalent to another based on result columns.
    fn equivalent_to(&self, other: &Self) -> PyResult<bool> {
        self.inner.equivalent_to(&other.inner)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e))
    }

    /// Exports the truth table to CSV format.
    fn to_csv(&self) -> String {
        self.inner.to_csv()
    }

    /// Exports the truth table to JSON format.
    fn to_json(&self) -> String {
        self.inner.to_json()
    }

    /// Supports len(table) in Python.
    fn __len__(&self) -> usize {
        self.inner.num_rows()
    }

    /// Supports table[index] for row access in Python.
    fn __getitem__(&self, index: usize, py: Python<'_>) -> PyResult<Py<PyDict>> {
        let row = self.inner.get_row(index)
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyIndexError, _>("Row index out of range"))?;
        let dict = PyDict::new(py);
        for (name, value) in row {
            dict.set_item(name, value)?;
        }
        Ok(dict.into())
    }

    /// Computes true/false counts for a specific column.
    fn column_stats(&self, column: String) -> PyResult<HashMap<String, f64>> {
        if !self.inner.columns.contains_key(&column) {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Column '{}' not found", column)));
        }
        let col = self.inner.columns.get(&column).unwrap();
        let true_count = col.iter().filter(|&&b| b).count() as f64;
        let total = col.len() as f64;
        let mut stats = HashMap::new();
        stats.insert("true_count".to_string(), true_count);
        stats.insert("false_count".to_string(), total - true_count);
        stats.insert("true_percentage".to_string(), if total > 0.0 { (true_count / total) * 100.0 } else { 0.0 });
        Ok(stats)
    }

    fn __repr__(&self) -> String {
        self.__str__()
    }
}

/// Expresión booleana para Python
#[pyclass(name = "BooleanExpr")]
pub struct PyBooleanExpr {
    inner: BooleanExpr,
}

#[pymethods]
impl PyBooleanExpr {
    #[new]
    pub fn new(expression: &str) -> PyResult<Self> {
        let inner = BooleanExpr::new(expression)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        Ok(PyBooleanExpr { inner })
    }

    pub fn evaluate(&self, values: &Bound<'_, PyDict>) -> PyResult<bool> {
        let mut rust_values = HashMap::new();
        
        for (key, value) in values.iter() {
            let key_str: String = key.extract()?;
            let value_bool: bool = value.extract()?;
            rust_values.insert(key_str, value_bool);
        }
        
        // Convert HashMap<String, bool> to HashMap<&str, bool>
        let ref_map: HashMap<&str, bool> = rust_values.iter()
            .map(|(k, v)| (k.as_str(), *v))
            .collect();
        
        self.inner.evaluate(&ref_map)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
    }

    // CORREGIDO: Usar &Bound en lugar de Bound
    pub fn evaluate_with_defaults(&self, values: &Bound<'_, PyDict>, default: bool) -> bool {
        let mut rust_values = HashMap::new();
        
        for (key, value) in values.iter() {
            if let (Ok(key_str), Ok(value_bool)) = (key.extract::<String>(), value.extract::<bool>()) {
                rust_values.insert(key_str, value_bool);
            }
        }
        
        // Convert HashMap<String, bool> to HashMap<&str, bool>
        let ref_map: HashMap<&str, bool> = rust_values.iter()
            .map(|(k, v)| (k.as_str(), *v))
            .collect();

        self.inner.evaluate_with_defaults(&ref_map, default)
    }

    pub fn truth_table(&self) -> bindings::boolean_algebra::PyTruthTable {
        bindings::boolean_algebra::PyTruthTable { inner: self.inner.truth_table() }
    }

    pub fn full_truth_table(&self) -> bindings::boolean_algebra::PyTruthTable {
        bindings::boolean_algebra::PyTruthTable { inner: self.inner.full_truth_table().to_truth_table().expect("Failed to generate truth table") }
    }
        
    // AÑADIDO: Método faltante
    pub fn to_prefix_notation(&self) -> String {
        self.inner.to_prefix_notation()
    }
    
    pub fn is_tautology(&self) -> bool {
        self.inner.is_tautology()
    }
    
    pub fn is_contradiction(&self) -> bool {
        self.inner.is_contradiction()
    }
    
    pub fn equivalent_to(&self, other: &Self) -> bool {  // CORREGIDO: usar &Self
        self.inner.equivalent_to(&other.inner)
    }
    
    #[getter]  // AÑADIDO: Usar getter para propiedades
    pub fn variables(&self) -> Vec<String> {
        self.inner.variables.clone()
    }
    
    #[getter]  // AÑADIDO: Usar getter para propiedades
    pub fn complexity(&self) -> usize {
        self.inner.complexity()
    }
    
    fn __str__(&self) -> String {
        self.inner.to_string()
    }
    
    fn __repr__(&self) -> String {
        format!("BooleanExpr('{}')", self.inner.to_string())
    }
    
    fn __and__(&self, other: &Self) -> PyResult<Self> {  // CORREGIDO: usar &Self
        let new_expr = BooleanExpr::new(&format!("({}) & ({})", self.inner.to_string(), other.inner.to_string()))
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        Ok(PyBooleanExpr { inner: new_expr })
    }
    
    fn __or__(&self, other: &Self) -> PyResult<Self> {  // CORREGIDO: usar &Self
        let new_expr = BooleanExpr::new(&format!("({}) | ({})", self.inner.to_string(), other.inner.to_string()))
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        Ok(PyBooleanExpr { inner: new_expr })
    }
    
    fn __invert__(&self) -> PyResult<Self> {
        let new_expr = BooleanExpr::new(&format!("~({})", self.inner.to_string()))
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        Ok(PyBooleanExpr { inner: new_expr })
    }
}

/// Función de utilidad para debugging: muestra el AST de una expresión
#[pyfunction]
fn parse_expression_debug(expression: &str) -> PyResult<String> {
    let expr = BooleanExpr::new(expression)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    Ok(expr.to_prefix_notation())
}

/// Función de utilidad: crea expresión desde tabla de verdad
#[pyfunction]
fn truth_table_from_expr(variables: Vec<String>, results: Vec<bool>) -> PyResult<PyBooleanExpr> {
    let expression = generate_expression_from_truth_table(&variables, &results);
    let inner = BooleanExpr::new(&expression)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    Ok(PyBooleanExpr { inner })
}

/// Función auxiliar para generar expresión desde tabla de verdad
fn generate_expression_from_truth_table(variables: &[String], results: &[bool]) -> String {
    let mut terms = Vec::new();
    let num_combinations = results.len();
    
    for i in 0..num_combinations {
        if results[i] {
            let mut term = String::new();
            for (j, var) in variables.iter().enumerate() {
                let value = (i >> (variables.len() - 1 - j)) & 1 == 1;
                if j > 0 {
                    term.push_str(" & ");
                }
                if !value {
                    term.push('~');
                }
                term.push_str(var);
            }
            terms.push(term);
        }
    }
    
    if terms.is_empty() {
        "false".to_string()
    } else if terms.len() == num_combinations {
        "true".to_string()
    } else {
        terms.join(" | ")
    }
}

/// Registra el módulo de álgebra booleana
pub fn register(parent: &Bound<'_, PyModule>) -> PyResult<()> {
    let submodule = PyModule::new(parent.py(), "boolean_algebra")?;

    submodule.add_class::<PyBooleanExpr>()?;
    submodule.add_class::<PyTruthTable>()?;
    submodule.add_function(wrap_pyfunction!(parse_expression_debug, &submodule)?)?;
    submodule.add_function(wrap_pyfunction!(truth_table_from_expr, &submodule)?)?;

    parent.add_submodule(&submodule)?;
    parent.py().import("sys")?
        .getattr("modules")?
        .set_item(&format!("suma_ulsa.boolean_algebra"), submodule)?;
    
    Ok(())
}