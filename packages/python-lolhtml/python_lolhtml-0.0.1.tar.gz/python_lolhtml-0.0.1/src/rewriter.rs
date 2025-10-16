use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyBytes, PyString};
use pyo3::PyClass;
use pyo3::PyErr;

use lol_html as lh;
use pyo3::pyclass::boolean_struct::False;
use std::cell::RefCell;
use std::ptr::NonNull;
use std::rc::Rc;

use crate::proxy::{Comment, Element, Invalidate, RawComment, RawElement, RawTextChunk, TextChunk};

#[pyclass(unsendable)]
pub struct HTMLRewriter {
    pub(crate) selectors: Vec<(String, Py<PyAny>)>,
}

#[pymethods]
impl HTMLRewriter {
    #[new]
    fn new() -> Self {
        HTMLRewriter {
            selectors: Vec::new(),
        }
    }

    fn on<'a>(mut slf: PyRefMut<'a, Self>, selector: &str, element_handler: Py<PyAny>) -> PyResult<PyRefMut<'a, Self>> {
        slf.selectors.push((selector.to_string(), element_handler));
        Ok(slf)
    }

    fn transform(&self, html: &Bound<PyAny>) -> PyResult<Py<PyAny>> {
        let py = html.py();
        let input_slice: &[u8] = if let Ok(s) = html.downcast::<PyString>() {
            s.to_str()?.as_bytes()
        } else if let Ok(b) = html.downcast::<PyBytes>() {
            b.as_bytes()
        } else {
            return Err(PyRuntimeError::new_err("transform() expects str or bytes"));
        };

        // Reserve roughly the input size for output buffer
        let mut output = Vec::<u8>::with_capacity(input_slice.len());

        // Build element handlers
        let mut ehandlers = Vec::with_capacity(self.selectors.len() * 3);

        // Shared cell to capture the first Python exception raised in any handler
        let captured_exc: Rc<RefCell<Option<PyErr>>> = Rc::new(RefCell::new(None));

        for (selector, handler) in &self.selectors {
            // element handler
            let sel_el = selector.clone();
            let handler_el = handler.clone_ref(py);
            let exc_el = captured_exc.clone();
            let eh = lh::element!(
                sel_el.as_str(),
                move |el: &mut lh::html_content::Element| {
                    Python::attach(|py| {
                        let py_el: Py<Element> = Py::new(
                            py,
                            Element {
                                ptr: Some(NonNull::from(el).cast::<RawElement>()),
                                alive: true,
                            },
                        )?;
                        dispatch_and_invalidate(py, &handler_el, "element", py_el, &exc_el);
                        Ok(())
                    })
                }
            );
            ehandlers.push(eh);

            // comments handler
            let sel_c = selector.clone();
            let handler_c = handler.clone_ref(py);
            let exc_c = captured_exc.clone();
            let ch = lh::comments!(sel_c.as_str(), move |c: &mut lh::html_content::Comment| {
                Python::attach(|py| {
                    let py_c: Py<Comment> = Py::new(
                        py,
                        Comment {
                            ptr: Some(NonNull::from(c).cast::<RawComment>()),
                            alive: true,
                        },
                    )?;
                    dispatch_and_invalidate(py, &handler_c, "comments", py_c, &exc_c);
                    Ok(())
                })
            });
            ehandlers.push(ch);

            // text handler
            let sel_t = selector.clone();
            let handler_t = handler.clone_ref(py);
            let exc_t = captured_exc.clone();
            let th = lh::text!(
                sel_t.as_str(),
                move |t: &mut lh::html_content::TextChunk| {
                    Python::attach(|py| {
                        let py_t: Py<TextChunk> = Py::new(
                            py,
                            TextChunk {
                                ptr: Some(NonNull::from(t).cast::<RawTextChunk>()),
                                alive: true,
                            },
                        )?;
                        dispatch_and_invalidate(py, &handler_t, "text", py_t, &exc_t);
                        Ok(())
                    })
                }
            );
            ehandlers.push(th);
        }

        let mut rewriter = lh::HtmlRewriter::new(
            lh::Settings {
                element_content_handlers: ehandlers,
                ..lh::Settings::new()
            },
            |c: &[u8]| {
                output.extend_from_slice(c);
            },
        );

        rewriter
            .write(input_slice)
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;
        rewriter
            .end()
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

        // If a Python exception occurred in any handler, raise it now
        if let Some(err) = captured_exc.borrow_mut().take() {
            return Err(err);
        }

        let result: Py<PyBytes> = PyBytes::new(py, &output).unbind();
        Ok(result.into_any())
    }
}

fn dispatch_and_invalidate<T>(
    py: Python<'_>,
    handler_obj: &Py<PyAny>,
    method_name: &str,
    arg: Py<T>,
    captured_exc: &Rc<RefCell<Option<PyErr>>>,
) where
    T: Invalidate + PyClass<Frozen = False>,
{
    let obj = handler_obj.bind(py);
    if let Ok(method) = obj.getattr(method_name) {
        let passed = arg.clone_ref(py);
        if let Err(e) = method.call1((passed,)) {
            if captured_exc.borrow().is_none() {
                *captured_exc.borrow_mut() = Some(e);
            }
        }
    }

    // Invalidate after callback regardless of success
    let bound = arg.bind(py);
    let mut inner = bound.borrow_mut();
    inner.invalidate();
}
