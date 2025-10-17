use crate::core::boolean_algebra::ast::Node;
use crate::core::boolean_algebra::error::{ParseError, BooleanAlgebraError};
use super::lexer::{Lexer, Token};

pub struct Parser {
    lexer: Lexer,
    current_token: Token,
}

impl Parser {
    pub fn new(input: &str) -> Result<Self, ParseError> {
        let mut lexer = Lexer::new(input);
        let current_token = lexer.next_token()?;
        
        Ok(Parser { lexer, current_token })
    }
    
    fn advance(&mut self) -> Result<(), ParseError> {
        self.current_token = self.lexer.next_token()?;
        Ok(())
    }
    
    fn expect(&mut self, expected: Token) -> Result<(), ParseError> {
        if self.current_token == expected {
            self.advance()?;
            Ok(())
        } else {
            Err(ParseError::UnexpectedToken {
                expected: format!("{:?}", expected),
                found: format!("{:?}", self.current_token),
            })
        }
    }
    
    // Métodos de parsing recursivo descendente
    pub fn parse_expression(&mut self) -> Result<Node, BooleanAlgebraError> {
        self.parse_iff()
    }
    
    fn parse_iff(&mut self) -> Result<Node, BooleanAlgebraError> {
        let mut node = self.parse_implies()?;
        
        while self.current_token == Token::Iff {
            self.advance()?;
            let right = self.parse_implies()?;
            node = Node::Iff(Box::new(node), Box::new(right));
        }
        
        Ok(node)
    }
    
    fn parse_implies(&mut self) -> Result<Node, BooleanAlgebraError> {
        let mut node = self.parse_or()?;
        
        while self.current_token == Token::Implies {
            self.advance()?;
            let right = self.parse_or()?;
            node = Node::Implies(Box::new(node), Box::new(right));
        }
        
        Ok(node)
    }
    
    fn parse_or(&mut self) -> Result<Node, BooleanAlgebraError> {
        let mut node = self.parse_xor()?;
        
        while self.current_token == Token::Or {
            self.advance()?;
            let right = self.parse_xor()?;
            node = Node::Or(Box::new(node), Box::new(right));
        }
        
        Ok(node)
    }
    
    fn parse_xor(&mut self) -> Result<Node, BooleanAlgebraError> {
        let mut node = self.parse_and()?;
        
        while self.current_token == Token::Xor {
            self.advance()?;
            let right = self.parse_and()?;
            node = Node::Xor(Box::new(node), Box::new(right));
        }
        
        Ok(node)
    }
    
    fn parse_and(&mut self) -> Result<Node, BooleanAlgebraError> {
        let mut node = self.parse_not()?;
        
        while self.current_token == Token::And {
            self.advance()?;
            let right = self.parse_not()?;
            node = Node::And(Box::new(node), Box::new(right));
        }
        
        Ok(node)
    }
    
    fn parse_not(&mut self) -> Result<Node, BooleanAlgebraError> {
        if self.current_token == Token::Not {
            self.advance()?;
            let node = self.parse_not()?;
            Ok(Node::Not(Box::new(node)))
        } else {
            self.parse_atom()
        }
    }
    
    fn parse_atom(&mut self) -> Result<Node, BooleanAlgebraError> {
        match &self.current_token {
            Token::Variable(name) => {
                let node = Node::Variable(name.clone());
                self.advance()?;
                Ok(node)
            }
            Token::Constant(value) => {
                let node = Node::Constant(*value);
                self.advance()?;
                Ok(node)
            }
            Token::LeftParen => {
                self.advance()?;
                let node = self.parse_expression()?;
                self.expect(Token::RightParen)
                    .map_err(|e| BooleanAlgebraError::ParseError(e))?;
                Ok(node)
            }
            _ => Err(BooleanAlgebraError::ParseError(
                ParseError::ExpectedExpression(format!("Token inesperado: {:?}", self.current_token))
            )),
        }
    }
}

/// Función pública de conveniencia
pub fn parse_expression(input: &str) -> Result<Node, BooleanAlgebraError> {
    let mut parser = Parser::new(input)?;
    let ast = parser.parse_expression()?;
    
    // Verificar que no queden tokens sin procesar
    if parser.current_token != Token::EOF {
        return Err(BooleanAlgebraError::ParseError(
            ParseError::ExpectedExpression("Tokens adicionales al final de la expresión".to_string())
        ));
    }
    
    Ok(ast)
}