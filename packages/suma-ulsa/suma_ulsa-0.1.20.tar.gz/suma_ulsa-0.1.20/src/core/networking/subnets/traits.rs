use crate::core::formatting::formats::{CsvRow, Exportable, Exporter, MarkdownRow, TableRow, XmlRow};
use crate::core::networking::subnets::{SubnetCalculator, SubnetRow};

impl Exportable for SubnetRow {
    fn export_with(&self, exporter: &mut dyn Exporter) {
        exporter.begin();
        exporter.write_field("subnet", &self.subred.to_string());
        exporter.write_field("network_address", &self.direccion_red);
        exporter.write_field("first_host", &self.primera_ip);
        exporter.write_field("last_host", &self.ultima_ip);
        exporter.write_field("broadcast", &self.broadcast);
        exporter.end();
    }
    

}
impl CsvRow for SubnetRow {}
impl MarkdownRow for SubnetRow {}
impl XmlRow for SubnetRow {}

impl TableRow for SubnetRow {
    fn headers() -> Vec<&'static str> {
        vec![
            "Subnet",
            "Network Address",
            "First Host",
            "Last Host",
            "Broadcast",
        ]
    }

    fn values(&self) -> Vec<String> {
        vec![
            self.subred.to_string(),
            self.direccion_red.clone(),
            self.primera_ip.clone(),
            self.ultima_ip.clone(),
            self.broadcast.clone(),
        ]
    }
}


impl Exportable for SubnetCalculator {
    fn export_with(&self, exporter: &mut dyn Exporter) {
        exporter.begin();
        
        // Información de la red original
        exporter.begin_object("original_network");
        exporter.write_field("ip_address", self.original_ip());
        exporter.write_field("network_class", self.net_class());
        exporter.write_field("original_mask", self.subnet_mask());
        exporter.write_field("binary_original_mask", self.binary_subnet_mask());
        
        if self.has_cidr {
            exporter.write_field("original_cidr", &self.cidr().unwrap_or(24).to_string());
        }
        exporter.end_object();
        
        // Información de la nueva configuración
        exporter.begin_object("subnet_configuration");
        exporter.write_field("subnet_quantity", &self.subnet_quantity().to_string());
        exporter.write_field("hosts_per_subnet", &self.hosts_quantity().to_string());
        exporter.write_field("new_subnet_mask", self.new_subnet_mask());
        exporter.write_field("binary_new_mask", self.binary_new_mask());
        exporter.write_field("network_jump", &self.net_jump().to_string());
        
        if self.has_cidr {
            let new_cidr = self.mask_to_cidr(self.new_subnet_mask());
            exporter.write_field("new_cidr", &new_cidr.to_string());
        }
        exporter.end_object();
        
        // Lista de subredes
        exporter.begin_array("subnets");
        let rows = self.generate_rows();
        for row in &rows {
            row.export_with(exporter);
        }
        exporter.end_array();
        
        // Información resumen
        exporter.begin_object("summary");
        let total_usable_hosts = if self.hosts_quantity() >= 2 {
            (self.hosts_quantity() - 2) * rows.len() as u32
        } else {
            self.hosts_quantity() * rows.len() as u32
        };
        exporter.write_field("total_subnets", &rows.len().to_string());
        exporter.write_field("total_usable_hosts", &total_usable_hosts.to_string());
        exporter.write_field("utilization_rate", 
            &format!("{:.1}%", (rows.len() as f32 / self.subnet_quantity() as f32) * 100.0));
        exporter.end_object();
        
        exporter.end();
    }
}



pub fn export_subnet_calculation(
    calculator: &SubnetCalculator, 
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
            // TABULAR EXPORT
            let rows = calculator.generate_rows();
            let mut out = String::new();

            // Header
            out.push_str(&SubnetRow::headers().join(","));
            out.push('\n');

            // Rows
            for row in rows {
                out.push_str(&row.to_csv_row());
                out.push('\n');
            }

            Ok(out)
        }
        "md" | "markdown" => {
            let rows = calculator.generate_rows();
            let mut out = String::new();

            // Markdown table header
            out.push_str(&SubnetRow::markdown_header());
            out.push('\n');

            for row in rows {
                out.push_str(&row.to_markdown_row());
                out.push('\n');
            }

            Ok(out)
        }
        _ => Err("Formato no soportado. Use: json, csv, xml, yaml, markdown"),
    }
}



#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::networking::subnets::SubnetCalculator;

    fn sample_calculator() -> SubnetCalculator {
        // Suponiendo que SubnetCalculator::new recibe una IP y cantidad de subredes
        SubnetCalculator::new("192.168.1.0", 4)
    }

    #[test]
    fn test_export_json_contains_expected_keys() {
        let calc = sample_calculator();
        let result = export_subnet_calculation(&calc, "json").unwrap();

        assert!(result.contains("\"original_network\""), "JSON must include 'original_network' key");
        assert!(result.contains("\"subnets\""), "JSON must include 'subnets' array");
        assert!(result.contains("192.168.1.0"), "JSON must contain original IP address");
    }

    #[test]
    fn test_export_csv_has_headers() {
        let calc = sample_calculator();
        let result = export_subnet_calculation(&calc, "csv").unwrap();

        assert!(result.starts_with("Subnet,Network Address,First Host,Last Host,Broadcast"),
                "CSV must start with header line");
        assert!(result.lines().count() > 1, "CSV must contain at least one data line");
    }

    #[test]
    fn test_export_yaml_structure() {
        let calc = sample_calculator();
        let result = export_subnet_calculation(&calc, "yaml").unwrap();

        assert!(result.contains("original_network:"), "YAML must contain 'original_network' mapping");
        assert!(result.contains("subnets:"), "YAML must contain 'subnets' sequence");
    }


    #[test]
    fn test_export_markdown_headers_and_table() {
        let calc = sample_calculator();
        let result = export_subnet_calculation(&calc, "markdown").unwrap();

        println!("Markdown Output:\n{}", result); // Debug output
        assert!(result.contains("| Subnet | Network Address | First Host |"), "Markdown table header must be present");
    }

}
