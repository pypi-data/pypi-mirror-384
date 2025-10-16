use std::f32::consts::E;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use pyo3::wrap_pyfunction;

use crate::core::networking::{SubnetCalculator, SubnetRow, export_subnet_calculation};

#[pyclass(name = "SubnetCalculator", module = "suma_ulsa.networking")]
pub struct PySubnetCalculator {
    inner: SubnetCalculator,
}

#[pymethods]
impl PySubnetCalculator {
    #[new]
    #[pyo3(signature = (ip, subnet_quantity))]
    #[pyo3(text_signature = "(ip, subnet_quantity)")]
    pub fn new(ip: &str, subnet_quantity: usize) -> PyResult<Self> {
        // Agregar validación básica
        if subnet_quantity == 0 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "subnet_quantity must be greater than 0",
            ));
        }
        
        Ok(Self {
            inner: SubnetCalculator::new(ip, subnet_quantity),
        })
    }

    /// Returns a simple summary string of the subnet calculation.
    #[pyo3(name = "summary")]
    #[pyo3(text_signature = "($self)")]
    pub fn summary(&self) -> String {
        let rows = self.inner.generate_rows();

        // Helper para convertir máscara a binario
        fn mask_to_bin(mask: &str) -> String {
            mask.split('.')
                .map(|octet| format!("{:08b}", octet.parse::<u8>().unwrap_or(0)))
                .collect::<Vec<_>>()
                .join(".")
        }

        let orig_mask = self.inner.subnet_mask();
        let new_mask = self.inner.new_subnet_mask();

        format!(
            "Subnet Summary\n\
            ───────────────\n\
            IP Address        : {ip}\n\
            Network Class     : {class}\n\
            Original Mask     : {orig_mask}   ({orig_bin})\n\
            New Subnet Mask   : {new_mask}   ({new_bin})\n\
            Network Jump      : {jump}\n\
            Hosts/Subnet      : {hosts}\n\
            Total Subnets     : {total}\n\
            Usable Subnets    : {usable}\n",
            ip = self.inner.original_ip(),
            class = self.inner.net_class(),
            orig_mask = orig_mask,
            orig_bin = mask_to_bin(&orig_mask),
            new_mask = new_mask,
            new_bin = mask_to_bin(&new_mask),
            jump = self.inner.net_jump(),
            hosts = format_number(self.inner.hosts_quantity().try_into().unwrap()),
            total = self.inner.subnet_quantity(),
            usable = rows.len()
        )
    }

    /// Prints the summary to stdout.
    #[pyo3(name = "print_summary")]
    #[pyo3(text_signature = "($self)")]
    pub fn print_summary(&self) {
        println!("{}", self.summary());
    }

    /// Prints the subnet table to stdout.
    #[pyo3(name = "print_table")]
    #[pyo3(text_signature = "($self)")]
    pub fn print_table(&self) {
        println!("{}", self.subnets_table());
    }

    /// Returns a subnets table format
    #[pyo3(name = "subnets_table")]
    #[pyo3(text_signature = "($self)")]
    pub fn subnets_table(&self) -> String {
        let rows = self.inner.generate_rows();
        
        let mut output = String::new();
        output.push_str("Subnet │ Network       │ First Host    │ Last Host     │ Broadcast\n");
        output.push_str("───────┼───────────────┼───────────────┼───────────────┼───────────────\n");
        
        for row in rows {
            output.push_str(&format!(
                "{:6} │ {:13} │ {:13} │ {:13} │ {:13}\n",
                row.subred,
                truncate_string(&row.direccion_red, 13),
                truncate_string(&row.primera_ip, 13),
                truncate_string(&row.ultima_ip, 13),
                truncate_string(&row.broadcast, 13)
            ));
        }
        
        output
    }

    /// Returns all subnet rows as Python objects
    #[pyo3(name = "get_rows")]
    #[pyo3(text_signature = "($self)")]
    pub fn get_rows(&self) -> Vec<PySubnetRow> {
        self.inner.generate_rows()
            .into_iter()
            .map(PySubnetRow::from)
            .collect()
    }

    /// Returns a specific subnet row
    #[pyo3(name = "get_row")]
    #[pyo3(text_signature = "($self, subnet_number)")]
    pub fn get_row(&self, subnet_number: usize) -> PyResult<PySubnetRow> {
        let rows = self.inner.generate_rows();
        if subnet_number == 0 || subnet_number > rows.len() {
            return Err(PyErr::new::<pyo3::exceptions::PyIndexError, _>(
                format!("Subnet number {} out of range (1-{})", subnet_number, rows.len())
            ));
        }
        
        Ok(PySubnetRow::from(rows[subnet_number - 1].clone()))
    }

    /// Convert to Python dictionary
