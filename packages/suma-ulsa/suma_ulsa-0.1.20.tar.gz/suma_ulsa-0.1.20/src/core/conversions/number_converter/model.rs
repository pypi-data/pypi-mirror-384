#[derive(Debug, Clone)]
pub struct NumberConverter {
    pub value: i64,
    pub history: Vec<String>,
}

impl NumberConverter {
    pub fn new(value: i64) -> Self {
        NumberConverter {
            value,
            history: vec![format!("Inicial: decimal={}", value)],
        }
    }

    // Métodos que no modifican el estado deberían usar &self
    pub fn as_binary(&self) -> String {
        format!("{:b}", self.value)
    }
    
    pub fn as_hex(&self) -> String {
        format!("{:X}", self.value)
    }
    
    pub fn as_letters(&self) -> String {
        let mut letters = String::new();
        let mut num = self.value;
        
        while num > 0 {
            let rem = ((num - 1) % 26) as u8;
            letters.insert(0, (b'A' + rem) as char);
            num = (num - 1) / 26;
        }
        letters
    }

    // Métodos que agregan al historial (modifican estado)
    pub fn to_binary(&mut self) -> String {
        let binary = self.as_binary();
        self.history.push(format!("Convertido a binario: {}", binary));
        binary
    }

    pub fn to_hex(&mut self) -> String {
        let hex = self.as_hex();
        self.history.push(format!("Convertido a hexadecimal: {}", hex));
        hex
    }

    pub fn to_letters(&mut self) -> String {
        let letters = self.as_letters();
        self.history.push(format!("Convertido a letras: {}", letters));
        letters
    }

    // Mejor rendimiento: evitar clone del Vec
    pub fn get_history(&self) -> &[String] {
        &self.history
    }
    
    // Para obtener una copia si es necesario
    pub fn history_cloned(&self) -> Vec<String> {
        self.history.clone()
    }
}