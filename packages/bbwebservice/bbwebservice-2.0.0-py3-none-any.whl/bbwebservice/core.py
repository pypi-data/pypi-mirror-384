import socket
from threading import Thread, Event, current_thread, Lock
import ssl
import os
import time
from queue import Queue, Empty, Full
from .config_loader import Config
from .http_parser import HTTP_Message_Factory, log, LOGGING_OPTIONS, LOGGING_CALLBACK, LOGGING_SCOPED_OPTIONS, LOGGING_SCOPED_CALLBACKS
import traceback
from .url_utils import format_ip_port


SSL_CONTEXTS = {}
SESSIONS = {}
PAGES = {}
GET_TEMPLATES = []
POST_HANDLER = {}
POST_TEMPLATES = []
ERROR_HANDLER = {}
ROUTES = {
    'GET': {'static': {}, 'templates': []},
    'POST': {'static': {}, 'templates': []}
}
SERVER_THREADS = []
CORS_SETTINGS = {
    'enabled': False,
    'allow_origin': '*',
    'allow_methods': ['GET', 'POST', 'OPTIONS'],
    'allow_headers': ['*'],
    'expose_headers': [],
    'allow_credentials': False,
    'max_age': 600,
}

CONFIG = Config()
SERVER_MANAGER = None


class WorkerPool:
    def __init__(self, max_workers: int, max_queue: int):
        self.queue: Queue = Queue(max_queue)
        self.max_workers = max_workers
        self.shutdown_event = Event()
        self.lock = Lock()
        self.active = 0
        self.workers: list[Thread] = []
        for _ in range(max_workers):
            worker = Thread(target=self._worker, daemon=True)
            worker.start()
            self.workers.append(worker)

    def _worker(self):
        while not self.shutdown_event.is_set():
            try:
                task = self.queue.get(timeout=0.5)
            except Empty:
                continue
            if task is None:
                self.queue.task_done()
                break
            func, args = task
            with self.lock:
                self.active += 1
            try:
                func(*args)
            finally:
                with self.lock:
                    self.active -= 1
                self.queue.task_done()

    def submit(self, func, *args) -> bool:
        try:
            self.queue.put_nowait((func, args))
            return True
        except Full:
            return False

    def shutdown(self):
        self.shutdown_event.set()
        for _ in self.workers:
            self.queue.put(None)
        for worker in self.workers:
            worker.join(timeout=1)
        while True:
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except Empty:
                break

    @property
    def active_count(self) -> int:
        with self.lock:
            return self.active

    @property
    def queue_length(self) -> int:
        return self.queue.qsize()


class ScheduledTask:
    def __init__(self, manager, func, interval):
        self.manager = manager
        self.func = func
        self.interval = max(interval, 0)
        self.state = Event()
        self.thread = None
        self._expects_data = False
        if hasattr(func, '__code__'):
            arg_count = func.__code__.co_argcount
            arg_names = func.__code__.co_varnames[:arg_count]
            self._expects_data = 'data' in arg_names

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.state.set()
        self.thread = Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.state.clear()
        if self.thread:
            self.thread.join(timeout=1)
            self.thread = None

    def _run(self):
        while self.state.is_set():
            try:
                if self._expects_data:
                    self.func(data=self.manager.build_task_data())
                else:
                    self.func()
            except Exception as err:
                log(f'[SERVER TASK] error: {err}', log_lvl='debug')
                traceback.print_exc()
            if not self.state.is_set():
                break
            if self.interval == 0:
                self.state.wait(0.1)
                continue
            self.state.wait(self.interval)


