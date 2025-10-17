use crate::core::boolean_algebra::error::ParseError;

/// Tokens reconocidos por el lexer
#[derive(Debug, Clone, PartialEq)]
pub enum Token {
    Variable(String),
    And,
    Or,
    Not,
    Xor,
    Implies,
    Iff,
    LeftParen,
    RightParen,
    Constant(bool),
    EOF, 
}

/// Lexer que convierte strings en tokens
pub struct Lexer {
    input: Vec<char>,
    position: usize,
    current_char: Option<char>,
}

impl Lexer {
    /// Crea un nuevo lexer a partir de un string
    pub fn new(input: &str) -> Self {
        let chars: Vec<char> = input.chars().collect();
        let current_char = if chars.is_empty() { None } else { Some(chars[0]) };
        
        Lexer {
            input: chars,
            position: 0,
            current_char,
        }
    }
    
    /// Avanza al siguiente carácter
    fn advance(&mut self) {
        self.position += 1;
        self.current_char = if self.position < self.input.len() {
            Some(self.input[self.position])
        } else {
            None
        };
    }
    
    /// Salta espacios en blanco y comentarios
    fn skip_whitespace(&mut self) {
        while let Some(c) = self.current_char {
            if c.is_whitespace() {
                self.advance();
            } else if c == '#' {
                // Salta comentarios (hasta fin de línea)
                self.skip_comment();
            } else {
                break;
            }
        }
    }
    
    /// Salta comentarios (todo después de # hasta fin de línea)
    fn skip_comment(&mut self) {
        while let Some(c) = self.current_char {
            if c == '\n' {
                self.advance();
                break;
            }
            self.advance();
        }
    }
    
    /// Lee un identificador (variable o operador textual)
    fn read_identifier(&mut self) -> String {
        let mut identifier = String::new();
        
        while let Some(c) = self.current_char {
            if c.is_alphanumeric() || c == '_' {
                identifier.push(c);
                self.advance();
            } else {
                break;
            }
        }
        
        identifier
    }
    
    /// Determina si un identificador es un operador reservado
    fn identifier_to_token(&mut self, identifier: &str) -> Token {
        match identifier.to_lowercase().as_str() {
            "and" | "&&" | "∧" => Token::And,
            "or" | "||" | "∨" => Token::Or,
            "not" | "!" | "¬" | "~" => Token::Not,
            "xor" | "⊕" | "⊻" => Token::Xor,
            "implies" | "→" | "->" | "=>" => Token::Implies,
            "iff" | "↔" | "<->" | "<=>" => Token::Iff,
            "true" | "1" => Token::Constant(true),
            "false" | "0" => Token::Constant(false),
            _ => Token::Variable(identifier.to_string()),
        }
    }
    
    /// Lee el siguiente token
    pub fn next_token(&mut self) -> Result<Token, ParseError> {
        self.skip_whitespace();
        
        match self.current_char {
            Some(c) => {
                let token = match c {
                    // Operadores de un solo carácter
                    '&' | '∧' => {
                        self.advance();
                        // Verificar si es '&&'
                        if let Some('&') = self.current_char {
                            self.advance();
                        }
                        Token::And
                    },
                    '|' | '∨' => {
                        self.advance();
                        // Verificar si es '||'
                        if let Some('|') = self.current_char {
                            self.advance();
                        }
                        Token::Or
                    },
                    '!' | '¬' | '~' => {
                        self.advance();
                        Token::Not
                    },
                    '⊕' | '⊻' => {
                        self.advance();
                        Token::Xor
                    },
                    '→' => {
                        self.advance();
                        Token::Implies
                    },
                    '↔' => {
                        self.advance();
                        Token::Iff
                    },
                    
                    // Operadores multi-carácter
                    '-' => {
                        self.advance();
                        if let Some('>') = self.current_char {
                            self.advance();
                            Token::Implies
                        } else {
                            return Err(ParseError::InvalidOperator(format!("-{}", self.current_char.unwrap_or(' '))));
                        }
                    },
                    '<' => {
                        self.advance();
                        if let Some('-') = self.current_char {
                            self.advance();
                            if let Some('>') = self.current_char {
                                self.advance();
                                Token::Iff
                            } else {
                                return Err(ParseError::InvalidOperator("<--".to_string()));
                            }
                        } else {
                            return Err(ParseError::InvalidOperator(format!("<{}", self.current_char.unwrap_or(' '))));
                        }
                    },
                    '=' => {
                        self.advance();
                        if let Some('>') = self.current_char {
                            self.advance();
                            Token::Implies
                        } else {
                            return Err(ParseError::InvalidOperator(format!("={}", self.current_char.unwrap_or(' '))));
                        }
                    },
                    
                    // Paréntesis
                    '(' => {
                        self.advance();
                        Token::LeftParen
                    },
                    ')' => {
                        self.advance();
                        Token::RightParen
                    },
                    
                    // Variables (deben empezar con letra)
                    _ if c.is_alphabetic() => {
                        let identifier = self.read_identifier();
                        self.identifier_to_token(&identifier)
                    },
                    
                    // Números (solo 0 y 1 como constantes)
                    '0' => {
                        self.advance();
                        Token::Constant(false)
                    },
                    '1' => {
                        self.advance();
                        Token::Constant(true)
                    },
                    
                    // Carácter inválido
                    _ => {
                        return Err(ParseError::InvalidCharacter(c));
                    }
                };
                
                Ok(token)
            }
            
            // Fin de entrada
            None => Ok(Token::EOF),
        }
    }
    
