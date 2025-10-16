use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct SubnetRow {
    pub subred: u32,
    pub direccion_red: String,
    pub primera_ip: String,
    pub ultima_ip: String,
    pub broadcast: String,
}

#[derive(Debug, Clone)]
pub struct SubnetCalculator {
    original_ip: String,
    pub has_cidr: bool,
    ip: String,
    cidr: Option<u8>,
    subnet_quantity: usize,
    net_class: String,
    subnet_mask: String,
    binary_subnet_mask: String,
    new_subnet_mask: String,
    binary_new_mask: String,
    net_jump: u32,
    hosts_quantity: u32,
}

impl SubnetCalculator {
    pub fn new(ip: &str, subnet_quantity: usize) -> Self {
        let has_cidr = ip.contains('/');
        let (ip_str, cidr_opt) = if has_cidr {
            let parts: Vec<&str> = ip.split('/').collect();
            (parts[0].to_string(), Some(parts[1].parse::<u8>().unwrap_or(24)))
        } else {
            (ip.to_string(), None)
        };

        let mut calculator = Self {
            original_ip: ip.to_string(),
            has_cidr,
            ip: ip_str,
            cidr: cidr_opt,
            subnet_quantity,
            net_class: String::new(),
            subnet_mask: String::new(),
            binary_subnet_mask: String::new(),
            new_subnet_mask: String::new(),
            binary_new_mask: String::new(),
            net_jump: 0,
            hosts_quantity: 0,
        };

        calculator.net_class = calculator.get_net_class();
        calculator.subnet_mask = calculator.get_subnet_mask();
        calculator.binary_subnet_mask = calculator.get_binary_submask();
        calculator.new_subnet_mask = calculator.new_mask();
        calculator.binary_new_mask = calculator.get_binary_new_mask();
        calculator.net_jump = calculator.get_jump();
        calculator.hosts_quantity = calculator.calculate_hosts();

        calculator
    }

    fn get_net_class(&self) -> String {
        let first_octet = self.ip.split('.').next()
            .and_then(|s| s.parse::<u8>().ok())
            .unwrap_or(0);

        if self.has_cidr {
            let cidr_val = self.cidr.unwrap_or(24);
            if cidr_val <= 8 {
                return "Clase A (CIDR)".to_string();
            } else if cidr_val <= 16 {
                return "Clase B (CIDR)".to_string();
            } else if cidr_val <= 24 {
                return "Clase C (CIDR)".to_string();
            } else {
                return format!("CIDR /{}", cidr_val);
            }
        }

        match first_octet {
            1..=126 => "Clase A".to_string(),
            128..=191 => "Clase B".to_string(),
            192..=223 => "Clase C".to_string(),
            224..=239 => "Clase D".to_string(),
            240..=255 => "Clase E".to_string(),
            _ => "Desconocida".to_string(),
        }
    }

    fn get_subnet_mask(&self) -> String {
        if self.has_cidr {
            return self.cidr_to_mask(self.cidr.unwrap_or(24));
        }

        if self.net_class.starts_with("Clase A") {
            "255.0.0.0".to_string()
        } else if self.net_class.starts_with("Clase B") {
            "255.255.0.0".to_string()
        } else if self.net_class.starts_with("Clase C") {
            "255.255.255.0".to_string()
        } else {
            "0.0.0.0".to_string()
        }
    }

    fn cidr_to_mask(&self, cidr: u8) -> String {
        let mask = (0xffffffff_u32 >> (32 - cidr)) << (32 - cidr);
        format!(
            "{}.{}.{}.{}",
            (mask >> 24) & 0xff,
            (mask >> 16) & 0xff,
            (mask >> 8) & 0xff,
            mask & 0xff
        )
    }

    pub fn mask_to_cidr(&self, mask: &str) -> u8 {
        mask.split('.')
            .map(|x| x.parse::<u8>().unwrap_or(0).count_ones() as u8)
            .sum()
    }

