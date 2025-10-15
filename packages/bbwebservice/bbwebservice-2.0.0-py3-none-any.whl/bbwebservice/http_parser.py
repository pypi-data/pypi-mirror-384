import socket
import re
from datetime import datetime
from . import url_utils
from .special_media_type import PartialContent
from .special_media_type import Redirect
from .special_media_type import Dynamic
from .special_media_type import Response as AppResponse

import traceback

HEADER_SIZE_MAX = 16 * 1024
BODY_SIZE_MAX = 10 * 1024 * 1024
HEADER_TERMINATOR = b'\r\n\r\n'


class HeaderTooLarge(Exception):
    """Raised when the HTTP header section exceeds configured limits."""


class BodyTooLarge(Exception):
    """Raised when the HTTP body exceeds configured limits."""


class ChunkedDecodingError(Exception):
    """Raised when chunked transfer decoding fails."""


class _BufferedSocketReader:
    """Utility to read from a socket while retaining already fetched bytes."""

    def __init__(self, connection: socket.socket, initial: bytes = b'', limit: int | None = None):
        self.connection = connection
        self.buffer = bytearray(initial)
        self.limit = limit
        self.eof = False

    def _ensure(self, size: int) -> None:
        """Ensure at least `size` bytes are buffered."""
        while len(self.buffer) < size and not self.eof:
            needed = size - len(self.buffer)
            chunk = self.connection.recv(max(1, min(4096, needed)))
            if not chunk:
                self.eof = True
                break
            self.buffer.extend(chunk)
            if self.limit is not None and len(self.buffer) > self.limit:
                raise BodyTooLarge("Request body exceeds configured limit.")
        if len(self.buffer) < size:
            raise EOFError("Unexpected end of stream while reading request body.")

    def readexact(self, size: int) -> bytes:
        self._ensure(size)
        data = bytes(self.buffer[:size])
        del self.buffer[:size]
        return data

    def readline(self) -> bytes:
        delimiter = b'\r\n'
        while True:
            idx = self.buffer.find(delimiter)
            if idx != -1:
                line = bytes(self.buffer[:idx])
                del self.buffer[:idx + len(delimiter)]
                return line
            chunk = self.connection.recv(4096)
            if not chunk:
                raise EOFError("Unexpected end of stream while reading chunked data.")
            self.buffer.extend(chunk)
            if self.limit is not None and len(self.buffer) > self.limit:
                raise BodyTooLarge("Request body exceeds configured limit.")

    def drain(self) -> bytes:
        data = bytes(self.buffer)
        self.buffer.clear()
        return data

LOGGING_OPTIONS:dict = {'response':False, 'request':False, 'debug':False, 'info':False, 'warning':False, 'error':False, 'critical':False, 'time':False}
LOGGING_CALLBACK = []
LOGGING_SCOPED_OPTIONS = {}
LOGGING_SCOPED_CALLBACKS = []

def get_http_date():
    now = datetime.utcnow()
    http_date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
    return http_date

def _normalize_scope_value(value):
    return value if value is not None else '*'


def _collect_scope_candidates(scope):
    if scope is None:
        return [('*', '*', '*')]
    if not isinstance(scope, (list, tuple)):
        scope = (scope,)
    ip = scope[0] if len(scope) > 0 else None
    port = scope[1] if len(scope) > 1 else None
    domain = scope[2] if len(scope) > 2 else None
    ip_options = [ip, None] if ip is not None else [None]
    port_options = [port, None] if port is not None else [None]
    domain_options = [domain, None] if domain is not None else [None]
    seen = set()
    result = []
    for ip_val in ip_options:
        for port_val in port_options:
            for domain_val in domain_options:
                candidate = (
                    _normalize_scope_value(ip_val),
                    _normalize_scope_value(port_val),
                    _normalize_scope_value(domain_val),
                )
                if candidate not in seen:
                    seen.add(candidate)
                    result.append(candidate)
    if ('*', '*', '*') not in seen:
        result.append(('*', '*', '*'))
    return result

def log(*msg, log_lvl='info', sep=None, scope=None) -> None:
    #TODO: Encoding safe logging
    candidates = _collect_scope_candidates(scope)
    effective_options = LOGGING_OPTIONS
    callbacks = []

    if LOGGING_CALLBACK:
        callbacks.extend(LOGGING_CALLBACK)

    for candidate in candidates:
        scoped = LOGGING_SCOPED_OPTIONS.get(candidate)
        if scoped:
            effective_options = scoped
            break

    for candidate in candidates:
        for entry in LOGGING_SCOPED_CALLBACKS:
            if entry['scope'] == candidate:
                callbacks.append(entry['callback'])

    include_time = bool(effective_options.get('time'))
    should_print = bool(effective_options.get(log_lvl))
    if not callbacks and not include_time and not should_print:
        return

    timestamp = None
    parts = msg
    if include_time:
        timestamp = get_http_date()
        parts = (f'({timestamp})', *msg)

    if callbacks:
        if timestamp is None:
            timestamp = get_http_date()
        message = sep.join(map(str, parts)) if sep else ' '.join(map(str, parts))
        for callback in callbacks:
            try:
                callback(message, timestamp, log_lvl)
            except Exception as e:
                print('[LOGGING]', e)

    if should_print:
        if sep:
            print(*parts, sep=sep)
        else:
            print(*parts)

def approach(func, args=None, switch=None):
    try:
        if args:
            return func(*args)
        return func()
    except Exception as e:
        if switch:
            log(f'[APP][{switch}] error: {e}', log_lvl='debug')
        else:
            log(f'[APP] error: {e}', log_lvl='debug')
        

def get_class_fields(klass) -> dict:
    
    class_attrs = vars(klass)
    res = {}
    for key in class_attrs:
        if not key.startswith("__"):  # Exclude attributes starting with '__'
            res[key] = class_attrs[key]
    return res

def merge_dicts(*dicts):
    result = {}
    for d in dicts:
        result.update(d.copy())
    return result
    

class HTTP_Message_Type:
    REQUEST = 'REQUEST'
    RESPONSE = 'RESPONSE'