class ServerInstance:
    def __init__(self, manager, settings):
        self.manager = manager
        self.settings = settings
        self.ip = settings['ip']
        self.port = settings['port']
        self.queue_size = settings['queue_size']
        self.max_threads = settings.get('max_threads', manager.global_max_threads)
        self.ssl_enabled = settings['SSL']
        self.host_entries = settings.get('host', [])
        self.cert_path = settings.get('cert_path', '')
        self.key_path = settings.get('key_path', '')
        self.https_redirect = settings.get('https-redirect', False)
        self.https_redirect_escape_paths = settings.get('https-redirect-escape-paths', [])
        self.update_cert_state = settings.get('update-cert-state', False)
        self.state = Event()
        self.server_socket = None
        self.thread = None
        self.worker_handles = []
        self.lock = Lock()
        self.active_connections = 0
        self.ssl_context = None
        self.sni_contexts = {}
        self._cert_monitor_state = Event()
        self._cert_monitor_thread = None
        self._cert_sources = []
        self.bound_ip = None
        self.address_family = socket.AF_INET

    def _resolve_ip(self):
        if self.ip == 'default':
            resolved = socket.gethostbyname(socket.gethostname())
        else:
            resolved = self.ip
        if isinstance(resolved, str) and resolved.startswith('[') and resolved.endswith(']'):
            resolved = resolved[1:-1]
        return resolved

    def _record_cert_source(self, name, cert_path, key_path, context):
        if not cert_path or not key_path:
            return
        cert_mtime = None
        key_mtime = None
        try:
            cert_mtime = os.path.getmtime(cert_path)
        except OSError:
            pass
        try:
            key_mtime = os.path.getmtime(key_path)
        except OSError:
            pass
        self._cert_sources.append({
            'name': name,
            'cert_path': cert_path,
            'key_path': key_path,
            'context': context,
            'cert_mtime': cert_mtime,
            'key_mtime': key_mtime,
        })

    def _init_ssl_contexts(self, server_socket):
        try:
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            if self.cert_path and self.key_path:
                try:
                    self.ssl_context.load_cert_chain(certfile=self.cert_path, keyfile=self.key_path)
                except Exception as err:
                    log(f"[SERVER] failed to load default certificate ({self.cert_path}, {self.key_path}): {err}", log_lvl='error')
                    raise
                endpoint = format_ip_port(self.bound_ip, self.port)
                self._record_cert_source(endpoint or '', self.cert_path, self.key_path, self.ssl_context)
            self.sni_contexts = {}
            if self.host_entries:
                for host in self.host_entries:
                    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                    try:
                        ctx.load_cert_chain(certfile=host['cert_path'], keyfile=host['key_path'])
                    except Exception as err:
                        log(f"[SERVER] failed to load SNI certificate for {host['host']} ({host['cert_path']}, {host['key_path']}): {err}", log_lvl='error')
                        continue
                    self.sni_contexts[host['host']] = ctx
                    SSL_CONTEXTS[host['host']] = ctx
                    self._record_cert_source(host['host'], host['cert_path'], host['key_path'], ctx)

                def _sni_callback(sock, server_name, context):
                    new_context = self.sni_contexts.get(server_name)
                    if new_context:
                        sock.context = new_context
                        log(f'[SNI CALLBACK] Loaded certificate for {server_name}', log_lvl='debug')
                    else:
                        log(f'[SNI CALLBACK] Unknown server name: {server_name}', log_lvl='debug')

                self.ssl_context.sni_callback = _sni_callback

            SSL_CONTEXTS[format_ip_port(self.bound_ip, self.port) or ''] = self.ssl_context
            wrapped = self.ssl_context.wrap_socket(server_socket, server_side=True)
            log(f'[SERVER] ssl active on {format_ip_port(self.bound_ip, self.port)}', log_lvl='debug')
            return wrapped
        except Exception as err:
            log(f'[SERVER] error starting ssl: {err}', log_lvl='debug')
            traceback.print_exc()
            raise

    def _start_cert_monitor(self):
        if not self.update_cert_state or not self.ssl_enabled:
            return
        self._cert_monitor_state.set()
        self._cert_monitor_thread = Thread(target=self._cert_monitor_loop, daemon=True)
        self._cert_monitor_thread.start()

    def _stop_cert_monitor(self):
        if not self._cert_monitor_thread:
            return
        self._cert_monitor_state.clear()
        self._cert_monitor_thread.join(timeout=1)
        self._cert_monitor_thread = None

    def _cert_monitor_loop(self):
        while self._cert_monitor_state.is_set():
            for source in self._cert_sources:
                cert_path = source['cert_path']
                key_path = source['key_path']
                context = source['context']
                if not cert_path or not key_path:
                    continue
                try:
                    cert_mtime = os.path.getmtime(cert_path)
                    key_mtime = os.path.getmtime(key_path)
                except OSError:
                    continue
                if cert_mtime != source['cert_mtime'] or key_mtime != source['key_mtime']:
                    try:
                        context.load_cert_chain(certfile=cert_path, keyfile=key_path)
                        source['cert_mtime'] = cert_mtime
                        source['key_mtime'] = key_mtime
                        log(f'[CERT REFRESH] Reloaded certificate for {source["name"]}', log_lvl='debug')
                    except Exception as err:
                        log(f'[CERT REFRESH] Failed to reload {source["name"]}: {err}', log_lvl='debug')
            self._cert_monitor_state.wait(15)

    def _init_socket(self):
        self.bound_ip = self._resolve_ip()
        socket.setdefaulttimeout(2)
        use_ipv6 = self.bound_ip and ':' in self.bound_ip and self.bound_ip.count('.') == 0
        self.address_family = socket.AF_INET6 if use_ipv6 else socket.AF_INET
        if self.address_family == socket.AF_INET6:
            server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            try:
                server_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
            except AttributeError:
                pass
            bind_addr = (self.bound_ip, self.port, 0, 0)
        else:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            bind_addr = (self.bound_ip, self.port)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(bind_addr)
        server_socket.listen(self.queue_size)
        server_socket.settimeout(1.0)
        if self.ssl_enabled:
            server_socket = self._init_ssl_contexts(server_socket)
        return server_socket

    def _cleanup_workers(self):
        with self.lock:
            self.worker_handles = [handle for handle in self.worker_handles if handle.get('active')]

    def _accept_loop(self):
        endpoint = format_ip_port(self.bound_ip, self.port) or f':{self.port}'
        print(f'[SERVER] {endpoint} running...')
        while self.state.is_set():
            self.manager.cleanup_workers()
            self._cleanup_workers()
            if self.manager.total_worker_count() >= self.manager.global_max_threads:
                self.state.wait(0.05)
                continue
            if self.active_connections >= self.max_threads:
                self.state.wait(0.05)
                continue
            try:
                conn, addr = self.server_socket.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            except Exception as err:
                if self.state.is_set():
                    log(f'[CONNECTION_ERROR] {err}', log_lvl='debug')
                continue
            worker_state = Event()
            worker_state.set()
            worker_state.server_instance = self
            handle = {'event': worker_state, 'connection': conn, 'instance': self, 'active': True}
            submitted = self.manager.worker_pool.submit(self._serve_connection, conn, addr, worker_state, handle)
            if not submitted:
                self._reject_connection(conn)
                continue
            try:
                conn.settimeout(15)
            except Exception:
                pass
            with self.lock:
                self.active_connections += 1
                self.worker_handles.append(handle)
            SERVER_THREADS.append(handle)

    def _serve_connection(self, conn, addr, worker_state, handle):
        try:
            servlet(conn, addr, worker_state, self)
        finally:
            self._finalize_handle(handle)

    def _finalize_handle(self, handle):
        handle['active'] = False
        with self.lock:
            if handle in self.worker_handles:
                self.worker_handles.remove(handle)
            if self.active_connections > 0:
                self.active_connections -= 1
        try:
            SERVER_THREADS.remove(handle)
        except ValueError:
            pass

    def _reject_connection(self, conn):
        try:
            response = b"HTTP/1.1 503 Service Unavailable\r\nConnection: close\r\nContent-Length: 0\r\n\r\n"
            conn.sendall(response)
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.server_socket = self._init_socket()
        self.state.set()
        self.thread = Thread(target=self._accept_loop, daemon=True)
        self.thread.start()
        self._start_cert_monitor()

    def shutdown(self):
        self.state.clear()
        for handle in list(self.worker_handles):
            worker_state = handle['event']
            connection = handle['connection']
            worker_state.clear()
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                connection.close()
            except Exception:
                pass
            handle['active'] = False
        while True:
            with self.lock:
                remaining = self.active_connections
            if remaining == 0:
                break
            time.sleep(0.05)
        with self.lock:
            self.worker_handles = []
        if self.server_socket:
            try:
                self.server_socket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None
        if self.thread:
            self.thread.join(timeout=1)
            self.thread = None
        self._stop_cert_monitor()


