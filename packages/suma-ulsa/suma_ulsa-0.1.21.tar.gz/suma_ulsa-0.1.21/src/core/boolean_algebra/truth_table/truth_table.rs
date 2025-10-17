use std::collections::HashMap;

#[derive(Debug, Clone, PartialEq)]
pub struct TruthTable {
    pub variables: Vec<String>,
    pub combinations: Vec<Vec<bool>>,
    pub column_order: Vec<String>,
    pub columns: HashMap<String, Vec<bool>>,
}

impl TruthTable {
    pub fn new(
        variables: Vec<String>,
        columns: HashMap<String, Vec<bool>>,
        column_order: Vec<String>,
        combinations: Vec<Vec<bool>>,
    ) -> Result<Self, String> {
        let num_rows = combinations.len();
        // Validate combinations
        if num_rows > 0 && !combinations.iter().all(|row| row.len() == variables.len()) {
            return Err("All combinations must match the number of variables".to_string());
        }
        // Validate columns
        if !variables.iter().all(|v| columns.contains_key(v)) {
            return Err("All variables must have corresponding columns".to_string());
        }
        if !columns.values().all(|col| col.len() == num_rows) {
            return Err("All columns must have the same number of rows as combinations".to_string());
        }
        // Validate column_order
        if !column_order.iter().all(|name| columns.contains_key(name)) {
            return Err("All column names in column_order must exist in columns".to_string());
        }
        // Validate unique variables and column names
        let unique_vars: std::collections::HashSet<_> = variables.iter().collect();
        if unique_vars.len() != variables.len() {
            return Err("Variable names must be unique".to_string());
        }
        let unique_columns: std::collections::HashSet<_> = column_order.iter().collect();
        if unique_columns.len() != column_order.len() {
            return Err("Column names must be unique".to_string());
        }
        Ok(TruthTable {
            variables,
            columns,
            column_order,
            combinations,
        })
    }

    pub fn num_rows(&self) -> usize {
        self.combinations.len()
    }

    pub fn num_variables(&self) -> usize {
        self.variables.len()
    }

    pub fn satisfiable_assignments(&self, value: bool, result_label: &str) -> Vec<HashMap<String, bool>> {
        if !self.columns.contains_key(result_label) {
            return Vec::new();
        }
        self.combinations
            .iter()
            .enumerate()
            .filter(|(i, _)| self.columns.get(result_label).unwrap()[*i] == value)
            .map(|(i, _)| {
                self.column_order
                    .iter()
                    .map(|name| (name.clone(), self.columns.get(name).unwrap()[i]))
                    .collect::<HashMap<String, bool>>()
            })
            .collect()
    }

    pub fn to_named_rows(&self) -> Vec<HashMap<String, bool>> {
        let result_label = self.column_order.last()
            .expect("Truth table must have at least one column");
        self.combinations.iter().enumerate().map(|(i, _)| {
            self.column_order
                .iter()
                .map(|name| (name.clone(), self.columns.get(name).unwrap()[i]))
                .collect::<HashMap<String, bool>>()
        }).collect()
    }

    pub fn to_column_dict(&self) -> HashMap<&str, &Vec<bool>> {
        self.column_order.iter().map(|name| (name.as_str(), self.columns.get(name).unwrap())).collect()
    }

    pub fn get_row(&self, index: usize) -> Option<HashMap<String, bool>> {
        if index >= self.combinations.len() {
            return None;
        }
        Some(self.column_order
            .iter()
            .map(|name| (name.clone(), self.columns.get(name).unwrap()[index]))
            .collect())
    }

    pub fn get_column(&self, variable: &str) -> Option<Vec<bool>> {
        self.columns.get(variable).cloned()
    }

    pub fn is_tautology(&self) -> Result<bool, String> {
        let result_label = self.column_order.last().ok_or("Truth table must have at least one column")?;
        Ok(self.columns.get(result_label).ok_or("Result column must exist")?.iter().all(|&r| r))
    }

    pub fn is_contradiction(&self) -> Result<bool, String> {
        let result_label = self.column_order.last().ok_or("Truth table must have at least one column")?;
        Ok(self.columns.get(result_label).ok_or("Result column must exist")?.iter().all(|&r| !r))
    }