class Mime_Type:

    HTML = 'text/html'
    JAVA_SCRIPT = 'text/javascript'
    CSS = 'text/css'
    ICO = 'image/x-icon'
    PNG = 'image/png'
    JPEG = 'image/jpeg'
    SVG = 'image/svg+xml'
    TEXT = 'text/plain'
    MP4 = 'video/mp4'
    JSON = 'application/json'
    WEBM_AUDIO = 'audio/webm'
    PDF = 'application/pdf'
    XML = 'application/xml'
    MPEG = 'audio/mpeg'
    CSV = 'text/csv'


class CSP_Directive:

    DEFAULT_SRC = 'default-src'
    SCRIPT_SRC = 'script-src'
    STYLE_SRC = 'style-src'
    IMG_SRC = 'img-src'
    FONT_SRC = 'font-src'
    CONNECT_SRC = 'connect-src'
    FRAME_SRC = 'frame-src'
    OBJECT_SRC = 'object-src'

class CSP_Values:

    NONE = '\'none\''
    SELF = '\'self\''
    UNSAFE_INLINE = '\'unsafe-inline\''
    UNSAFE_EVAL = '\'unsafe-eval\''    


class CSP_Policy:

    def __init__(self, csp_directive:str, csp_value: str|list) -> None:
        self.csp_directive = csp_directive
        self.csp_value = csp_value

    def __str__(self) -> str:
        res = ''
        if isinstance(self.csp_value,str):
            res = f'{self.csp_directive} {self.csp_value}'
        if isinstance(self.csp_value,list):
            res += self.csp_directive
            for val in self.csp_value:
                res += f' {val}'
        return res

class CSP:

    def __init__(self) -> None:
        self.policies = []
    
    def add_policy(self, policy:CSP_Policy) -> None:
        self.policies.append(policy)

    def is_set(self):
        return not bool(self.policies)

    def __str__(self) -> str:
        return '; '.join([str(x) for x in self.policies])
    
    
#<https://en.wikipedia.org/wiki/List_of_HTTP_status_codes>

class HTTP_Status_Code:
    CONTINUE = [100,'Continue']
    SWITCHING_PROTOCOLS = [101,'Switching Protocols']
    PROCESSING = [102, 'Processing']
    EARLY_HINTS = [103,'Early Hints']
    OK = [200,'OK']
    CREATED = [201,'Created']
    ACCEPTED = [202,'Accepted']
    NON_ATHORITATIVE_INFORMATION = [203, 'Non-Authoritative Information']
    NO_CONTENT = [204, 'No Content']
    RESET_CONTENT = [205, 'Reset Content']
    PARTIAL_CONTENT = [206, 'Partial Content']
    MULTI_STATUS = [207, 'Multi-Status']
    ALREADY_REPORTED = [208, 'Already Reported']
    IM_USED = [226, 'IM Used']
    MULTIPLE_CHOICES = [300, 'Multiple Choices']
    MOVED_PERMANENTLY = [301,'Moved Permanently']
    FOUND = [302, 'Found']
    SEE_OTHER = [303, 'See Other']
    NOT_MODIFIED = [304, 'Not Modified']
    USE_PROXY = [305, 'Use Proxy']
    SWITCH_PROXY = [306, 'Switch Proxy']
    TEMPORARY_REDIRECT = [307, 'Temporary Redirect']
    PERMANENT_REDIRECT = [308, 'Permanent Redirect']
    BAD_REQUEST = [400, 'Bad Request']
    UNAUTHERIZED = [401, 'Unautherized']
    PAYMENT_REQUIRED = [402, 'Payment Required']
    FORBIDDEN = [403, 'Forbidden']
    NOT_FOUND = [404, 'Not Found']
    METHOD_NOT_ALLOWED = [405, 'Method Not Allowed']
    NOT_ACCEPTABLE = [406, 'Not Acceptable']
    PROXY_AUTHENTICATION_REQUIRED = [407, 'Proxy Authentication Required']
    REQUEST_TIMEOUT = [408, 'Request Timeout']
    CONFLICT = [409, 'Conflict']
    GONE = [410, 'Gone']
    LENGTH_REQUIRED = [411, 'Length Required']
    PRECONDITION_FAILED = [412,'Precondition Failed']
    PAYLOAD_TOO_LARGE = [413, 'Payload Too Large']
    URI_TOO_LONG = [414, 'URI Too Long']
    UNSUPPORTED_MEDIA_TYPE = [415, 'Unsupported Media Type']
    RANGE_NOT_SATISFIABLE = [416, 'Range Not Satisfiable']
    EXCEPTION_FAILED = [417, 'Exception Failed']
    IM_A_TEAPOT = [418, "I'm a teapot"]
    MISDIRECTED_REQUEST = [421, 'Misdirected Request']
    UNPROCESSABLE_ENTITY = [422, 'Unprocessable Entity']
    LOCKED = [423, 'Locked']
    FAILED_DEPENDENCY = [424, 'Failed Dependency']
    TOO_EARLY = [425, 'Too Early']
    UPGRADE_REQUIRED = [426, 'Upgrade Required']
    PRECONDITION_REQUIRED = [428, 'Precondition Required']
    TOO_MANY_REQUESTS = [429, 'Too Many Requests']
    REQUEST_HEADER_FIELDS_TOO_LARGE = [431, 'Request Header Fields Too Large']
    UNAVAILABLE_FOR_LEGAL_REASONS = [451, 'Unavailable For Legal Reasons']
    INTERNAL_SERVER_ERROR = [500, 'Internal Server Error']
    NOT_IMPLEMENTED = [501,'Not Implemented']
    BAD_GATEWAY = [502, 'Bad Gateway']
    SERVICE_UNAVAILABLE = [503, 'Service Unavailable']
    GATEWAY_TIMEOUT = [504, 'Gateway Timeout']
    HTTP_VERSION_NOT_SUPPORTED = [505, 'HTTP Version Not Supported']
    VARIANT_ALSO_NEGOTIATES = [506, 'Variant Also Negotiates']
    INSUFFICIENT_STORAGE = [507, 'Insufficient Storage']
    LOOP_DETECTED = [508, 'Loop Detected']
    NOT_EXTENDED = [510, 'Not Extended']
    NETWORK_AUTHENTICATION_REQUIRED = [511, 'Network Authentication Required']