#[pyo3(name = "to_dict")]
#[pyo3(text_signature = "($self)")]
pub fn to_dict(&self, py: Python<'_>) -> PyResult<Py<PyDict>> {
    let dict = PyDict::new(py);
    dict.set_item("ip", self.inner.original_ip())?;
    dict.set_item("subnet_quantity", self.inner.subnet_quantity())?;
    dict.set_item("hosts_per_subnet", self.inner.hosts_quantity())?;
    dict.set_item("network_class", self.inner.net_class())?;
    dict.set_item("subnet_mask", self.inner.subnet_mask())?;
    dict.set_item("new_subnet_mask", self.inner.new_subnet_mask())?;
    dict.set_item("network_jump", self.inner.net_jump())?;
    
    let rows = self.get_rows();
    let py_rows = PyList::empty(py);
    for row in rows {
        py_rows.append(row.to_dict(py)?)?;
    }
    dict.set_item("subnets", py_rows)?;
    
    Ok(dict.into())
}

/// Convierte toda la información a formato JSON
#[pyo3(name = "to_json")]
#[pyo3(text_signature = "($self)")]
pub fn to_json(&self) -> PyResult<String> {
    export_subnet_calculation(&self.inner, "json")
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
}

/// Convierte la tabla de subredes a formato CSV
#[pyo3(name = "to_csv")]
#[pyo3(text_signature = "($self)")]
pub fn to_csv(&self) -> PyResult<String> {
    export_subnet_calculation(&self.inner, "csv")
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
}

/// Convierte a formato YAML
#[pyo3(name = "to_yaml")]
#[pyo3(text_signature = "($self)")]
pub fn to_yaml(&self) -> PyResult<String> {
    export_subnet_calculation(&self.inner, "yaml")
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
}

/// Convierte a formato XML
#[pyo3(name = "to_xml")]
#[pyo3(text_signature = "($self)")]
pub fn to_xml(&self) -> PyResult<String> {
    export_subnet_calculation(&self.inner, "xml")
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
}

