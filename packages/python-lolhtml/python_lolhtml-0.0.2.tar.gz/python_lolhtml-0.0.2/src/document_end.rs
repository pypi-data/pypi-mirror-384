use crate::{ContentType, IntoNative, NativeRefWrap};
use lol_html::html_content::DocumentEnd as NativeDocumentEnd;
use pyo3::prelude::*;

#[pyclass(unsendable)]
pub struct DocumentEnd {
    inner: NativeRefWrap<NativeDocumentEnd<'static>>,
}

impl DocumentEnd {
    pub(crate) fn from_native_mut(d: &mut NativeDocumentEnd<'_>) -> Self {
        Self {
            inner: unsafe { NativeRefWrap::wrap(d) },
        }
    }
}

#[pymethods]
impl DocumentEnd {
    #[pyo3(signature = (content, content_type=None))]
    pub fn append(&mut self, content: &str, content_type: Option<ContentType>) -> PyResult<()> {
        self.inner
            .get_mut()?
            .append(content, content_type.into_native());
        Ok(())
    }
}
