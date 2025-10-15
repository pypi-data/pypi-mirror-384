# bbwebservice

`bbwebservice` is a lightweight Python library for building small webservers. It keeps the original simplicity but now ships with multi-endpoint support, chunked request handling, scoped routing and a bounded worker pool.

## Installation

```bash
pip install bbwebservice
```

## Usage

- import helpers:

```python
from bbwebservice.webserver import *
from bbwebservice import core
```

### 1. Register pages for HTTP `GET`
   - `@register(route=..., type=...)` registers a handler for a GET route.
   - `route` accepts either a plain string or the selector syntax `ip:port::domain:/path`. Examples:
     * `'::/status'` – matches every endpoint
     * `'127.0.0.1::/debug'` – IPv4 127.0.0.1 on any port and any domain
     * `':::example.com:/info'` – any IP/port, only domain `example.com`
     * `UrlTemplate('[::1]:8000::/v1/{slug:str}')` – IPv6 with typed placeholders
   - `type` specifies the MIME type of the response.

```python
@register(route='::/hello', type=MIME_TYPE.TEXT)
def hello():
    return 'Hello World'
```

### 2. Register pages for HTTP `POST`
   - `@post_handler` works like `@register` but the decorated function must accept an `args` parameter.

```python
@post_handler(route='::/login', type=MIME_TYPE.JSON)
def login(args):
    payload = args[STORE_VARS.POST].decode('utf-8')
    return {'status': 'ok', 'raw': payload}
```

### 3. Redirects
   - Return a `Redirect` object to send 303/307 style responses.

```python
@register(route='::/old', type=MIME_TYPE.HTML)
def legacy():
    return Redirect('/new')
```

### 4. Partial content / streaming
   - Use `PartialContent` for ranged responses (video, downloads, etc.).

```python
@register(route='::/video', type=MIME_TYPE.MP4)
def video(_):
    return PartialContent('/content/movie.mp4', default_size=80_000)
```

### 5. Error handler
   - `@error_handler(error_code=..., type=...)` provides fallback pages.

```python
@error_handler(error_code=404, type=MIME_TYPE.HTML)
def not_found():
    return load_file('/content/404.html')
```

### 6. Handler arguments
   - Handlers that accept args can read or modify cookies, headers, query strings, etc.

```python
@register(route='::/inspect', type=MIME_TYPE.JSON)
def inspect(args):
    args['response'].header.add_header_line(
        Header_Line(Response_Header_Tag.SERVER, 'bbwebservice')
    )
    return args
```

### 7. Start the server
   - Use `core.start()` to launch all configured listeners.

```python
@register(route='::/index', type=MIME_TYPE.HTML)
def index():
    return load_file('/content/index.html')

core.start()
```

### 8. URL templates
   - Dynamic routes use `UrlTemplate` with typed placeholders.

| Supported Types | Example             |
|-----------------|--------------------|
| `str`           | `{name:str}`       |
| `int`           | `{id:int}`         |
| `float`         | `{value:float}`    |
| `bool`          | `{flag:bool}`      |
| `path`          | `{path:path}`      |

```python
@register(route=UrlTemplate('::/user/{name:str}/{age:int}'), type=MIME_TYPE.JSON)
def user(args):
    return args[STORE_VARS.TEMPLATE_VARS]
```

### 9. Selector hierarchy
   - The most specific selector wins automatically (IP > port > domain > global). Register routes knowing that concrete bindings take precedence over generic ones.

### 10. Response helpers
   - In addition to returning bytes/strings, you can respond with:
     * `Dynamic(content, mime_type)` – content with a custom MIME type
     * `PartialContent` / `Redirect`
     * `Response(...)` – convenience for setting status, headers, body in one object

### 11. Background tasks
   - `server_task(func, interval)` schedules functions (receives global state if `data` parameter present). Tasks shut down gracefully with the server.

### 12. CORS
   - Enable or disable at runtime:

```python
webserver.enable_cors(
    allow_origin="*",
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    expose_headers=["X-Total-Count"],
    allow_credentials=False,
    max_age=600,
)
```

`disable_cors()` and `get_cors_settings()` are provided as well. OPTIONS requests are answered automatically when CORS is active.

### 13. Worker pool and backpressure
   - All listeners share a bounded worker pool. If the queue is full, new connections get `503 Service Unavailable`. Per-listener `max_threads` throttle accept loops, while the global `max_threads` (see config) bounds total concurrency.

### 14. Request parsing
   - Headers are read incrementally up to `max_header_size`, bodies honour `Content-Length` or `Transfer-Encoding: chunked` (trailers are skipped). Chunked data is decoded into the `args[STORE_VARS.POST]` buffer. Oversized requests trigger 413/431 responses.

### 15. Logging
   - Logging honours scopes (`ip:port::domain`) and only formats messages when a sink is active.

```python
set_logging(LOGGING_OPTIONS.INFO, True)
log_to_file('/logs/server.log', [LOGGING_OPTIONS.ERROR, LOGGING_OPTIONS.INFO])
set_logging_callback(lambda msg, ts, lvl: print('[callback]', lvl, msg))
```

There is also `webserver.response()` for building structured responses and `log()` for manual logging with scopes.

## Server Configuration

`config/config.json` controls listeners and limits:

```json
{
  "max_threads": 100,
  "max_header_size": 16384,
  "max_body_size": 10485760,
  "server": [
    {
      "ip": "default",
      "port": 5000,
      "queue_size": 50,
      "max_threads": 25,
      "SSL": false,
      "host": "",
      "cert_path": "",
      "key_path": "",
      "https-redirect": false,
      "https-redirect-escape-paths": [],
      "update-cert-state": false
    }
  ]
}
```

* `ip`: `default` resolves at runtime, otherwise explicit IPv4/IPv6 (use `[::1]` style).
* Multiple entries in `server` bind additional sockets.
* `SSL` with `host` as list enables SNI (each entry supplies `host`, `cert_path`, `key_path`). Failed certificates are logged with full paths.
* `https-redirect` forces 301 to HTTPS except for paths listed in `https-redirect-escape-paths` (supports wildcard suffix `*`).
* `update-cert-state` watches certificate files and reloads them automatically.

Recommended ports: 5000 (local), 80 (HTTP), 443/8443 (HTTPS).

## Logging recap

```python
set_logging(LOGGING_OPTIONS.DEBUG, True)
set_logging(LOGGING_OPTIONS.TIME, True)
log_to_file()
```

Use `set_logging(scope='127.0.0.1:5000::example.com', ...)` to target specific endpoints.

## Testing

Run the integration script:

```bash
python testing/test_bbwebservice_example.py
```

It covers chunked uploads, CORS preflights, domain/IP selectors and redirects.

## License

MIT License © Lukas Walker (see `LICENSE` for details).
