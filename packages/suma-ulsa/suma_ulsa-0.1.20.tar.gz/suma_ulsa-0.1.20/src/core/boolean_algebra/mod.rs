// src/core/boolean_algebra/mod.rs
pub mod ast;
pub mod parser;
pub mod boolean_expr;
pub mod truth_table;
pub mod error;  // NUEVO

// Re-export para fácil acceso
pub use truth_table::TruthTable;
pub use boolean_expr::BooleanExpr;
pub use error::{BooleanAlgebraError};  // NUEVO

// Tipo Result personalizado para todo el módulo
pub type Result<T> = std::result::Result<T, BooleanAlgebraError>;