/// Convierte a formato Markdown
#[pyo3(name = "to_markdown")]
#[pyo3(text_signature = "($self)")]
pub fn to_markdown(&self) -> PyResult<String> {
    // Para Markdown necesitamos un exporter especial, por ahora usamos el texto plano
    export_subnet_calculation(&self.inner, "md")
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
}

    /// Exporta a un archivo en el formato especificado
    #[pyo3(name = "export_to_file")]
    #[pyo3(text_signature = "($self, filename, format)")]
    pub fn export_to_file(&self, filename: &str, format: &str) -> PyResult<()> {
        use std::fs::File;
        use std::io::Write;
        
        let content = match format.to_lowercase().as_str() {
            "json" => self.to_json()?,
            "csv" => self.to_csv()?,
            "yaml" | "yml" => self.to_yaml()?,
            "xml" => self.to_xml()?,
            "md" | "markdown" => self.to_markdown()?,
            "txt" | "text" => {
            self.subnets_table()  
            },
            _ => {
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    format!("Unsupported format: {}. Supported formats: json, csv, yaml, xml, md, txt", format)
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

    // Métodos auxiliares privados - ahora sin parámetros problemáticos
    fn calculate_usable_hosts_for_subnet(&self, _row: &PySubnetRow) -> usize {
        // En IPv4, se restan 2 hosts por subred (red y broadcast)
        let total_hosts: usize = self.inner.hosts_quantity().try_into().unwrap_or(0);
        if total_hosts >= 2 {
            total_hosts - 2
        } else {
            0
        }
    }

    fn calculate_total_usable_hosts(&self) -> usize {
        let rows = self.get_rows();
        let hosts_per_subnet: usize = self.inner.hosts_quantity().try_into().unwrap_or(0);
        let usable_per_subnet = if hosts_per_subnet >= 2 {
            hosts_per_subnet - 2
        } else {
            0
        };
        
        rows.len() * usable_per_subnet
    }

    // Properties para acceso directo a los atributos
    #[getter]
    fn ip(&self) -> String {
        self.inner.original_ip().to_string()
    }

    #[getter]
    fn subnet_quantity(&self) -> usize {
        self.inner.subnet_quantity()
    }

    #[getter]
    fn hosts_per_subnet(&self) -> usize {
        self.inner.hosts_quantity().try_into().unwrap()
    }

    #[getter]
    fn network_class(&self) -> String {
        self.inner.net_class().to_string()
    }

    #[getter]
    fn subnet_mask(&self) -> String {
        self.inner.subnet_mask().to_string()
    }

    #[getter]   
    fn new_subnet_mask(&self) -> String {
        self.inner.new_subnet_mask().to_string()
    }

    #[getter]
    fn network_jump(&self) -> String {
        self.inner.net_jump().to_string()
    }

    /// Default string representation
    fn __str__(&self) -> String {
        self.summary()
    }

    /// Representation for debugging
    fn __repr__(&self) -> String {
        format!(
            "SubnetCalculator(ip='{}', subnet_quantity={})",
            self.inner.original_ip(),
            self.inner.subnet_quantity()
        )
    }
}

// Wrapper para SubnetRow
#[pyclass(name = "SubnetRow", module = "suma_ulsa.networking")]
pub struct PySubnetRow {
    #[pyo3(get)]
    pub subred: u32,
    #[pyo3(get)]
    pub direccion_red: String,
    #[pyo3(get)]
    pub primera_ip: String,
    #[pyo3(get)]
    pub ultima_ip: String,
    #[pyo3(get)]
    pub broadcast: String,
}

impl From<SubnetRow> for PySubnetRow {
    fn from(row: SubnetRow) -> Self {
        Self {
            subred: row.subred,
            direccion_red: row.direccion_red,
            primera_ip: row.primera_ip,
            ultima_ip: row.ultima_ip,
            broadcast: row.broadcast,
        }
    }
}

#[pymethods]
impl PySubnetRow {
    #[pyo3(text_signature = "($self)")]
    pub fn to_dict(&self, py: Python<'_>) -> PyResult<Py<PyDict>> {
        let dict = PyDict::new(py);
        dict.set_item("subnet", self.subred)?;
        dict.set_item("network", &self.direccion_red)?;
        dict.set_item("first_host", &self.primera_ip)?;
        dict.set_item("last_host", &self.ultima_ip)?;
        dict.set_item("broadcast", &self.broadcast)?;
        Ok(dict.into())
    }

    /// Pretty display for individual subnet row
    #[pyo3(name = "to_pretty_string")]
    #[pyo3(text_signature = "($self)")]
    pub fn to_pretty_string(&self) -> String {
        format!(
            "┌─────────────────────────┐\n\
             │      SUBNET {:3}         │\n\
             ├─────────────────────────┤\n\
             │ Network:   {:15} │\n\
             │ First:     {:15} │\n\
             │ Last:      {:15} │\n\
             │ Broadcast: {:15} │\n\
             └─────────────────────────┘",
            self.subred,
            self.direccion_red,
            self.primera_ip,
            self.ultima_ip,
            self.broadcast
        )
    }

    fn __str__(&self) -> String {
        self.to_pretty_string()
    }

    fn __repr__(&self) -> String {
        format!(
            "SubnetRow(subnet={}, network='{}', first_host='{}', last_host='{}', broadcast='{}')",
            self.subred, self.direccion_red, self.primera_ip, self.ultima_ip, self.broadcast
        )
    }

}

// Funciones auxiliares
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

// Función de utilidad para crear un calculador rápido
#[pyfunction]
#[pyo3(signature = (ip, subnet_quantity))]
#[pyo3(text_signature = "(ip, subnet_quantity)")]
pub fn create_subnet_calculator(ip: &str, subnet_quantity: usize) -> PyResult<PySubnetCalculator> {
    PySubnetCalculator::new(ip, subnet_quantity)
}


/// Registra el módulo de redes
pub fn register(parent: &Bound<'_, PyModule>) -> PyResult<()> {
    let submodule = PyModule::new(parent.py(), "networking")?;
    
    submodule.add_class::<PySubnetCalculator>()?;
    submodule.add_class::<PySubnetRow>()?;
    submodule.add_function(wrap_pyfunction!(create_subnet_calculator, &submodule)?)?;
    
    
    parent.add_submodule(&submodule)?;
    
    // Registrar el módulo en sys.modules
    parent.py().import("sys")?
        .getattr("modules")?
        .set_item("suma_ulsa.networking", submodule)?;
    
    Ok(())
}
