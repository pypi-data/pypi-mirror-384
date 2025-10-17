use std::collections::HashSet;
use std::fmt;

/// Nodo del Árbol de Sintaxis Abstracta (AST) para expresiones booleanas
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Node {
    /// Variable booleana (ej: "A", "B", "x1")
    Variable(String),
    /// Operación AND (conjunción) entre dos expresiones
    And(Box<Node>, Box<Node>),
    /// Operación OR (disyunción) entre dos expresiones  
    Or(Box<Node>, Box<Node>),
    /// Operación NOT (negación) de una expresión
    Not(Box<Node>),
    /// Valor constante (true o false)
    Constant(bool),
    /// Operación XOR (o exclusivo) - útil para expansión
    Xor(Box<Node>, Box<Node>),
    /// Operación NAND (no y) - útil para expansión
    Nand(Box<Node>, Box<Node>),
    /// Operación NOR (no o) - útil para expansión
    Nor(Box<Node>, Box<Node>),
    /// Operación IMPLIES (implicación) A → B
    Implies(Box<Node>, Box<Node>),
    /// Operación IFF (doble implicación) A ↔ B
    Iff(Box<Node>, Box<Node>),
}

impl Node {
    /// Extrae todas las variables únicas de la expresión
    pub fn extract_variables(&self) -> Vec<String> {
        let mut variables = HashSet::new();
        self.extract_variables_recursive(&mut variables);
        
        let mut vars: Vec<String> = variables.into_iter().collect();
        vars.sort(); // Orden alfabético para consistencia
        vars
    }
    
    /// Recorrido recursivo para extraer variables
    fn extract_variables_recursive(&self, variables: &mut HashSet<String>) {
        match self {
            Node::Variable(name) => {
                variables.insert(name.clone());
            }
            Node::And(left, right) 
            | Node::Or(left, right) 
            | Node::Xor(left, right)
            | Node::Implies(left, right)
            | Node::Iff(left, right) => {
                left.extract_variables_recursive(variables);
                right.extract_variables_recursive(variables);
            }
            Node::Not(inner) => {
                inner.extract_variables_recursive(variables);
            }
            Node::Nand(left, right) => {
                left.extract_variables_recursive(variables);
                right.extract_variables_recursive(variables);
            }
            Node::Nor(left, right) => {
                left.extract_variables_recursive(variables);
                right.extract_variables_recursive(variables);
            }
            Node::Constant(_) => {} // Las constantes no tienen variables
        }
    }
    
    /// Evalúa la expresión con los valores dados
    pub fn evaluate(&self, values: &std::collections::HashMap<&str, bool>) -> bool {
        match self {
            Node::Variable(name) => {
                *values.get(name.as_str()).unwrap_or(&false)
            }
            Node::And(left, right) => {
                left.evaluate(values) && right.evaluate(values)
            }
            Node::Or(left, right) => {
                left.evaluate(values) || right.evaluate(values)
            }
            Node::Not(inner) => {
                !inner.evaluate(values)
            }
            Node::Constant(value) => *value,
            Node::Xor(left, right) => {
                left.evaluate(values) ^ right.evaluate(values)
            }
            Node::Implies(left, right) => {
                !left.evaluate(values) || right.evaluate(values)
            }
            Node::Iff(left, right) => {
                left.evaluate(values) == right.evaluate(values)
            }
            Node::Nand(left, right) => {
                !(left.evaluate(values) && right.evaluate(values))
            }
            Node::Nor(left, right) => {
                !(left.evaluate(values) || right.evaluate(values))
            }
        }
    }
    
