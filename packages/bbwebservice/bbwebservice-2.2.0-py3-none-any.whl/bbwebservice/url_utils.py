import re
HEX_CHARS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']


#TODO: unefficient af fix that 

def leading_ones_count(encoded_byte):
    byte_value = int(encoded_byte, 16)
    count = 0
    mask = 0x80 
    while mask != 0 and byte_value & mask:
        count += 1
        mask >>= 1
    return count

def unescape_url(url:str) -> str:
    unescaped = ''
    escape_sequence = ''
    index = 0
    count = 0
    url_len = len(url)
    
    while index < url_len:
        
        if len(escape_sequence) == 0 and url[index] == '%' and index + 3 <= url_len and url[index+1] in HEX_CHARS and url[index+2] in HEX_CHARS:
            escape_byte = url[index+1:index+3]
            count =  leading_ones_count(escape_byte)
            escape_sequence += escape_byte
            index += 3
            
        elif url[index] == '%' and index + 3 <= url_len and url[index+1] in HEX_CHARS and url[index+2] in HEX_CHARS and count > 1:
            escape_byte = url[index+1:index+3]
            count -= 1
            escape_sequence+= escape_byte
            index += 3
            
        elif escape_sequence:
            unescaped += decode_hex_string(escape_sequence)
            escape_sequence = ''
            count = 0
        else:
            unescaped += url[index]
            index += 1

    return unescaped if not escape_sequence else unescaped + decode_hex_string(escape_sequence)
            

def decode_hex_string(hex_string:str) ->str:
    try:
        decoded_bytes = bytes.fromhex(hex_string)
        unicode_char = decoded_bytes.decode('utf-8')
        return unicode_char
    except UnicodeDecodeError:
        return ''


def _normalize_port(port_str: str | None):
    if port_str is None:
        return None
    if port_str == '':
        return None
    if not port_str.isdigit():
        raise ValueError(f"Invalid port specifier '{port_str}'.")
    return int(port_str)


def _parse_ip_port(component: str):
    component = component.strip()
    if not component:
        return (None, None)
    ip = None
    port = None
    if component.startswith('['):
        end = component.find(']')
        if end == -1:
            raise ValueError(f"Invalid IPv6 specifier '{component}'.")
        ip = component[1:end]
        remainder = component[end+1:]
        if remainder.startswith(':'):
            port = _normalize_port(remainder[1:])
        elif remainder:
            raise ValueError(f"Invalid specifier '{component}'.")
    else:
        if component.startswith(':'):
            port = _normalize_port(component[1:])
        elif component.count(':') == 1:
            ip_part, port_part = component.split(':', 1)
            ip = ip_part or None
            port = _normalize_port(port_part)
        else:
            ip = component or None
    return (ip, port)


def split_route_scope(route):
    if isinstance(route, UrlTemplate):
        return (route.ip, route.port, route.domain, route.path_template)
    if not isinstance(route, str):
        return (None, None, None, route)
    slash_index = route.find('/')
    if slash_index == -1:
        prefix = route
        path = route if route.startswith('/') else '/' + route
    else:
        prefix = route[:slash_index]
        path = route[slash_index:]
    ip = port = domain = None
    if '::' in prefix:
        ip_part, domain_part = prefix.rsplit('::', 1)
        ip, port = _parse_ip_port(ip_part)
        domain = domain_part.rstrip(':') or None
    elif prefix:
        ip, port = _parse_ip_port(prefix)
    if not path.startswith('/'):
        path = '/' + path if path else '/'
    return (ip, port, domain, path)


def format_ip_port(ip, port):
    if ip is None and port is None:
        return ''
    ip_repr = ''
    if ip is not None:
        ip_repr = f'[{ip}]' if (':' in ip and not ip.startswith('[')) else ip
    if port is not None:
        port_str = str(port)
        if ip_repr:
            return f'{ip_repr}:{port_str}'
        return f':{port_str}'
    return ip_repr


#TODO: native URL matching withoug re for better performance 
#TODO: special hashing where string gets hash of matching template 
import re

class UrlTemplate:
    """
    A URL template wraps a route string with optional IP/port/domain selectors
    plus path placeholders.

    Syntax:
        ip:port::domain:/path/to/{placeholders}

    Examples:
        - '::/status'                                -> matches every endpoint regardless of IP or domain
        - '127.0.0.1::/debug'                        -> IPv4 127.0.0.1, all ports, all domains
        - ':8443::/metrics'                          -> any IP, port 8443
        - ':::example.com:/domain-only'              -> all IPs/ports, only domain `example.com`
        - '127.0.0.1:8000::example.com:/foo'         -> specific IP/port/domain combination
        - '[::1]:8080::/ipv6/{path:path}'            -> IPv6 loopback, port 8080, path wildcard

    Path placeholders use the familiar '{name:type}' syntax and support the built-in
    types ('int', 'str', 'float', 'bool', 'path').
    """

    def __init__(self, template_string):
        self.template = template_string
        self.ip, self.port, self.domain, self.path_template = split_route_scope(template_string)
        self.regex_pattern = '^' + re.sub(r'\{(\w+):(\w+)\}', self._repl, self.path_template) + '$'
        self.handler = None
        self.type = None
    
    def _repl(self, match):
        type_ = match.group(2)
        if type_ == 'int':
            return r'(\d+)'
        elif type_ == 'str':
            return r'(\w+)'
        elif type_ == 'float':
            return r'(\d+\.\d+)'
        elif type_ == 'bool':
            return r'(True|False)'
        elif type_ == 'path':
            return r'(.+)'
        else:
            raise ValueError(f"Unknown type: {type_}")
        
    def convert(self, value, type_):
        if type_ == 'int':
            return int(value)
        elif type_ == 'float':
            return float(value)
        elif type_ == 'bool':
            return value == 'True'
        else:
            return value
        
    def extract(self, url):
        match = re.match(self.regex_pattern, url)
        if match:
            return {k: self.convert(v, t) for (k, t), v in zip(re.findall(r'\{(\w+):(\w+)\}', self.path_template), match.groups())}
        else:
            return None

    def matches(self, ip, port, domain, path):
        if self.ip is not None:
            if ip is None or self.ip != ip:
                return False
        if self.port is not None:
            if port is None or self.port != port:
                return False
        if self.domain and domain and self.domain != domain:
            return False
        if self.domain and domain is None:
            return False
        return re.match(self.regex_pattern, path) is not None
        
    def __eq__(self, url):
        if isinstance(url, str):
            return re.match(self.regex_pattern, url) is not None
        if isinstance(url, self.__class__):
            return (
                self.path_template == url.path_template
                and self.ip == url.ip
                and self.port == url.port
                and self.domain == url.domain
            )
        
        return False
