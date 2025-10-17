use crate::core::formatting::formats::{CsvRow, Exportable, Exporter, MarkdownRow, TableRow, XmlRow};
use crate::core::networking::subnets::{SubnetRow, VLSMCalculator};

// Implementación para VLSMCalculator
impl Exportable for VLSMCalculator {
    fn export_with(&self, exporter: &mut dyn Exporter) {
        exporter.begin();
        
        // Información de la red original
        exporter.begin_object("original_network");
        exporter.write_field("ip_address", self.base_calculator.original_ip());
        exporter.write_field("network_class", self.base_calculator.net_class());
        exporter.write_field("original_mask", self.base_calculator.subnet_mask());
        exporter.write_field("binary_original_mask", self.base_calculator.binary_subnet_mask());
        
        if self.base_calculator.has_cidr() {
            exporter.write_field("original_cidr", &self.base_calculator.cidr().unwrap_or(24).to_string());
        }
        exporter.end_object();
        
        // Información de la configuración VLSM
        exporter.begin_object("vlsm_configuration");
        exporter.write_field("method", "VLSM");
        exporter.write_field("subnet_count", &self.hosts_requirements.len().to_string());
        exporter.write_field("total_hosts_required", &self.hosts_requirements.iter().sum::<u32>().to_string());
        exporter.write_field("efficiency", &format!("{:.1}%", self.calculate_efficiency()));
        
        // Lista de requerimientos de hosts
        exporter.begin_array("hosts_requirements");
        for (i, &hosts) in self.hosts_requirements.iter().enumerate() {
            exporter.begin_object("");
            exporter.write_field("subnet_id", &(i + 1).to_string());
            exporter.write_field("required_hosts", &hosts.to_string());
            exporter.end_object();
        }
        exporter.end_array();
        exporter.end_object();
        
        // Lista de subredes VLSM
        exporter.begin_array("subnets");
        let subnets = self.get_vlsm_subnets();
        for subnet in subnets {
            let req_hosts = self.hosts_requirements.get((subnet.subred - 1) as usize)
                .copied()
                .unwrap_or(0);
            let usable_hosts = self.calculate_usable_hosts_for_subnet(subnet);
            
            exporter.begin_object("");
            exporter.write_field("subnet", &subnet.subred.to_string());
            exporter.write_field("required_hosts", &req_hosts.to_string());
            exporter.write_field("usable_hosts", &usable_hosts.to_string());
            exporter.write_field("network_address", &subnet.direccion_red);
            exporter.write_field("first_host", &subnet.primera_ip);
            exporter.write_field("last_host", &subnet.ultima_ip);
            exporter.write_field("broadcast", &subnet.broadcast);
            exporter.write_field("efficiency", &format!("{:.1}%", 
                if req_hosts > 0 { (usable_hosts as f64 / req_hosts as f64) * 100.0 } else { 0.0 }));
            exporter.end_object();
        }
        exporter.end_array();
        
        // Información resumen VLSM
        exporter.begin_object("summary");
        let total_required: u32 = self.hosts_requirements.iter().sum();
        let total_allocated = subnets.iter().enumerate()
            .map(|(i, _)| {
                let req = self.hosts_requirements.get(i).unwrap_or(&0);
                *req
            })
            .sum::<u32>();
        
        let total_usable: u32 = subnets.iter()
            .map(|subnet| self.calculate_usable_hosts_for_subnet(subnet))
            .sum();
            
        exporter.write_field("total_subnets", &subnets.len().to_string());
        exporter.write_field("total_hosts_required", &total_required.to_string());
        exporter.write_field("total_hosts_allocated", &total_allocated.to_string());
        exporter.write_field("total_usable_hosts", &total_usable.to_string());
        exporter.write_field("overall_efficiency", &format!("{:.1}%", self.calculate_efficiency()));
        exporter.write_field("wasted_addresses", &(total_allocated - total_required).to_string());
        exporter.end_object();
        
        exporter.end();
    }
}