class HTTP_Method:
    GET     =  'GET'
    POST    =  'POST'
    PUT     =  'PUT'
    HEAD    =  'HEAD'
    DELETE  =  'DELETE'
    TRACE   =  'TRACE'
    OPTIONS =  'OPTIONS'
    CONNECT =  'CONNECT'

class HTTP_Protocol_Version:
        HTTP_1_0 = "HTTP/1.0"
        HTTP_1_1 = "HTTP/1.1"




class HTTP_Access_Control_Headers:
    ACCESS_CONTROL_ALLOW_ORIGIN = 'Access-Control-Allow-Origin'
    ACCESS_CONTROL_EXPOSE_HEADERS = 'Access-Control-Expose-Headers'
    ACCESS_CONTROL_ALLOW_HEADERS = 'Access-Control-Allow-Headers'
    ACCESS_CONTROL_MAX_AGE = 'Access-Control-Max-Age'
    ACCESS_CONTROL_ALLOW_CREDENTIALS = 'Access-Control-Allow-Credentials'
    ACCESS_CONTROL_ALLOW_METHODS = 'Access-Control-Allow-Methods'
    ACCESS_CONTROL_REQUEST_METHOD = 'Access-Control-Request-Method'
    ACCESS_CONTROL_REQUEST_HEADERS = 'Access-Control-Request-Headers'
    ORIGIN = 'Origin'



# <https://de.wikipedia.org/wiki/Liste_der_HTTP-Headerfelder>

class HTTP_Message_Request_Header_Tag:

    '''This class holds all HTTP message header tags that are supportet by this webserver'''

    ACCEPT = 'Accept'
    ACCEPT_CHARSET = 'Accept-Charset'
    ACCEPT_ENCODING = 'Accept-Encoding'
    ACCEPT_LANGUAGE = 'Accept-Language'
    AUTHORIZATION = 'Authorization'
    CACHE_CONTROL = 'Cache-Control'
    CONNECTION = 'Connection'
    COOKIE = 'Cookie'
    CONTENT_LENGTH = 'Content-Length'
    CONTENT_TYPE = 'Content-Type'
    CONTENT_LANGUAGE = 'Content-Language'
    DATE = 'Date'
    EXPECT = 'Expect'
    FORWARDED = 'Forwarded'
    FROM = 'From'
    HOST = 'Host'
    IF_MATCH = 'If-Match'
    IF_MODIFIED_SINCE = 'If-Modified-Since'
    IF_NONE_MATCH = 'If-None-Match'
    IF_RANGE = 'If-Range'
    IF_UNMODIFIED_SINCE = 'If-Unmodified-Since'
    MAX_FORWARDS = 'Max-Forwards'
    PRAGMA = 'Pragma'
    PROXY_AUTHORIZATION = 'Proxy-Authorization'
    RANGE = 'Range'
    REFERER = 'Referer'
    TE = 'TE'
    TRANSFER_ENCODING = 'Transfer-Encoding'
    UPGRADE = 'Upgrade'
    USER_AGENT = 'User-Agent'
    VIA = 'Via'
    WARNING = 'Warning'

class HTTP_Message_Response_Header_Tag:

    '''This class holds all HTTP message header tags that are supportet by this webserver'''

    ACCEPT_RANGES = 'Accept-Ranges'
    AGE = 'Age'
    ALLOW = 'Allow'
    CACHE_CONTROL = 'Cache-Control'
    CONNECTION = 'Connection'
    CONTENT_ENCODING = 'Content-Encoding'
    CONTENT_LANGUAGE = 'Content-Language'
    CONTENT_LENGTH = 'Content-Length'
    CONTENT_LOCATION = 'Content-Location'
    CONTENT_DISPOSITION = 'Content-Disposition'
    CONTENT_RANGE = 'Content-Range'
    CONTENT_SECURITY_POLICY = 'Content-Security-Policy'
    CONTENT_TYPE = 'Content-Type'
    DATE = 'Date'
    ETAG = 'ETag'
    EXPIRES = 'Expires'
    LAST_MODIFIED = 'Last-Modified'
    LINK = 'Link'
    LOCATION = 'Location'
    P3P = 'P3P'
    PRAGMA = 'Pragma'
    REFRESH = 'Refresh'
    RETRY_AFTER = 'Retry-After'
    SERVER = 'Server'
    SET_COOKIE = 'Set-Cookie'
    TRAILER = 'Trailer'
    TRANSFER_ENCODING = 'Transfer-Encoding'
    VARY = 'Vary'
    VIA = 'Via'
    WARNING = 'Warning'
    WWW_AUTHENTICATE = 'WWW-Authenticate'

class HTTP_Message_Header_Line():

    '''Defines form and functionalities of the lines which compose an HTTP Header'''
    
    def __init__(self, header_tag:str, values:str|list) -> None:
            self.header_tag = header_tag
            if isinstance(values, list):
                self.values = [str(value) for value in values]
            else:
                self.values = [str(values)]

    def add_value(self, value:str) -> None:
        self.values.append(value)

    def __str__(self) -> str:
        return f'{self.header_tag}: {", ".join(self.values)}'