    pub fn summary(&self) -> Result<HashMap<String, f64>, String> {
        let result_label = self.column_order.last().ok_or("Truth table must have at least one column")?;
        let true_count = self.columns.get(result_label).ok_or("Result column must exist")?
            .iter().filter(|&&b| b).count() as f64;
        let total = self.combinations.len() as f64;
        let mut summary = HashMap::new();
        summary.insert("num_variables".to_string(), self.variables.len() as f64);
        summary.insert("total_combinations".to_string(), total);
        summary.insert("true_count".to_string(), true_count);
        summary.insert("false_count".to_string(), total - true_count);
        summary.insert("true_percentage".to_string(), if total > 0.0 { (true_count / total) * 100.0 } else { 0.0 });
        for var in &self.variables {
            let column = self.get_column(var).ok_or(format!("Variable column {} must exist", var))?;
            let var_true_count = column.iter().filter(|&&b| b).count() as f64;
            summary.insert(format!("{}_true_count", var), var_true_count);
        }
        Ok(summary)
    }

    // Replace iter with a more general iterator over rows
    pub fn rows(&self) -> impl Iterator<Item = HashMap<String, bool>> + '_ {
        self.combinations.iter().enumerate().map(move |(i, _)| {
            self.column_order
                .iter()
                .map(|name| (name.clone(), self.columns.get(name).unwrap()[i]))
                .collect::<HashMap<String, bool>>()
        })
    }
    /// Creates a new TruthTable with a subset of columns specified by `selected_columns`.
    pub fn select_columns(&self, selected_columns: &[&str]) -> Result<Self, String> {
        // Validate selected columns
        if !selected_columns.iter().all(|name| self.columns.contains_key(*name)) {
            return Err("Selected columns must exist in the truth table".to_string());
        }
        let new_column_order: Vec<String> = selected_columns.iter().map(|s| s.to_string()).collect();
        let new_columns: HashMap<String, Vec<bool>> = selected_columns
            .iter()
            .map(|name| (name.to_string(), self.columns.get(*name).unwrap().clone()))
            .collect();
        let new_variables = self.variables.clone(); // Retain all variables for consistency
        let new_combinations = self.combinations.clone(); // Retain all combinations
        TruthTable::new(new_variables, new_columns, new_column_order, new_combinations)
    }

    /// Filters rows based on a custom predicate applied to the result column or a specified column.
    pub fn filter(&self, column: &str, predicate: impl Fn(bool) -> bool) -> Result<Self, String> {
        if !self.columns.contains_key(column) {
            return Err(format!("Column '{}' not found", column));
        }
        let assignments = self.combinations
            .iter()
            .enumerate()
            .filter(|(i, _)| predicate(self.columns.get(column).unwrap()[*i]))
            .map(|(i, _)| {
                self.column_order
                    .iter()
                    .map(|name| (name.clone(), self.columns.get(name).unwrap()[i]))
                    .collect::<HashMap<String, bool>>()
            })
            .collect::<Vec<_>>();
        let combinations = assignments
            .iter()
            .map(|assignment| {
                self.variables.iter().map(|var| *assignment.get(var).unwrap()).collect()
            })
            .collect();
        let columns = self.column_order.iter()
            .map(|name| {
                let values = assignments.iter().map(|a| *a.get(name).unwrap()).collect();
                (name.clone(), values)
            })
            .collect();
        TruthTable::new(self.variables.clone(), columns, self.column_order.clone(), combinations)
    }

    /// Checks if two truth tables are logically equivalent (same result column values).
    pub fn equivalent_to(&self, other: &Self) -> Result<bool, String> {
        let self_result = self.column_order.last()
            .ok_or("Truth table must have at least one column")?;
        let other_result = other.column_order.last()
            .ok_or("Other truth table must have at least one column")?;
        if self.combinations.len() != other.combinations.len() {
            return Ok(false);
        }
        let self_col = self.columns.get(self_result).ok_or("Result column missing")?;
        let other_col = other.columns.get(other_result).ok_or("Other result column missing")?;
        Ok(self_col == other_col)
    }

    /// Exports the truth table to CSV format.
    pub fn to_csv(&self) -> String {
        let mut csv = String::new();
        // Header
        csv.push_str(&self.column_order.join(","));
        csv.push('\n');
        // Rows
        for i in 0..self.combinations.len() {
            let row: Vec<String> = self.column_order.iter()
                .map(|name| self.columns.get(name).unwrap()[i].to_string())
                .collect();
            csv.push_str(&row.join(","));
            csv.push('\n');
        }
        csv
    }

    /// Exports the truth table to JSON format.
    pub fn to_json(&self) -> String {
        let mut json = String::from("{\n  \"columns\": {\n");
        for (i, name) in self.column_order.iter().enumerate() {
            json.push_str(&format!("    \"{name}\": {:?}", self.columns.get(name).unwrap()));
            if i < self.column_order.len() - 1 {
                json.push(',');
            }
            json.push('\n');
        }
        json.push_str("  }\n}");
        json
    }
}