    fn get_binary_submask(&self) -> String {
        self.octets_to_binary(&self.subnet_mask)
    }

    fn get_binary_new_mask(&self) -> String {
        self.octets_to_binary(&self.new_subnet_mask)
    }

    fn octets_to_binary(&self, ip: &str) -> String {
        ip.split('.')
            .map(|o| format!("{:08b}", o.parse::<u8>().unwrap_or(0)))
            .collect::<Vec<String>>()
            .join(".")
    }

    fn subnet_formula(&self) -> u32 {
        let mut bits = 0;
        while 2u32.pow(bits) < self.subnet_quantity as u32 {
            bits += 1;
        }
        bits
    }

    fn new_mask(&self) -> String {
        let bits = self.subnet_formula();

    if self.has_cidr {
        let new_cidr = self.cidr.unwrap_or(24) + bits as u8;
        let mask = self.cidr_to_mask(new_cidr);
        return mask;
    }

        let binary_mask: String = self.subnet_mask
            .split('.')
            .map(|o| format!("{:08b}", o.parse::<u8>().unwrap_or(0)))
            .collect::<Vec<String>>()
            .join("");

        let mut binary_list: Vec<char> = binary_mask.chars().collect();
        let mut ones_count = 0;

        for i in 0..binary_list.len() {
            if binary_list[i] == '0' && ones_count < bits {
                binary_list[i] = '1';
                ones_count += 1;
            }
            if ones_count >= bits {
                break;
            }
        }

        let new_binary_mask: String = binary_list.into_iter().collect();
        format!(
            "{}.{}.{}.{}",
            u8::from_str_radix(&new_binary_mask[0..8], 2).unwrap_or(0),
            u8::from_str_radix(&new_binary_mask[8..16], 2).unwrap_or(0),
            u8::from_str_radix(&new_binary_mask[16..24], 2).unwrap_or(0),
            u8::from_str_radix(&new_binary_mask[24..32], 2).unwrap_or(0)
        )
    }

    fn get_jump(&self) -> u32 {
        for octet in self.new_subnet_mask.split('.') {
            let octet_val = octet.parse::<u8>().unwrap_or(255);
            if octet_val != 255 {
                return 256 - octet_val as u32;
            }
        }
        0
    }

    pub fn get_jump_octet(&self) -> usize {
    
    if self.has_cidr {
        let new_cidr = self.mask_to_cidr(&self.new_subnet_mask);
        
        // Analizar cada octeto de la máscara
        let octets: Vec<u8> = self.new_subnet_mask
            .split('.')
            .map(|o| o.parse::<u8>().unwrap_or(0))
            .collect();
        
        
        // Encontrar el primer octeto que no es 255
        for (index, &octet) in octets.iter().enumerate() {
            if octet != 255 {
                return index;
            }
        }
    }

    // Fallback para sin CIDR
    for (index, octet) in self.new_subnet_mask.split('.').enumerate() {
        if octet.parse::<u8>().unwrap_or(255) != 255 {
            return index;
        }
    }
    
    println!("  Fallback to octet 3");
    3
}

    fn calculate_hosts(&self) -> u32 {
        let binary_mask: String = self.new_subnet_mask
            .split('.')
            .map(|o| format!("{:08b}", o.parse::<u8>().unwrap_or(0)))
            .collect::<Vec<String>>()
            .join("");

        let host_bits = binary_mask.chars().filter(|&c| c == '0').count() as u32;
        let new_cidr = self.mask_to_cidr(&self.new_subnet_mask);
        
        // Casos especiales para /31 y /32
        match new_cidr {
            31 => {
                2  // /31 permite 2 hosts en redes punto-a-punto
            },
            32 => {
                1  // /32 es una ruta de host único
            },
            _ => {
                let hosts = if host_bits > 0 {
                    (2u32.pow(host_bits)) - 2
                } else {
                    0
                };
                hosts
            }
        }
    }

