use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

use lol_html::{
    errors::RewritingError, DocumentContentHandlers as NativeDocumentContentHandlers,
    ElementContentHandlers as NativeElementContentHandlers, HtmlRewriter as NativeHTMLRewriter,
    OutputSink, Selector, Settings,
};

use std::borrow::Cow;
use std::io;

use crate::comment::Comment as PyComment;
use crate::doctype::Doctype as PyDoctype;
use crate::document_end::DocumentEnd as PyDocumentEnd;
use crate::element::Element as PyElement;
use crate::text_chunk::TextChunk as PyTextChunk;

fn call_python<F>(f: F) -> Result<(), Box<dyn std::error::Error + Send + Sync>>
where
    F: FnOnce(Python<'_>) -> PyResult<()>,
{
    match Python::attach(|py| {
        f(py)?;
        Ok::<(), PyErr>(())
    }) {
        Ok(()) => Ok(()),
        Err(err) => Err(
            Box::new(io::Error::new(io::ErrorKind::Other, err.to_string()))
                as Box<dyn std::error::Error + Send + Sync>,
        ),
    }
}

pub struct PythonOutputSink {
    callback: Py<PyAny>,
}

impl PythonOutputSink {
    pub fn new(cb: Py<PyAny>) -> Self {
        Self { callback: cb }
    }
}

impl OutputSink for PythonOutputSink {
    #[inline]
    fn handle_chunk(&mut self, chunk: &[u8]) {
        Python::attach(|py| {
            let py_bytes = PyBytes::new(py, chunk);
            let _ = self
                .callback
                .call1(py, (py_bytes,))
                .map_err(|e| PyRuntimeError::new_err(e.to_string()));
        });
    }
}

fn rewriting_error_to_py(err: RewritingError) -> PyErr {
    match err {
        RewritingError::ContentHandlerError(e) => {
            PyRuntimeError::new_err(format!("Content handler error: {}", e))
        }
        other => PyRuntimeError::new_err(other.to_string()),
    }
}

fn opt_callable(py: Python<'_>, obj: &Py<PyAny>, name: &str) -> Option<Py<PyAny>> {
    match obj.getattr(py, name) {
        Ok(v) => {
            if v.is_none(py) {
                None
            } else {
                Some(v)
            }
        }
        Err(_) => None,
    }
}

macro_rules! attach_handler {
    ($built:ident, $method:ident, $cb_opt:expr, $native_ty:ty, $wrap_ty:ty, $wrap_fn:ident) => {
        if let Some(cb_moved) = $cb_opt {
            $built = $built.$method(move |native: &mut $native_ty| {
                call_python(|py| {
                    let py_obj = Py::new(py, <$wrap_ty>::$wrap_fn(native))?;
                    cb_moved.call1(py, (py_obj,))?;
                    Ok(())
                })
            });
        }
    };
}

fn build_element_handler_pair(
    selector: Selector,
    py_handlers: Py<PyAny>,
) -> (
    Cow<'static, Selector>,
    NativeElementContentHandlers<'static>,
) {
    let (element_cb, comments_cb, text_cb): (
        Option<Py<PyAny>>,
        Option<Py<PyAny>>,
        Option<Py<PyAny>>,
    ) = Python::attach(|py| {
        (
            opt_callable(py, &py_handlers, "element"),
            opt_callable(py, &py_handlers, "comments"),
            opt_callable(py, &py_handlers, "text"),
        )
    });

    let mut built: NativeElementContentHandlers<'static> = NativeElementContentHandlers::default();

    attach_handler!(
        built,
        element,
        element_cb,
        lol_html::html_content::Element<'_, '_>,
        PyElement,
        from_native_mut
    );
    attach_handler!(
        built,
        comments,
        comments_cb,
        lol_html::html_content::Comment<'_>,
        PyComment,
        from_native_mut
    );
    attach_handler!(
        built,
        text,
        text_cb,
        lol_html::html_content::TextChunk<'_>,
        PyTextChunk,
        from_native_mut
    );

    (Cow::Owned(selector), built)
}

fn build_document_handler(py_handlers: Py<PyAny>) -> NativeDocumentContentHandlers<'static> {
    let (doctype_cb, comments_cb, text_cb, end_cb): (
        Option<Py<PyAny>>,
        Option<Py<PyAny>>,
        Option<Py<PyAny>>,
        Option<Py<PyAny>>,
    ) = Python::attach(|py| {
        (
            opt_callable(py, &py_handlers, "doctype"),
            opt_callable(py, &py_handlers, "comments"),
            opt_callable(py, &py_handlers, "text"),
            opt_callable(py, &py_handlers, "end"),
        )
    });

    let mut built: NativeDocumentContentHandlers<'static> =
        NativeDocumentContentHandlers::default();

    attach_handler!(
        built,
        doctype,
        doctype_cb,
        lol_html::html_content::Doctype<'_>,
        PyDoctype,
        from_native_mut
    );
    attach_handler!(
        built,
        comments,
        comments_cb,
        lol_html::html_content::Comment<'_>,
        PyComment,
        from_native_mut
    );
    attach_handler!(
        built,
        text,
        text_cb,
        lol_html::html_content::TextChunk<'_>,
        PyTextChunk,
        from_native_mut
    );
    attach_handler!(
        built,
        end,
        end_cb,
        lol_html::html_content::DocumentEnd<'_>,
        PyDocumentEnd,
        from_native_mut
    );

    built
}

