use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyDict;

use lol_html as lh;
use std::ptr::NonNull;

pub type RawElement = lh::html_content::Element<'static, 'static>;
pub type RawComment = lh::html_content::Comment<'static>;
pub type RawTextChunk = lh::html_content::TextChunk<'static>;

pub trait Invalidate {
    fn invalidate(&mut self);
}

#[pyclass(unsendable)]
pub struct Element {
    pub(crate) ptr: Option<NonNull<RawElement>>,
    pub(crate) alive: bool,
}

impl Element {
    #[inline]
    fn with_element<R>(
        &self,
        f: impl for<'a, 'b> FnOnce(&mut lh::html_content::Element<'a, 'b>) -> PyResult<R>,
    ) -> PyResult<R> {
        if !self.alive {
            return Err(PyRuntimeError::new_err(
                "Element handle is no longer valid (used outside callback)",
            ));
        }
        let ptr = match self.ptr {
            Some(p) => p,
            None => {
                return Err(PyRuntimeError::new_err(
                    "Element handle is no longer valid (used outside callback)",
                ))
            }
        };

        // SAFETY: pointer originates from a &mut Element valid only during the callback.
        let el = unsafe { &mut *ptr.as_ptr() };
        f(el)
    }
}

#[pymethods]
impl Element {
    #[getter]
    fn tag_name(&self) -> PyResult<String> {
        self.with_element(|el| Ok(el.tag_name().to_string()))
    }

    #[getter]
    fn removed(&self) -> PyResult<bool> {
        self.with_element(|el| Ok(el.removed()))
    }

    #[getter]
    fn attributes(&self, py: Python<'_>) -> PyResult<Py<PyDict>> {
        let dict = PyDict::new(py);
        self.with_element(|el| {
            for a in el.attributes() {
                dict.set_item(a.name(), a.value())?;
            }
            Ok(())
        })?;
        Ok(dict.unbind())
    }

    fn get_attribute(&self, name: &str) -> PyResult<Option<String>> {
        self.with_element(|el| Ok(el.get_attribute(name)))
    }

    fn has_attribute(&self, name: &str) -> PyResult<bool> {
        self.with_element(|el| Ok(el.has_attribute(name)))
    }

    fn set_attribute(&self, name: &str, value: &str) -> PyResult<()> {
        self.with_element(|el| {
            el.set_attribute(name, value)
                .map_err(|e| PyRuntimeError::new_err(e.to_string()))
        })
    }

    fn remove_attribute(&self, name: &str) -> PyResult<()> {
        self.with_element(|el| {
            let r = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                el.remove_attribute(name)
            }));
            match r {
                Ok(()) => Ok(()),
                Err(payload) => {
                    // Extract a meaningful panic message and surface it to Python
                    let any = &*payload;
                    let msg = if let Some(s) = any.downcast_ref::<&str>() {
                        s.to_string()
                    } else if let Some(s) = any.downcast_ref::<String>() {
                        s.clone()
                    } else {
                        "panic in remove_attribute".to_string()
                    };
                    Err(PyRuntimeError::new_err(msg))
                }
            }
        })
    }

    #[pyo3(signature = (content, text = true))]
    fn before(&self, content: &str, text: bool) -> PyResult<()> {
        use lh::html_content::ContentType;
        let content_type = if text {
            ContentType::Text
        } else {
            ContentType::Html
        };

        self.with_element(|el| {
            el.before(content, content_type);
            Ok(())
        })
    }

    #[pyo3(signature = (content, text = true))]
    fn after(&self, content: &str, text: bool) -> PyResult<()> {
        use lh::html_content::ContentType;
        let content_type = if text {
            ContentType::Text
        } else {
            ContentType::Html
        };

        self.with_element(|el| {
            el.after(content, content_type);
            Ok(())
        })
    }
}

impl Invalidate for Element {
    fn invalidate(&mut self) {
        self.alive = false;
        self.ptr = None;
    }
}

/// A proxy to lol_html::html_content::Comment used only synchronously during callbacks.
#[pyclass(unsendable)]
pub struct Comment {
    pub(crate) ptr: Option<NonNull<RawComment>>,
    pub(crate) alive: bool,
}