    fn calculate_broadcast_and_last_ip(&self, network_parts: [u8; 4], jump_octet: usize) -> (String, String) {
    match jump_octet {
        1 => { // Class A - saltos en segundo octeto
            let mut broadcast_parts = network_parts;
            // Usar saturating_add y convertir net_jump a u8 de forma segura
            let jump_adjustment = (self.net_jump as u8).saturating_sub(1);
            broadcast_parts[1] = network_parts[1].saturating_add(jump_adjustment);
            broadcast_parts[2] = 255;
            broadcast_parts[3] = 255;

            let mut last_ip_parts = broadcast_parts;
            last_ip_parts[3] = 254;

            (
                format!("{}.{}.{}.{}", 
                    broadcast_parts[0], broadcast_parts[1], broadcast_parts[2], broadcast_parts[3]),
                format!("{}.{}.{}.{}", 
                    last_ip_parts[0], last_ip_parts[1], last_ip_parts[2], last_ip_parts[3])
            )
        }
        2 => { // Class B - saltos en tercer octeto
            let mut broadcast_parts = network_parts;
            let jump_adjustment = (self.net_jump as u8).saturating_sub(1);
            broadcast_parts[2] = network_parts[2].saturating_add(jump_adjustment);
            broadcast_parts[3] = 255;

            let mut last_ip_parts = broadcast_parts;
            last_ip_parts[3] = 254;

            (
                format!("{}.{}.{}.{}", 
                    broadcast_parts[0], broadcast_parts[1], broadcast_parts[2], broadcast_parts[3]),
                format!("{}.{}.{}.{}", 
                    last_ip_parts[0], last_ip_parts[1], last_ip_parts[2], last_ip_parts[3])
            )
        }
        _ => { // Class C - saltos en cuarto octeto
            let mut broadcast_parts = network_parts;
            let jump_adjustment = (self.net_jump as u8).saturating_sub(1);
            broadcast_parts[3] = network_parts[3].saturating_add(jump_adjustment);

            let mut last_ip_parts = broadcast_parts;
            last_ip_parts[3] = broadcast_parts[3].saturating_sub(1);

            (
                format!("{}.{}.{}.{}", 
                    broadcast_parts[0], broadcast_parts[1], broadcast_parts[2], broadcast_parts[3]),
                format!("{}.{}.{}.{}", 
                    last_ip_parts[0], last_ip_parts[1], last_ip_parts[2], last_ip_parts[3])
            )
        }
    }
}

    fn get_network_address(&self, subnet_index: usize) -> [u8; 4] {
    let mut ip_parts: Vec<u8> = self.ip
        .split('.')
        .map(|s| s.parse::<u8>().unwrap_or(0))
        .collect();

    if ip_parts.len() != 4 {
        ip_parts = vec![0, 0, 0, 0];
    }

    let jump_octet = self.get_jump_octet();
    let jump = (self.net_jump as u8).min(255); // Asegurarse de que no exceda 255

    let mut result = [ip_parts[0], ip_parts[1], ip_parts[2], ip_parts[3]];

    match jump_octet {
        1 => {
            result[1] = (subnet_index as u8).saturating_mul(jump);
            result[2] = 0;
            result[3] = 0;
        }
        2 => {
            result[2] = (subnet_index as u8).saturating_mul(jump);
            result[3] = 0;
        }
        _ => {
            result[3] = (subnet_index as u8).saturating_mul(jump);
        }
    }

    result
}

