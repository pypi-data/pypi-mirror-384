use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::bindings::networking::subnet_calculator::PySubnetRow;
use crate::core::{SubnetRow, VLSMCalculator, export_vlsm_calculation};

#[pyclass(name = "VLSMCalculator", module = "suma_ulsa.networking")]
pub struct PyVLSMCalculator {
    inner: VLSMCalculator,
}

#[pymethods]
impl PyVLSMCalculator {
    #[new]
    #[pyo3(signature = (ip, hosts_requirements))]
    #[pyo3(text_signature = "(ip, hosts_requirements)")]
    pub fn new(ip: &str, hosts_requirements: Vec<u32>) -> PyResult<Self> {
        // Validación básica
        if hosts_requirements.is_empty() {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "hosts_requirements must not be empty",
            ));
        }

        if hosts_requirements.iter().any(|&h| h > 16777214) {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Host requirement cannot exceed 16,777,214 hosts",
            ));
        }
        
        Ok(Self {
            inner: VLSMCalculator::new(ip, hosts_requirements),
        })
    }

    /// Returns a summary of the VLSM calculation
    #[pyo3(name = "summary")]
    #[pyo3(text_signature = "($self)")]
    pub fn summary(&self) -> String {
        let subnets = self.inner.get_vlsm_subnets();
        let total_hosts: u32 = self.inner.hosts_requirements.iter().sum();
        let efficiency = self.calculate_efficiency();

        format!(
            "VLSM Subnetting Summary\n\
            ───────────────────────\n\
            IP Address           : {ip}\n\
            Total Subnets        : {subnet_count}\n\
            Total Hosts Required : {total_hosts}\n\
            Allocation Efficiency: {efficiency:.1}%\n\
            Requirements         : {requirements:?}\n",
            ip = self.inner.base_calculator.original_ip(),
            subnet_count = subnets.len(),
            total_hosts = format_number(total_hosts as usize),
            efficiency = efficiency,
            requirements = self.inner.hosts_requirements
        )
    }

    /// Prints the summary to stdout
    #[pyo3(name = "print_summary")]
    #[pyo3(text_signature = "($self)")]
    pub fn print_summary(&self) {
        println!("{}", self.summary());
    }

    /// Returns a detailed VLSM table
    #[pyo3(name = "subnets_table")]
    #[pyo3(text_signature = "($self)")]
    pub fn subnets_table(&self) -> String {
        let subnets = self.inner.get_vlsm_subnets();
        
        let mut output = String::new();
        output.push_str("Subnet │ Req Hosts │ Network       │ First Host    │ Last Host     │ Broadcast     │ Usable\n");
        output.push_str("───────┼───────────┼───────────────┼───────────────┼───────────────┼───────────────┼───────\n");
        
        for (i, subnet) in subnets.iter().enumerate() {
            let req_hosts = self.inner.hosts_requirements.get(i).unwrap_or(&0);
            let usable_hosts = self.calculate_usable_hosts_for_subnet(subnet);
            
            output.push_str(&format!(
                "{:6} │ {:9} │ {:13} │ {:13} │ {:13} │ {:13} │ {:6}\n",
                subnet.subred,
                req_hosts,
                truncate_string(&subnet.direccion_red, 13),
                truncate_string(&subnet.primera_ip, 13),
                truncate_string(&subnet.ultima_ip, 13),
                truncate_string(&subnet.broadcast, 13),
                usable_hosts
            ));
        }
        
        output
    }

    /// Prints the VLSM table to stdout
    #[pyo3(name = "print_table")]
    #[pyo3(text_signature = "($self)")]
    pub fn print_table(&self) {
        println!("{}", self.subnets_table());
    }

    /// Returns all VLSM subnet rows as Python objects
    #[pyo3(name = "get_rows")]
    #[pyo3(text_signature = "($self)")]
    pub fn get_rows(&self) -> Vec<PySubnetRow> {
        self.inner.get_vlsm_subnets()
            .iter()
            .map(|row| PySubnetRow::from(row.clone()))
            .collect()
    }

    /// Returns a specific VLSM subnet row
    #[pyo3(name = "get_row")]
    #[pyo3(text_signature = "($self, subnet_number)")]
    pub fn get_row(&self, subnet_number: usize) -> PyResult<PySubnetRow> {
        let subnets = self.inner.get_vlsm_subnets();
        if subnet_number == 0 || subnet_number > subnets.len() {
            return Err(PyErr::new::<pyo3::exceptions::PyIndexError, _>(
                format!("Subnet number {} out of range (1-{})", subnet_number, subnets.len())
            ));
        }
        
        Ok(PySubnetRow::from(subnets[subnet_number - 1].clone()))
    }

    /// Convert to Python dictionary
    #[pyo3(name = "to_dict")]
    #[pyo3(text_signature = "($self)")]
    pub fn to_dict(&self, py: Python<'_>) -> PyResult<Py<PyDict>> {
        let dict = PyDict::new(py);
        dict.set_item("ip", self.inner.base_calculator.original_ip())?;
        dict.set_item("hosts_requirements", &self.inner.hosts_requirements)?;
        dict.set_item("subnet_count", self.inner.hosts_requirements.len())?;
        dict.set_item("total_hosts_required", self.inner.hosts_requirements.iter().sum::<u32>())?;
        dict.set_item("efficiency", self.calculate_efficiency())?;
        
        let rows = self.get_rows();
        let py_rows = PyList::empty(py);
        for row in rows {
            py_rows.append(row.to_dict(py)?)?;
        }
        dict.set_item("subnets", py_rows)?;
        
        Ok(dict.into())
    }

    /// Export to JSON format
    #[pyo3(name = "to_json")]
    #[pyo3(text_signature = "($self)")]
    pub fn to_json(&self) -> PyResult<String> {
        export_vlsm_calculation(&self.inner, "json")
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
    }

    /// Export to CSV format
    #[pyo3(name = "to_csv")]
    #[pyo3(text_signature = "($self)")]
    pub fn to_csv(&self) -> PyResult<String> {
        export_vlsm_calculation(&self.inner, "csv")
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
    }

    pub fn to_markdown(&self) -> PyResult<String> {
        export_vlsm_calculation(&self.inner, "md")
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
    }

    /// Export to file in specified format
    #[pyo3(name = "export_to_file")]
    #[pyo3(text_signature = "($self, filename, format)")]
    pub fn export_to_file(&self, filename: &str, format: &str) -> PyResult<()> {
        use std::fs::File;
        use std::io::Write;
        
        let content = match format.to_lowercase().as_str() {
            "json" => self.to_json()?,
            "csv" => self.to_csv()?,
            "md" => self.to_markdown()?,
            "txt" | "text" => self.subnets_table(),
            _ => {
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    format!("Unsupported format: {}. Supported formats: json, csv, txt", format)
                ));
            }
        };
        
        let mut file = File::create(filename)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(
                format!("Error creating file {}: {}", filename, e)
            ))?;
            
        file.write_all(content.as_bytes())
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(
                format!("Error writing to file {}: {}", filename, e)
            ))?;
            
        Ok(())
    }

    // Removed duplicate get_efficiency method to resolve conflict

    /// Get detailed information about a specific subnet
    #[pyo3(name = "get_subnet_details")]
    #[pyo3(text_signature = "($self, subnet_number)")]
    pub fn get_subnet_details(&self, subnet_number: usize) -> PyResult<String> {
        let subnet = self.get_row(subnet_number)?;
        let req_hosts = self.inner.hosts_requirements.get(subnet_number - 1).unwrap_or(&0);
        let usable_hosts = self.calculate_usable_hosts_for_subnet(&subnet.clone().into());
        
        Ok(format!(
            "VLSM Subnet {} Details\n\
            ────────────────────\n\
            Required Hosts : {}\n\
            Usable Hosts   : {}\n\
            Network        : {}\n\
            First Host     : {}\n\
            Last Host      : {}\n\
            Broadcast      : {}\n\
            Efficiency     : {:.1}%",
            subnet_number,
            req_hosts,
            usable_hosts,
            subnet.direccion_red,
            subnet.primera_ip,
            subnet.ultima_ip,
            subnet.broadcast,
            if *req_hosts > 0 {
                (usable_hosts as f64 / *req_hosts as f64) * 100.0
            } else { 0.0 }
        ))
    }

    // Properties
    #[getter]
    fn ip(&self) -> String {
        self.inner.base_calculator.original_ip().to_string()
    }

    #[getter]
    fn hosts_requirements(&self) -> Vec<u32> {
        self.inner.hosts_requirements.clone()
    }

    #[getter]
    fn subnet_count(&self) -> usize {
        self.inner.hosts_requirements.len()
    }

    #[getter]
    fn total_hosts_required(&self) -> u32 {
        self.inner.hosts_requirements.iter().sum()
    }

    #[getter]
    fn efficiency(&self) -> f64 {
        self.calculate_efficiency()
    }

    /// Default string representation
    fn __str__(&self) -> String {
        self.summary()
    }

    /// Representation for debugging
    fn __repr__(&self) -> String {
        format!(
            "VLSMCalculator(ip='{}', hosts_requirements={:?})",
            self.inner.base_calculator.original_ip(),
            self.inner.hosts_requirements
        )
    }
}