    /// Convierte el AST a una representación de string (notación prefija)
    pub fn to_prefix_notation(&self) -> String {
        match self {
            Node::Variable(name) => name.clone(),
            Node::And(left, right) => {
                format!("AND({}, {})", left.to_prefix_notation(), right.to_prefix_notation())
            }
            Node::Or(left, right) => {
                format!("OR({}, {})", left.to_prefix_notation(), right.to_prefix_notation())
            }
            Node::Not(inner) => {
                format!("NOT({})", inner.to_prefix_notation())
            }
            Node::Constant(value) => value.to_string(),
            Node::Xor(left, right) => {
                format!("XOR({}, {})", left.to_prefix_notation(), right.to_prefix_notation())
            }
            Node::Implies(left, right) => {
                format!("IMPLIES({}, {})", left.to_prefix_notation(), right.to_prefix_notation())
            }
            Node::Iff(left, right) => {
                format!("IFF({}, {})", left.to_prefix_notation(), right.to_prefix_notation())
            }
            Node::Nand(left, right) => {
                format!("NAND({}, {})", left.to_prefix_notation(), right.to_prefix_notation())
            }
            Node::Nor(left, right) => {
                format!("NOR({}, {})", left.to_prefix_notation(), right.to_prefix_notation())
            }
        }
    }
    
    pub fn to_infix_notation_ascii(&self) -> String {
        match self {
            Node::Variable(name) => name.clone(),
            Node::And(left, right) => {
                format!("({} & {})", left.to_infix_notation_ascii(), right.to_infix_notation_ascii())
            }
            Node::Or(left, right) => {
                format!("({} | {})", left.to_infix_notation_ascii(), right.to_infix_notation_ascii())
            }
            Node::Not(inner) => {
                format!("~{}", inner.to_infix_notation_ascii())
            }
            Node::Constant(value) => value.to_string(),
            Node::Xor(left, right) => {
                format!("({} ^ {})", left.to_infix_notation_ascii(), right.to_infix_notation_ascii())
            }
            Node::Implies(left, right) => {
                format!("({} -> {})", left.to_infix_notation_ascii(), right.to_infix_notation_ascii())
            }
            Node::Iff(left, right) => {
                format!("({} <-> {})", left.to_infix_notation_ascii(), right.to_infix_notation_ascii())
            }
            Node::Nand(left, right) => {
                format!("~({} & {})", left.to_infix_notation_ascii(), right.to_infix_notation_ascii())
            }
            Node::Nor(left, right) => {
                format!("~({} | {})", left.to_infix_notation_ascii(), right.to_infix_notation_ascii())
            }
        }
    }

    pub fn to_infix_notation_text(&self) -> String {
        match self {
            Node::Variable(name) => name.clone(),
            Node::And(left, right) => {
                format!("({} and {})", left.to_infix_notation_text(), right.to_infix_notation_text())
            }
            Node::Or(left, right) => {
                format!("({} or {})", left.to_infix_notation_text(), right.to_infix_notation_text())
            }
            Node::Not(inner) => {
                format!("not {}", inner.to_infix_notation_text())
            }
            Node::Constant(value) => value.to_string(),
            Node::Xor(left, right) => {
                format!("({} xor {})", left.to_infix_notation_text(), right.to_infix_notation_text())
            }
            Node::Implies(left, right) => {
                format!("({} implies {})", left.to_infix_notation_text(), right.to_infix_notation_text())
            }
            Node::Iff(left, right) => {
                format!("({} biconditional {})", left.to_infix_notation_text(), right.to_infix_notation_text())
            }
            Node::Nand(left, right) => {
                format!("not({} and {})", left.to_infix_notation_text(), right.to_infix_notation_text())
            }
            Node::Nor(left, right) => {
                format!("not({} or {})", left.to_infix_notation_text(), right.to_infix_notation_text())
            }
        }
    }

    /// Convierte el AST a una representación infija (notación tradicional)
    pub fn to_infix_notation_unicode(&self) -> String {
        match self {
            Node::Variable(name) => name.clone(),
            Node::And(left, right) => {
                format!("({} ∧ {})", left.to_infix_notation_unicode(), right.to_infix_notation_unicode())
            }
            Node::Or(left, right) => {
                format!("({} ∨ {})", left.to_infix_notation_unicode(), right.to_infix_notation_unicode())
            }
            Node::Not(inner) => {
                format!("¬{}", inner.to_infix_notation_unicode())
            }
            Node::Constant(value) => value.to_string(),
            Node::Xor(left, right) => {
                format!("({} ⊕ {})", left.to_infix_notation_unicode(), right.to_infix_notation_unicode())
            }
            Node::Implies(left, right) => {
                format!("({} → {})", left.to_infix_notation_unicode(), right.to_infix_notation_unicode())
            }
            Node::Iff(left, right) => {
                format!("({} ↔ {})", left.to_infix_notation_unicode(), right.to_infix_notation_unicode())
            }
            Node::Nand(left, right) => {
                format!("¬({} ∧ {})", left.to_infix_notation_unicode(), right.to_infix_notation_unicode())
            }
            Node::Nor(left, right) => {
                format!("¬({} ∨ {})", left.to_infix_notation_unicode(), right.to_infix_notation_unicode())
            }
        }
    }
    