    // Método principal que genera los datos estructurados
    pub fn generate_rows(&self) -> Vec<SubnetRow> {
        let mut rows = Vec::new();

        for i in 0..self.subnet_quantity {
            let network_parts = self.get_network_address(i);
            let jump_octet = self.get_jump_octet();

            // Dirección de red
            let network_addr = format!("{}.{}.{}.{}", 
                network_parts[0], network_parts[1], network_parts[2], network_parts[3]);

            // Primera IP útil
            let mut first_ip_parts = network_parts;
            first_ip_parts[3] = first_ip_parts[3].saturating_add(1);
            let first_ip = format!("{}.{}.{}.{}", 
                first_ip_parts[0], first_ip_parts[1], first_ip_parts[2], first_ip_parts[3]);

            // Broadcast y última IP
            let (broadcast_addr, last_ip) = self.calculate_broadcast_and_last_ip(network_parts, jump_octet);

            rows.push(SubnetRow {
                subred: (i + 1) as u32,
                direccion_red: network_addr,
                primera_ip: first_ip,
                ultima_ip: last_ip,
                broadcast: broadcast_addr,
            });
        }

        rows
    }

    // Método para convertir a HashMap (útil para JSON o otros formatos)
    pub fn generate_hashmap(&self) -> Vec<HashMap<String, String>> {
        self.generate_rows()
            .into_iter()
            .map(|row| {
                let mut map = HashMap::new();
                map.insert("subred".to_string(), row.subred.to_string());
                map.insert("direccion_red".to_string(), row.direccion_red);
                map.insert("primera_ip".to_string(), row.primera_ip);
                map.insert("ultima_ip".to_string(), row.ultima_ip);
                map.insert("broadcast".to_string(), row.broadcast);
                map
            })
            .collect()
    }


    // Getters para acceder a los campos privados
    pub fn original_ip(&self) -> &str { &self.original_ip }
    pub fn net_class(&self) -> &str { &self.net_class }
    pub fn subnet_mask(&self) -> &str { &self.subnet_mask }
    pub fn new_subnet_mask(&self) -> &str { &self.new_subnet_mask }
    pub fn net_jump(&self) -> u32 { self.net_jump }
    pub fn hosts_quantity(&self) -> u32 { self.hosts_quantity }

    // Getters adicionales para testing
    pub fn subnet_quantity(&self) -> usize { self.subnet_quantity }
    pub fn has_cidr(&self) -> bool { self.has_cidr }
    pub fn cidr(&self) -> Option<u8> { self.cidr }
    pub fn ip(&self) -> &str { &self.ip }

    // Getters para campos binarios
    pub fn binary_subnet_mask(&self) -> &str { &self.binary_subnet_mask }
    pub fn binary_new_mask(&self) -> &str { &self.binary_new_mask }
}

