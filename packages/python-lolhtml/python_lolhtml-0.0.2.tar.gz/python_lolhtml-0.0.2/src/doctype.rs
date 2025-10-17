use lol_html::html_content::Doctype as NativeDoctype;
use pyo3::prelude::*;

use crate::{HasNative, NativeRefWrap};

#[pyclass(unsendable)]
pub struct Doctype {
    inner: NativeRefWrap<NativeDoctype<'static>>,
}

impl HasNative for Doctype {
    type Native = NativeDoctype<'static>;
}

impl Doctype {
    pub(crate) fn from_native_mut(d: &mut NativeDoctype<'_>) -> Self {
        Self {
            inner: unsafe { NativeRefWrap::wrap(d) },
        }
    }
}

#[pymethods]
impl Doctype {
    #[getter]
    pub fn name(&self) -> PyResult<Option<String>> {
        self.inner
            .get()
            .map(|d| d.name().map(|s| s.to_string()))
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }

    #[getter]
    pub fn public_id(&self) -> PyResult<Option<String>> {
        self.inner
            .get()
            .map(|d| d.public_id().map(|s| s.to_string()))
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }

    #[getter]
    pub fn system_id(&self) -> PyResult<Option<String>> {
        self.inner
            .get()
            .map(|d| d.system_id().map(|s| s.to_string()))
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }
}
