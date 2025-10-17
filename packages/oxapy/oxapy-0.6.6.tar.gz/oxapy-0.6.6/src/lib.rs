mod catcher;
mod cors;
mod exceptions;
mod into_response;
mod json;
#[cfg(not(target_arch = "aarch64"))]
mod jwt;
mod macros;
mod middleware;
mod multipart;
mod request;
mod response;
mod routing;
mod serializer;
mod session;
mod status;
mod templating;

use std::net::SocketAddr;
use std::ops::Deref;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

use crate::catcher::Catcher;
use crate::cors::Cors;
use crate::multipart::File;
use crate::request::{Request, RequestBuilder};
use crate::response::{FileStreaming, Redirect, Response};
use crate::routing::*;
use crate::session::{Session, SessionStore};
use crate::status::Status;
use crate::templating::Template;

use ahash::HashMap;
use hyper::server::conn::http1;
use hyper::service::service_fn;
use hyper_util::rt::TokioIo;
use middleware::MiddlewareChain;
use pyo3::exceptions::PyValueError;
use pyo3::types::{PyDict, PyInt, PyString};
use pyo3_async_runtimes::tokio::{future_into_py, into_future};
use pyo3_stub_gen::derive::*;
use tokio::net::TcpListener;
use tokio::sync::mpsc::{channel, Sender};
use tokio::sync::Semaphore;

use pyo3::{exceptions::PyException, prelude::*};

trait IntoPyException<T> {
    fn into_py_exception(self) -> PyResult<T>;
}

impl<T, E: ToString> IntoPyException<T> for Result<T, E> {
    fn into_py_exception(self) -> PyResult<T> {
        self.map_err(|err| PyException::new_err(err.to_string()))
    }
}

struct ProcessRequest {
    request: Arc<Request>,
    router: Option<Arc<Router>>,
    match_route: Option<MatchRoute<'static>>,
    tx: Sender<Response>,
    cors: Option<Arc<Cors>>,
    catchers: Option<Arc<HashMap<Status, Py<PyAny>>>>,
}

#[derive(Clone)]
struct RequestContext {
    request_sender: Sender<ProcessRequest>,
    routers: Vec<Arc<Router>>,
    channel_capacity: usize,
    cors: Option<Arc<Cors>>,
    catchers: Option<Arc<HashMap<Status, Py<PyAny>>>>,
}

/// HTTP Server for handling web requests.
///
/// The HttpServer is the main entry point for creating web applications with OxAPY.
/// It manages routers, middleware, templates, sessions, and other components.
///
/// Args:
///     addr (tuple): A tuple containing the IP address and port to bind to.
///
/// Returns:
///     HttpServer: A new server instance.
///
/// Example:
/// ```python
/// from oxapy import HttpServer, Router
///
/// # Create a server on localhost port 8000
/// app = HttpServer(("127.0.0.1", 8000))
///
/// # Create a router
/// router = Router()
///
/// # Define route handlers
/// @router.get("/")
/// def home(request):
///     return "Hello, World!"
///
/// @router.get("/users/{user_id}")
/// def get_user(request, user_id: int):
///     return {"user_id": user_id, "name": f"User {user_id}"}
///
/// @router.post("/api/data")
/// def create_data(request):
///     # Access JSON data from the request
///     data = request.json()
///     return {"status": "success", "received": data}
///
/// # Attach the router to the server
/// app.attach(router)
///
/// # Run the server
/// app.run()
///     ```
#[gen_stub_pyclass]
#[pyclass]
#[derive(Clone)]
struct HttpServer {
    addr: SocketAddr,
    routers: Vec<Arc<Router>>,
    app_data: Option<Arc<Py<PyAny>>>,
    max_connections: Arc<Semaphore>,
    channel_capacity: usize,
    cors: Option<Arc<Cors>>,
    template: Option<Arc<Template>>,
    session_store: Option<Arc<SessionStore>>,
    catchers: Option<Arc<HashMap<Status, Py<PyAny>>>>,
    is_async: bool,
}

#[gen_stub_pymethods]
#[pymethods]
impl HttpServer {
    /// Create a new instance of HttpServer.
    ///
    /// Args:
    ///     addr (tuple): A tuple containing (ip_address: str, port: int)
    ///
    /// Returns:
    ///     HttpServer: A new server instance ready to be configured.
    ///
    /// Example:
    /// ```python
    /// server = HttpServer(("127.0.0.1", 5555))
    /// ```
    #[new]
    fn new(addr: (String, u16)) -> PyResult<Self> {
        let (ip, port) = addr;
        Ok(Self {
            addr: SocketAddr::new(ip.parse()?, port),
            routers: Vec::new(),
            app_data: None,
            max_connections: Arc::new(Semaphore::new(100)),
            channel_capacity: 100,
            cors: None,
            template: None,
            session_store: None,
            catchers: None,
            is_async: false,
        })
    }

