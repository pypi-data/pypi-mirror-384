use pyo3::prelude::*;

mod proxy;
mod rewriter;

pub use proxy::{Comment, Element, TextChunk};
pub use rewriter::HTMLRewriter;

#[pymodule]
fn lolhtml(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<HTMLRewriter>()?;
    m.add_class::<Element>()?;
    m.add_class::<Comment>()?;
    m.add_class::<TextChunk>()?;
    Ok(())
}