// Implementación de TableRow para VLSM (para mostrar en tablas)
impl TableRow for VLSMCalculator {
    fn headers() -> Vec<&'static str> {
        vec![
            "Subnet",
            "Req Hosts",
            "Network",
            "First Host",
            "Last Host", 
            "Broadcast",
            "Usable",
            "Efficiency",
        ]
    }

    fn values(&self) -> Vec<String> {
        // Para VLSM, devolvemos los valores de la primera subred o un resumen
        let subnets = self.get_vlsm_subnets();
        if let Some(first_subnet) = subnets.first() {
            let req_hosts = self.hosts_requirements.first().unwrap_or(&0);
            let usable_hosts = self.calculate_usable_hosts_for_subnet(first_subnet);
            let efficiency = if *req_hosts > 0 {
                format!("{:.1}%", (usable_hosts as f64 / *req_hosts as f64) * 100.0)
            } else {
                "0%".to_string()
            };
            
            vec![
                first_subnet.subred.to_string(),
                req_hosts.to_string(),
                first_subnet.direccion_red.clone(),
                first_subnet.primera_ip.clone(),
                first_subnet.ultima_ip.clone(),
                first_subnet.broadcast.clone(),
                usable_hosts.to_string(),
                efficiency,
            ]
        } else {
            vec!["N/A".to_string(); 8]
        }
    }
}

// Función de exportación para VLSMCalculator
pub fn export_vlsm_calculation(
    calculator: &VLSMCalculator, 
    format: &str
) -> Result<String, &'static str> {
    match format.to_lowercase().as_str() {
        "json" => {
            let mut exporter = crate::core::formatting::formats::JsonExporter::new();
            calculator.export_with(&mut exporter);
            Ok(exporter.output())
        }
        "xml" => {
            let mut exporter = crate::core::formatting::formats::XmlExporter::new();
            calculator.export_with(&mut exporter);
            Ok(exporter.output())
        }
        "yaml" => {
            let mut exporter = crate::core::formatting::formats::YamlExporter::new();
            calculator.export_with(&mut exporter);
            Ok(exporter.output())
        }
        "csv" => {
            let subnets = calculator.get_vlsm_subnets();
            let mut out = String::new();

            // Header con columnas adicionales para VLSM
            out.push_str("Subnet,Required Hosts,Network Address,First Host,Last Host,Broadcast,Usable Hosts,Efficiency\n");

            // Rows
            for (i, subnet) in subnets.iter().enumerate() {
                let req_hosts = calculator.hosts_requirements.get(i).unwrap_or(&0);
                let usable_hosts = calculator.calculate_usable_hosts_for_subnet(subnet);
                let efficiency = if *req_hosts > 0 {
                    format!("{:.1}%", (usable_hosts as f64 / *req_hosts as f64) * 100.0)
                } else {
                    "0%".to_string()
                };
                
                out.push_str(&format!(
                    "{},{},{},{},{},{},{},{}\n",
                    subnet.subred,
                    req_hosts,
                    subnet.direccion_red,
                    subnet.primera_ip,
                    subnet.ultima_ip,
                    subnet.broadcast,
                    usable_hosts,
                    efficiency
                ));
            }

            Ok(out)
        }
        "md" | "markdown" => {
            let subnets = calculator.get_vlsm_subnets();
            let total_required: u32 = calculator.hosts_requirements.iter().sum();
            let efficiency = calculator.calculate_efficiency();
            
            let mut out = String::new();

            out.push_str("# VLSM Subnetting Calculation Results\n\n");
            out.push_str(&format!("**Original Network:** {}\n", calculator.base_calculator.original_ip()));
            out.push_str(&format!("**Network Class:** {}\n", calculator.base_calculator.net_class()));
            out.push_str(&format!("**Original Subnet Mask:** {}\n", calculator.base_calculator.subnet_mask()));
            out.push_str(&format!("**Total Subnets:** {}\n", calculator.hosts_requirements.len()));
            out.push_str(&format!("**Total Hosts Required:** {}\n", total_required));
            out.push_str(&format!("**Allocation Efficiency:** {:.1}%\n\n", efficiency));

            out.push_str("## Host Requirements\n\n");
            out.push_str("| Subnet | Required Hosts |\n");
            out.push_str("|--------|----------------|\n");
            for (i, &hosts) in calculator.hosts_requirements.iter().enumerate() {
                out.push_str(&format!("| {} | {} |\n", i + 1, hosts));
            }
            out.push_str("\n");

            out.push_str("## Subnet Details\n\n");
            out.push_str("| Subnet | Req Hosts | Network | First Host | Last Host | Broadcast | Usable | Efficiency |\n");
            out.push_str("|--------|-----------|---------|------------|-----------|-----------|--------|------------|\n");

            for (i, subnet) in subnets.iter().enumerate() {
                let req_hosts = calculator.hosts_requirements.get(i).unwrap_or(&0);
                let usable_hosts = calculator.calculate_usable_hosts_for_subnet(subnet);
                let subnet_efficiency = if *req_hosts > 0 {
                    format!("{:.1}%", (usable_hosts as f64 / *req_hosts as f64) * 100.0)
                } else {
                    "0%".to_string()
                };
                
                out.push_str(&format!(
                    "| {} | {} | {} | {} | {} | {} | {} | {} |\n",
                    subnet.subred,
                    req_hosts,
                    subnet.direccion_red,
                    subnet.primera_ip,
                    subnet.ultima_ip,
                    subnet.broadcast,
                    usable_hosts,
                    subnet_efficiency
                ));
            }

            Ok(out)
        }
        _ => Err("Formato no soportado. Use: json, csv, xml, yaml, markdown"),
    }
}


