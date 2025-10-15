#2.0

import os
import re
from . import core
from .__init__ import MAIN_PATH
from .app_utils import urlencoded_to_dict
from .http_parser import Redirect
from .url_utils import UrlTemplate, split_route_scope, format_ip_port 
from .http_parser import PartialContent
from .http_parser import HTTP_Status_Code
from .special_media_type import Response
from .http_parser import HTTP_Message_Header_Line as Header_Line
from .http_parser import HTTP_Message_Request_Header_Tag as Request_Header_Tag
from .http_parser import HTTP_Message_Response_Header_Tag as Response_Header_Tag

class MIME_TYPE:
    HTML = 'text/html'
    JAVA_SCRIPT = 'text/javascript'
    CSS = 'text/css'
    ICO = "image/x-icon"
    PNG = "image/png"
    SVG = "image/svg+xml"
    TEXT = "text/plain"
    MP4 = "video/mp4"
    JSON = "application/json"
    WEBM_AUDIO = "audio/webm"


class STORE_VARS:
    #TODO: UPDATE Vars
    '''Keys used to access attributes of the dict provided to the respective handler methods'''

    COOKIES = 'cookies'
    QUERY_STRING = 'query_string'
    RESPONSE = 'response'
    POST = 'post'
    FLAGS = 'flags'
    REQUEST_HEADER = 'request_header'
    TEMPLATE_VARS = 'template_args'
    

class LOGGING_OPTIONS:

    '''Options used to set the logging mode via the ``set_logging`` function'''

    REQUESTS = 'request'
    RESPONSES = 'response'
    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'
    TIME = 'time'


def _scope_value(value):
    return value if value is not None else '*'


def _store_static_route(method, route, func, mime_type):
    ip, port, domain, path = split_route_scope(route)
    ip_key = _scope_value(ip)
    port_key = _scope_value(port)
    domain_key = _scope_value(domain)
    static_routes = core.ROUTES[method]['static']
    key = (ip_key, port_key, domain_key)
    if key not in static_routes:
        static_routes[key] = {}
    static_routes[key][path] = {
        'handler': func,
        'type': mime_type,
    }


def _template_weight(entry):
    weight = 0
    if entry.get('ip') is not None:
        weight += 4
    if entry.get('port') is not None:
        weight += 2
    if entry.get('domain') is not None:
        weight += 1
    return weight


def _register_template_route(method, template_obj, func, mime_type):
    entry = {
        'ip': template_obj.ip,
        'port': template_obj.port,
        'domain': template_obj.domain,
        'template': template_obj,
        'handler': func,
        'type': mime_type,
    }
    templates = core.ROUTES[method]['templates']
    templates = [item for item in templates if item['template'] != template_obj]
    templates.append(entry)
    templates.sort(key=_template_weight, reverse=True)
    core.ROUTES[method]['templates'] = templates


def _parse_scope(scope):
    if isinstance(scope, tuple):
        ip = scope[0] if len(scope) > 0 else None
        port = scope[1] if len(scope) > 1 else None
        domain = scope[2] if len(scope) > 2 else None
        if isinstance(port, str) and port.isdigit():
            port = int(port)
        return (ip or None, port, domain or None)
    if not scope:
        return (None, None, None)
    fake_route = scope if scope.endswith('/') else f'{scope}/'
    ip, port, domain, _ = split_route_scope(fake_route)
    if isinstance(port, str) and port.isdigit():
        port = int(port)
    return (ip, port, domain)


def _scope_repr(ip, port, domain):
    if ip is None and port is None and domain is None:
        return '*'
    ip_part = format_ip_port(ip, port) or '*'
    domain_part = domain if domain is not None else '*'
    return f'{ip_part}::{domain_part}'