#[derive(Debug, Clone, PartialEq)]
pub struct DetailedTruthTable {
pub variables: Vec<String>,
pub subexpressions: Vec<String>,  // Ordered list of all subexpression labels (including variables and result)
pub columns: HashMap<String, Vec<bool>>,  // Key: subexpr label, Value: column values
pub combinations: Vec<Vec<bool>>,  // Original combinations for reference
}

// Método opcional para mostrar la tabla detallada
impl DetailedTruthTable {
    pub fn display(&self) {
        let max_len = self.subexpressions.iter().map(|s| s.len()).max().unwrap_or(0).max(6);
        // Header
        let header: String = self.subexpressions
        .iter()
        .map(|s| format!("{:^width$}", s, width = max_len + 2))
        .collect::<Vec<_>>()
        .join("|");
        println!("{}", header);
        println!("{}", "-".repeat(header.len()));
        // Rows
        for i in 0..self.combinations.len() {
            let row_str: String = self.subexpressions
            .iter()
            .map(|s| {
            let val = self.columns.get(s).unwrap()[i];
            format!("{:^width$}", val, width = max_len + 2)
            })
            .collect::<Vec<_>>()
            .join("|");
            println!("{}", row_str);
        }
    }

    pub fn to_truth_table(&self) -> Result<TruthTable, String> {
        TruthTable::new(
            self.variables.clone(),
            self.columns.clone(),
            self.subexpressions.clone(), // Use subexpressions as column_order
            self.combinations.clone(),
        )
    }
    }


