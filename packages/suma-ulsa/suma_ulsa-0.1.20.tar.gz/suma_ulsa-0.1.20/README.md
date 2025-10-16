# SUMA — Sistema Universitario de Métodos Académicos

<div align="center">

[![Versión](https://img.shields.io/badge/SUMA-v0.1.0-blue.svg)](https://github.com/Void-CA/SUMA)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)]()
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)]()
[![Rust](https://img.shields.io/badge/rust-1.70+-orange.svg)]()

</div>

**Librería académica para el aprendizaje y resolución rigurosa de métodos universitarios, con un enfoque práctico y accesible.**

---

## 📚 Módulo de Álgebra Booleana

El módulo de álgebra booleana proporciona herramientas completas para trabajar con expresiones lógicas, tablas de verdad, simplificación y análisis de circuitos digitales.

## 🎯 Características Principales

- Expresiones Booleanas: soporte para operadores lógicos básicos y compuestos.
- Tablas de Verdad: generación automática y análisis de propiedades.
- Simplificación: reducción de expresiones usando métodos algebraicos.
- Validación: verificación de tautologías, contradicciones y equivalencias.
- Compatibilidad Python: API intuitiva para usuarios de Python.

---

## 🔧 Instalación (en desarrollo)

```bash
pip install suma_ulsa
```

> Nota: Si usas este repositorio desde fuentes, sigue las instrucciones de "Instalación para desarrollo" más abajo.

## 💡 Uso Rápido

```python
from suma_ulsa.boolean_algebra import BooleanExpr

# Crear y evaluar expresiones booleanas
expr = BooleanExpr("(A and B) or (not C)")
resultado = expr.evaluate({'A': True, 'B': False, 'C': True})
print(f"Resultado: {resultado}")

# Generar tabla de verdad completa
tabla = expr.truth_table()
print(tabla)

# Verificar propiedades
print(f"¿Es tautología? {expr.is_tautology()}")
print(f"¿Es contradicción? {expr.is_contradiction()}")
```

---

## 📖 Ejemplos Detallados

### 1. Expresiones Básicas

```python
from suma_ulsa.boolean_algebra import BooleanExpr

# Expresión simple
expr1 = BooleanExpr("A and B")
print(expr1.evaluate({'A': True, 'B': True}))  # True

# Expresión con múltiples operadores
expr2 = BooleanExpr("(A or B) and not C")
valores = {'A': True, 'B': False, 'C': True}
print(expr2.evaluate(valores))  # False
```

### 2. Tablas de Verdad

```python
# Generar tabla de verdad
expr = BooleanExpr("A xor B")
tabla = expr.truth_table()

# La tabla muestra todas las combinaciones y resultados
print(tabla)
# Salida aproximada:
# | A | B | Result |
# |---|---|--------|
# | 0 | 0 |   0    |
# | 0 | 1 |   1    |
# | 1 | 0 |   1    |
# | 1 | 1 |   0    |
```

#### 2.1 Metodos de la Tabla de Verdad

```python
print("CSV:\n", tabla.to_csv())
print("JSON:", tabla.to_json())
print("Lazyframe:", tabla.to_lazyframe())
print("Polars Dataframe:", tabla.to_polars())
print("Dictionary:", tabla.to_column_dict())
print("List: ", tabla.to_list())
print("Named rows:", tabla.to_named_rows())
```

---

## 🏗️ API Principal

Clase `Expression` — métodos principales:

- `__init__(expr: str)`: Crea expresión desde string
- `evaluar(**variables)`: Evalúa con valores específicos
- `tabla_verdad()`: Genera tabla de verdad completa
- `es_tautologia()`: Verifica si siempre es verdadera
- `es_tautologia()`: Verifica si siempre es falsa
- `es_contingencia()`: Verifica si depende de variables
- `simplificar()`: Retorna expresión simplificada
- `equivalentes(otra_expr)`: Compara equivalencia lógica

### Operadores soportados

- AND: `and`, `&`, `∧`
- OR: `or`, `|`, `∨`
- NOT: `not`, `~`, `¬`
- XOR: `xor`, `^`, `⊕`
- IMPLICA: `implies`, `=>`, `→`
- EQUIVALE: `iff`, `<=>`, `↔`

---


## 🔬 Características Avanzadas

- Optimización de rendimiento: Implementado en Rust para máxima velocidad
- Manejo de errores: Mensajes descriptivos para expresiones inválidas
- Variables ilimitadas: Soporte para expresiones con múltiples variables
- Formas normales: Conversión a FNC y FND
- Mapas de Karnaugh: (Próximamente) Simplificación visual

---

## 🗓️ Próximos Módulos

| Módulo | Estado | Funcionalidades |
|---|---:|---|
| Álgebra Booleana | ✅ Implementado | Expresiones, tablas de verdad, simplificación |
| Estructuras de Datos | 🔄 En desarrollo | Grafos, árboles, algoritmos de búsqueda |
| Finanzas Computacionales | 📅 Planeado | TVM, análisis de inversiones, préstamos |
| Métodos Numéricos | 📅 Planeado | Ecuaciones, derivación, integración |

---

## 🚀 Instalación para Desarrollo

```bash
# Clonar repositorio
git clone https://github.com/Void-CA/suma.git
cd suma

# Instalar en modo desarrollo
pip install -e .

# Ejecutar tests
cargo test
python -m pytest tests/
```

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Áreas prioritarias:

- Nuevos módulos académicos
- Mejoras en álgebra booleana (Karnaugh, Quine-McCluskey)
- Documentación y ejemplos
- Tests y validación

---

## 📊 Estructura del Proyecto (resumen)

```
suma/
├── src/                   
│   ├── lib.rs
│   ├── core/    # Módulo core codificado en Rust
│   |   ├── boolean_algebra/    # Módulo de álgebra booleana
│   |   ├── ...
│   └── bindings/             # Bindings Python
├── suma_ulsa/                   # Paquete Python
│   ├── __init__.py
│   └── boolean_algebra/

---

## 📄 Licencia

MIT License — ver `LICENSE` para detalles.

---

_Desarrollado por estudiantes, para estudiantes, con dedicación y rigor académico._