class HTTP_Message_Header():
    def __init__(self) -> None:
        self.header_lines = []
    
    def add_header_line(self, header_line:HTTP_Message_Header_Line) -> None:
            self.header_lines.append(header_line)

    #TODO: remove heade line
    def remove(self, key) -> None:
        for idx, val in enumerate(self.header_lines):
            if val.header_tag == key:
                del self.header_lines[idx]
                return 

    def add_values_to_header(self, header_line:HTTP_Message_Header_Line) -> bool:
            header = [h for h in self.header_lines if h.header_tag.lower() == header_line.header_tag.lower()]
            if header:
                header = header[0]
                values  = [val for val in header_line.values if val not in header.values]
                if values:
                    for value in values:
                        header.add_value(value)
                    return True
            return False
                                
    
    def parse_header(self, raw_message:str) -> None:
        for line in raw_message.split('\r\n'):
            if len(line.split(':',1)) == 2:
                if line.split(':',1)[0].lower() in [x.lower() for x in get_class_fields(HTTP_Message_Request_Header_Tag).values()]:
                    tokens = line.split(':',1)
                    header_line = HTTP_Message_Header_Line(tokens[0].strip(), tokens[1].strip())
                    self.header_lines.append(header_line)

                else:
                    #TODO: append other list so user can work with it
                    log(f'[parse_header] \'{line.split(":",1)[0]}\' is not a recognized header.',log_lvl='debug')

    def get_fields(self)->dict:
        res = {}
        for line in self.header_lines:
            res[line.header_tag] = line.values
        return res


    def bin(self) -> bytes:
        return self.__str__().encode('utf-8')

    def __contains__(self, item):
        return item .lower() in [x.lower() for x in self.get_fields().keys()]

    def __str__(self) -> str:
        if not self.header_lines:
            return ''
        return '\r\n'.join([str(x) for x in self.header_lines]) + '\r\n'


class HTTP_Response:

    def __init__(self, header:HTTP_Message_Header, error_handler = None, content:bytes=None) -> None:
        
        self.header = header
        self.protocol_version = HTTP_Protocol_Version.HTTP_1_1
        self.http_status_code = HTTP_Status_Code.BAD_REQUEST
        self.error_handler = error_handler or {}
        self._chunks: list[bytes] = []
        self._length = 0

        if content:
            self.content = content

    def set_status(self, http_status_code) -> None:
            self.http_status_code = http_status_code
            status_code = http_status_code[0]
            if  status_code > 300:

                if status_code in self.error_handler:
                    handler = self.error_handler[status_code][0]
                    content_type = self.error_handler[status_code][1]
                    content = handler()

                    if isinstance(content, bytes):
                        self.header.add_header_line(HTTP_Message_Header_Line(HTTP_Message_Response_Header_Tag.CONTENT_TYPE,content_type))
                        self.append_content(content)

                    if isinstance(content, str):
                        self.header.add_header_line(HTTP_Message_Header_Line(HTTP_Message_Response_Header_Tag.CONTENT_TYPE,[content_type, 'charset=utf-8']))
                        self.append_content(content.encode('utf-8'))
                else:
                    self.header.add_header_line(HTTP_Message_Header_Line(HTTP_Message_Response_Header_Tag.CONTENT_TYPE,[Mime_Type.TEXT, 'charset=utf-8']))
                    self.append_content(f'{self.http_status_code[0]} {self.http_status_code[1]}'.encode('utf-8'))


        #TODO: error handling

    def set_protocol(self, http_protocol_version) -> None:
        self.protocol_version = http_protocol_version

    def set_csp(self, csp:CSP):
        self.header.add_header_line(HTTP_Message_Header_Line(HTTP_Message_Response_Header_Tag.CONTENT_SECURITY_POLICY, str(csp)))
    
    def append_content(self, content:bytes) -> None:
        if content is None:
            return
        if isinstance(content, str):
            content = content.encode('utf-8')
        elif isinstance(content, bytearray):
            content = bytes(content)
        elif not isinstance(content, bytes):
            raise TypeError('Response content must be bytes or str.')
        self._chunks.append(content)
        self._length += len(content)

    @property
    def content(self) -> bytes:
        return b''.join(self._chunks)

    @content.setter
    def content(self, value) -> None:
        self._chunks.clear()
        self._length = 0
        if value is None:
            return
        if isinstance(value, str):
            value = value.encode('utf-8')
        elif isinstance(value, bytearray):
            value = bytes(value)
        elif not isinstance(value, bytes):
            raise TypeError('Response content must be bytes or str.')
        self._chunks.append(value)
        self._length = len(value)

    def get_first_line(self) -> bytes:
        return f'{self.protocol_version} {self.http_status_code[0]} {self.http_status_code[1]}\r\n'.encode('utf-8')

    def bin(self):
        body = b''.join(self._chunks)
        if True:
            self.header.remove(HTTP_Message_Response_Header_Tag.CONTENT_LENGTH)
            self.header.add_header_line(HTTP_Message_Header_Line(HTTP_Message_Response_Header_Tag.CONTENT_LENGTH,str(len(body))))
        header_bytes = self.header.bin()
        return self.get_first_line() + header_bytes + b'\r\n' + body

    def __str__(self) -> str:
        return str(self.bin(),'utf-8')