impl Comment {
    #[inline]
    fn with_comment<R>(
        &self,
        f: impl for<'a> FnOnce(&mut lh::html_content::Comment<'a>) -> PyResult<R>,
    ) -> PyResult<R> {
        if !self.alive {
            return Err(PyRuntimeError::new_err(
                "Comment handle is no longer valid (used outside callback)",
            ));
        }
        let ptr = match self.ptr {
            Some(p) => p,
            None => {
                return Err(PyRuntimeError::new_err(
                    "Comment handle is no longer valid (used outside callback)",
                ))
            }
        };
        let c = unsafe { &mut *ptr.as_ptr() };
        f(c)
    }
}

#[pymethods]
impl Comment {
    #[getter]
    fn text(&self) -> PyResult<String> {
        self.with_comment(|c| Ok(c.text().to_string()))
    }

    fn set_text(&self, value: &str) -> PyResult<()> {
        self.with_comment(|c| {
            c.set_text(value)
                .map_err(|e| PyRuntimeError::new_err(e.to_string()))
        })
    }

    #[getter]
    fn removed(&self) -> PyResult<bool> {
        self.with_comment(|c| Ok(c.removed()))
    }

    fn remove(&self) -> PyResult<()> {
        self.with_comment(|c| Ok(c.remove()))
    }

    #[pyo3(signature = (content, text = true))]
    fn before(&self, content: &str, text: bool) -> PyResult<()> {
        use lh::html_content::ContentType;
        let content_type = if text {
            ContentType::Text
        } else {
            ContentType::Html
        };

        self.with_comment(|c| {
            c.before(content, content_type);
            Ok(())
        })
    }

    #[pyo3(signature = (content, text = true))]
    fn after(&self, content: &str, text: bool) -> PyResult<()> {
        use lh::html_content::ContentType;
        let content_type = if text {
            ContentType::Text
        } else {
            ContentType::Html
        };

        self.with_comment(|c| {
            c.after(content, content_type);
            Ok(())
        })
    }
}

impl Invalidate for Comment {
    fn invalidate(&mut self) {
        self.alive = false;
        self.ptr = None;
    }
}

/// A proxy to lol_html::html_content::TextChunk used only synchronously during callbacks.
#[pyclass(unsendable)]
pub struct TextChunk {
    pub(crate) ptr: Option<NonNull<RawTextChunk>>,
    pub(crate) alive: bool,
}

impl TextChunk {
    #[inline]
    fn with_text<R>(
        &self,
        f: impl for<'a> FnOnce(&mut lh::html_content::TextChunk<'a>) -> PyResult<R>,
    ) -> PyResult<R> {
        if !self.alive {
            return Err(PyRuntimeError::new_err(
                "TextChunk handle is no longer valid (used outside callback)",
            ));
        }
        let ptr = match self.ptr {
            Some(p) => p,
            None => {
                return Err(PyRuntimeError::new_err(
                    "TextChunk handle is no longer valid (used outside callback)",
                ))
            }
        };
        let t = unsafe { &mut *ptr.as_ptr() };
        f(t)
    }
}

#[pymethods]
impl TextChunk {
    #[getter]
    fn text(&self) -> PyResult<String> {
        self.with_text(|t| Ok(t.as_str().to_string()))
    }

    fn set_text(&self, value: &str) -> PyResult<()> {
        use lh::html_content::ContentType;
        self.with_text(|t| {
            t.replace(value, ContentType::Text);
            Ok(())
        })
    }

    #[getter]
    fn removed(&self) -> PyResult<bool> {
        self.with_text(|t| Ok(t.removed()))
    }

    fn remove(&self) -> PyResult<()> {
        self.with_text(|t| Ok(t.remove()))
    }

    #[getter]
    fn last_in_text_node(&self) -> PyResult<bool> {
        self.with_text(|t| Ok(t.last_in_text_node()))
    }

    #[pyo3(signature = (content, text = true))]
    fn before(&self, content: &str, text: bool) -> PyResult<()> {
        use lh::html_content::ContentType;
        let content_type = if text {
            ContentType::Text
        } else {
            ContentType::Html
        };

        self.with_text(|t| {
            t.before(content, content_type);
            Ok(())
        })
    }

    #[pyo3(signature = (content, text = true))]
    fn after(&self, content: &str, text: bool) -> PyResult<()> {
        use lh::html_content::ContentType;
        let content_type = if text {
            ContentType::Text
        } else {
            ContentType::Html
        };

        self.with_text(|t| {
            t.after(content, content_type);
            Ok(())
        })
    }
}

impl Invalidate for TextChunk {
    fn invalidate(&mut self) {
        self.alive = false;
        self.ptr = None;
    }
}