    /// Set application-wide data that will be available to all request handlers.
    ///
    /// This is the perfect place to store shared resources like database connection pools,
    /// counters, or any other data that needs to be accessible across your application.
    ///
    /// Args:
    ///     app_data (any): Any Python object to be stored as application data.
    ///
    /// Returns:
    ///     None
    ///
    /// Example:
    /// ```python
    /// class AppState:
    ///     def __init__(self):
    ///         self.counter = 0
    ///         # You can store database connection pools here
    ///         self.db_pool = create_database_pool()
    ///
    /// app = HttpServer(("127.0.0.1", 5555))
    /// app.app_data(AppState())
    ///
    /// # Example of a handler that increments the counter
    /// @router.get("/counter")
    /// def increment_counter(request):
    ///     state = request.app_data
    ///     state.counter += 1
    ///     return {"count": state.counter}
    /// ```
    fn app_data(&mut self, app_data: Py<PyAny>) {
        self.app_data = Some(Arc::new(app_data))
    }

    /// Attach a router to the server.
    ///
    /// Args:
    ///     router (Router): The router instance to attach.
    ///
    /// Returns:
    ///     None
    ///
    /// Example:
    /// ```python
    /// router = Router()
    ///
    /// # Define a simple hello world handler
    /// @router.get("/")
    /// def hello(request):
    ///     return "Hello, World!"
    ///
    /// # Handler with path parameters
    /// @router.get("/users/{user_id}")
    /// def get_user(request, user_id: int):
    ///     return f"User ID: {user_id}"
    ///
    /// # Handler that returns JSON
    /// @router.get("/api/data")
    /// def get_data(request):
    ///     return {"message": "Success", "data": [1, 2, 3]}
    ///
    /// # Attach the router to the server
    /// server.attach(router)
    /// ```
    fn attach(&mut self, router: Router) {
        self.routers.push(Arc::new(router));
    }

    /// Set up a session store for managing user sessions.
    ///
    /// When configured, session data will be available in request handlers.
    ///
    /// Args:
    ///     session_store (SessionStore): The session store instance to use.
    ///
    /// Returns:
    ///     None
    ///
    /// Example:
    /// ```python
    /// server.session_store(SessionStore())
    /// ```
    fn session_store(&mut self, session_store: SessionStore) {
        self.session_store = Some(Arc::new(session_store));
    }

    /// Enable template rendering for the server.
    ///
    /// Args:
    ///     template (Template): An instance of Template for rendering HTML.
    ///
    /// Returns:
    ///     None
    ///
    /// Example:
    /// ```python
    /// from oxapy import templating
    ///
    /// server.template(templating.Template())
    /// ```
    fn template(&mut self, template: Template) {
        self.template = Some(Arc::new(template))
    }

    /// Set up Cross-Origin Resource Sharing (CORS) for the server.
    ///
    /// Args:
    ///     cors (Cors): An instance of Cors with your desired CORS configuration.
    ///
    /// Returns:
    ///     None
    ///
    /// Example:
    /// ```python
    /// cors = Cors()
    /// cors.origins = ["https://example.com"]
    /// server.cors(cors)
    /// ```
    fn cors(&mut self, cors: Cors) {
        self.cors = Some(Arc::new(cors));
    }

    /// Set the maximum number of concurrent connections the server will handle.
    ///
    /// Args:
    ///     max_connections (int): Maximum number of concurrent connections.
    ///
    /// Returns:
    ///     None
    ///
    /// Example:
    /// ```python
    /// server.max_connections(1000)
    /// ```
    fn max_connections(&mut self, max_connections: usize) {
        self.max_connections = Arc::new(Semaphore::new(max_connections));
    }

    /// Set the internal channel capacity for handling requests.
    ///
    /// This is an advanced setting that controls how many pending requests
    /// can be buffered internally.
    ///
    /// Args:
    ///     channel_capacity (int): The channel capacity.
    ///
    /// Returns:
    ///     None
    ///
    /// Example:
    /// ```python
    /// server.channel_capacity(200)
    /// ```
    fn channel_capacity(&mut self, channel_capacity: usize) {
        self.channel_capacity = channel_capacity;
    }

