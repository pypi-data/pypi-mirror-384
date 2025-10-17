use lol_html::html_content::ContentType as NativeContentType;
use lol_html::html_content::TextChunk as NativeTextChunk;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;

use crate::{
    ContentType, HasInner, HasNative, IntoNative, NativeBeforeAfter, NativeRefWrap, PyBeforeAfter,
};

#[pyclass(unsendable)]
pub struct TextChunk {
    inner: NativeRefWrap<NativeTextChunk<'static>>,
}

impl HasNative for TextChunk {
    type Native = NativeTextChunk<'static>;
}

impl TextChunk {
    pub(crate) fn from_native_mut(t: &mut NativeTextChunk<'_>) -> Self {
        Self {
            inner: unsafe { NativeRefWrap::wrap(t) },
        }
    }
}

impl HasInner<NativeTextChunk<'static>> for TextChunk {
    #[inline]
    fn inner_native(&mut self) -> &mut NativeRefWrap<NativeTextChunk<'static>> {
        &mut self.inner
    }
}

impl NativeBeforeAfter for lol_html::html_content::TextChunk<'static> {
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
impl TextChunk {
    #[getter]
    pub fn text(&self) -> PyResult<String> {
        self.inner
            .get()
            .map(|c| c.as_str().to_string())
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))
    }

    #[getter]
    pub fn last_in_text_node(&self) -> PyResult<bool> {
        self.inner
            .get()
            .map(|c| c.last_in_text_node())
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))
    }

    #[pyo3(signature = (content, content_type=None))]
    pub fn before(&mut self, content: &str, content_type: Option<ContentType>) -> PyResult<()> {
        <Self as PyBeforeAfter<NativeTextChunk<'static>>>::before_impl(self, content, content_type)
    }

    #[pyo3(signature = (content, content_type=None))]
    pub fn after(&mut self, content: &str, content_type: Option<ContentType>) -> PyResult<()> {
        <Self as PyBeforeAfter<NativeTextChunk<'static>>>::after_impl(self, content, content_type)
    }

    #[pyo3(signature = (content, content_type=None))]
    pub fn replace(&mut self, content: &str, content_type: Option<ContentType>) -> PyResult<()> {
        self.inner
            .get_mut()?
            .replace(content, content_type.into_native());
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

    pub fn __repr__(&self) -> PyResult<String> {
        let text = self.text()?;
        Ok(format!("TextChunk(text={:?})", text))
    }
}