def register(*args, **kwargs):
    """
    Decorator to register a GET route. Accepts either raw strings or `UrlTemplate`
    instances using the `ip:port::domain:/path` selector syntax.

    Examples:
        - `register(route='::/status', type=MIME_TYPE.JSON)`              -> matches all endpoints
        - `register(route='127.0.0.1:8443::/admin', type=MIME_TYPE.HTML)` -> specific IP/port
        - `register(route=':::example.com:/only-domain', ...)`            -> any IP/port, domain `example.com`
        - `register(route=':8080::example.com:/info', ...)`               -> any IP, port 8080, domain `example.com`
        - `register(route=UrlTemplate('[::1]:8000::/v1/{resource:str}'), ...)` -> IPv6 template with placeholders

    When the handler expects an argument it receives the session dict. Supported return
    values include `str`, `bytes`, `Dynamic`, `PartialContent`, `Redirect`, or `Response`.
    """

    if 'route' not in kwargs:
        raise Exception('The "route" argument is missing.')
    if 'type' not in kwargs:
        raise Exception('The "type" argument is missing.')
    route = kwargs['route']
    mime_type = kwargs['type']
    def inner(func):
        if isinstance(route, str):
            core.PAGES[route] = [func, mime_type]
            _store_static_route('GET', route, func, mime_type)
        elif isinstance(route, UrlTemplate):
            route.type = mime_type
            route.handler = func
            _register_template_route('GET', route, func, mime_type)
            core.GET_TEMPLATES[:] = [template for template in core.GET_TEMPLATES if template != route]
            core.GET_TEMPLATES.append(route)
        else:
            raise Exception('Unsupported route type.')
        return func            
    return inner

def post_handler(*args, **kwargs):

    '''
    ``General Information:``\n
    The post_handler decorator adds the decorated function to the servers POST_HANDLER
    dictionary. The decorater requires a path and a type argument to be specified the decorated function
    gets called whenever a post is targeted to the speciefied path. The function is expected to return a string of the
    under the type attribute declared MIME-type. The function decorated gets passed a dictionary containing
    the variables passed with the ``POST so it has to take an argument``
    
    ``Usage:``
    ```python
    @post_handler(route= '/', type= MIME_TYPE.TEXT)
    def main(args):
        return str(args)
    ```
    ``Note:`` The ``args`` argument is necessary!
    '''
    

    if 'route' not in kwargs:
        raise Exception('The "route" argument is missing.')
    if 'type' not in kwargs:
        raise Exception('The "type" argument is missing.')
    route = kwargs['route']
    mime_type = kwargs['type']
    def inner(func):
        if func.__code__.co_argcount != 1:
            raise Exception('The function decorated with the post_handler decorater has to\n accept one Argument "args":dict')

        if isinstance(route, str):
            core.POST_HANDLER[route] = [func, mime_type]
            _store_static_route('POST', route, func, mime_type)
        elif isinstance(route, UrlTemplate):
            route.type = mime_type
            route.handler = func
            _register_template_route('POST', route, func, mime_type)
            core.POST_TEMPLATES[:] = [template for template in core.POST_TEMPLATES if template != route]
            core.POST_TEMPLATES.append(route)
        else:
            raise Exception('Unsupported route type.')
        return func                  
    return inner


def error_handler(*args, **kwargs):

    '''
    ``General Information:``\n
    The error_handler decorator is used to serve a specific page if an error-code occurs.
    ``
    
    ``Usage:``
    ```python
    @error_handler(error_code= 404, type= MIME_TYPE.TEXT)
    def main():
        return str('Page not found!')
    ```
    '''
    

    if 'error_code' not in kwargs:
        raise Exception('The "error_code" argument is missing.')
    if 'type' not in kwargs:
        raise Exception('The "type" argument is missing.')
    err = kwargs['error_code']
    def inner(func):
        if func.__code__.co_argcount != 0:
            raise Exception('The function decorated with the error_handler is not allowed to take arguments.')
        if kwargs['error_code'] not in core.ERROR_HANDLER:
                core.ERROR_HANDLER[err] = [func,kwargs['type']]
        return func            
    return inner

def load_file(path:str) -> str:

    '''The load_file function attempts to read the content of a file with given path and returns it as a utf-8 encoded string'''

    with open(MAIN_PATH+path,'r',encoding='utf-8') as content:
            lines = content.readlines()
            return ''.join(lines)

def load_bin_file(path:str) -> bytes:

    '''The load_file function attempts to read the content of a file with given path and returns it as bytes'''

    path = MAIN_PATH+path
    size = os.path.getsize(path)
    with open(path,'rb') as content:
            return content.read(size)

