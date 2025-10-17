use lol_html::html_content::ContentType as NativeContentType;
use lol_html::html_content::EndTag as NativeEndTag;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;

use crate::{ContentType, HasInner, HasNative, NativeBeforeAfter, NativeRefWrap, PyBeforeAfter};

#[pyclass(unsendable)]
pub struct EndTag {
    inner: NativeRefWrap<NativeEndTag<'static>>,
}

impl HasNative for EndTag {
    type Native = NativeEndTag<'static>;
}

impl HasInner<NativeEndTag<'static>> for EndTag {
    #[inline]
    fn inner_native(&mut self) -> &mut NativeRefWrap<NativeEndTag<'static>> {
        &mut self.inner
    }
}

impl NativeBeforeAfter for lol_html::html_content::EndTag<'static> {
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
impl EndTag {
    #[getter]
    pub fn name(&self) -> PyResult<String> {
        self.inner
            .get()
            .map(|e| e.name())
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))
    }

    #[setter]
    pub fn set_name(&mut self, name: &str) -> PyResult<()> {
        self.inner.get_mut()?.set_name_str(name.to_string());
        Ok(())
    }

    #[pyo3(signature = (content, content_type=None))]
    pub fn before(&mut self, content: &str, content_type: Option<ContentType>) -> PyResult<()> {
        <Self as PyBeforeAfter<NativeEndTag<'static>>>::before_impl(self, content, content_type)
    }

    #[pyo3(signature = (content, content_type=None))]
    pub fn after(&mut self, content: &str, content_type: Option<ContentType>) -> PyResult<()> {
        <Self as PyBeforeAfter<NativeEndTag<'static>>>::after_impl(self, content, content_type)
    }

    pub fn remove(&mut self) -> PyResult<()> {
        self.inner.get_mut()?.remove();
        Ok(())
    }
}
