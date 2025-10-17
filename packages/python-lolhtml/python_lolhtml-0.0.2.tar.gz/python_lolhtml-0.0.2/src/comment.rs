use lol_html::html_content::Comment as NativeComment;
use lol_html::html_content::ContentType as NativeContentType;
use pyo3::prelude::*;

use crate::{ContentType, HasInner, NativeBeforeAfter, NativeRefWrap, PyBeforeAfter};

#[pyclass(unsendable)]
pub struct Comment {
    inner: NativeRefWrap<NativeComment<'static>>,
}

impl Comment {
    pub(crate) fn from_native_mut(c: &mut NativeComment<'_>) -> Self {
        Self {
            inner: unsafe { NativeRefWrap::wrap(c) },
        }
    }
}

impl HasInner<NativeComment<'static>> for Comment {
    #[inline]
    fn inner_native(&mut self) -> &mut NativeRefWrap<NativeComment<'static>> {
        &mut self.inner
    }
}

impl NativeBeforeAfter for lol_html::html_content::Comment<'static> {
    #[inline]
    fn native_before(&mut self, content: &str, ct: NativeContentType) {
        self.before(content, ct);
    }
    #[inline]
    fn native_after(&mut self, content: &str, ct: NativeContentType) {
        self.after(content, ct);
    }
}

#[pymethods]
impl Comment {
    #[getter]
    pub fn text(&self) -> PyResult<String> {
        self.inner
            .get()
            .map(|c| c.text().to_string())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }

    #[setter]
    pub fn set_text(&mut self, text: &str) -> PyResult<()> {
        self.inner
            .get_mut()?
            .set_text(text)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        Ok(())
    }

    pub fn remove(&mut self) -> PyResult<()> {
        self.inner.get_mut()?.remove();
        Ok(())
    }

    #[getter]
    pub fn removed(&self) -> PyResult<bool> {
        Ok(self.inner.get()?.removed())
    }

    #[pyo3(signature = (content, content_type=None))]
    pub fn before(&mut self, content: &str, content_type: Option<ContentType>) -> PyResult<()> {
        <Self as PyBeforeAfter<NativeComment<'static>>>::before_impl(self, content, content_type)
    }

    #[pyo3(signature = (content, content_type=None))]
    pub fn after(&mut self, content: &str, content_type: Option<ContentType>) -> PyResult<()> {
        <Self as PyBeforeAfter<NativeComment<'static>>>::after_impl(self, content, content_type)
    }

    pub fn __repr__(&self) -> PyResult<String> {
        let text = self.text()?;
        Ok(format!("Comment(text={:?})", text))
    }
}