    /// Add status code catchers to the server.
    ///
    /// Args:
    ///     catchers (list): A list of Catcher handlers for specific status codes.
    ///
    /// Returns:
    ///     None
    ///
    /// Example:
    /// ```python
    /// @catcher(Status.NOT_FOUND)
    /// def not_found(request, response):
    ///     return Response("<h1>Page Not Found</h1>", content_type="text/html")
    ///
    /// server.catchers([not_found])
    /// ```
    fn catchers(&mut self, catchers: Vec<PyRef<Catcher>>, py: Python<'_>) {
        let mut map = HashMap::default();

        for catcher in catchers {
            map.insert(catcher.status, catcher.handler.clone_ref(py));
        }

        self.catchers = Some(Arc::new(map))
    }

    /// Enable asynchronous mode for the server.
    ///
    /// In asynchronous mode, request handlers can be asynchronous Python functions
    /// (i.e., defined with `async def`). This allows you to perform non-blocking
    /// I/O operations within your handlers.
    ///
    /// Returns:
    ///     HttpServer: A new HttpServer instance configured for asynchronous operation.
    ///
    /// Example:
    /// ```python
    /// import asyncio
    /// app = HttpServer(("127.0.0.1", 8000))
    ///
    /// @router.get("/")
    /// async def home(request):
    ///     # Asynchronous operations are allowed here
    ///     data = await fetch_data_from_database()
    ///     return "Hello, World!"
    ///
    /// app.attach(router)
    ///
    /// await def main():
    ///     await app.async_mode().run()
    ///
    /// asyncio.run(main())
    /// ```
    fn async_mode(&mut self) -> Self {
        self.is_async = true;
        self.clone()
    }

    /// Run the HTTP server.
    ///
    /// This starts the server and blocks until interrupted (e.g., with Ctrl+C).
    ///
    /// Args:
    ///     workers (int, optional): Number of worker threads to use. If not specified,
    ///                              the Tokio runtime will decide automatically.
    ///
    /// Returns:
    ///     None
    ///
    /// Example:
    /// ```python
    /// # Run with default number of workers
    /// server.run()
    ///
    /// # Or specify number of workers based on CPU count
    /// import multiprocessing
    /// workers = multiprocessing.cpu_count()
    /// server.run(workers)
    /// ```
    #[pyo3(signature=(workers=None))]
    fn run<'l>(&'l self, workers: Option<usize>, py: Python<'l>) -> PyResult<Bound<'l, PyAny>> {
        let server = self.clone();
        if self.is_async {
            future_into_py(py, async move { server.run_server().await })
        } else {
            py.detach(move || block_on(server.run_server(), workers));
            Ok(py.None().into_bound(py))
        }
    }
}

impl HttpServer {
    async fn run_server(&self) -> PyResult<()> {
        let running = Arc::new(AtomicBool::new(true));
        let r = running.clone();
        let addr = self.addr;
        let channel_capacity = self.channel_capacity;

        let (tx, mut rx) = channel::<ProcessRequest>(channel_capacity);
        let (kill_tx, mut kill_rx) = channel::<()>(1);

        ctrlc::set_handler(move || {
            println!("\nReceived Ctrl+C! Shutting Down...");
            r.store(false, Ordering::SeqCst);
            block_on(kill_tx.send(()), None);
        })
        .into_py_exception()?;

        let listener = TcpListener::bind(addr).await?;
        println!("Listening on {}", addr);

        let running_clone = running.clone();
        let max_connections = self.max_connections.clone();

        let request_ctx = RequestContext {
            routers: self.routers.clone(),
            request_sender: tx.clone(),
            cors: self.cors.clone(),
            channel_capacity,
            catchers: self.catchers.clone(),
        };

        let app_data = self.app_data.clone();
        let template = self.template.clone();
        let session_store = self.session_store.clone();

        tokio::spawn(async move {
            while running_clone.load(Ordering::SeqCst) {
                let permit = max_connections.clone().acquire_owned().await.unwrap();
                let (stream, _) = listener.accept().await.unwrap();
                let io = TokioIo::new(stream);

                let request_ctx = request_ctx.clone();
                let app_data = app_data.clone();
                let template = template.clone();
                let session_store = session_store.clone();

                tokio::spawn(async move {
                    let _permit = permit;
                    http1::Builder::new()
                        .serve_connection(
                            io,
                            service_fn(move |req| {
                                let request_ctx = request_ctx.clone();
                                let app_data = app_data.clone();
                                let template = template.clone();
                                let session_store = session_store.clone();

                                async move {
                                    let request = RequestBuilder::new(req)
                                        .with_app_data(app_data)
                                        .with_template(template)
                                        .with_session_store(session_store)
                                        .build()
                                        .await
                                        .unwrap();
                                    request.handle(request_ctx).await
                                }
                            }),
                        )
                        .await
                        .into_py_exception()
                });
            }
        });

        loop {
            tokio::select! {
                Some(pros_req) = rx.recv() => {
                    let mut response = call_python_handler(
                            pros_req.router,
                            pros_req.match_route,
                            pros_req.request.deref().clone(),
                            self.is_async,
                        ).await
                    .unwrap_or_else(Response::from);

                    if let Some(catchers) = pros_req.catchers {
                        if let Some(handler) = catchers.get(&response.status)  {
                            let request: Request = pros_req.request.as_ref().clone();
                            response = Python::attach(|py|{
                                let result = handler.call(py, (request, response), None)?;
                                into_response::convert_to_response(result, py)
                            })
                            .unwrap_or_else(Response::from);
                        }
                    }

                    if let (Some(session), Some(store)) =
                        (&pros_req.request.session, &pros_req.request.session_store)
                    {
                        let cookie_header = store.get_cookie_header(session);
                        response.insert_or_append_cookie(cookie_header);
                    }

                    if let Some(cors) = pros_req.cors {
                        response = cors.apply_to_response(response)?;
                    }

                    pros_req.tx.send(response).await.ok();
                }
                _ = kill_rx.recv() => {break}
            }
        }

        Ok(())
    }
}

