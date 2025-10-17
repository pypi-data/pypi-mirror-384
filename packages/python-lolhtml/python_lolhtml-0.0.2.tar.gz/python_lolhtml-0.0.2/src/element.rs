use lol_html::html_content::ContentType as NativeContentType;
use lol_html::html_content::Element as NativeElement;

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;

use crate::{
    ContentType, HasInner, HasNative, IntoNative, NativeBeforeAfter, NativeRefWrap, PyBeforeAfter,
};

#[pyclass(unsendable)]
pub struct Element {
    inner: NativeRefWrap<NativeElement<'static, 'static>>,
}

impl HasNative for Element {
    type Native = NativeElement<'static, 'static>;
}

impl Element {
    pub(crate) fn from_native_mut(el: &mut NativeElement<'_, '_>) -> Self {
        Self {
            inner: unsafe { NativeRefWrap::wrap(el) },
        }
    }
}

impl HasInner<NativeElement<'static, 'static>> for Element {
    #[inline]
    fn inner_native(&mut self) -> &mut NativeRefWrap<NativeElement<'static, 'static>> {
        &mut self.inner
    }
}

impl NativeBeforeAfter for lol_html::html_content::Element<'static, 'static> {
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
impl Element {
    #[getter]
    pub fn tag_name(&self) -> PyResult<String> {
        self.inner
            .get()
            .map(|e| e.tag_name())
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))
    }

    #[setter]
    pub fn set_tag_name(&mut self, name: &str) -> PyResult<()> {
        self.inner
            .get_mut()?
            .set_tag_name(name)
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;
        Ok(())
    }

    #[getter]
    pub fn namespace_uri(&self) -> PyResult<String> {
        self.inner
            .get()
            .map(|e| e.namespace_uri().to_string())
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))
    }

    #[getter]
    pub fn attributes(&self) -> PyResult<Vec<(String, String)>> {
        self.inner
            .get()
            .map(|e| {
                e.attributes()
                    .iter()
                    .map(|a| (a.name().to_string(), a.value().to_string()))
                    .collect::<Vec<_>>()
            })
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))
    }

    pub fn get_attribute(&self, name: &str) -> PyResult<Option<String>> {
        self.inner
            .get()
            .map(|e| e.get_attribute(name).map(|s| s.to_string()))
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))
    }

    pub fn has_attribute(&self, name: &str) -> PyResult<bool> {
        self.inner
            .get()
            .map(|e| e.has_attribute(name))
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))
    }

    pub fn set_attribute(&mut self, name: &str, value: &str) -> PyResult<()> {
        self.inner
            .get_mut()?
            .set_attribute(name, value)
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;
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

    pub fn remove_attribute(&mut self, name: &str) -> PyResult<()> {
        self.inner.get_mut()?.remove_attribute(name);
        Ok(())
    }

    #[pyo3(signature = (content, content_type=None))]
    pub fn prepend(&mut self, content: &str, content_type: Option<ContentType>) -> PyResult<()> {
        self.inner
            .get_mut()?
            .prepend(content, content_type.into_native());
        Ok(())
    }

    #[pyo3(signature = (content, content_type=None))]
    pub fn append(&mut self, content: &str, content_type: Option<ContentType>) -> PyResult<()> {
        self.inner
            .get_mut()?
            .append(content, content_type.into_native());
        Ok(())
    }

    #[pyo3(signature = (content, content_type=None))]
    pub fn before(&mut self, content: &str, content_type: Option<ContentType>) -> PyResult<()> {
        <Self as PyBeforeAfter<NativeElement<'static, 'static>>>::before_impl(
            self,
            content,
            content_type,
        )
    }

    #[pyo3(signature = (content, content_type=None))]
    pub fn after(&mut self, content: &str, content_type: Option<ContentType>) -> PyResult<()> {
        <Self as PyBeforeAfter<NativeElement<'static, 'static>>>::after_impl(
            self,
            content,
            content_type,
        )
    }

    #[pyo3(signature = (content, content_type=None))]
    pub fn set_inner_content(
        &mut self,
        content: &str,
        content_type: Option<ContentType>,
    ) -> PyResult<()> {
        self.inner
            .get_mut()?
            .set_inner_content(content, content_type.into_native());
        Ok(())
    }

    pub fn remove_and_keep_content(&mut self) -> PyResult<()> {
        self.inner.get_mut()?.remove_and_keep_content();
        Ok(())
    }
}