// Implementación de métodos privados para PyVLSMCalculator
impl PyVLSMCalculator {
    fn calculate_efficiency(&self) -> f64 {
        let total_required: u32 = self.inner.hosts_requirements.iter().sum();
        if total_required == 0 {
            return 0.0;
        }

        let subnets = self.inner.get_vlsm_subnets();
        let mut total_allocated = 0u32;

        for (i, subnet) in subnets.iter().enumerate() {
            let req_hosts = self.inner.hosts_requirements.get(i).unwrap_or(&0);
            if *req_hosts > 0 {
                total_allocated += *req_hosts;
            }
        }

        (total_required as f64 / total_allocated as f64) * 100.0
    }

    fn calculate_usable_hosts_for_subnet(&self, subnet: &SubnetRow) -> u32 {
        let first_ip: u32 = subnet.primera_ip.parse::<std::net::Ipv4Addr>()
            .unwrap_or(std::net::Ipv4Addr::new(0, 0, 0, 0)).into();
        let last_ip: u32 = subnet.ultima_ip.parse::<std::net::Ipv4Addr>()
            .unwrap_or(std::net::Ipv4Addr::new(0, 0, 0, 0)).into();
        
        if last_ip >= first_ip {
            last_ip - first_ip + 1
        } else {
            0
        }
    }
}

// Función de utilidad para crear un calculador VLSM rápido
#[pyfunction]
#[pyo3(signature = (ip, hosts_requirements))]
#[pyo3(text_signature = "(ip, hosts_requirements)")]
pub fn create_vlsm_calculator(ip: &str, hosts_requirements: Vec<u32>) -> PyResult<PyVLSMCalculator> {
    PyVLSMCalculator::new(ip, hosts_requirements)
}


// Funciones auxiliares (las mismas que ya tenías)
fn format_number(num: usize) -> String {
    if num >= 1_000_000 {
        format!("{:.1}M", num as f64 / 1_000_000.0)
    } else if num >= 1_000 {
        format!("{:.1}K", num as f64 / 1_000.0)
    } else {
        num.to_string()
    }
}

fn truncate_string(s: &str, max_len: usize) -> String {
    if s.len() > max_len {
        format!("{}...", &s[..max_len.saturating_sub(3)])
    } else {
        s.to_string()
    }
}