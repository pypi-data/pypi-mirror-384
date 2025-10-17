use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;

use lol_html::html_content::{ContentType as NativeContentType, SourceLocation};

mod comment;
mod doctype;
mod document_end;
mod element;
mod end_tag;
mod html_rewriter;
mod text_chunk;

pub struct NativeRefWrap<R> {
    inner_ptr: *mut R,
    poisoned: std::cell::Cell<bool>,
}

impl<R> std::fmt::Debug for NativeRefWrap<R> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("NativeRefWrap")
            .field("inner_ptr", &(self.inner_ptr as usize))
            .field("poisoned", &self.poisoned.get())
            .finish()
    }
}

impl<R> NativeRefWrap<R> {
    #[inline]
    pub unsafe fn wrap<I>(inner: &mut I) -> Self {
        let inner_ptr = std::ptr::from_mut(inner).cast::<R>();
        NativeRefWrap {
            inner_ptr,
            poisoned: std::cell::Cell::new(false),
        }
    }

    fn assert_not_poisoned(&self) -> PyResult<()> {
        if self.poisoned.get() {
            Err(PyRuntimeError::new_err(
                "The object has been freed and can't be used anymore.",
            ))
        } else {
            Ok(())
        }
    }

    pub fn get(&self) -> PyResult<&R> {
        self.assert_not_poisoned()?;
        Ok(unsafe { self.inner_ptr.as_ref() }.expect("inner_ptr was null"))
    }

    pub fn get_mut(&mut self) -> PyResult<&mut R> {
        self.assert_not_poisoned()?;
        Ok(unsafe { self.inner_ptr.as_mut() }.expect("inner_ptr was null"))
    }

    pub fn poison(&self) {
        self.poisoned.set(true);
    }
}

pub trait HasNative {
    type Native;
}

pub fn location_to_py(location: SourceLocation) -> (u32, u32) {
    let range = location.bytes();
    (range.start as u32, range.end as u32)
}

#[derive(Clone, Copy, Debug)]
pub enum ContentType {
    Text,
    Html,
}

impl<'py> FromPyObject<'py> for ContentType {
    fn extract_bound(ob: &Bound<'py, PyAny>) -> PyResult<Self> {
        // Try to get Enum.value if passed a Python Enum
        if let Ok(val_obj) = ob.getattr("value") {
            if let Ok(v) = val_obj.extract::<u8>() {
                return match v {
                    0 => Ok(ContentType::Text),
                    1 => Ok(ContentType::Html),
                    _ => Err(PyRuntimeError::new_err("Invalid ContentType enum value")),
                };
            }
        }
        // Fallback: look at Enum.name
        if let Ok(name_obj) = ob.getattr("name") {
            if let Ok(name) = name_obj.extract::<&str>() {
                return match name {
                    "TEXT" | "Text" | "text" => Ok(ContentType::Text),
                    "HTML" | "Html" | "html" => Ok(ContentType::Html),
                    _ => Err(PyRuntimeError::new_err("Invalid ContentType enum name")),
                };
            }
        }
        // Fallback: accept integers 0/1
        if let Ok(v) = ob.extract::<u8>() {
            return match v {
                0 => Ok(ContentType::Text),
                1 => Ok(ContentType::Html),
                _ => Err(PyRuntimeError::new_err("Invalid ContentType integer value")),
            };
        }
        Err(PyRuntimeError::new_err(
            "Expected a ContentType enum instance (TEXT or HTML)",
        ))
    }
}

pub trait IntoNative<T> {
    fn into_native(self) -> T;
}

impl IntoNative<NativeContentType> for Option<ContentType> {
    fn into_native(self) -> NativeContentType {
        match self {
            Some(ContentType::Html) => NativeContentType::Html,
            Some(ContentType::Text) => NativeContentType::Text,
            None => NativeContentType::Text,
        }
    }
}

pub trait HasInner<N> {
    fn inner_native(&mut self) -> &mut NativeRefWrap<N>;
}

pub trait NativeBeforeAfter {
    fn native_before(&mut self, content: &str, ct: NativeContentType);
    fn native_after(&mut self, content: &str, ct: NativeContentType);
}

pub trait PyBeforeAfter<N>: HasInner<N>
where
    N: NativeBeforeAfter,
{
    #[inline]
    fn before_impl(&mut self, content: &str, content_type: Option<ContentType>) -> PyResult<()> {
        let ct = content_type.into_native();
        self.inner_native().get_mut()?.native_before(content, ct);
        Ok(())
    }

    #[inline]
    fn after_impl(&mut self, content: &str, content_type: Option<ContentType>) -> PyResult<()> {
        let ct = content_type.into_native();
        self.inner_native().get_mut()?.native_after(content, ct);
        Ok(())
    }
}

impl<T, N> PyBeforeAfter<N> for T
where
    T: HasInner<N>,
    N: NativeBeforeAfter,
{
}

use comment::Comment as PyComment;
use doctype::Doctype as PyDoctype;
use document_end::DocumentEnd as PyDocumentEnd;
use element::Element as PyElement;
use end_tag::EndTag as PyEndTag;
use html_rewriter::{HTMLRewriter as PyHTMLRewriter, HTMLRewriterOptions as PyHTMLRewriterOptions};
use text_chunk::TextChunk as PyTextChunk;

#[pymodule]
fn lolhtml(m: &Bound<PyModule>) -> PyResult<()> {
    m.add_class::<PyComment>()?;
    m.add_class::<PyDoctype>()?;
    m.add_class::<PyDocumentEnd>()?;
    m.add_class::<PyElement>()?;
    m.add_class::<PyEndTag>()?;
    m.add_class::<PyTextChunk>()?;

    // Create a Python Enum for ContentType with members: TEXT=0, HTML=1
    let py = m.py();
    let enum_mod = PyModule::import(py, "enum")?;
    let enum_cls = enum_mod.getattr("Enum")?;
    let dict = pyo3::types::PyDict::new(py);
    dict.set_item("TEXT", 0u8)?;
    dict.set_item("HTML", 1u8)?;
    let content_type_enum = enum_cls.call1(("ContentType", dict))?;
    m.add("ContentType", content_type_enum)?;

    m.add_class::<PyHTMLRewriter>()?;
    m.add_class::<PyHTMLRewriterOptions>()?;

    Ok(())
}