// Implementación de Display para debugging
impl std::fmt::Display for SubnetCalculator {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        writeln!(f, "IP: {}", self.original_ip)?;
        writeln!(f, "Clase: {}", self.net_class)?;
        if self.has_cidr {
            writeln!(f, "CIDR: /{}", self.cidr.unwrap_or(24))?;
        }
        writeln!(f, "Máscara base: {} - {}", self.subnet_mask, self.binary_subnet_mask)?;
        writeln!(f, "Nueva máscara: {} - {}", self.new_subnet_mask, self.binary_new_mask)?;
        if self.has_cidr {
            writeln!(f, "Nuevo CIDR: /{}", self.mask_to_cidr(&self.new_subnet_mask))?;
        }
        writeln!(f, "Saltos entre subredes: {}", self.net_jump)?;
        write!(f, "Hosts por subred: {}", self.hosts_quantity)
    }
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_subnet_calculator_creation() {
        let calculator = SubnetCalculator::new("192.168.1.0/24", 4);
        
        assert_eq!(calculator.original_ip(), "192.168.1.0/24");
        assert_eq!(calculator.subnet_quantity(), 4);
        assert!(calculator.has_cidr());
        assert_eq!(calculator.cidr(), Some(24));
        assert_eq!(calculator.ip(), "192.168.1.0");
    }

    #[test]
    fn test_subnet_calculator_no_cidr() {
        let calculator = SubnetCalculator::new("192.168.1.0", 4);
        
        assert_eq!(calculator.original_ip(), "192.168.1.0");
        assert!(!calculator.has_cidr());
        assert_eq!(calculator.cidr(), None);
        assert_eq!(calculator.ip(), "192.168.1.0");
    }

    #[test]
    fn test_net_class_with_cidr() {
        let class_a = SubnetCalculator::new("10.0.0.0/8", 2);
        let class_b = SubnetCalculator::new("172.16.0.0/16", 2);
        let class_c = SubnetCalculator::new("192.168.1.0/24", 2);
        let small_cidr = SubnetCalculator::new("192.168.1.0/30", 2);
        
        assert!(class_a.net_class().contains("Clase A"));
        assert!(class_b.net_class().contains("Clase B"));
        assert!(class_c.net_class().contains("Clase C"));
        assert!(small_cidr.net_class().contains("CIDR /30"));
    }

    #[test]
    fn test_net_class_without_cidr() {
        let class_a = SubnetCalculator::new("10.0.0.0", 2);
        let class_b = SubnetCalculator::new("172.16.0.0", 2);
        let class_c = SubnetCalculator::new("192.168.1.0", 2);
        let class_d = SubnetCalculator::new("224.0.0.0", 2);
        let class_e = SubnetCalculator::new("240.0.0.0", 2);
        
        assert_eq!(class_a.net_class(), "Clase A");
        assert_eq!(class_b.net_class(), "Clase B");
        assert_eq!(class_c.net_class(), "Clase C");
        assert_eq!(class_d.net_class(), "Clase D");
        assert_eq!(class_e.net_class(), "Clase E");
    }

    #[test]
    fn test_cidr_to_mask() {
        let calculator = SubnetCalculator::new("192.168.1.0/24", 2);
        
        assert_eq!(calculator.cidr_to_mask(8), "255.0.0.0");
        assert_eq!(calculator.cidr_to_mask(16), "255.255.0.0");
        assert_eq!(calculator.cidr_to_mask(24), "255.255.255.0");
        assert_eq!(calculator.cidr_to_mask(25), "255.255.255.128");
        assert_eq!(calculator.cidr_to_mask(32), "255.255.255.255");
    }

    #[test]
    fn test_mask_to_cidr() {
        let calculator = SubnetCalculator::new("192.168.1.0/24", 2);
        
        assert_eq!(calculator.mask_to_cidr("255.0.0.0"), 8);
        assert_eq!(calculator.mask_to_cidr("255.255.0.0"), 16);
        assert_eq!(calculator.mask_to_cidr("255.255.255.0"), 24);
        assert_eq!(calculator.mask_to_cidr("255.255.255.128"), 25);
        assert_eq!(calculator.mask_to_cidr("255.255.255.255"), 32);
    }

    #[test]
    fn test_subnet_formula() {
        let calc_2 = SubnetCalculator::new("192.168.1.0/24", 2);
        let calc_4 = SubnetCalculator::new("192.168.1.0/24", 4);
        let calc_8 = SubnetCalculator::new("192.168.1.0/24", 8);
        let calc_16 = SubnetCalculator::new("192.168.1.0/24", 16);
        
        assert_eq!(calc_2.subnet_formula(), 1);  // 2^1 = 2 >= 2
        assert_eq!(calc_4.subnet_formula(), 2);  // 2^2 = 4 >= 4
        assert_eq!(calc_8.subnet_formula(), 3);  // 2^3 = 8 >= 8
        assert_eq!(calc_16.subnet_formula(), 4); // 2^4 = 16 >= 16
    }

    #[test]
    fn test_new_mask_with_cidr() {
        let calculator = SubnetCalculator::new("192.168.1.0/24", 4);
        
        // /24 + 2 bits = /26
        assert_eq!(calculator.new_subnet_mask(), "255.255.255.192");
        assert_eq!(calculator.mask_to_cidr(calculator.new_subnet_mask()), 26);
    }

    #[test]
    fn test_new_mask_without_cidr() {
        let calculator = SubnetCalculator::new("192.168.1.0", 4); // Clase C
        
        // Máscara base 255.255.255.0 + 2 bits = 255.255.255.192
        assert_eq!(calculator.new_subnet_mask(), "255.255.255.192");
    }

    #[test]
    fn test_get_jump() {
        let calc_24 = SubnetCalculator::new("192.168.1.0/24", 4);  // /26 -> jump 64
        let calc_16 = SubnetCalculator::new("172.16.0.0/16", 4);   // /18 -> jump 64
        let calc_8 = SubnetCalculator::new("10.0.0.0/8", 4);      // /10 -> jump 64
        
        assert_eq!(calc_24.net_jump(), 64);
        assert_eq!(calc_16.net_jump(), 64);
        assert_eq!(calc_8.net_jump(), 64);
    }

    #[test]