// Tests para VLSM export
#[cfg(test)]
mod vlsm_export_tests {
    use super::*;

    fn sample_vlsm_calculator() -> VLSMCalculator {
        VLSMCalculator::new("192.168.1.0", vec![50, 25, 10, 5])
    }

    #[test]
    fn test_vlsm_export_json_contains_expected_keys() {
        let calc = sample_vlsm_calculator();
        let result = export_vlsm_calculation(&calc, "json").unwrap();

        assert!(result.contains("\"vlsm_configuration\""), "JSON must include 'vlsm_configuration' key");
        assert!(result.contains("\"hosts_requirements\""), "JSON must include 'hosts_requirements' array");
        assert!(result.contains("\"efficiency\""), "JSON must include efficiency");
        assert!(result.contains("192.168.1.0"), "JSON must contain original IP address");
    }

    #[test]
    fn test_vlsm_export_csv_has_vlsm_headers() {
        let calc = sample_vlsm_calculator();
        let result = export_vlsm_calculation(&calc, "csv").unwrap();

        assert!(result.starts_with("Subnet,Required Hosts,Network Address,First Host,Last Host,Broadcast,Usable Hosts,Efficiency"),
                "CSV must start with VLSM-specific header line");
        assert!(result.lines().count() > 1, "CSV must contain data lines");
    }

    #[test]
    fn test_vlsm_export_yaml_structure() {
        let calc = sample_vlsm_calculator();
        let result = export_vlsm_calculation(&calc, "yaml").unwrap();

        assert!(result.contains("vlsm_configuration:"), "YAML must contain 'vlsm_configuration' mapping");
        assert!(result.contains("hosts_requirements:"), "YAML must contain 'hosts_requirements' sequence");
    }

    #[test]
    fn test_vlsm_export_markdown_headers_and_table() {
        let calc = sample_vlsm_calculator();
        let result = export_vlsm_calculation(&calc, "markdown").unwrap();

        assert!(result.contains("# VLSM Subnetting Calculation Results"), "Markdown must have VLSM title");
        assert!(result.contains("| Subnet | Req Hosts | Network |"), "Markdown table header must be present");
        assert!(result.contains("Allocation Efficiency"), "Markdown must show efficiency");
    }

    #[test]
    fn test_vlsm_export_xml_structure() {
        let calc = sample_vlsm_calculator();
        let result = export_vlsm_calculation(&calc, "xml").unwrap();

        assert!(result.contains("<vlsm_configuration>"), "XML must contain vlsm_configuration element");
        assert!(result.contains("<hosts_requirements>"), "XML must contain hosts_requirements element");
    }

    #[test]
    fn test_vlsm_efficiency_calculation() {
        let calc = sample_vlsm_calculator();
        let efficiency = calc.calculate_efficiency();
        
        // La eficiencia debe estar entre 0% y 100%
        assert!(efficiency >= 0.0 && efficiency <= 100.0, 
                "Efficiency should be between 0% and 100%, got {}", efficiency);
    }

    #[test]
    fn test_vlsm_usable_hosts_calculation() {
        let calc = sample_vlsm_calculator();
        let subnets = calc.get_vlsm_subnets();
        
        for subnet in subnets {
            let usable = calc.calculate_usable_hosts_for_subnet(&subnet);
            // Los hosts utilizables deben ser >= 0
            assert!(usable >= 0, "Usable hosts should be non-negative");
        }
    }
}