async fn call_python_handler<'l>(
    router: Option<Arc<Router>>,
    match_route: Option<MatchRoute<'l>>,
    request: Request,
    is_async: bool,
) -> PyResult<Response> {
    match (match_route, router) {
        (Some(route), Some(router)) => {
            let params = route.params;
            let route = route.value;

            let mut result = Python::attach(|py| {
                let kwargs = PyDict::new(py);

                for (key, value) in params.iter() {
                    match key.split_once(":") {
                        Some((name, ty)) => {
                            let parsed_value: Py<PyAny> = match ty {
                                "int" => PyInt::new(kwargs.py(), value.parse::<i64>()?).into(),
                                "str" => PyString::new(kwargs.py(), value).into(),
                                other => {
                                    let message = format!("Unsupported type annotation '{other}' in parameter key '{key}'.");
                                    return Err(PyValueError::new_err(message));
                                }
                            };
                            kwargs.set_item(name, parsed_value)?;
                        }
                        _ => kwargs.set_item(key, value)?,
                    }
                }

                Python::attach(|py| {
                    if router.middlewares.is_empty() {
                        route.handler.call(py, (request,), Some(&kwargs))
                    } else {
                        let chain = MiddlewareChain::new(router.middlewares.clone());
                        chain.execute(py, route.handler.deref(), (request,), kwargs.clone())
                    }
                })
            })?;

            if is_async {
                result = Python::attach(|py| into_future(result.into_bound(py)))?.await?
            }

            Python::attach(|py| into_response::convert_to_response(result, py))
        }
        _ => Ok(Status::NOT_FOUND.into()),
    }
}

fn block_on<F: std::future::Future>(future: F, workers: Option<usize>) {
    let mut runtime = tokio::runtime::Builder::new_multi_thread();
    workers.map(|w| runtime.worker_threads(w));
    runtime.enable_all().build().unwrap().block_on(future);
}

pyo3_stub_gen::define_stub_info_gatherer!(stub_info);

#[pymodule]
fn oxapy(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<HttpServer>()?;
    m.add_class::<Router>()?;
    m.add_class::<Status>()?;
    m.add_class::<Response>()?;
    m.add_class::<Request>()?;
    m.add_class::<Cors>()?;
    m.add_class::<Session>()?;
    m.add_class::<SessionStore>()?;
    m.add_class::<Redirect>()?;
    m.add_class::<File>()?;
    m.add_class::<FileStreaming>()?;
    m.add_function(wrap_pyfunction!(get, m)?)?;
    m.add_function(wrap_pyfunction!(post, m)?)?;
    m.add_function(wrap_pyfunction!(delete, m)?)?;
    m.add_function(wrap_pyfunction!(patch, m)?)?;
    m.add_function(wrap_pyfunction!(put, m)?)?;
    m.add_function(wrap_pyfunction!(head, m)?)?;
    m.add_function(wrap_pyfunction!(options, m)?)?;
    m.add_function(wrap_pyfunction!(static_file, m)?)?;
    m.add_function(wrap_pyfunction!(catcher::catcher, m)?)?;
    m.add_function(wrap_pyfunction!(into_response::convert_to_response, m)?)?;

    json::init_orjson(m.py())?;
    templating::templating_submodule(m)?;
    serializer::serializer_submodule(m)?;
    exceptions::exceptions(m)?;

    #[cfg(not(target_arch = "aarch64"))]
    jwt::jwt_submodule(m)?;

    Ok(())
}