class ServerManager:
    def __init__(self, config):
        self.config = config
        self.instances = []
        self.global_max_threads = config.MAX_THREADS
        self.running = False
        self.tasks = []
        self.worker_pool = WorkerPool(self.global_max_threads, self.global_max_threads * 2)

    def start(self):
        if self.running:
            return
        self.running = True
        for settings in self.config.SERVERS:
            instance = ServerInstance(self, settings)
            instance.start()
            self.instances.append(instance)
        self._start_tasks()

    def _start_tasks(self):
        for task in self.tasks:
            task.start()

    def register_task(self, func, interval):
        task = ScheduledTask(self, func, interval)
        self.tasks.append(task)
        if self.running:
            task.start()
        return task

    def cleanup_workers(self):
        alive = []
        for handle in SERVER_THREADS:
            if handle.get('active'):
                alive.append(handle)
            else:
                connection = handle.get('connection')
                try:
                    connection.close()
                except Exception:
                    pass
        SERVER_THREADS[:] = alive
        for instance in self.instances:
            instance._cleanup_workers()

    def total_worker_count(self):
        return self.worker_pool.active_count

    def shutdown(self):
        if not self.running:
            return
        self.running = False
        for task in self.tasks:
            task.stop()
        for instance in list(self.instances):
            instance.shutdown()
        self.instances = []
        self.cleanup_workers()
        self.worker_pool.shutdown()

    def build_task_data(self):
        return {
            'sessions': SESSIONS,
            'config': self.config,
            'servers': self.instances,
            'routes': {
                'pages': PAGES,
                'get_templates': GET_TEMPLATES,
                'post_handler': POST_HANDLER,
                'post_templates': POST_TEMPLATES,
                'error_handler': ERROR_HANDLER,
                'scoped': ROUTES,
            },
            'logging': {
                'options': LOGGING_OPTIONS,
                'callbacks': LOGGING_CALLBACK,
                'scoped_options': LOGGING_SCOPED_OPTIONS,
                'scoped_callbacks': LOGGING_SCOPED_CALLBACKS,
            }
        }

    def get_default_instance(self):
        if self.instances:
            return self.instances[0]
        return None