    /// Calcula la complejidad de la expresión (número de operadores)
    pub fn complexity(&self) -> usize {
        match self {
            Node::Variable(_) | Node::Constant(_) => 0,
            Node::Not(inner) => 1 + inner.complexity(),
            Node::And(left, right) 
            | Node::Or(left, right)
            | Node::Xor(left, right)
            | Node::Implies(left, right)
            | Node::Iff(left, right) => {
                1 + left.complexity() + right.complexity()
            }
            Node::Nand(left, right)
            | Node::Nor(left, right) => {
                1 + left.complexity() + right.complexity()
            }

        }
    }

    pub fn collect_subexprs(&self, list: &mut Vec<(String, Node)>) {
        match self {
            Node::Variable(name) => {
                list.push((name.clone(), self.clone()));
            }
            Node::Constant(value) => {
                list.push((value.to_string(), self.clone()));
            }
            Node::Not(child) => {
                child.collect_subexprs(list);
                let label = format!("not {}", child.to_infix_notation_text());
                list.push((label, self.clone()));
            }
            Node::And(left, right) => {
                left.collect_subexprs(list);
                right.collect_subexprs(list);
                let label = format!("{} and {}", left.to_infix_notation_text(), right.to_infix_notation_text());
                list.push((label, self.clone()));
            }
            Node::Or(left, right) => {
                left.collect_subexprs(list);
                right.collect_subexprs(list);
                let label = format!("{} or {}", left.to_infix_notation_text(), right.to_infix_notation_text());
                list.push((label, self.clone()));
            }
            Node::Xor(left, right) => {
                left.collect_subexprs(list);
                right.collect_subexprs(list);
                let label = format!("{} xor {}", left.to_infix_notation_text(), right.to_infix_notation_text());
                list.push((label, self.clone()));
            }
            Node::Implies(left, right) => {
                left.collect_subexprs(list);
                right.collect_subexprs(list);
                let label = format!("{} implies {}", left.to_infix_notation_text(), right.to_infix_notation_text());
                list.push((label, self.clone()));
            }
            Node::Iff(left, right) => {
                left.collect_subexprs(list);
                right.collect_subexprs(list);
                let label = format!("{} iff {}", left.to_infix_notation_text(), right.to_infix_notation_text());
                list.push((label, self.clone()));
            }
            Node::Nand(left, right) => {
                left.collect_subexprs(list);
                right.collect_subexprs(list);
                let label = format!("{} nand {}", left.to_infix_notation_text(), right.to_infix_notation_text());
                list.push((label, self.clone()));
            }
            Node::Nor(left, right) => {
                left.collect_subexprs(list);
                right.collect_subexprs(list);
                let label = format!("{} nor {}", left.to_infix_notation_text(), right.to_infix_notation_text());
                list.push((label, self.clone()));
            }
            _ => unimplemented!("Operador no soportado"),
        }
    }

}

/// Implementación de Display para fácil debugging
impl fmt::Display for Node {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.to_infix_notation_text())
    }
}

/// Métodos de conveniencia para crear nodos
impl Node {
    /// Crea un nodo variable
    pub fn var(name: &str) -> Self {
        Node::Variable(name.to_string())
    }
    
    /// Crea un nodo constante
    pub fn constant(value: bool) -> Self {
        Node::Constant(value)
    }
    
    /// Crea una operación AND entre dos nodos
    pub fn and(left: Node, right: Node) -> Self {
        Node::And(Box::new(left), Box::new(right))
    }
    
    /// Crea una operación OR entre dos nodos  
    pub fn or(left: Node, right: Node) -> Self {
        Node::Or(Box::new(left), Box::new(right))
    }
    
