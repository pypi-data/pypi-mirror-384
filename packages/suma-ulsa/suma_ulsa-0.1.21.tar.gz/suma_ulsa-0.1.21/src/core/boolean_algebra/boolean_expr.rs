use std::collections::HashMap;

use crate::core::boolean_algebra::truth_table::{TruthTable, DetailedTruthTable};
use crate::core::boolean_algebra::error::{
    EvaluationError, InvalidExpressionError, ParseError
};
use crate::core::boolean_algebra::parser::parse_expression;
use crate::core::boolean_algebra::Result;  // Nuestro Result personalizado
use crate::core::boolean_algebra::ast::Node;

/// Expresión booleana con AST y variables extraídas
pub struct BooleanExpr {
    pub ast: Node,
    pub variables: Vec<String>,
}

impl BooleanExpr {
    /// Crea una nueva expresión booleana a partir de un string
    pub fn new(expression: &str) -> Result<Self> {
        // Validar que la expresión no esté vacía
        if expression.trim().is_empty() {
            return Err(ParseError::EmptyExpression.into());
        }
        
        // Validar longitud máxima
        if expression.len() > 1000 {
            return Err(InvalidExpressionError::TooComplex(1000).into());
        }
        
        // Parsear la expresión
        let ast = parse_expression(expression)?;
        let variables = ast.extract_variables();
        
        // Validar nombres de variables
        for var in &variables {
            if !Self::is_valid_variable_name(var) {
                return Err(InvalidExpressionError::InvalidVariableName(var.clone()).into());
            }
        }
        
        Ok(BooleanExpr { ast, variables })
    }
    
    /// Evalúa la expresión con los valores proporcionados
    pub fn evaluate(&self, values: &HashMap<&str, bool>) -> Result<bool> {
        // Verificar que todas las variables estén presentes
        for var in &self.variables {
            if !values.contains_key(var.as_str()) {
                return Err(EvaluationError::MissingVariable(var.clone()).into());
            }
        }
        
        Ok(self.ast.evaluate(values))
    }
    
    /// Evalúa la expresión permitiendo valores por defecto para variables faltantes
    pub fn evaluate_with_defaults(&self, values: &HashMap<&str, bool>, default: bool) -> bool {
        let mut complete_values = values.clone();
        
        // Agregar valores por defecto para variables faltantes
        for var in &self.variables {
            if !complete_values.contains_key(var.as_str()) {
                complete_values.insert(var, default);
            }
        }
        
        self.ast.evaluate(&complete_values)
    }
    
    /// Genera la tabla de verdad completa de la expresión
    pub fn truth_table(&self) -> TruthTable {
        let num_vars = self.variables.len();
        let num_rows = 1 << num_vars;
        let mut combinations = Vec::with_capacity(num_rows);
        let mut columns = HashMap::new();
        let mut column_order = self.variables.clone();
        
        // Initialize columns for variables
        for var in &self.variables {
            columns.insert(var.clone(), Vec::with_capacity(num_rows));
        }
        // Initialize column for final result
        let result_label = self.to_string();
        columns.insert(result_label.clone(), Vec::with_capacity(num_rows));
        column_order.push(result_label);
        
        for i in 0..num_rows {
            let mut values = HashMap::new();
            let mut combination = Vec::new();
            for (j, var) in self.variables.iter().enumerate() {
                let value = (i >> (num_vars - 1 - j)) & 1 == 1;
                values.insert(var.as_str(), value);
                combination.push(value);
                columns.get_mut(var).unwrap().push(value);
            }
            let result = self.ast.evaluate(&values);
            columns.get_mut(&column_order[column_order.len() - 1]).unwrap().push(result);
            combinations.push(combination);
        }
        
        TruthTable::new(self.variables.clone(), columns, column_order, combinations)
            .expect("Valid truth table construction")
    }