class HTTP_Message_Factory:
    def __init__(
        self,
        connection: socket.socket,
        addr,
        get_handler: dict,
        get_templates: list,
        post_handler: dict,
        post_templates: list,
        error_handler: dict,
        routes=None,
        server_instance=None,
        max_header_size: int = HEADER_SIZE_MAX,
        max_body_size: int = BODY_SIZE_MAX,
        cors_settings=None,
    ) -> None:
        self.stay_alive: bool = False
        self.get_handler: dict = get_handler
        self.get_templates: list = get_templates
        self.post_templates: list = post_templates
        self.post_handler: dict = post_handler
        self.error_handler: dict = error_handler
        self.routes = routes or {'GET': {'static': {}, 'templates': []}, 'POST': {'static': {}, 'templates': []}}
        self.server_instance = server_instance
        self.server_ip = server_instance.bound_ip if server_instance else None
        self.server_port = server_instance.port if server_instance else None
        self.scope = (self.server_ip, self.server_port, None)
        self.connection = connection
        self.addr = addr
        self.max_header_size = max_header_size or HEADER_SIZE_MAX
        self.max_body_size = max_body_size or BODY_SIZE_MAX
        self.cors_settings = cors_settings or {}
        self.target_host = None
        self.mime_type = Mime_Type.TEXT
        self.post = bytearray()
        self.request_header: HTTP_Message_Header = HTTP_Message_Header()
        self.response_header: HTTP_Message_Header = HTTP_Message_Header()
        self.response_message: HTTP_Response = HTTP_Response(self.response_header, error_handler=self.error_handler)
        self.http_parser: HTTP_Parser | None = None
        self.message_temp = ''
        self.range = None

        try:
            header_bytes, initial_remainder = self._read_header()
            self.message_temp = header_bytes.decode('iso-8859-1')
            self.request_header.parse_header(self.message_temp)
            self._read_body(initial_remainder)
            self.http_parser = HTTP_Parser(self)
            self.http_parser.parse()
            self.request_header.get_fields()
            self._apply_connection_policy()
            self._apply_cors_headers(self.http_parser.http_message_method)
            self.scope = (self.server_ip, self.server_port, self.target_host if self.target_host else None)
            log('\n\nREQUEST:', self.message_temp + '\n\n', log_lvl='request', sep="\n", scope=self.scope)
        except HeaderTooLarge:
            self.response_message.set_status(HTTP_Status_Code.REQUEST_HEADER_FIELDS_TOO_LARGE)
            self.stay_alive = False
        except BodyTooLarge:
            self.response_message.set_status(HTTP_Status_Code.PAYLOAD_TOO_LARGE)
            self.stay_alive = False
        except ChunkedDecodingError as error:
            log(f'[PARSER] chunked decoding failed: {error}', log_lvl='debug', scope=self.scope)
            self.response_message.set_status(HTTP_Status_Code.BAD_REQUEST)
            self.stay_alive = False
        except Exception as error:
            log(f'[PARSER] error: {error}', log_lvl='debug', scope=self.scope)
            self.response_message.set_status(HTTP_Status_Code.BAD_REQUEST)
            self.stay_alive = False

        if not any(line.header_tag.lower() == HTTP_Message_Response_Header_Tag.CONNECTION.lower() for line in self.response_header.header_lines):
            connection_value = 'keep-alive' if self.stay_alive else 'close'
            self.response_header.add_header_line(HTTP_Message_Header_Line(HTTP_Message_Response_Header_Tag.CONNECTION, connection_value))

    def _read_header(self) -> tuple[bytes, bytes]:
        buffer = bytearray()
        while True:
            idx = buffer.find(HEADER_TERMINATOR)
            if idx != -1:
                body_start = idx + len(HEADER_TERMINATOR)
                return bytes(buffer[:idx]), bytes(buffer[body_start:])
            if len(buffer) >= self.max_header_size:
                raise HeaderTooLarge()
            chunk = self.connection.recv(4096)
            if not chunk:
                raise EOFError('Client closed connection while reading headers.')
            buffer.extend(chunk)

    def _read_body(self, initial_remainder: bytes) -> None:
        headers = self.request_header.get_fields()
        transfer_encodings = []
        transfer_header = self._get_header_values(headers, HTTP_Message_Request_Header_Tag.TRANSFER_ENCODING)
        if transfer_header:
            for value in transfer_header:
                transfer_encodings.extend(token.strip().lower() for token in value.split(',') if token.strip())
        content_length = None
        content_length_header = self._get_header_values(headers, HTTP_Message_Request_Header_Tag.CONTENT_LENGTH)
        if content_length_header:
            raw_value = content_length_header[0]
            try:
                content_length = int(raw_value)
            except (ValueError, TypeError):
                raise ChunkedDecodingError('Invalid Content-Length header.')

        reader = _BufferedSocketReader(self.connection, initial_remainder, self.max_body_size)

        if transfer_encodings:
            if transfer_encodings[-1] != 'chunked':
                raise ChunkedDecodingError('Unsupported transfer-encoding.')
            body = bytearray()
            while True:
                size_line = reader.readline()
                size_token = size_line.split(b';', 1)[0].strip()
                if not size_token:
                    raise ChunkedDecodingError('Invalid chunk size line.')
                try:
                    chunk_size = int(size_token, 16)
                except ValueError:
                    raise ChunkedDecodingError('Invalid chunk size.')
                if chunk_size == 0:
                    reader.readexact(2)
                    if reader.buffer:
                        while True:
                            trailer = reader.readline()
                            if trailer == b'':
                                break
                    break
                chunk = reader.readexact(chunk_size)
                body.extend(chunk)
                reader.readexact(2)
                if self.max_body_size and len(body) > self.max_body_size:
                    raise BodyTooLarge()
            self.post = body
        elif content_length is not None:
            if content_length < 0:
                raise ChunkedDecodingError('Invalid Content-Length header.')
            if content_length == 0:
                self.post = bytearray()
            else:
                if self.max_body_size and content_length > self.max_body_size:
                    raise BodyTooLarge()
                body = reader.readexact(content_length)
                self.post = bytearray(body)
        else:
            self.post = bytearray()

    def _apply_connection_policy(self) -> None:
        headers = self.request_header.get_fields()
        connection_tokens = []
        connection_header = self._get_header_values(headers, HTTP_Message_Request_Header_Tag.CONNECTION)
        if connection_header:
            for value in connection_header:
                connection_tokens.extend(token.strip().lower() for token in value.split(',') if token.strip())

        protocol = self.http_parser.http_protocol if self.http_parser else HTTP_Protocol_Version.HTTP_1_1
        keep_alive = False
        if protocol == HTTP_Protocol_Version.HTTP_1_1:
            keep_alive = 'close' not in connection_tokens
        else:
            keep_alive = 'keep-alive' in connection_tokens

        self.stay_alive = keep_alive

    def _apply_cors_headers(self, request_method: str) -> None:
        if not self.cors_settings.get('enabled'):
            return

        def _prepare(value):
            if isinstance(value, (list, tuple, set)):
                return ', '.join(str(v) for v in value)
            return str(value)

        allow_origin = self.cors_settings.get('allow_origin', '*')
        allow_methods = self.cors_settings.get('allow_methods', ['GET', 'POST', 'OPTIONS'])
        allow_headers = self.cors_settings.get('allow_headers', ['*'])
        expose_headers = self.cors_settings.get('expose_headers', [])
        allow_credentials = self.cors_settings.get('allow_credentials', False)
        max_age = self.cors_settings.get('max_age', 600)

        header = self.response_header
        header.add_header_line(HTTP_Message_Header_Line(HTTP_Access_Control_Headers.ACCESS_CONTROL_ALLOW_ORIGIN, _prepare(allow_origin)))
        header.add_header_line(HTTP_Message_Header_Line(HTTP_Access_Control_Headers.ACCESS_CONTROL_ALLOW_METHODS, _prepare(allow_methods)))
        header.add_header_line(HTTP_Message_Header_Line(HTTP_Access_Control_Headers.ACCESS_CONTROL_ALLOW_HEADERS, _prepare(allow_headers)))
        header.add_header_line(HTTP_Message_Header_Line(HTTP_Access_Control_Headers.ACCESS_CONTROL_MAX_AGE, str(max_age)))
        if expose_headers:
            header.add_header_line(HTTP_Message_Header_Line(HTTP_Access_Control_Headers.ACCESS_CONTROL_EXPOSE_HEADERS, _prepare(expose_headers)))
        if allow_credentials:
            header.add_header_line(HTTP_Message_Header_Line(HTTP_Access_Control_Headers.ACCESS_CONTROL_ALLOW_CREDENTIALS, 'true'))
        if allow_methods and allow_methods != ['*']:
            header.add_header_line(
                HTTP_Message_Header_Line(
                    HTTP_Message_Response_Header_Tag.ALLOW,
                    _prepare([method.upper() for method in allow_methods])
                )
            )
        if request_method == HTTP_Method.OPTIONS:
            self.response_message.set_status(HTTP_Status_Code.NO_CONTENT)
            self.response_message.content = b''

    @staticmethod
    def _get_header_values(header_map: dict, target: str):
        target_lower = target.lower()
        for key, value in header_map.items():
            if key.lower() == target_lower:
                return value
        return None


    def get_message(self) -> bytes:
        status = self.response_message.http_status_code
        if status == HTTP_Status_Code.BAD_REQUEST:
                self.response_message.set_status(HTTP_Status_Code.BAD_REQUEST)
        path = self.http_parser.http_request_path if self.http_parser else (getattr(self, 'http_request_path', None) or 'unknown')
        log(f'[{status[0]}] [{path}] {status[1]}', log_lvl='info', scope=self.scope)
        return self.response_message.bin()
    
