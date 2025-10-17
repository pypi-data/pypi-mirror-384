use pyo3::{Bound, FromPyObject, PyAny, PyErr, PyResult, types::PyAnyMethods};

#[pyo3::pymodule]
mod parse_int {
    use pyo3::{
        exceptions::PyTypeError,
        prelude::*,
        types::{PyFloat, PyInt},
    };

    use crate::Number;

    /// Parse a strictly integer value
    #[pyfunction]
    fn parse_int(s: &str) -> PyResult<i64> {
        Ok(::parse_int::parse(s)?)
    }

    /// Parse an integer or floaty value
    #[pyfunction]
    fn parse_num<'py>(py: Python<'py>, s: &str) -> PyResult<Bound<'py, PyAny>> {
        if let Ok(i) = ::parse_int::parse::<i64>(s) {
            return Ok(PyInt::new(py, i).into_any());
        }

        let f: f64 = ::parse_int::parse(s).map_err(|e| PyTypeError::new_err(format!("{e:?}")))?;

        Ok(PyFloat::new(py, f).into_any())
    }

    /// Parse a float value (decimal)
    #[pyfunction]
    fn parse_float(s: &str) -> PyResult<f64> {
        Ok(::parse_int::parse(s).map_err(|e| PyTypeError::new_err(format!("{e:?}")))?)
    }

    /// Formats the sum of two numbers as string.
    #[pyfunction]
    fn format_dec(input: Number) -> PyResult<String> {
        match input {
            Number::Int(i) => Ok(::parse_int::format_pretty_dec(i)),
            Number::Float(f) => Ok(::parse_int::format_pretty_dec(f)),
        }
    }

    /// Formats the sum of two numbers as string.
    #[pyfunction]
    fn format_hex(num: i64) -> PyResult<String> {
        Ok(::parse_int::format_pretty_hex(num))
    }
}

#[derive(Debug)]
enum Number {
    Int(i64),
    Float(f64),
}

impl<'source> FromPyObject<'source> for Number {
    fn extract_bound(ob: &Bound<'source, PyAny>) -> PyResult<Self> {
        // First, try to extract as integer
        if let Ok(int_val) = ob.extract::<i64>() {
            return Ok(Number::Int(int_val));
        }

        // Then, try to extract as float
        if let Ok(float_val) = ob.extract::<f64>() {
            return Ok(Number::Float(float_val));
        }

        // If neither works, return an error
        Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
            "Expected a number (int or float)",
        ))
    }
}