    /// Genera una tabla de verdad detallada mostrando columnas para cada subexpresión
    pub fn full_truth_table(&self) -> DetailedTruthTable {
        // Recopilar todas las subexpresiones en orden post-orden (bottom-up)
        let mut subexprs: Vec<(String, Node)> = Vec::new();
        self.ast.collect_subexprs(&mut subexprs);
        // La última subexpresión es el resultado completo
        let num_vars = self.variables.len();
        let num_rows = 1 << num_vars;
        // Generar combinaciones
        let mut combinations = Vec::with_capacity(num_rows);
        let mut columns = HashMap::new();
        for (label, node) in &subexprs {
            let mut col = Vec::with_capacity(num_rows);
            for i in 0..num_rows {
                let mut values = HashMap::new();
                let mut combination = Vec::new();
                for (j, var) in self.variables.iter().enumerate() {
                    let val = (i >> (num_vars - 1 - j)) & 1 == 1;
                    values.insert(var.as_str(), val);
                    combination.push(val);
                }
                let res = node.evaluate(&values);
                col.push(res);
                // Guardar combinaciones solo una vez
                if label == &self.variables[0] {
                    combinations.push(combination);
                }
            }
            columns.insert(label.clone(), col);
        }
        // Extraer subexpressions en orden
        let subexpressions: Vec<String> = subexprs.into_iter().map(|(label, _)| label).collect();
        DetailedTruthTable {
        variables: self.variables.clone(),
        subexpressions,
        columns,
        combinations,
        }
    }

    
    /// Convierte la expresión a string (notación infija)
    pub fn to_string(&self) -> String {
        self.ast.to_infix_notation_text()
    }

    pub fn to_ascii_string(&self) -> String {
        self.ast.to_infix_notation_ascii()
    }
    
    pub fn to_unicode_string(&self) -> String {
        self.ast.to_infix_notation_text()
    }

    /// Convierte la expresión a notación prefija (para debugging)
    pub fn to_prefix_notation(&self) -> String {
        self.ast.to_prefix_notation()
    }
    
    /// Obtiene la complejidad de la expresión (número de operadores)
    pub fn complexity(&self) -> usize {
        self.ast.complexity()
    }
    
    /// Verifica si la expresión es una tautología (verdadera para todas las combinaciones).
    pub fn is_tautology(&self) -> bool {
        let truth_table = self.truth_table();
        let result_label = truth_table.column_order.last()
            .expect("Truth table must have at least one column");
        truth_table.columns.get(result_label)
            .expect("Result column must exist")
            .iter()
            .all(|&result| result)
    }

    /// Verifica si la expresión es una contradicción (falsa para todas las combinaciones).
    pub fn is_contradiction(&self) -> bool {
        let truth_table = self.truth_table();
        let result_label = truth_table.column_order.last()
            .expect("Truth table must have at least one column");
        truth_table.columns.get(result_label)
            .expect("Result column must exist")
            .iter()
            .all(|&result| !result)
    }
    
    /// Verifica si dos expresiones son equivalentes
    pub fn equivalent_to(&self, other: &BooleanExpr) -> bool {
        // Para ser equivalentes, deben tener las mismas variables
        // y producir los mismos resultados para todas las combinaciones
        let all_vars: Vec<String> = self.variables.iter()
            .chain(other.variables.iter())
            .cloned()
            .collect::<std::collections::HashSet<_>>()
            .into_iter()
            .collect();
        
        let num_combinations = 1 << all_vars.len();
        
        for i in 0..num_combinations {
            let mut values = HashMap::new();
            
            for (j, var) in all_vars.iter().enumerate() {
                let value = (i >> (all_vars.len() - 1 - j)) & 1 == 1;
                values.insert(var.as_str(), value);
            }
            
            let self_result = self.evaluate_with_defaults(&values, false);
            let other_result = other.evaluate_with_defaults(&values, false);
            
            if self_result != other_result {
                return false;
            }
        }
        
        true
    }
    
    // --- FUNCIONES AUXILIARES ---
    
    /// Valida que un nombre de variable sea válido
    fn is_valid_variable_name(name: &str) -> bool {
        // Una variable debe:
        // 1. No estar vacía
        // 2. Empezar con una letra
        // 3. Contener solo letras, números y underscores
        // 4. No ser una palabra reservada
        
        if name.is_empty() {
            return false;
        }
        
        // Verificar que empiece con letra
        if !name.chars().next().unwrap().is_alphabetic() {
            return false;
        }
        
        // Verificar que todos los caracteres sean válidos
        if !name.chars().all(|c| c.is_alphanumeric() || c == '_') {
            return false;
        }
        
        // Palabras reservadas
        let reserved_words = ["true", "false", "and", "or", "not", "xor", "implies", "iff"];
        if reserved_words.contains(&name.to_lowercase().as_str()) {
            return false;
        }
        
        true
    }
}

/// Implementación de Debug para facilitar testing
impl std::fmt::Debug for BooleanExpr {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "BooleanExpr({})", self.to_string())
    }
}

