use std::sync::Arc;

use pyo3::{call::PyCallArgs, ffi::c_str, prelude::*, types::PyDict, Py, PyAny, PyResult, Python};

#[derive(Clone, Debug)]
pub struct Middleware {
    handler: Arc<Py<PyAny>>,
}

impl Middleware {
    pub fn new(handler: Py<PyAny>) -> Self {
        Self {
            handler: Arc::new(handler),
        }
    }
}

pub struct MiddlewareChain {
    middlewares: Vec<Middleware>,
}

impl MiddlewareChain {
    pub fn new(middlewares: Vec<Middleware>) -> Self {
        Self { middlewares }
    }

    pub fn execute<'py, A>(
        &self,
        py: Python<'py>,
        route_handler: &Py<PyAny>,
        args: A,
        kwargs: Bound<'py, PyDict>,
    ) -> PyResult<Py<PyAny>>
    where
        A: PyCallArgs<'py>,
    {
        let handler = self.build_middleware_chain(py, route_handler, 0)?;
        handler.call(py, args, Some(&kwargs))
    }

    fn build_middleware_chain(
        &self,
        py: Python<'_>,
        route_handler: &Py<PyAny>,
        index: usize,
    ) -> PyResult<Py<PyAny>> {
        if index >= self.middlewares.len() {
            return Ok(route_handler.clone_ref(py));
        }
        let middleware = &self.middlewares[index];
        let next = self.build_middleware_chain(py, route_handler, index + 1)?;
        let globals = PyDict::new(py);
        globals.set_item("middleware", middleware.handler.clone_ref(py))?;
        globals.set_item("next", next)?;
        let wrapper_code =
            c_str!(r#"lambda *args, **kwargs: middleware(next=next, *args, **kwargs)"#);
        let wrapper = py.eval(wrapper_code, Some(&globals), None)?;
        Ok(wrapper.into())
    }
}