def create_ssl_context(cert_path, key_path):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=cert_path, keyfile=key_path)
    return context


def _ensure_manager():
    global SERVER_MANAGER
    if SERVER_MANAGER is None:
        SERVER_MANAGER = ServerManager(CONFIG)
    return SERVER_MANAGER


def servlet(conn, addr, worker_state, server_instance=None):
    instance = server_instance
    if instance is None:
        manager = _ensure_manager()
        instance = manager.get_default_instance()
        if instance is None:
            log('[THREADING] No server instance available for servlet.', log_lvl='debug')
            return
    try:
        while worker_state.is_set():
            log(f'[THREADING] thread {current_thread().ident} listens now.', log_lvl='debug')
            try:
                message_factory = HTTP_Message_Factory(
                    conn,
                    addr,
                    PAGES,
                    GET_TEMPLATES,
                    POST_HANDLER,
                    POST_TEMPLATES,
                    ERROR_HANDLER,
                    routes=ROUTES,
                    server_instance=instance,
                    max_header_size=CONFIG.MAX_HEADER_SIZE,
                    max_body_size=CONFIG.MAX_BODY_SIZE,
                    cors_settings=CORS_SETTINGS
                )
                if not hasattr(message_factory, 'response_message'):
                    log(f'[THREADING] Factory init failed, closing thread {current_thread().ident}.', log_lvl='debug')
                    break
                resp = message_factory.get_message()
                conn.sendall(resp)

                header, _, content = resp.partition(b'\r\n\r\n')
                log('\n\nRESPONSE:', str(header, 'utf-8'), content, '\n\n', log_lvl='response', sep='\n', scope=message_factory.scope)

                if not message_factory.stay_alive:
                    log(f'[THREADING] thread {current_thread().ident} closes because stay_alive is set to False', log_lvl='debug')
                    break
            except TimeoutError:
                log(f'[THREADING] thread {current_thread().ident} closes due to a timeout error.', log_lvl='debug')
                break
            except Exception as err:
                log(f'[THREADING] thread {current_thread().ident} closes due to an error: "{err}"', log_lvl='debug')
                traceback.print_exc()
                break
    finally:
        try:
            conn.settimeout(1.0)
            conn.close()
        except Exception as e:
            log(f'[THREADING] thread {current_thread().ident} encountered an error while closing connection: {e}', log_lvl='debug')


def main(server=None, state=None, server_config=None):
    manager = _ensure_manager()
    if server is None:
        manager.start()
        return manager
    settings = CONFIG.SERVERS[0] if not server_config else server_config
    instance = ServerInstance(manager, settings)
    instance.server_socket = server
    instance.state = state if state else Event()
    instance.state.set()
    instance.bound_ip = server.getsockname()[0]
    instance.port = server.getsockname()[1]
    try:
        server.settimeout(1.0)
    except Exception:
        pass
    if instance.ssl_enabled:
        log('[SERVER] Existing socket provided, SSL settings ignored.', log_lvl='debug')
    instance.thread = Thread(target=instance._accept_loop, daemon=True)
    instance.thread.start()
    manager.instances.append(instance)
    return instance


def shutdown_server(server=None, server_thread=None, server_state=None):
    manager = _ensure_manager()
    manager.shutdown()
    print('[SERVER] Closed...')


def start():
    manager = _ensure_manager()
    manager.start()
    try:
        while True:
            state = input()
            if state in ['quit', 'q', 'exit', 'e', 'stop']:
                manager.shutdown()
                break
    except KeyboardInterrupt:
        manager.shutdown()
        os._exit(0)


def schedule_task(func, interval):
    manager = _ensure_manager()
    return manager.register_task(func, interval)
