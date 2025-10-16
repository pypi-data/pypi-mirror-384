pub trait Exporter {
    fn begin(&mut self);
    fn write_field(&mut self, key: &str, value: &str);
    fn begin_object(&mut self, key: &str);
    fn end_object(&mut self);
    fn begin_array(&mut self, key: &str);
    fn write_array_item(&mut self, value: &str);
    fn end_array(&mut self);
    fn end(&mut self);
    fn output(&self) -> String;
}

pub trait Exportable {
    fn export_with(&self, exporter: &mut dyn Exporter);
}

// Implementación para CSV
pub struct CsvExporter {
    output: String,
    first: bool,
}

impl CsvExporter {
    pub fn new() -> Self {
        Self {
            output: String::new(),
            first: true,
        }
    }
}

impl Exporter for CsvExporter {
    fn begin(&mut self) {
        // CSV típicamente no necesita un begin especial
    }

    fn write_field(&mut self, key: &str, value: &str) {
        if self.first {
            self.output.push_str("key,value\n");
            self.first = false;
        }
        self.output.push_str(&format!("\"{}\",\"{}\"\n", key, value));
    }

    fn begin_object(&mut self, _key: &str) {
        // CSV no soporta objetos anidados de forma nativa
    }

    fn end_object(&mut self) {
        // CSV no soporta objetos anidados
    }

    fn begin_array(&mut self, key: &str) {
        self.output.push_str(&format!("\"{}\",\"[", key));
    }

    fn write_array_item(&mut self, value: &str) {
        self.output.push_str(&format!("{};", value));
    }

    fn end_array(&mut self) {
        if self.output.ends_with(';') {
            self.output.pop(); // Remover el último ';'
        }
        self.output.push_str("]\"\n");
    }

    fn end(&mut self) {
        // CSV no necesita un end especial
    }

    fn output(&self) -> String {
        self.output.clone()
    }
}

// Implementación para JSON
pub struct JsonExporter {
    output: String,
    stack: Vec<char>,
    first_in_container: bool,
}

impl JsonExporter {
    pub fn new() -> Self {
        Self {
            output: String::new(),
            stack: Vec::new(),
            first_in_container: true,
        }
    }

    fn current_container(&self) -> Option<char> {
        self.stack.last().copied()
    }

    fn write_comma_if_needed(&mut self) {
        if !self.first_in_container {
            self.output.push(',');
        }
        self.first_in_container = false;
    }
}

impl Exporter for JsonExporter {
    fn begin(&mut self) {
        self.output.push('{');
        self.stack.push('{');
        self.first_in_container = true;
    }

    fn write_field(&mut self, key: &str, value: &str) {
        self.write_comma_if_needed();
        self.output.push_str(&format!("\"{}\":\"{}\"", key, value));
    }

    fn begin_object(&mut self, key: &str) {
        self.write_comma_if_needed();
        self.output.push_str(&format!("\"{}\":{{", key));
        self.stack.push('{');
        self.first_in_container = true;
    }

    fn end_object(&mut self) {
        if let Some('{') = self.stack.pop() {
            self.output.push('}');
        }
        self.first_in_container = false;
    }

    fn begin_array(&mut self, key: &str) {
        self.write_comma_if_needed();
        self.output.push_str(&format!("\"{}\":[", key));
        self.stack.push('[');
        self.first_in_container = true;
    }

    fn write_array_item(&mut self, value: &str) {
        self.write_comma_if_needed();
        self.output.push_str(&format!("\"{}\"", value));
    }

    fn end_array(&mut self) {
        if let Some('[') = self.stack.pop() {
            self.output.push(']');
        }
        self.first_in_container = false;
    }

    fn end(&mut self) {
        while let Some(container) = self.stack.pop() {
            match container {
                '{' => self.output.push('}'),
                '[' => self.output.push(']'),
                _ => {}
            }
        }
    }

    fn output(&self) -> String {
        self.output.clone()
    }
}

// Implementación para XML
pub struct XmlExporter {
    output: String,
    stack: Vec<String>,
}

impl XmlExporter {
    pub fn new() -> Self {
        Self {
            output: String::new(),
            stack: Vec::new(),
        }
    }
}

impl Exporter for XmlExporter {
    fn begin(&mut self) {
        self.output.push_str("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<root>");
        self.stack.push("root".to_string());
    }

    fn write_field(&mut self, key: &str, value: &str) {
        let sanitized_key = key.replace(' ', "_");
        self.output.push_str(&format!("\n  <{}>{}</{}>", sanitized_key, value, sanitized_key));
    }

    fn begin_object(&mut self, key: &str) {
        let sanitized_key = key.replace(' ', "_");
        self.output.push_str(&format!("\n  <{}>", sanitized_key));
        self.stack.push(sanitized_key);
    }

    fn end_object(&mut self) {
        if let Some(key) = self.stack.pop() {
            self.output.push_str(&format!("\n  </{}>", key));
        }
    }

    fn begin_array(&mut self, key: &str) {
        let sanitized_key = key.replace(' ', "_");
        self.output.push_str(&format!("\n  <{}>", sanitized_key));
        self.stack.push(sanitized_key);
    }