    /// Crea una operación NOT
    pub fn not(inner: Node) -> Self {
        Node::Not(Box::new(inner))
    }

    /// Crea una operación XOR entre dos nodos
    pub fn xor(left: Node, right: Node) -> Self {
        Node::Xor(Box::new(left), Box::new(right))
    }

    /// Crea una operación IMPLIES entre dos nodos
    pub fn implies(left: Node, right: Node) -> Self {
        Node::Implies(Box::new(left), Box::new(right))
    }

    /// Crea una operación IFF entre dos nodos
    pub fn iff(left: Node, right: Node) -> Self {
        Node::Iff(Box::new(left), Box::new(right))
    }

    /// Crea una operación NAND entre dos nodos
    pub fn nand(left: Node, right: Node) -> Self {
        Node::Nand(Box::new(left), Box::new(right))
    }

    /// Crea una operación NOR entre dos nodos
    pub fn nor(left: Node, right: Node) -> Self {
        Node::Nor(Box::new(left), Box::new(right))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_variable_extraction() {
        let expr = Node::and(
            Node::var("A"),
            Node::or(Node::var("B"), Node::var("C"))
        );
        
        let variables = expr.extract_variables();
        assert_eq!(variables, vec!["A", "B", "C"]);
    }
    
    #[test]
    fn test_evaluation() {
        let expr = Node::and(Node::var("A"), Node::not(Node::var("B")));
        let mut values = std::collections::HashMap::new();
        values.insert("A", true);
        values.insert("B", false);
        
        assert_eq!(expr.evaluate(&values), true);
    }
    
    #[test]
    fn test_complexity() {
        let simple = Node::var("A");
        let complex = Node::and(
            Node::var("A"), 
            Node::or(Node::var("B"), Node::not(Node::var("C")))
        );
        
        assert_eq!(simple.complexity(), 0);
        assert_eq!(complex.complexity(), 3); // AND, OR, NOT
        
    }

    #[test]
    fn test_infix_notation() {
        let expr = Node::and(
            Node::var("A"),
            Node::or(Node::var("B"), Node::not(Node::var("C")))
        );
        
        let infix = expr.to_infix_notation_text();
        assert_eq!(infix, "(A and (B or not C))");

        let infix_unicode = expr.to_infix_notation_unicode();
        assert_eq!(infix_unicode, "(A ∧ (B ∨ ¬C))");

        let infix_ascii = expr.to_infix_notation_ascii();
        assert_eq!(infix_ascii, "(A & (B | ~C))");
    }

    #[test]
    fn test_prefix_notation() {
        let expr = Node::and(
            Node::var("A"),
            Node::or(Node::var("B"), Node::not(Node::var("C")))
        );
        
        let prefix = expr.to_prefix_notation();
        assert_eq!(prefix, "AND(A, OR(B, NOT(C)))");
    }

    #[test]
    fn test_collect_subexprs() {
        let expr = Node::and(
            Node::var("A"),
            Node::or(Node::var("B"), Node::not(Node::var("C")))
        );

        let mut subexprs = Vec::new();
        expr.collect_subexprs(&mut subexprs);

        let labels: Vec<String> = subexprs.iter().map(|(label, _)| label.clone()).collect();
        assert!(labels.contains(&"A".to_string()));
        assert!(labels.contains(&"B".to_string()));
        assert!(labels.contains(&"C".to_string()));
        assert!(labels.contains(&"not C".to_string()));
        assert!(labels.contains(&"B or not C".to_string()));
        assert!(labels.contains(&"A and (B or not C)".to_string()));
    }

    #[test]
    fn test_convenience_methods() {
        let expr = Node::and(
            Node::var("A"),
            Node::or(Node::var("B"), Node::not(Node::var("C")))
        );

        let expected = Node::And(
            Box::new(Node::Variable("A".to_string())),
            Box::new(Node::Or(
                Box::new(Node::Variable("B".to_string())),
                Box::new(Node::Not(Box::new(Node::Variable("C".to_string()))))
            ))
        );

        assert_eq!(expr, expected);
    }
}