fn test_get_jump_octet() {
    println!("=== Testing get_jump_octet ===");
    
    // Para Class A con /8 -> /10, salto en segundo octeto
    let calc_a = SubnetCalculator::new("10.0.0.0/8", 4);
    println!("Class A case:");
    let jump_a = calc_a.get_jump_octet();
    assert_eq!(jump_a, 1, "Class A should jump in octet 1");
    
    // Para Class B con /16 -> /18, salto en tercer octeto  
    let calc_b = SubnetCalculator::new("172.16.0.0/16", 4);
    println!("\nClass B case:");
    let jump_b = calc_b.get_jump_octet();
    assert_eq!(jump_b, 2, "Class B should jump in octet 2");
    
    // Para Class C con /24 -> /26, salto en cuarto octeto
    let calc_c = SubnetCalculator::new("192.168.1.0/24", 4);
    println!("\nClass C case:");
    let jump_c = calc_c.get_jump_octet();
    assert_eq!(jump_c, 3, "Class C should jump in octet 3");
}

#[test]
fn test_get_jump_octet_detailed() {
    let test_cases = vec![
        ("10.0.0.0/8", 4, 1),    // Class A: /8 -> /10, jump in octet 1
        ("172.16.0.0/16", 4, 2), // Class B: /16 -> /18, jump in octet 2  
        ("192.168.1.0/24", 4, 3), // Class C: /24 -> /26, jump in octet 3
        ("192.168.1.0/24", 2, 3), // Class C: /24 -> /25, jump in octet 3
        ("192.168.1.0/24", 8, 3), // Class C: /24 -> /27, jump in octet 3
    ];
    
    for (ip, subnets, expected_octet) in test_cases {
        let calculator = SubnetCalculator::new(ip, subnets);
        let actual_octet = calculator.get_jump_octet();
        let new_cidr = calculator.mask_to_cidr(calculator.new_subnet_mask());
        assert_eq!(actual_octet, expected_octet, 
                   "{} with {} subnets -> /{} should jump in octet {}, got {}", 
                   ip, subnets, new_cidr, expected_octet, actual_octet);
    }
}

    #[test]
    fn test_calculate_hosts() {
        println!("=== Testing Host Calculations ===");
        
        let calc_24 = SubnetCalculator::new("192.168.1.0/24", 4);
        assert_eq!(calc_24.hosts_quantity(), 62, "/26 should have 62 hosts");
        
        let calc_30 = SubnetCalculator::new("192.168.1.0/30", 2);
        assert_eq!(calc_30.hosts_quantity(), 2, "/30 with 2 subnets becomes /31 with 2 hosts");
        
        // ¡ESTO ES CORRECTO! /31 con 2 subredes se convierte en /32 con 1 host
        let calc_31 = SubnetCalculator::new("192.168.1.0/31", 2);
        assert_eq!(calc_31.hosts_quantity(), 1, "/31 with 2 subnets becomes /32 with 1 host");
        
        let calc_32 = SubnetCalculator::new("192.168.1.0/32", 1);
        assert_eq!(calc_32.hosts_quantity(), 1, "/32 should have 1 host");
    }

    #[test]
    fn test_get_network_address() {
        let calculator = SubnetCalculator::new("192.168.1.0/24", 4); // /26 -> jump 64
        
        let net0 = calculator.get_network_address(0);
        let net1 = calculator.get_network_address(1);
        let net2 = calculator.get_network_address(2);
        let net3 = calculator.get_network_address(3);
        
        assert_eq!(net0, [192, 168, 1, 0]);
        assert_eq!(net1, [192, 168, 1, 64]);
        assert_eq!(net2, [192, 168, 1, 128]);
        assert_eq!(net3, [192, 168, 1, 192]);
    }