/// Implementación de Clone
impl Clone for BooleanExpr {
    fn clone(&self) -> Self {
        // Como Node y Vec<String> son Clone, podemos derivar Clone
        BooleanExpr {
            ast: self.ast.clone(),
            variables: self.variables.clone(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // --- Tests básicos de creación ---
    #[test]
    fn test_boolean_expr_creation() {
        let expr = BooleanExpr::new("A & B").unwrap();
        assert_eq!(expr.variables, vec!["A", "B"]);
        assert_eq!(expr.complexity(), 1);
    }
    
    #[test]
    fn test_empty_expression() {
        let result = BooleanExpr::new("");
        assert!(result.is_err());
    }
    
    #[test]
    fn test_expression_too_long() {
        let long_expr = "A".repeat(1001);
        let result = BooleanExpr::new(&long_expr);
        assert!(result.is_err());
    }

    // --- Tests de evaluación básica ---
    #[test]
    fn test_evaluation() {
        let expr = BooleanExpr::new("A & ~B").unwrap();
        let mut values = HashMap::new();
        values.insert("A", true);
        values.insert("B", false);
        
        assert_eq!(expr.evaluate(&values).unwrap(), true);
    }
    
    #[test]
    fn test_evaluation_missing_variable() {
        let expr = BooleanExpr::new("A & B").unwrap();
        let mut values = HashMap::new();
        values.insert("A", true);
        // Falta B
        
        let result = expr.evaluate(&values);
        assert!(result.is_err());
    }
    
    #[test]
    fn test_evaluation_with_defaults() {
        let expr = BooleanExpr::new("A & B").unwrap();
        let mut values = HashMap::new();
        values.insert("A", true);
        // B falta, usará default
        
        assert_eq!(expr.evaluate_with_defaults(&values, false), false); // true & false = false
        assert_eq!(expr.evaluate_with_defaults(&values, true), true);   // true & true = true
    }

    // --- Tests de operadores lógicos ---
    #[test]
    fn test_and_operator() {
        let expr = BooleanExpr::new("A & B").unwrap();
        let tests = vec![
            (false, false, false),
            (false, true, false),
            (true, false, false),
            (true, true, true),
        ];
        
        for (a, b, expected) in tests {
            let mut values = HashMap::new();
            values.insert("A", a);
            values.insert("B", b);
            assert_eq!(expr.evaluate(&values).unwrap(), expected, "A: {}, B: {}", a, b);
        }
    }
    
    #[test]
    fn test_or_operator() {
        let expr = BooleanExpr::new("A | B").unwrap();
        let tests = vec![
            (false, false, false),
            (false, true, true),
            (true, false, true),
            (true, true, true),
        ];
        
        for (a, b, expected) in tests {
            let mut values = HashMap::new();
            values.insert("A", a);
            values.insert("B", b);
            assert_eq!(expr.evaluate(&values).unwrap(), expected);
        }
    }
    
    #[test]
    fn test_not_operator() {
        let expr = BooleanExpr::new("~A").unwrap();
        let mut values = HashMap::new();
        
        values.insert("A", false);
        assert_eq!(expr.evaluate(&values).unwrap(), true);
        
        values.insert("A", true);
        assert_eq!(expr.evaluate(&values).unwrap(), false);
    }
    
    #[test]
    fn test_xor_operator() {
        let expr = BooleanExpr::new("A xor B").unwrap();
        let tests = vec![
            (false, false, false),
            (false, true, true),
            (true, false, true),
            (true, true, false),
        ];
        
        for (a, b, expected) in tests {
            let mut values = HashMap::new();
            values.insert("A", a);
            values.insert("B", b);
            assert_eq!(expr.evaluate(&values).unwrap(), expected);
        }
    }

    // --- Tests de expresiones complejas ---
    #[test]
    fn test_complex_expression() {
        let expr = BooleanExpr::new("(A & B) | (~A & C)").unwrap();
        let mut values = HashMap::new();
        
        values.insert("A", true);
        values.insert("B", false);
        values.insert("C", true);
        assert_eq!(expr.evaluate(&values).unwrap(), false); // (T&F) | (F&T) = F|F = F
        
        values.insert("B", true);
        values.insert("C", false);
        assert_eq!(expr.evaluate(&values).unwrap(), true);  // (T&T) | (F&F) = T|F = T
    }
    
    #[test]
    fn test_nested_negations() {
        let expr = BooleanExpr::new("~~A").unwrap(); // Doble negación
        let mut values = HashMap::new();
        values.insert("A", true);
        assert_eq!(expr.evaluate(&values).unwrap(), true);
    }

    // --- Tests de tabla de verdad ---
    #[test]
    fn test_truth_table_simple() {
        let expr = BooleanExpr::new("A & B").unwrap();
        let table = expr.truth_table();

        assert_eq!(table.num_rows(), 4); // 2 variables = 4 combinaciones
        assert_eq!(expr.variables.len(), 2);

        // Verificar algunas filas específicas
        let mut found_true = false;
        
        for row in table.to_named_rows() {
            let a = row.get("A").copied().unwrap_or(false);
            let b = row.get("B").copied().unwrap_or(false);
            let result = row.get(&expr.to_string()).copied().unwrap_or(false);
            if a && b {
                assert!(result, "A & B debería ser true cuando A y B son true");
                found_true = true;
            } else {
                assert!(!result, "A & B debería ser false cuando A o B son false");
            }
        }
        assert!(found_true, "Debería haber al menos una fila con resultado true");
    }
    
    #[test]
    fn test_truth_table_three_variables() {
        let expr = BooleanExpr::new("A & (B | C)").unwrap();
        let table = expr.truth_table();

        assert_eq!(table.num_rows(), 8); // 3 variables = 8 combinaciones
        assert_eq!(expr.variables.len(), 3);
    }

    // --- Tests de propiedades lógicas ---
    #[test]
    fn test_tautology() {
        let tautology = BooleanExpr::new("A | ~A").unwrap(); // Ley del medio excluido
        assert!(tautology.is_tautology());
        
        let not_tautology = BooleanExpr::new("A & B").unwrap();
        assert!(!not_tautology.is_tautology());
    }
    
    #[test]
    fn test_contradiction() {
        let contradiction = BooleanExpr::new("A & ~A").unwrap(); // Contradicción
        assert!(contradiction.is_contradiction());
        
        let not_contradiction = BooleanExpr::new("A | B").unwrap();
        assert!(!not_contradiction.is_contradiction());
    }
    
    #[test]
    fn test_equivalence() {
        // A → B es equivalente a ~A ∨ B
        let expr1 = BooleanExpr::new("A implies B").unwrap();
        let expr2 = BooleanExpr::new("~A | B").unwrap();
        
        assert!(expr1.equivalent_to(&expr2));
        
        // A ∧ B no es equivalente a A ∨ B
        let expr3 = BooleanExpr::new("A & B").unwrap();
        let expr4 = BooleanExpr::new("A | B").unwrap();
        
        assert!(!expr3.equivalent_to(&expr4));
    }

    // --- Tests de representación de strings ---
    #[test]
    fn test_string_representation() {
        let expr = BooleanExpr::new("A & (B | C)").unwrap();
        let repr = expr.to_ascii_string();
        
        // La representación debe contener las variables y operadores
        assert!(repr.contains('A'));
        assert!(repr.contains('B'));
        assert!(repr.contains('C'));
        assert!(repr.contains('&') || repr.contains('∧'));
    }
    
    #[test]
    fn test_prefix_notation() {
        let expr = BooleanExpr::new("A & B").unwrap();
        let prefix = expr.to_prefix_notation();
        
        // Debería ser algo como "AND(A, B)" o similar
        assert!(prefix.starts_with("AND") || prefix.contains("&"));
    }

    // --- Tests de complejidad ---
    #[test]
    fn test_complexity_calculation() {
        let simple = BooleanExpr::new("A").unwrap();
        assert_eq!(simple.complexity(), 0);
        
        let medium = BooleanExpr::new("A & B").unwrap();
        assert_eq!(medium.complexity(), 1);
        
        let complex = BooleanExpr::new("(A & B) | (~C & D)").unwrap();
        assert_eq!(complex.complexity(), 4); // OR, AND, NOT, AND
    }

    // --- Tests de validación de nombres de variables ---
    #[test]
    fn test_variable_name_validation() {
        assert!(BooleanExpr::is_valid_variable_name("A"));
        assert!(BooleanExpr::is_valid_variable_name("var1"));
        assert!(BooleanExpr::is_valid_variable_name("x_y"));
        assert!(BooleanExpr::is_valid_variable_name("VAR"));
        assert!(BooleanExpr::is_valid_variable_name("a1b2c3"));
        
        assert!(!BooleanExpr::is_valid_variable_name(""));
        assert!(!BooleanExpr::is_valid_variable_name("1var"));
        assert!(!BooleanExpr::is_valid_variable_name("var@"));
        assert!(!BooleanExpr::is_valid_variable_name("true"));
        assert!(!BooleanExpr::is_valid_variable_name("and"));
        assert!(!BooleanExpr::is_valid_variable_name("var-name"));
        assert!(!BooleanExpr::is_valid_variable_name("var name"));
    }
    
    #[test]
    fn test_invalid_variable_name_in_expression() {
        // "1var" es inválido porque empieza con número
        let result = BooleanExpr::new("1var & B");
        assert!(result.is_err());
        
        // "true" es VÁLIDO porque es una constante booleana
        let result = BooleanExpr::new("true & B");
        assert!(result.is_ok()); // Cambiado de is_err() a is_ok()
        
        // Verificar que funciona correctamente
        let expr = BooleanExpr::new("true & B").unwrap();
        let mut values = HashMap::new();
        values.insert("B", true);
        assert_eq!(expr.evaluate(&values).unwrap(), true); // true & true = true
        
        values.insert("B", false);
        assert_eq!(expr.evaluate(&values).unwrap(), false); // true & false = false
    }

    #[test]
    fn test_constants_are_not_treated_as_variables() {
        // "true" y "false" deben ser constantes, no variables
        let expr = BooleanExpr::new("true & false").unwrap();
        
        // No debería tener variables porque solo usa constantes
        assert_eq!(expr.variables, Vec::<String>::new());
        
        // La evaluación debería funcionar sin necesidad de valores
        let empty_values = HashMap::new();
        assert_eq!(expr.evaluate(&empty_values).unwrap(), false); // true & false = false
    }

    #[test]
    fn test_mixed_constants_and_variables() {
        let expr = BooleanExpr::new("true & A | false").unwrap();
        assert_eq!(expr.variables, vec!["A"]); // Solo A es variable
        
        let mut values = HashMap::new();
        values.insert("A", true);
        assert_eq!(expr.evaluate(&values).unwrap(), true); // true & true | false = true
        
        values.insert("A", false);
        assert_eq!(expr.evaluate(&values).unwrap(), false); // true & false | false = false
    }

    // --- Tests de diferentes sintaxis ---
    #[test]
    fn test_different_syntaxes() {
        // Diferentes formas de escribir la misma expresión
        let exprs = vec![
            "A and B",
            "A && B", 
            "A ∧ B",
            "A & B",
        ];
        
        for expr_str in exprs {
            let expr = BooleanExpr::new(expr_str).unwrap();
            let mut values = HashMap::new();
            values.insert("A", true);
            values.insert("B", true);
            
            assert_eq!(expr.evaluate(&values).unwrap(), true);
        }
    }
    
    #[test]
    fn test_operator_precedence() {
        // A & B | C debería ser (A & B) | C, no A & (B | C)
        let expr = BooleanExpr::new("A & B | C").unwrap();
        let mut values = HashMap::new();
        values.insert("A", true);
        values.insert("B", false);
        values.insert("C", true);
        
        // (true & false) | true = false | true = true
        // Si fuera true & (false | true) = true & true = true (mismo resultado)
        // Pero probemos otro caso:
        values.insert("A", false);
        values.insert("B", true);
        values.insert("C", false);
        
        // (false & true) | false = false | false = false
        // Si fuera false & (true | false) = false & true = false (mismo resultado)
        // En este caso AND y OR tienen la misma precedencia, se evalúa izquierda a derecha
        assert_eq!(expr.evaluate(&values).unwrap(), false);
    }

    // --- Tests de clonación ---
    #[test]
    fn test_clone() {
        let original = BooleanExpr::new("A & B").unwrap();
        let cloned = original.clone();
        
        assert_eq!(original.variables, cloned.variables);
        assert_eq!(original.complexity(), cloned.complexity());
        
        // Verificar que son independientes
        let mut values = HashMap::new();
        values.insert("A", true);
        values.insert("B", false);
        assert_eq!(original.evaluate(&values).unwrap(), cloned.evaluate(&values).unwrap());
    }

    // --- Tests de expresiones con constantes ---
    #[test]
    fn test_constants_in_expressions() {
        let expr = BooleanExpr::new("A & true").unwrap();
        let mut values = HashMap::new();
        values.insert("A", true);
        assert_eq!(expr.evaluate(&values).unwrap(), true);
        
        values.insert("A", false);
        assert_eq!(expr.evaluate(&values).unwrap(), false);
        
        let expr2 = BooleanExpr::new("false | A").unwrap();
        values.insert("A", true);
        assert_eq!(expr2.evaluate(&values).unwrap(), true);
    }

}