    /// Convierte todo el input en una lista de tokens
    pub fn tokenize(input: &str) -> Result<Vec<Token>, ParseError> {
        let mut lexer = Lexer::new(input);
        let mut tokens = Vec::new();
        
        loop {
            let token = lexer.next_token()?;
            if token == Token::EOF {
                break;
            }
            tokens.push(token);
        }
        
        Ok(tokens)
    }
}

/// Función pública de conveniencia
pub fn tokenize(input: &str) -> Result<Vec<Token>, ParseError> {
    Lexer::tokenize(input)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_operators() {
        let tokens = tokenize("A & B | C").unwrap();
        assert_eq!(tokens, vec![
            Token::Variable("A".to_string()),
            Token::And,
            Token::Variable("B".to_string()),
            Token::Or,
            Token::Variable("C".to_string()),
        ]);
        println!("{:?}", tokens);
    }
    
    #[test]
    fn test_parentheses() {
        let tokens = tokenize("(A & B) | C").unwrap();
        assert_eq!(tokens, vec![
            Token::LeftParen,
            Token::Variable("A".to_string()),
            Token::And,
            Token::Variable("B".to_string()),
            Token::RightParen,
            Token::Or,
            Token::Variable("C".to_string()),
        ]);
    }
    
    #[test]
    fn test_text_operators() {
        let tokens = tokenize("A and B or not C").unwrap();
        assert_eq!(tokens, vec![
            Token::Variable("A".to_string()),
            Token::And,
            Token::Variable("B".to_string()),
            Token::Or,
            Token::Not,
            Token::Variable("C".to_string()),
        ]);
    }
    
    #[test]
    fn test_unicode_operators() {
        let tokens = tokenize("A ∧ B ∨ ¬C").unwrap();
        assert_eq!(tokens, vec![
            Token::Variable("A".to_string()),
            Token::And,
            Token::Variable("B".to_string()),
            Token::Or,
            Token::Not,
            Token::Variable("C".to_string()),
        ]);
    }
    
    #[test]
    fn test_constants() {
        let tokens = tokenize("true & false").unwrap();
        assert_eq!(tokens, vec![
            Token::Constant(true),
            Token::And,
            Token::Constant(false),
        ]);
    }
    
    #[test]
    fn test_whitespace_ignored() {
        let tokens1 = tokenize("A&B").unwrap();
        let tokens2 = tokenize("A & B").unwrap();
        assert_eq!(tokens1, tokens2);
    }
    
    #[test]
    fn test_comments() {
        let tokens = tokenize("A & # esto es un comentario\n B").unwrap();
        assert_eq!(tokens, vec![
            Token::Variable("A".to_string()),
            Token::And,
            Token::Variable("B".to_string()),
        ]);
    }
    
    #[test]
    fn test_invalid_character() {
        let result = tokenize("A @ B");
        assert!(result.is_err());
    }
}