#TODO: File through new file not found error so status code 404 can be returned
def load_file_from_directory(root_path: str, file_path: str) -> str:
    """The load_file_from_directory function attempts to read the content of a file with given path 
    relative to root_path and returns it as a utf-8 encoded string.
    """
    
    abs_root_path = os.path.abspath(root_path)
    abs_file_path = os.path.abspath(os.path.join(root_path, file_path))
    if os.path.commonpath([abs_root_path]) != os.path.commonpath([abs_root_path, abs_file_path]):
        raise ValueError("Attempt to access file outside the root directory")
    
    with open(abs_file_path, 'r', encoding='utf-8') as content:
        return content.read()

def load_bin_file_from_directory(root_path: str, file_path: str) -> bytes:
    """The load_bin_file_from_directory function attempts to read the content of a file with given path 
    relative to root_path and returns it as bytes.
    """
    
    abs_root_path = os.path.abspath(root_path)
    abs_file_path = os.path.abspath(os.path.join(root_path, file_path))
    

    if os.path.commonpath([abs_root_path]) != os.path.commonpath([abs_root_path, abs_file_path]):
        raise ValueError("Attempt to access file outside the root directory")
    
    with open(abs_file_path, 'rb') as content:
        return content.read()



def render_page(path:str, args:dict) -> str:

    '''The render_page function reads a files content and executes python-code wrapped in double curly braces "{{".
    If a variable name starts with an underscore "_" the python code wrapped in curley braces will be substituded by it's content.
    The values passed with the args dictionary can be accessed with the globals() function in the targeted file'''

    content = ''
    try:
        with open(MAIN_PATH+path,'r',encoding='utf-8') as page:
            content = '\n'.join(page.readlines())
            res_content = content[:]
        to_eval = re.finditer("{{(.|\n)*?}}",content)
        for var in to_eval:
            OUTPUT = {}
            var = content[var.span()[0]:var.span()[1]]
            exec(compile(var.strip('{{}}'),'temp','exec'),args,OUTPUT)
            insert = '\n'.join([str(OUTPUT[x]) for x in OUTPUT.keys() if x[0] == '_'])
            res_content = res_content.replace(var,insert)
    except Exception as e:
        print('[RENDERER] Error with rendering Page.')
        print(e)
    return res_content

def substitude_vars(content:str, vars:dict) -> str:
    
    '''This function accepts a string and substitudes all "%% + key + %%" with the according value from the dictionary'''
    
    try:
        _content = content
        for key in vars:
            _content = re.sub(f'%%{key}%%',vars[key],_content)
    except:
        print('[SUBSTITUDE_VARS] Error substituding vars.')
    return _content

def set_cookie(args, key, value) -> bool:
    if key not in args[STORE_VARS.COOKIES]:
        res:Response = args[STORE_VARS.RESPONSE]
        res.header.add_header_line(Header_Line(Response_Header_Tag.SET_COOKIE,f'{key}={value}'))
        return True
    return False


def is_partial(args) -> bool:
    return 'partial' in args[STORE_VARS.FLAGS]


def set_logging(option:str, state:bool, scope=None) -> None:
    if option not in core.LOGGING_OPTIONS:
        print(f'[LOGGING] Error: There is no logging-option called "{option}".')
        return
    if scope is None:
        core.LOGGING_OPTIONS[option] = state
        print(f'[LOGGING] logging-option "{option}" set to {state}.')
        return
    ip, port, domain = _parse_scope(scope)
    scope_key = (_scope_value(ip), _scope_value(port), _scope_value(domain))
    scoped_options = core.LOGGING_SCOPED_OPTIONS.get(scope_key)
    if not scoped_options:
        scoped_options = dict(core.LOGGING_OPTIONS)
        core.LOGGING_SCOPED_OPTIONS[scope_key] = scoped_options
    scoped_options[option] = state
    print(f'[LOGGING] logging-option "{option}" set to {state} for scope {_scope_repr(ip, port, domain)}.')