    fn write_array_item(&mut self, value: &str) {
        self.output.push_str(&format!("\n    <item>{}</item>", value));
    }

    fn end_array(&mut self) {
        if let Some(key) = self.stack.pop() {
            self.output.push_str(&format!("\n  </{}>", key));
        }
    }

    fn end(&mut self) {
        while let Some(_) = self.stack.pop() {
            self.output.push_str("</root>");
        }
    }

    fn output(&self) -> String {
        self.output.clone()
    }
}

// Implementación para YAML
pub struct YamlExporter {
    output: String,
    indent_level: usize,
    first_in_container: bool,
}

impl YamlExporter {
    pub fn new() -> Self {
        Self {
            output: String::new(),
            indent_level: 0,
            first_in_container: true,
        }
    }

    fn indent(&self) -> String {
        "  ".repeat(self.indent_level)
    }
}

impl Exporter for YamlExporter {
    fn begin(&mut self) {
        // YAML no necesita begin especial
    }

    fn write_field(&mut self, key: &str, value: &str) {
        self.output.push_str(&format!("{}{}: {}\n", self.indent(), key, value));
    }

    fn begin_object(&mut self, key: &str) {
        self.output.push_str(&format!("{}{}:\n", self.indent(), key));
        self.indent_level += 1;
    }

    fn end_object(&mut self) {
        if self.indent_level > 0 {
            self.indent_level -= 1;
        }
    }

    fn begin_array(&mut self, key: &str) {
        self.output.push_str(&format!("{}{}:\n", self.indent(), key));
        self.indent_level += 1;
    }

    fn write_array_item(&mut self, value: &str) {
        self.output.push_str(&format!("{}- {}\n", self.indent(), value));
    }

    fn end_array(&mut self) {
        if self.indent_level > 0 {
            self.indent_level -= 1;
        }
    }

    fn end(&mut self) {
        // YAML no necesita end especial
    }

    fn output(&self) -> String {
        self.output.clone()
    }
}

pub struct MarkdownExporter {
    output: String,
    stack: Vec<(String, bool)>, // (key, is_array)
}

impl MarkdownExporter {
    pub fn new() -> Self {
        Self {
            output: String::new(),
            stack: Vec::new(),
        }
    }

    fn indent(&self) -> String {
        "  ".repeat(self.stack.len())
    }
}

impl Exporter for MarkdownExporter {
    fn begin(&mut self) {
        self.output.push_str("# Export\n\n");
    }

    fn write_field(&mut self, key: &str, value: &str) {
        let indent = self.indent();
        if self.stack.is_empty() {
            self.output.push_str(&format!("- **{}**: {}\n", key, value));
        } else {
            // inside an object => use list-style key/value with indentation
            self.output.push_str(&format!("{}- **{}**: {}\n", indent, key, value));
        }
    }

    fn begin_object(&mut self, key: &str) {
        let indent = self.indent();
        self.output.push_str(&format!("{}### {}\n\n", indent, key));
        self.stack.push((key.to_string(), false));
    }

    fn end_object(&mut self) {
        if !self.stack.is_empty() {
            self.stack.pop();
            self.output.push('\n');
        }
    }

    fn begin_array(&mut self, key: &str) {
        let indent = self.indent();
        self.output.push_str(&format!("{}### {}\n\n", indent, key));
        self.stack.push((key.to_string(), true));
    }

    fn write_array_item(&mut self, value: &str) {
        let indent = self.indent();
        // array items are simple list items
        self.output.push_str(&format!("{}- {}\n", indent, value));
    }

    fn end_array(&mut self) {
        if !self.stack.is_empty() {
            self.stack.pop();
            self.output.push('\n');
        }
    }

    fn end(&mut self) {
        // close any remaining containers gently
        while !self.stack.is_empty() {
            self.stack.pop();
            self.output.push('\n');
        }
    }

    fn output(&self) -> String {
        self.output.clone()
    }
}

/// Representa una fila de datos tabulares.
pub trait TableRow {
    /// Devuelve los encabezados de la fila (una sola vez por tipo).
    fn headers() -> Vec<&'static str> where Self: Sized;
    /// Devuelve los valores de la fila, en el mismo orden que los encabezados.
    fn values(&self) -> Vec<String>;
}

pub trait CsvRow: TableRow {
    fn to_csv_row(&self) -> String {
        self.values().join(",")
    }
}

pub trait MarkdownRow: TableRow {
    fn to_markdown_row(&self) -> String {
        format!("| {} |", self.values().join(" | "))
    }

    fn markdown_header() -> String where Self: Sized {
        let headers = Self::headers().join(" | ");
        let separator = Self::headers().iter().map(|_| "---").collect::<Vec<_>>().join(" | ");
        format!("| {} |\n| {} |", headers, separator)
    }
}

pub trait XmlRow: TableRow {
    fn to_xml_row(&self) -> String where Self: Sized {
        let fields = Self::headers()
            .into_iter()
            .zip(self.values())
            .map(|(k, v)| format!("<{k}>{v}</{k}>"))
            .collect::<Vec<_>>()
            .join("");
        format!("<row>{}</row>", fields)
    }
}
