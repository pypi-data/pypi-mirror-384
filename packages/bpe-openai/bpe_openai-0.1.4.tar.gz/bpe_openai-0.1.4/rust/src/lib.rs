use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

type CoreTokenizer = bpe_openai::Tokenizer;

fn resolve_tokenizer(lower_name: &str) -> Option<&'static CoreTokenizer> {
    match lower_name {
        "cl100k_base" => Some(bpe_openai::cl100k_base()),
        "o200k_base" => Some(bpe_openai::o200k_base()),
        "voyage3_base" => Some(bpe_openai::voyage3_base()),
        _ => None,
    }
}

fn model_alias(lower_name: &str) -> Option<&'static str> {
    match lower_name {
        "gpt-4o" | "gpt-4o-mini" | "gpt-4.1" | "gpt-4.1-mini" => Some("o200k_base"),
        "gpt-4o-128k" | "gpt-4.1-128k" => Some("o200k_base"),
        "voyage-3" => Some("voyage3_base"),
        _ => None,
    }
}

#[pyclass(module = "bpe_openai._bindings")]
pub struct PyTokenizer {
    tokenizer: &'static CoreTokenizer,
}

#[pymethods]
impl PyTokenizer {
    pub fn encode(&self, text: &str) -> Vec<u32> {
        self.tokenizer.encode(text)
    }

    pub fn decode(&self, tokens: Vec<u32>) -> PyResult<String> {
        self.tokenizer
            .decode(&tokens)
            .ok_or_else(|| PyValueError::new_err("Token sequence cannot be decoded as UTF-8"))
    }

    pub fn count(&self, text: &str) -> usize {
        self.tokenizer.count(text)
    }

    pub fn count_till_limit(&self, text: &str, token_limit: usize) -> Option<usize> {
        let normalized = self.tokenizer.normalize(text);
        self.tokenizer.count_till_limit(&normalized, token_limit)
    }

    pub fn pretokenize(&self, text: &str) -> Vec<String> {
        self.tokenizer
            .split(text)
            .map(|piece| piece.to_string())
            .collect()
    }
}

#[pyfunction]
fn tokenizer_for_model(name: &str) -> PyResult<PyTokenizer> {
    let lower = name.to_lowercase();
    let tokenizer = resolve_tokenizer(&lower)
        .or_else(|| model_alias(&lower).and_then(resolve_tokenizer))
        .ok_or_else(|| PyValueError::new_err(format!("Unsupported model '{name}'")))?;
    Ok(PyTokenizer { tokenizer })
}

#[pyfunction]
fn tokenizer_for_encoding(name: &str) -> PyResult<PyTokenizer> {
    let lower = name.to_lowercase();
    resolve_tokenizer(&lower)
        .map(|tok| PyTokenizer { tokenizer: tok })
        .ok_or_else(|| PyValueError::new_err(format!("Unsupported encoding '{name}'")))
}

#[pyfunction]
fn supported_encodings() -> Vec<&'static str> {
    vec!["cl100k_base", "o200k_base", "voyage3_base"]
}

#[pyfunction]
fn supported_models() -> Vec<&'static str> {
    vec![
        "cl100k_base",
        "o200k_base",
        "voyage3_base",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4o-128k",
        "gpt-4.1-128k",
        "voyage-3",
    ]
}

#[pymodule]
fn _bindings(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<PyTokenizer>()?;
    module.add_function(wrap_pyfunction!(tokenizer_for_model, module)?)?;
    module.add_function(wrap_pyfunction!(tokenizer_for_encoding, module)?)?;
    module.add_function(wrap_pyfunction!(supported_encodings, module)?)?;
    module.add_function(wrap_pyfunction!(supported_models, module)?)?;
    module.add("RUST_BACKEND_VERSION", env!("CARGO_PKG_VERSION"))?;
    module.add("PYTHON_API_VERSION", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