def set_logging_callback(callback, scope=None):
    try:
        assert callable(callback), 'The logging callback is not a callable'
        assert callback.__code__.co_argcount == 3, 'The logging callback needs to accept 3 arguments (message, time_stamp, loglvl)'
        if scope is None:
            core.LOGGING_CALLBACK.append(callback)
        else:
            ip, port, domain = _parse_scope(scope)
            scope_key = (_scope_value(ip), _scope_value(port), _scope_value(domain))
            core.LOGGING_SCOPED_CALLBACKS.append({'scope': scope_key, 'callback': callback})
        print('[LOGGING]', "Logging callback has been set")
    except Exception as e:
        print('[LOGGING]','Error:',e)

def log_to_file(path='/log.txt', logging_options=[LOGGING_OPTIONS.DEBUG], scope=None):
    try:
        for option in logging_options:
            assert option in core.LOGGING_OPTIONS, f'log_to_file: There is no logging-option called "{option}".'

        def file_writer_callback(message, time_stamp, loglvl):
            if  loglvl in logging_options:
                with open(MAIN_PATH+path,'a') as file:
                    file.write(f'({time_stamp}) {message}\n')
        if scope is None:
            core.LOGGING_CALLBACK.append(file_writer_callback)
        else:
            ip, port, domain = _parse_scope(scope)
            scope_key = (_scope_value(ip), _scope_value(port), _scope_value(domain))
            core.LOGGING_SCOPED_CALLBACKS.append({'scope': scope_key, 'callback': file_writer_callback})
        print('[LOGGING]', f"File-logging has been activated path= {path}")
        
    except Exception as e:
        print('[LOGGING]', e)
        

def enable_cors(
    allow_origin='*',
    allow_methods=None,
    allow_headers=None,
    expose_headers=None,
    allow_credentials=False,
    max_age=600,
) -> None:
    if allow_methods is None:
        allow_methods = ['GET', 'POST', 'OPTIONS']
    if allow_headers is None:
        allow_headers = ['*']
    if expose_headers is None:
        expose_headers = []

    def _normalize(value, transform=None):
        if isinstance(value, (list, tuple, set)):
            items = list(value)
        else:
            items = [value]
        if transform:
            return [transform(item) for item in items]
        return [str(item) for item in items]

    origin_value = allow_origin
    if isinstance(allow_origin, (list, tuple, set)):
        origin_value = list(allow_origin)

    if allow_methods == '*' or (isinstance(allow_methods, str) and allow_methods.strip() == '*'):
        normalized_methods = ['*']
    else:
        normalized_methods = _normalize(allow_methods, lambda item: str(item).upper())
        if 'OPTIONS' not in normalized_methods:
            normalized_methods.append('OPTIONS')

    if allow_headers == '*' or (isinstance(allow_headers, str) and allow_headers.strip() == '*'):
        normalized_headers = ['*']
    else:
        normalized_headers = _normalize(allow_headers)

    normalized_expose = _normalize(expose_headers)

    core.CORS_SETTINGS.update({
        'enabled': True,
        'allow_origin': origin_value,
        'allow_methods': normalized_methods,
        'allow_headers': normalized_headers,
        'expose_headers': normalized_expose,
        'allow_credentials': bool(allow_credentials),
        'max_age': int(max_age),
    })
    print('[CORS]', 'CORS support enabled.')


def disable_cors() -> None:
    core.CORS_SETTINGS['enabled'] = False
    core.CORS_SETTINGS['expose_headers'] = []
    print('[CORS]', 'CORS support disabled.')


def get_cors_settings() -> dict:
    return dict(core.CORS_SETTINGS)


def response(content=None, status=None, headers=None, mime_type=None) -> Response:
    return Response(content=content, status=status, headers=headers, mime_type=mime_type)


def server_task(task, interval):
    if not callable(task):
        raise Exception('server_task expects a callable task.')
    if interval < 0:
        raise Exception('server_task expects a non-negative interval.')
    return core.schedule_task(task, interval)

 
def get_pages() -> dict:
    return core.PAGES

def get_sessions() -> dict:
    return core.SESSIONS
    
def get_post_handler() -> dict:
    return core.POST_HANDLER

def start() -> None:

    '''The start function causes the server to start by invoking core.start()'''

    core.start()