#[test]
fn test_generate_rows() {
    let calculator = SubnetCalculator::new("192.168.1.0/24", 2);
    let rows = calculator.generate_rows();
    
    assert_eq!(rows.len(), 2);
    
    // Verificar estructura de datos
    assert_eq!(rows[0].subred, 1);
    assert_eq!(rows[0].direccion_red, "192.168.1.0");
    assert_eq!(rows[0].primera_ip, "192.168.1.1");
    assert_eq!(rows[0].ultima_ip, "192.168.1.126");  // CORREGIDO: 126 no 62
    assert_eq!(rows[0].broadcast, "192.168.1.127");  // CORREGIDO: 127 no 63
    
    assert_eq!(rows[1].subred, 2);
    assert_eq!(rows[1].direccion_red, "192.168.1.128");
    assert_eq!(rows[1].primera_ip, "192.168.1.129");
    assert_eq!(rows[1].ultima_ip, "192.168.1.254");  // CORREGIDO: 254 no 190
    assert_eq!(rows[1].broadcast, "192.168.1.255");  // CORREGIDO: 255 no 191
}

#[test]
fn test_generate_hashmap() {
    let calculator = SubnetCalculator::new("192.168.1.0/24", 2);
    let hashmap_data = calculator.generate_hashmap();
    
    assert_eq!(hashmap_data.len(), 2);
    
    // Verificar estructura del primer elemento con valores CORREGIDOS para /25
    let first_row = &hashmap_data[0];
    assert_eq!(first_row.get("subred"), Some(&"1".to_string()));
    assert_eq!(first_row.get("direccion_red"), Some(&"192.168.1.0".to_string()));
    assert_eq!(first_row.get("primera_ip"), Some(&"192.168.1.1".to_string()));
    assert_eq!(first_row.get("ultima_ip"), Some(&"192.168.1.126".to_string()));  // CORREGIDO: 126 no 62
    assert_eq!(first_row.get("broadcast"), Some(&"192.168.1.127".to_string()));  // CORREGIDO: 127 no 63
    
    // Verificar segundo elemento
    let second_row = &hashmap_data[1];
    assert_eq!(second_row.get("subred"), Some(&"2".to_string()));
    assert_eq!(second_row.get("direccion_red"), Some(&"192.168.1.128".to_string()));
    assert_eq!(second_row.get("primera_ip"), Some(&"192.168.1.129".to_string()));
    assert_eq!(second_row.get("ultima_ip"), Some(&"192.168.1.254".to_string()));  // CORREGIDO: 254 no 190
    assert_eq!(second_row.get("broadcast"), Some(&"192.168.1.255".to_string()));  // CORREGIDO: 255 no 191
}

    #[test]
    fn test_binary_masks() {
        let calculator = SubnetCalculator::new("192.168.1.0/24", 4);
        
        // Verificar que las máscaras binarias tienen el formato correcto
        assert!(calculator.binary_subnet_mask().contains("."));
        assert!(calculator.binary_new_mask().contains("."));
        
        // Máscara base /24 en binario
        assert_eq!(calculator.binary_subnet_mask(), "11111111.11111111.11111111.00000000");
        
        // Nueva máscara /26 en binario
        assert_eq!(calculator.binary_new_mask(), "11111111.11111111.11111111.11000000");
    }

    #[test]
    fn test_display_implementation() {
        let calculator = SubnetCalculator::new("192.168.1.0/24", 4);
        let display_output = format!("{}", calculator);
        
        // Verificar que contiene información clave
        assert!(display_output.contains("IP: 192.168.1.0/24"));
        assert!(display_output.contains("Clase:"));
        assert!(display_output.contains("Máscara base:"));
        assert!(display_output.contains("Nueva máscara:"));
        assert!(display_output.contains("Saltos entre subredes:"));
        assert!(display_output.contains("Hosts por subred:"));
    }

    #[test]
    fn test_edge_cases() {
        // Test con cantidad mínima de subredes
        let calc_min = SubnetCalculator::new("192.168.1.0/24", 1);
        assert_eq!(calc_min.subnet_formula(), 0); // 2^0 = 1 >= 1
        assert_eq!(calc_min.new_subnet_mask(), "255.255.255.0"); // Sin cambios
        
        // Test con IP inválida (debería manejarse gracefulmente)
        let calc_invalid = SubnetCalculator::new("300.400.500.600", 2);
        // Verificar que no panic y tenga valores por defecto razonables
        assert_eq!(calc_invalid.net_class(), "Desconocida");
    }

    #[test]
    fn test_class_a_subnetting() {
        let calculator = SubnetCalculator::new("10.0.0.0/8", 4);
        let rows = calculator.generate_rows();
        
        assert_eq!(rows.len(), 4);
        assert_eq!(rows[0].direccion_red, "10.0.0.0");
        assert_eq!(rows[1].direccion_red, "10.64.0.0"); // Jump en segundo octeto
    }

    #[test]
    fn test_class_b_subnetting() {
        let calculator = SubnetCalculator::new("172.16.0.0/16", 4);
        let rows = calculator.generate_rows();
        
        assert_eq!(rows.len(), 4);
        assert_eq!(rows[0].direccion_red, "172.16.0.0");
        assert_eq!(rows[1].direccion_red, "172.16.64.0"); // Jump en tercer octeto
    }

    #[test]
    fn test_large_subnet_quantity() {
        let calculator = SubnetCalculator::new("192.168.1.0/24", 16);
        
        // 16 subredes requieren 4 bits (2^4 = 16)
        assert_eq!(calculator.subnet_formula(), 4);
        // /24 + 4 = /28
        assert_eq!(calculator.mask_to_cidr(calculator.new_subnet_mask()), 28);
        assert_eq!(calculator.hosts_quantity(), 14); // 2^4 - 2 = 14
    }
    #[test]
fn test_overflow_protection() {
    // Test que específicamente causaría overflow sin protección
    let calculator = SubnetCalculator::new("192.168.1.0/24", 2);
    
    // Verificar que net_jump es 128 (que causaría overflow en u8)
    assert_eq!(calculator.net_jump(), 128);
    
    // Esto no debería panic
    let rows = calculator.generate_rows();
    
    // Debería generar las filas correctamente
    assert_eq!(rows.len(), 2);
    assert_eq!(rows[0].direccion_red, "192.168.1.0");
    assert_eq!(rows[0].broadcast, "192.168.1.127");
    assert_eq!(rows[1].direccion_red, "192.168.1.128");
    assert_eq!(rows[1].broadcast, "192.168.1.255");
}

#[test]
fn test_edge_case_large_jump() {
    // Test con saltos grandes que podrían causar overflow
    let calculator = SubnetCalculator::new("10.0.0.0/8", 2);
    let rows = calculator.generate_rows();
    
    // No debería panic
    assert_eq!(rows.len(), 2);
}
}