class HTTP_Parser():

    def __init__(self, http_message_factory:HTTP_Message_Factory) -> None:
        self.http_message_factory = http_message_factory

    def _resolve_handler(self, method, path, host):
        routes = self.http_message_factory.routes.get(method, {}) if self.http_message_factory.routes else {}
        if not routes:
            return None
        static_routes = routes.get('static', {})
        templates = routes.get('templates', [])
        server_ip = self.http_message_factory.server_ip
        server_port = self.http_message_factory.server_port
        seen = set()
        candidates = []
        ip_options = [server_ip, None] if server_ip is not None else [None]
        port_options = [server_port, None] if server_port is not None else [None]
        domain_options = [host, None] if host is not None else [None]
        for ip_val in ip_options:
            for port_val in port_options:
                for domain_val in domain_options:
                    key = (
                        _normalize_scope_value(ip_val),
                        _normalize_scope_value(port_val),
                        _normalize_scope_value(domain_val),
                    )
                    if key not in seen:
                        seen.add(key)
                        candidates.append(key)
        if ('*', '*', '*') not in seen:
            candidates.append(('*', '*', '*'))
        for key in candidates:
            entries = static_routes.get(key)
            if entries and path in entries:
                entry = entries[path]
                return (entry['handler'], entry['type'], None)
        for entry in templates:
            template_ip = entry['ip']
            template_port = entry.get('port')
            template_domain = entry['domain']
            if template_ip is not None and template_ip != server_ip:
                continue
            if template_port is not None and template_port != server_port:
                continue
            if template_domain is not None and template_domain != host:
                continue
            template = entry['template']
            if template.matches(server_ip, server_port, host, path):
                extracted = template.extract(path) or {}
                return (entry['handler'], entry['type'], extracted)
        return None

    def _is_https_redirect_exempt(self, path):
        instance = self.http_message_factory.server_instance
        if not instance:
            return False
        for pattern in instance.https_redirect_escape_paths:
            if pattern.endswith('*'):
                if path.startswith(pattern[:-1]):
                    return True
            else:
                if path == pattern:
                    return True
        return False

    def _should_redirect_to_https(self, path):
        instance = self.http_message_factory.server_instance
        if not instance or instance.ssl_enabled or not instance.https_redirect:
            return False
        return not self._is_https_redirect_exempt(path)

    def _apply_https_redirect(self):
        instance = self.http_message_factory.server_instance
        target_host = self.http_message_factory.target_host
        if not target_host and instance and instance.host_entries:
            target_host = instance.host_entries[0]['host']
        if not target_host:
            target_host = instance.bound_ip if instance else 'localhost'
        location_path = self.request_path_with_query if hasattr(self, 'request_path_with_query') else self.http_request_path
        location = f'https://{target_host}{location_path}'
        self.http_message_factory.response_message.set_status(HTTP_Status_Code.MOVED_PERMANENTLY)
        self.http_message_factory.response_message.header.add_header_line(
            HTTP_Message_Header_Line(HTTP_Message_Response_Header_Tag.LOCATION, location)
        )
        self.http_message_factory.response_message.header.add_header_line(
            HTTP_Message_Header_Line(HTTP_Message_Response_Header_Tag.CONTENT_LENGTH, '0')
        )
        self.http_message_factory.response_message.header.add_header_line(
            HTTP_Message_Header_Line(HTTP_Message_Response_Header_Tag.CONNECTION, 'close')
        )
        self.http_message_factory.mime_type = Mime_Type.TEXT
        self.http_message_factory.response_message.content = b''
        self.http_message_factory.stay_alive = False

    def _legacy_get_handler(self, request_path, host, host_rq_path, method):
        handler = None
        mime_type = None
        template_args = None
        if method == HTTP_Method.GET:
            if request_path in self.http_message_factory.get_handler:
                handler = self.http_message_factory.get_handler[request_path][0]
                mime_type = self.http_message_factory.get_handler[request_path][1]
            elif host_rq_path and host_rq_path in self.http_message_factory.get_handler:
                handler = self.http_message_factory.get_handler[host_rq_path][0]
                mime_type = self.http_message_factory.get_handler[host_rq_path][1]
            else:
                template = next(
                    (
                        tpl for tpl in self.http_message_factory.get_templates
                        if tpl.matches(
                            self.http_message_factory.server_ip,
                            self.http_message_factory.server_port,
                            host,
                            request_path
                        )
                    ),
                    None
                )
                if template:
                    handler = template.handler
                    template_args = template.extract(request_path)
                    mime_type = template.type
        if method == HTTP_Method.POST:
            if request_path in self.http_message_factory.post_handler:
                handler = self.http_message_factory.post_handler[request_path][0]
                mime_type = self.http_message_factory.post_handler[request_path][1]
            elif host_rq_path and host_rq_path in self.http_message_factory.post_handler:
                handler = self.http_message_factory.post_handler[host_rq_path][0]
                mime_type = self.http_message_factory.post_handler[host_rq_path][1]
            else:
                template = next(
                    (
                        tpl for tpl in self.http_message_factory.post_templates
                        if tpl.matches(
                            self.http_message_factory.server_ip,
                            self.http_message_factory.server_port,
                            host,
                            request_path
                        )
                    ),
                    None
                )
                if template:
                    handler = template.handler
                    template_args = template.extract(request_path)
                    mime_type = template.type
        if handler:
            return (handler, mime_type, template_args or {})
        return None


    def parse_first_line(self) -> tuple:

        first_line = self.http_message_factory.message_temp.split('\n')[0]
        err = Exception(f'[parse_first_line] failing to parse first line. \'{first_line}\'')
        first_line_tokens = [x for x in re.split(r'\s+',first_line) if x]
        if len(first_line_tokens) == 3:
            http_message_method = first_line_tokens[0]
            http_request_path = first_line_tokens[1]
            http_protocol = first_line_tokens[2]

            if http_message_method not in get_class_fields(HTTP_Method).values():
                self.http_message_factory.response_message.set_status(HTTP_Status_Code.BAD_REQUEST)
                raise err
            
            if http_protocol not in get_class_fields(HTTP_Protocol_Version).values():
                self.http_message_factory.response_message.set_status(HTTP_Status_Code.BAD_REQUEST)
                raise err

            return (http_message_method, http_request_path, http_protocol)
        else:
            self.http_message_factory.response_message.set_status(HTTP_Status_Code.BAD_REQUEST)
            raise err
        

    def set_default_header(self):

        server = HTTP_Message_Header_Line(HTTP_Message_Response_Header_Tag.SERVER,'unknown')
        date = HTTP_Message_Header_Line(HTTP_Message_Response_Header_Tag.DATE,get_http_date())
        cache_control = HTTP_Message_Header_Line(HTTP_Message_Response_Header_Tag.CACHE_CONTROL,'no-store')
        self.http_message_factory.response_message.header.add_header_line(cache_control)
        self.http_message_factory.response_message.header.add_header_line(date)
        self.http_message_factory.response_message.header.add_header_line(server)


    def set_content(self) -> None:

        content = None
        host = self.http_message_factory.target_host
        request_path = self.http_request_path
        host_rq_path =  f"{host}:{self.http_request_path}" if host else None
        if self.http_message_method == HTTP_Method.OPTIONS:
            self.http_message_factory.response_message.set_status(HTTP_Status_Code.NO_CONTENT)
            return
        if self._should_redirect_to_https(request_path):
            self._apply_https_redirect()
            return

        handler_info = None

        if self.http_message_method == HTTP_Method.GET:
            handler_info = self._resolve_handler('GET', request_path, host)
            if handler_info is None:
                handler_info = self._legacy_get_handler(request_path, host, host_rq_path, HTTP_Method.GET)
        elif self.http_message_method == HTTP_Method.POST:
            handler_info = self._resolve_handler('POST', request_path, host)
            if handler_info is None:
                handler_info = self._legacy_get_handler(request_path, host, host_rq_path, HTTP_Method.POST)
        elif self.http_message_method == HTTP_Method.HEAD:
            handler_info = self._resolve_handler('GET', request_path, host)
            if handler_info is None:
                handler_info = self._legacy_get_handler(request_path, host, host_rq_path, HTTP_Method.GET)

        if handler_info:
            handler, mime_type, template_args = handler_info
            if template_args is not None:
                self.args['template_args'] = template_args
            if mime_type:
                self.http_message_factory.mime_type = mime_type
            if handler.__code__.co_argcount == 1:
                content = approach(handler, args=(self.args,), switch=request_path)
            else:
                content = approach(handler, switch=request_path)
        else:
            if self.http_message_method in [HTTP_Method.GET, HTTP_Method.POST]:
                self.http_message_factory.response_message.set_status(HTTP_Status_Code.NOT_FOUND)
            return

        if isinstance(content, AppResponse):
            if content.status:
                self.http_message_factory.response_message.set_status(content.status)
            if content.mime_type:
                self.http_message_factory.mime_type = content.mime_type
            if content.headers:
                for header in content.headers:
                    header_name = None
                    header_value = None
                    if isinstance(header, tuple) and len(header) == 2:
                        header_name, header_value = header
                    elif isinstance(header, dict) and header:
                        header_name, header_value = next(iter(header.items()))
                    if header_name is not None and header_value is not None:
                        self.http_message_factory.response_message.header.add_header_line(
                            HTTP_Message_Header_Line(str(header_name), header_value)
                        )
            content = content.content
            if content is None:
                content = b''

        if isinstance(content, Dynamic):
            data = content.get_bytes()
            mime_type = content.mime_type
            self.http_message_factory.mime_type = mime_type
            header_value = mime_type
            if isinstance(mime_type, (list, tuple)):
                header_value = list(mime_type)
            self.http_message_factory.response_message.header.add_header_line(
                HTTP_Message_Header_Line(HTTP_Message_Response_Header_Tag.CONTENT_TYPE, header_value)
            )
            self.http_message_factory.response_message.set_status(HTTP_Status_Code.OK)
            self.http_message_factory.response_message.append_content(data)
            return

        if isinstance(content, bytes):
            content_type_header = HTTP_Message_Header_Line(HTTP_Message_Response_Header_Tag.CONTENT_TYPE,self.http_message_factory.mime_type)
            self.http_message_factory.response_message.header.add_header_line(content_type_header)
            self.http_message_factory.response_message.set_status(HTTP_Status_Code.OK)
            self.http_message_factory.response_message.append_content(content)
        elif isinstance(content, str):
            content_type_header = HTTP_Message_Header_Line(HTTP_Message_Response_Header_Tag.CONTENT_TYPE,[self.http_message_factory.mime_type,'charset=utf-8'])
            self.http_message_factory.response_message.header.add_header_line(content_type_header)
            self.http_message_factory.response_message.set_status(HTTP_Status_Code.OK)
            self.http_message_factory.response_message.append_content(content.encode('utf-8'))

        elif isinstance(content, PartialContent):
            partial_content:PartialContent = content
            range = self.http_message_factory.range
            if range:
                start = range[0]
                end = range[1] if range[1] else start + partial_content.default_size
                content = content.get_range(start,end)
                content_range_header = HTTP_Message_Header_Line(
                    HTTP_Message_Response_Header_Tag.CONTENT_RANGE,
                    f'bytes {start}-{min(end,partial_content.get_size()-1)}/{partial_content.get_size()}'
                )
                content_type_header1 = HTTP_Message_Header_Line(HTTP_Message_Response_Header_Tag.CONTENT_TYPE,self.http_message_factory.mime_type)
                self.http_message_factory.response_message.header.add_header_line(content_range_header)
                self.http_message_factory.response_message.header.add_header_line(content_type_header1)
                self.http_message_factory.response_message.set_status(HTTP_Status_Code.PARTIAL_CONTENT)
                self.http_message_factory.response_message.append_content(content)
        
        elif isinstance(content, Redirect):
            redirect:Redirect = content
            if redirect.status:
                self.http_message_factory.response_message.set_status(redirect.status)
                self.http_message_factory.response_message.header.add_header_line(HTTP_Message_Header_Line(HTTP_Message_Response_Header_Tag.LOCATION, redirect.path))
            else:
                self.http_message_factory.response_message.set_status(HTTP_Status_Code.SEE_OTHER)
                self.http_message_factory.response_message.header.add_header_line(HTTP_Message_Header_Line(HTTP_Message_Response_Header_Tag.LOCATION, redirect.path))
    def analyze_header(self):

        for header, value in self.http_message_factory.request_header.get_fields().items():
            header = header.lower()
           

            #If the request Message to the server holds content which makes the message larger than 8kb fetch the rest
            if header == HTTP_Message_Request_Header_Tag.HOST.lower():
                host_field = value[0] if value else ''
                host_name = host_field
                if host_field.startswith('['):
                    end = host_field.find(']')
                    if end != -1:
                        host_name = host_field[1:end]
                elif ':' in host_field:
                    host_name = host_field.split(':', 1)[0]
                host_value = host_name or None
                self.http_message_factory.target_host = host_value
                self.args['domain'] = host_value
            if header == HTTP_Message_Request_Header_Tag.COOKIE.lower():
                for val in value:
                    cookie_tokens = val.split("=")
                    if len(cookie_tokens) == 2:
                        self.args['cookies'][cookie_tokens[0]] = cookie_tokens[1]

            if header == HTTP_Message_Request_Header_Tag.CONTENT_TYPE.lower():
                content_type = value[0]
                if content_type == 'application/x-www-form-urlencoded':
                    self.args['flags'].append('urlencoded')

            if header == HTTP_Message_Request_Header_Tag.RANGE.lower():
                if value:
                    value_tokens = value[0].split('=')

                    if len(value_tokens) == 2:
                        whole_range = value_tokens[1]
                        range_parts = whole_range.split('-')
                        start = 0
                        end = 0
                        if len(range_parts) == 2:
                            start = int(range_parts[0])
                            if range_parts[1]:
                                end = int(range_parts[1])
                        self.http_message_factory.range = [start,end]
                        self.args['flags'].append('partial')


    def get_query_string(self, query_string) -> dict:
        
        inner_args = {}
        key_value = query_string.split('&')
        for pair in key_value:
            p = pair.split('=')
            if len(p) == 2:
                inner_args[url_utils.unescape_url(p[0])] = url_utils.unescape_url(p[1])
        self.args['query_string'] = inner_args
   

    def parse(self) -> None:
        
        try:
            self.args = {   
                            'query_string':{},
                            'flags':[],
                            'template_args':{},
                            'cookies': {},
                            'address': self.http_message_factory.addr,
                            'post' : self.http_message_factory.post,
                            'request_header': self.http_message_factory.request_header.get_fields(),
                            'response':self.http_message_factory.response_message,
                            'server': self.http_message_factory.server_instance,
                            'server_ip': self.http_message_factory.server_ip,
                            'server_port': self.http_message_factory.server_port,
                            'domain': None
                        }
            
            self.http_message_method, self.http_request_path, self.http_protocol = self.parse_first_line()
            self.raw_request_target = self.http_request_path
            self.request_path_with_query = self.http_request_path
            self.query_string_raw = ''
            path_tokens = re.split(r'\?(?!.+\/)',self.http_request_path)
            
            #Parse query_string 
            if len(path_tokens) == 2:
                self.http_request_path = url_utils.unescape_url(path_tokens[0])
                self.request_path_with_query = self.http_request_path + '?' + path_tokens[1]
                self.query_string_raw = path_tokens[1]
                self.get_query_string(path_tokens[1])
            else:
                self.http_request_path = url_utils.unescape_url(path_tokens[0])
                self.request_path_with_query = self.http_request_path
                
                
            self.http_message_factory.response_message.set_protocol(self.http_protocol)
            self.http_message_factory.stay_alive = (self.http_protocol == HTTP_Protocol_Version.HTTP_1_1)

            self.analyze_header()
            self.set_default_header()
            self.set_content()
            
        except Exception as e:
            #trace = traceback.print_exc()
            log(f'[PARSE] {e}',log_lvl='debug')