#[pyclass]
#[derive(Clone)]
pub struct HTMLRewriterOptions {
    #[pyo3(get, set)]
    pub enable_esi_tags: Option<bool>,
}

#[pymethods]
impl HTMLRewriterOptions {
    #[new]
    pub fn new(enable_esi_tags: Option<bool>) -> Self {
        HTMLRewriterOptions { enable_esi_tags }
    }
}

#[pyclass(unsendable)]
#[derive(Default)]
pub struct HTMLRewriter {
    selectors: Vec<Selector>,
    element_py_handlers: Vec<Py<PyAny>>,
    document_py_handlers: Vec<Py<PyAny>>,
    output_sink_cb: Option<Py<PyAny>>,
    inner: Option<NativeHTMLRewriter<'static, PythonOutputSink>>,
    inner_constructed: bool,
    enable_esi_tags: bool,
}

#[pymethods]
impl HTMLRewriter {
    #[new]
    #[pyo3(signature = (output_sink, options=None))]
    pub fn new(output_sink: Py<PyAny>, options: Option<HTMLRewriterOptions>) -> Self {
        HTMLRewriter {
            output_sink_cb: Some(output_sink),
            enable_esi_tags: options.and_then(|o| o.enable_esi_tags).unwrap_or(false),
            ..Self::default()
        }
    }

    pub fn on(&mut self, selector: &str, handlers: &Bound<PyAny>) -> PyResult<()> {
        self.assert_not_fully_constructed()?;

        let selector: Selector = selector
            .parse::<Selector>()
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

        let py_handlers: Py<PyAny> = handlers.extract()?;

        self.selectors.push(selector);
        self.element_py_handlers.push(py_handlers);

        Ok(())
    }

    #[pyo3(name = "on_document")]
    pub fn on_document(&mut self, handlers: &Bound<PyAny>) -> PyResult<()> {
        self.assert_not_fully_constructed()?;
        let py_handler: Py<PyAny> = handlers.extract()?;
        self.document_py_handlers.push(py_handler);
        Ok(())
    }

    pub fn write(&mut self, chunk: &Bound<PyAny>) -> PyResult<()> {
        let bytes: &[u8] = chunk
            .extract()
            .map_err(|_| PyRuntimeError::new_err("Expected a bytes-like object"))?;

        self.inner_mut()
            .and_then(|inner| inner.write(bytes).map_err(rewriting_error_to_py))?;

        Ok(())
    }

    pub fn end(&mut self) -> PyResult<()> {
        self.inner_mut()?;
        if let Some(inner) = self.inner.take() {
            inner.end().map_err(rewriting_error_to_py)?;
            Ok(())
        } else {
            Err(PyRuntimeError::new_err("Inner rewriter missing"))
        }
    }

    #[getter]
    pub fn constructed(&self) -> bool {
        self.inner_constructed
    }
}

impl HTMLRewriter {
    fn assert_not_fully_constructed(&self) -> PyResult<()> {
        if self.inner_constructed {
            Err(PyRuntimeError::new_err(
                "Handlers can't be added after write.",
            ))
        } else {
            Ok(())
        }
    }

    fn inner_mut(&mut self) -> Result<&mut NativeHTMLRewriter<'static, PythonOutputSink>, PyErr> {
        if let Some(ref mut inner) = self.inner {
            return Ok(inner);
        }

        let cb = match self.output_sink_cb.take() {
            Some(cb) => cb,
            None => return Err(PyRuntimeError::new_err("Output sink callback missing")),
        };

        let element_handlers_built: Vec<(
            Cow<'static, Selector>,
            NativeElementContentHandlers<'static>,
        )> = self
            .selectors
            .drain(..)
            .zip(self.element_py_handlers.drain(..))
            .map(|(selector, py_handlers)| build_element_handler_pair(selector, py_handlers))
            .collect();

        let document_handlers_built: Vec<NativeDocumentContentHandlers<'static>> = self
            .document_py_handlers
            .drain(..)
            .map(build_document_handler)
            .collect();

        let settings = Settings {
            element_content_handlers: element_handlers_built,
            document_content_handlers: document_handlers_built,
            enable_esi_tags: self.enable_esi_tags,
            ..Settings::default()
        };

        let output_sink = PythonOutputSink::new(cb);
        let rewriter = NativeHTMLRewriter::new(settings, output_sink);

        self.inner = Some(rewriter);
        self.inner_constructed = true;
        Ok(self.inner.as_mut().unwrap())
    }
}
