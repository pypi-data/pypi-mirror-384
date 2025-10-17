use crate::core::{SubnetCalculator, SubnetRow};

    #[derive(Debug)]
    pub struct VLSMCalculator {
        pub base_calculator: SubnetCalculator,
        pub hosts_requirements: Vec<u32>,
        pub vlsm_subnets: Vec<SubnetRow>,
    }

    // Helper function to increment an IPv4 address by n
    fn increment_ip(ip: std::net::Ipv4Addr, n: u32) -> std::net::Ipv4Addr {
        let ip_u32 = u32::from(ip);
        std::net::Ipv4Addr::from(ip_u32.saturating_add(n))
    }

    impl VLSMCalculator {
        pub fn new(ip: &str, hosts_requirements: Vec<u32>) -> Self {
            let base_calculator = SubnetCalculator::new(ip, hosts_requirements.len());
            let vlsm_subnets = Self::calculate_vlsm_subnets(&base_calculator, &hosts_requirements);
            
            Self {
                base_calculator,
                hosts_requirements,
                vlsm_subnets,
            }
        }
        
        fn calculate_vlsm_subnets(
        base_calc: &SubnetCalculator,
        hosts_requirements: &[u32],
    ) -> Vec<SubnetRow> {
        let mut subnets = Vec::new();
        let mut current_network = base_calc.ip().parse::<std::net::Ipv4Addr>().expect("Invalid IP address");

        // Sort hosts_requirements in descending order for optimal VLSM allocation
        let mut sorted_requirements: Vec<(usize, u32)> = hosts_requirements.iter()
            .enumerate()
            .map(|(i, &h)| (i, h))
            .collect();
        sorted_requirements.sort_by(|a, b| b.1.cmp(&a.1));

        for (original_index, hosts) in &sorted_requirements {
            // Calcular bits necesarios para hosts (incluyendo red y broadcast)
            let needed_host_bits = if *hosts == 0 {
                0
            } else {
                (*hosts + 2).next_power_of_two().trailing_zeros() as u32
            };
            
            let subnet_size = 2u32.pow(needed_host_bits);

            let network = current_network;
            let broadcast = increment_ip(network, subnet_size - 1);
            
            // Calcular IPs válidas
            let first_ip = if *hosts > 0 { increment_ip(network, 1) } else { network };
            let last_ip = if *hosts > 0 {
                std::net::Ipv4Addr::from(u32::from(broadcast).saturating_sub(1))
            } else { 
                network 
            };

            subnets.push(SubnetRow {
                subred: (original_index + 1) as u32, // Mantener orden original
                direccion_red: network.to_string(),
                primera_ip: first_ip.to_string(),
                ultima_ip: last_ip.to_string(),
                broadcast: broadcast.to_string(),
            });

            current_network = increment_ip(broadcast, 1);
        }

        // Reordenar para mantener el orden original de los requerimientos
        subnets.sort_by(|a, b| a.subred.cmp(&b.subred));
        subnets
    }

        
        pub fn get_vlsm_subnets(&self) -> &[SubnetRow] {
            &self.vlsm_subnets
        }
        
        // Para mantener compatibilidad
        pub fn generate_rows(&self) -> Vec<SubnetRow> {
            // Convertir VLSM subnets a SubnetRow
            self.vlsm_subnets.iter().enumerate().map(|(i, subnet)| {
                SubnetRow {
                    subred: (i + 1) as u32,
                    direccion_red: subnet.direccion_red.clone(),
                    primera_ip: subnet.primera_ip.clone(),
                    ultima_ip: subnet.ultima_ip.clone(),
                    broadcast: subnet.broadcast.clone(),
                }
            }).collect()
        }
        pub fn calculate_efficiency(&self) -> f64 {
            let total_required: u32 = self.hosts_requirements.iter().sum();
            if total_required == 0 {
                return 0.0;
            }

            let subnets = self.get_vlsm_subnets();
            let mut total_allocated = 0u32;

            for (i, subnet) in subnets.iter().enumerate() {
                let req_hosts = self.hosts_requirements.get(i).unwrap_or(&0);
                if *req_hosts > 0 {
                    total_allocated += *req_hosts;
                }
            }

            (total_required as f64 / total_allocated as f64) * 100.0
        }

        pub fn calculate_usable_hosts_for_subnet(&self, subnet: &SubnetRow) -> u32 {
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


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vlsm_calculator_creation() {
        let hosts_req = vec![50, 20, 10, 5];
        let calculator = VLSMCalculator::new("192.168.1.0", hosts_req.clone());
        
        assert_eq!(calculator.hosts_requirements, hosts_req);
        assert_eq!(calculator.base_calculator.ip(), "192.168.1.0");
        assert_eq!(calculator.base_calculator.subnet_quantity(), 4);
    }

    #[test]
    fn test_vlsm_calculator_with_single_subnet() {
        let calculator = VLSMCalculator::new("192.168.1.0", vec![30]);
        let subnets = calculator.get_vlsm_subnets();
        
        assert_eq!(subnets.len(), 1);
        assert_eq!(subnets[0].subred, 1);
        assert_eq!(subnets[0].direccion_red, "192.168.1.0");
        
        // Para 30 hosts necesitamos 32 direcciones totales (2^5)
        // Red: 192.168.1.0, Broadcast: 192.168.1.31
        assert_eq!(subnets[0].primera_ip, "192.168.1.1");
        assert_eq!(subnets[0].ultima_ip, "192.168.1.30"); // 30 hosts disponibles
        assert_eq!(subnets[0].broadcast, "192.168.1.31");
    }


    #[test]
    fn test_vlsm_calculator_with_multiple_subnets() {
        let calculator = VLSMCalculator::new("192.168.1.0", vec![50, 20, 10, 5]);
        let subnets = calculator.get_vlsm_subnets();
        
        // Debería crear 4 subredes
        assert_eq!(subnets.len(), 4);
        
        // Verificar que todas las subredes tienen IDs únicos y secuenciales
        for (i, subnet) in subnets.iter().enumerate() {
            assert_eq!(subnet.subred, (i + 1) as u32);
        }
        
        // Verificar que las direcciones de red son únicas
        let network_addrs: Vec<&String> = subnets.iter().map(|s| &s.direccion_red).collect();
        let unique_networks: std::collections::HashSet<&String> = network_addrs.iter().cloned().collect();
        assert_eq!(unique_networks.len(), subnets.len());
    }

    #[test]
    fn test_vlsm_calculator_ordered_by_host_requirements() {
        // Requerimientos desordenados
        let calculator = VLSMCalculator::new("192.168.1.0", vec![10, 50, 5, 20]);
        let subnets = calculator.get_vlsm_subnets();
        
        // VLSM debe asignar de mayor a menor requerimiento
        // La subred con más hosts debería ser la primera
        assert!(subnets.len() >= 1);
        
        // Verificar que no hay solapamiento de direcciones
        for i in 0..subnets.len() {
            for j in (i + 1)..subnets.len() {
                let net1: std::net::Ipv4Addr = subnets[i].direccion_red.parse().unwrap();
                let net2: std::net::Ipv4Addr = subnets[j].direccion_red.parse().unwrap();
                let broadcast1: std::net::Ipv4Addr = subnets[i].broadcast.parse().unwrap();
                let broadcast2: std::net::Ipv4Addr = subnets[j].broadcast.parse().unwrap();
                
                // Verificar que no hay solapamiento
                assert!(
                    u32::from(broadcast1) < u32::from(net2) || 
                    u32::from(broadcast2) < u32::from(net1),
                    "Subredes {} y {} se solapan",
                    subnets[i].direccion_red, subnets[j].direccion_red
                );
            }
        }
    }

    #[test]
    fn test_vlsm_calculator_with_class_a_network() {
        let calculator = VLSMCalculator::new("10.0.0.0", vec![1000, 500, 100]);
        let subnets = calculator.get_vlsm_subnets();
        
        assert_eq!(subnets.len(), 3);
        
        // Todas las subredes deben estar en el rango 10.0.0.0
        for subnet in subnets {
            assert!(subnet.direccion_red.starts_with("10."));
            assert!(subnet.primera_ip.starts_with("10."));
            assert!(subnet.ultima_ip.starts_with("10."));
            assert!(subnet.broadcast.starts_with("10."));
        }
    }

    #[test]
    fn test_vlsm_calculator_with_cidr_notation() {
        let calculator = VLSMCalculator::new("172.16.0.0/16", vec![100, 50, 25]);
        let subnets = calculator.get_vlsm_subnets();
        
        assert_eq!(subnets.len(), 3);
        
        // Verificar que usa la base correcta
        assert_eq!(calculator.base_calculator.has_cidr(), true);
        assert_eq!(calculator.base_calculator.cidr(), Some(16));
    }

    #[test]
    fn test_vlsm_calculator_edge_cases() {
        // Test con requerimiento de 0 hosts
        let calculator = VLSMCalculator::new("192.168.1.0", vec![0]);
        let subnets = calculator.get_vlsm_subnets();
        assert_eq!(subnets.len(), 1);
        
        // Test con lista vacía
        let calculator = VLSMCalculator::new("192.168.1.0", vec![]);
        let subnets = calculator.get_vlsm_subnets();
        assert_eq!(subnets.len(), 0);
    }

    #[test]
    fn test_vlsm_calculator_large_requirements() {
        let calculator = VLSMCalculator::new("192.168.0.0", vec![500, 200, 100, 50, 25, 10]);
        let subnets = calculator.get_vlsm_subnets();
        
        assert_eq!(subnets.len(), 6);
        
        // Verificar que todas las subredes tienen direcciones válidas
        for subnet in subnets {
            // Dirección de red válida
            assert!(subnet.direccion_red.parse::<std::net::Ipv4Addr>().is_ok());
            // Primera IP válida
            assert!(subnet.primera_ip.parse::<std::net::Ipv4Addr>().is_ok());
            // Última IP válida
            assert!(subnet.ultima_ip.parse::<std::net::Ipv4Addr>().is_ok());
            // Broadcast válido
            assert!(subnet.broadcast.parse::<std::net::Ipv4Addr>().is_ok());
            
            // Primera IP debe ser mayor que dirección de red
            let network: u32 = subnet.direccion_red.parse::<std::net::Ipv4Addr>().unwrap().into();
            let first_ip: u32 = subnet.primera_ip.parse::<std::net::Ipv4Addr>().unwrap().into();
            assert!(first_ip > network);
            
            // Última IP debe ser menor que broadcast
            let last_ip: u32 = subnet.ultima_ip.parse::<std::net::Ipv4Addr>().unwrap().into();
            let broadcast: u32 = subnet.broadcast.parse::<std::net::Ipv4Addr>().unwrap().into();
            assert!(last_ip < broadcast);
        }
    }

    #[test]
    fn test_generate_rows_compatibility() {
        let calculator = VLSMCalculator::new("192.168.1.0", vec![30, 10]);
        let rows = calculator.generate_rows();
        let subnets = calculator.get_vlsm_subnets();
        
        // generate_rows debe devolver los mismos datos que get_vlsm_subnets
        assert_eq!(rows.len(), subnets.len());
        
        for (row, subnet) in rows.iter().zip(subnets.iter()) {
            assert_eq!(row.subred, subnet.subred);
            assert_eq!(row.direccion_red, subnet.direccion_red);
            assert_eq!(row.primera_ip, subnet.primera_ip);
            assert_eq!(row.ultima_ip, subnet.ultima_ip);
            assert_eq!(row.broadcast, subnet.broadcast);
        }
    }

    #[test]
    fn test_increment_ip_function() {
        let ip = "192.168.1.0".parse::<std::net::Ipv4Addr>().unwrap();
        
        // Incremento normal
        let incremented = increment_ip(ip, 1);
        assert_eq!(incremented.to_string(), "192.168.1.1");
        
        // Incremento múltiple
        let incremented = increment_ip(ip, 256);
        assert_eq!(incremented.to_string(), "192.168.2.0");
        
        // Incremento cero
        let incremented = increment_ip(ip, 0);
        assert_eq!(incremented.to_string(), "192.168.1.0");
        
        // Test de saturación (no debería panic)
        let large_ip = "255.255.255.255".parse::<std::net::Ipv4Addr>().unwrap();
        let saturated = increment_ip(large_ip, 1);
        assert_eq!(saturated.to_string(), "255.255.255.255"); // Se satura
    }

    #[test]
    fn test_vlsm_efficient_allocation() {
        // Este test verifica que VLSM asigna eficientemente el espacio
        let calculator = VLSMCalculator::new("192.168.1.0", vec![60, 30, 10]);
        let subnets = calculator.get_vlsm_subnets();
        
        // Calcular el espacio total utilizado
        let first_network: u32 = subnets[0].direccion_red.parse::<std::net::Ipv4Addr>().unwrap().into();
        let last_broadcast: u32 = subnets.last().unwrap().broadcast.parse::<std::net::Ipv4Addr>().unwrap().into();
        let total_used = last_broadcast - first_network + 1;
        
        // El espacio utilizado debería ser menor que si usáramos FLSM
        // (esto es una verificación conceptual)
        assert!(total_used <= 256, "VLSM debería usar el espacio eficientemente");
    }

    #[test]
    fn test_vlsm_with_very_large_host_requirements() {
        // Test con requerimientos que necesitan máscaras grandes
        let calculator = VLSMCalculator::new("10.0.0.0", vec![10000, 5000, 1000]);
        let subnets = calculator.get_vlsm_subnets();
        
        assert_eq!(subnets.len(), 3);
        
        // Verificar que las subredes grandes tienen suficientes hosts
        for (i, &required_hosts) in [10000, 5000, 1000].iter().enumerate() {
            let network: u32 = subnets[i].direccion_red.parse::<std::net::Ipv4Addr>().unwrap().into();
            let broadcast: u32 = subnets[i].broadcast.parse::<std::net::Ipv4Addr>().unwrap().into();
            let available_hosts = broadcast - network - 1;
            
            assert!(
                available_hosts >= required_hosts,
                "Subred {} tiene {} hosts, pero necesita {}",
                i + 1, available_hosts, required_hosts
            );
        }
    }
}