#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::boolean_algebra::BooleanExpr;
    use std::collections::HashMap;

    #[test]
    fn test_truth_table_construction() {
        let variables = vec!["A".to_string(), "B".to_string()];
        let combinations = vec![
            vec![true, true],
            vec![true, false],
            vec![false, true],
            vec![false, false],
        ];
        let mut columns = HashMap::new();
        columns.insert("A".to_string(), vec![true, true, false, false]);
        columns.insert("B".to_string(), vec![true, false, true, false]);
        columns.insert("A and B".to_string(), vec![true, false, false, false]);
        let column_order = vec!["A".to_string(), "B".to_string(), "A and B".to_string()];

        let table = TruthTable::new(variables.clone(), columns, column_order.clone(), combinations)
            .expect("Valid truth table");
        assert_eq!(table.num_rows(), 4, "Incorrect number of rows");
        assert_eq!(table.num_variables(), 2, "Incorrect number of variables");
        assert_eq!(table.column_order, column_order, "Incorrect column order");
        assert_eq!(table.is_tautology(), Ok(false), "Should not be a tautology");
        assert_eq!(table.is_contradiction(), Ok(false), "Should not be a contradiction");
        assert_eq!(
            table.get_column("A").unwrap(),
            vec![true, true, false, false],
            "Incorrect A column"
        );
        assert_eq!(
            table.get_row(0).unwrap().get("A and B").unwrap(),
            &true,
            "Incorrect result in first row"
        );
    }

    #[test]
    fn test_truth_table_construction_invalid() {
        // Test invalid combinations
        let variables = vec!["A".to_string()];
        let combinations = vec![vec![true, false]]; // Wrong length
        let mut columns = HashMap::new();
        columns.insert("A".to_string(), vec![true]);
        let column_order = vec!["A".to_string()];
        assert!(
            TruthTable::new(variables, columns, column_order, combinations).is_err(),
            "Should fail with invalid combination length"
        );

        // Test missing column
        let variables = vec!["A".to_string()];
        let combinations = vec![vec![true]];
        let mut columns = HashMap::new();
        let column_order = vec!["A".to_string()];
        assert!(
            TruthTable::new(variables, columns, column_order, combinations).is_err(),
            "Should fail with missing column"
        );

        // Test non-unique variables
        let variables = vec!["A".to_string(), "A".to_string()];
        let combinations = vec![vec![true, true]];
        let mut columns = HashMap::new();
        columns.insert("A".to_string(), vec![true]);
        let column_order = vec!["A".to_string()];
        assert!(
            TruthTable::new(variables, columns, column_order, combinations).is_err(),
            "Should fail with non-unique variables"
        );
    }

    #[test]
    fn test_truth_table_simple() {
        let expr = BooleanExpr::new("A & B").expect("Valid expression");
        let table = expr.truth_table();

        assert_eq!(table.num_rows(), 4, "Incorrect number of rows");
        assert_eq!(table.num_variables(), 2, "Incorrect number of variables");
        assert_eq!(table.column_order, vec!["A", "B", "(A and B)"], "Incorrect column order");
        assert_eq!(
            table.get_column("A").unwrap(),
            vec![false, false, true, true],
            "Incorrect A column"
        );
        assert_eq!(
            table.get_column("B").unwrap(),
            vec![false, true, false, true],
            "Incorrect B column"
        );
        assert_eq!(
            table.get_column("(A and B)").unwrap(),
            vec![false, false, false, true],
            "Incorrect result column"
        );
        assert_eq!(
            table.to_named_rows()[0],
            HashMap::from([
                ("A".to_string(), false),
                ("B".to_string(), false),
                ("(A and B)".to_string(), false),
            ]),
            "Incorrect first row"
        );
    }

    #[test]
    fn test_truth_table_tautology() {
        let expr = BooleanExpr::new("A | !A").expect("Valid expression");
        println!("Expression: {:?}", expr);
        let table = expr.truth_table();

        assert_eq!(table.num_rows(), 2, "Incorrect number of rows");
        assert_eq!(table.is_tautology(), Ok(true), "Should be a tautology");
        assert_eq!(table.is_contradiction(), Ok(false), "Should not be a contradiction");
        assert_eq!(
            table.get_column("(A or not A)").unwrap(),
            vec![true, true],
            "Incorrect result column"
        );
    }

    #[test]
    fn test_truth_table_contradiction() {
        let expr = BooleanExpr::new("A & !A").expect("Valid expression");
        let table = expr.truth_table();

        assert_eq!(table.num_rows(), 2, "Incorrect number of rows");
        assert_eq!(table.is_tautology(), Ok(false), "Should not be a tautology");
        assert_eq!(table.is_contradiction(), Ok(true), "Should be a contradiction");
        assert_eq!(
            table.get_column("(A and not A)").unwrap(),
            vec![false, false],
            "Incorrect result column"
        );
    }

    #[test]
    fn test_detailed_truth_table() {
        let expr = BooleanExpr::new("A & (B | C)").expect("Valid expression");
        let detailed_table = expr.full_truth_table();
        let table = detailed_table.to_truth_table().expect("Valid truth table");

        // Verify variables and subexpressions
        assert_eq!(
            detailed_table.variables,
            vec!["A", "B", "C"],
            "Incorrect variables"
        );
        let expected_subexprs = vec!["A", "B", "C", "B or C", "A and (B or C)"];
        assert_eq!(
            detailed_table.subexpressions,
            expected_subexprs,
            "Incorrect subexpressions"
        );
        assert_eq!(table.column_order, expected_subexprs, "Incorrect column order");

        // Verify column lengths
        let num_rows = detailed_table.combinations.len();
        assert_eq!(num_rows, 8, "Incorrect number of rows");
        for col in &detailed_table.subexpressions {
            let column = detailed_table.columns.get(col).expect("Column should exist");
            assert_eq!(column.len(), num_rows, "Incorrect column length for {}", col);
        }

        // Verify specific values
        let a_col = detailed_table.columns.get("A").unwrap();
        let b_col = detailed_table.columns.get("B").unwrap();
        let c_col = detailed_table.columns.get("C").unwrap();
        let b_or_c_col = detailed_table.columns.get("B or C").unwrap();
        let result_col = detailed_table.columns.get("A and (B or C)").unwrap();

        assert_eq!(
            a_col,
            &vec![false, false, false, false, true, true, true, true],
            "Incorrect A column"
        );
        assert_eq!(
            b_col,
            &vec![false, false, true, true, false, false, true, true],
            "Incorrect B column"
        );
        assert_eq!(
            c_col,
            &vec![false, true, false, true, false, true, false, true],
            "Incorrect C column"
        );

        for i in 0..num_rows {
            let expected_b_or_c = b_col[i] || c_col[i];
            assert_eq!(
                b_or_c_col[i],
                expected_b_or_c,
                "Incorrect B or C at row {}",
                i
            );
            let expected_result = a_col[i] && expected_b_or_c;
            assert_eq!(
                result_col[i],
                expected_result,
                "Incorrect result at row {}",
                i
            );
        }

        // Verify to_named_rows and to_column_dict
        let rows = table.to_named_rows();
        assert_eq!(rows.len(), 8, "Incorrect number of rows");
        assert_eq!(
            rows[0].get("A and (B or C)").unwrap(),
            &false,
            "Incorrect result in first row"
        );

        let columns = table.to_column_dict();
        assert_eq!(columns.len(), 5, "Incorrect number of columns");
        assert_eq!(
            columns.get("A and (B or C)").unwrap(),
            &&vec![false, false, false, false, false, true, true, true],
            "Incorrect result column"
        );
    }

    #[test]
    fn test_satisfiable_assignments() {
        let expr = BooleanExpr::new("A & B").expect("Valid expression");
        let table = expr.truth_table();
        let true_assignments = table.satisfiable_assignments(true, "(A and B)");
        let false_assignments = table.satisfiable_assignments(false, "(A and B)");

        print!("True assignments: {:?}\n", true_assignments);
        print!("False assignments: {:?}\n", false_assignments);
        assert_eq!(true_assignments.len(), 1, "Incorrect number of true assignments");
        assert_eq!(
            true_assignments[0],
            HashMap::from([
                ("A".to_string(), true),
                ("B".to_string(), true),
                ("(A and B)".to_string(), true),
            ]),
            "Incorrect true assignment"
        );

        assert_eq!(false_assignments.len(), 3, "Incorrect number of false assignments");
        let expected_false = vec![
            HashMap::from([
                ("A".to_string(), true),
                ("B".to_string(), false),
                ("(A and B)".to_string(), false),
            ]),
            HashMap::from([
                ("A".to_string(), false),
                ("B".to_string(), true),
                ("(A and B)".to_string(), false),
            ]),
            HashMap::from([
                ("A".to_string(), false),
                ("B".to_string(), false),
                ("(A and B)".to_string(), false),
            ]),
        ];
        for assignment in false_assignments {
            assert!(
                expected_false.contains(&assignment),
                "Unexpected false assignment: {:?}", assignment
            );
        }
    }

    #[test]
    fn test_invalid_expression() {
        assert!(
            BooleanExpr::new("A & & B").is_err(),
            "Should fail with invalid expression"
        );
        assert!(
            BooleanExpr::new("").is_err(),
            "Should fail with empty expression"
        );
    }

    #[test]
    fn test_empty_table() {
        let expr = BooleanExpr::new("True").expect("Valid constant expression");
        let table = expr.truth_table();
        assert_eq!(table.num_rows(), 1, "Constant expression should have one row");
        assert_eq!(table.num_variables(), 0, "Constant expression should have no variables");
        assert_eq!(
            table.get_column("true").unwrap(),
            vec![true],
            "Incorrect constant value"
        );
        assert!(table.is_tautology().unwrap(), "Constant true should be a tautology");
    }

    #[test]
    fn test_summary() {
        let expr = BooleanExpr::new("A & B").expect("Valid expression");
        let table = expr.truth_table();
        let summary = table.summary().expect("Valid summary");
        assert_eq!(summary.get("num_variables").unwrap(), &2.0, "Incorrect num_variables");
        assert_eq!(summary.get("total_combinations").unwrap(), &4.0, "Incorrect total_combinations");
        assert_eq!(summary.get("true_count").unwrap(), &1.0, "Incorrect true_count");
        assert_eq!(summary.get("false_count").unwrap(), &3.0, "Incorrect false_count");
        assert_eq!(summary.get("true_percentage").unwrap(), &25.0, "Incorrect true_percentage");
        assert_eq!(summary.get("A_true_count").unwrap(), &2.0, "Incorrect A_true_count");
        assert_eq!(summary.get("B_true_count").unwrap(), &2.0, "Incorrect B_true_count");
    }
}