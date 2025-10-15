import sys as system
import json
from typing import List, Literal, Optional, Union

from .__init__ import MAIN_PATH
from .type_validation import Constraint, Scheme, ValidationError, satisfies

ERROR_PREFIX = '[CONFIG_ERROR]'

HOST_ENTRY_SCHEMA = {
    "host": {"type": str},
    "cert_path": {"type": str},
    "key_path": {"type": str},
}

HOST_TYPE = Union[str, List[Scheme[HOST_ENTRY_SCHEMA]]]

SERVER_BASE_SCHEMA = {
    "ip": {"type": str},
    "port": {"type": Constraint[int, '>=', 0]},
    "queue_size": {"type": Constraint[int, '>=', 0]},
    "max_threads": {"type": Optional[Constraint[int, '>=', 0]], "default": None},
    "https-redirect": {"type": Optional[Literal[True, False]], "default": False},
    "https-redirect-escape-paths": {"type": Optional[List[str]], "default": []},
    "update-cert-state": {"type": Optional[Literal[True, False]], "default": False},
}

SSL_DISABLED_SCHEMA = {
    **SERVER_BASE_SCHEMA,
    "SSL": {"type": Literal[False]},
    "host": {"type": HOST_TYPE, "default": ""},
    "cert_path": {"type": Optional[str], "default": ""},
    "key_path": {"type": Optional[str], "default": ""},
}

SSL_ENABLED_SCHEMA = {
    **SERVER_BASE_SCHEMA,
    "SSL": {"type": Literal[True]},
    "host": {"type": HOST_TYPE, "default": ""},
    "cert_path": {"type": Optional[str], "default": ""},
    "key_path": {"type": Optional[str], "default": ""},
}

SERVER_SCHEMA = Union[Scheme[SSL_DISABLED_SCHEMA], Scheme[SSL_ENABLED_SCHEMA]]

CONFIG_SCHEMA = Scheme({
    "max_threads": {"type": Constraint[int, '>=', 0], "default": 100},
    "max_header_size": {"type": Constraint[int, '>', 0], "default": 16384},
    "max_body_size": {"type": Constraint[int, '>', 0], "default": 10485760},
    "server": {"type": List[SERVER_SCHEMA]},
})


def _normalize_host_entries(host):
    if isinstance(host, list):
        return host
    if isinstance(host, str) and host:
        return [{"host": host, "cert_path": "", "key_path": ""}]
    return []


class Config:
    def __init__(self) -> None:
        """Load and validate configuration values from config.json."""

        config_path = MAIN_PATH + "/config/config.json"

        with open(config_path, 'r', encoding='utf-8') as file:
            config_raw = json.load(file)

        config_data = dict(config_raw)
        errors: List[ValidationError] = []
        is_valid = satisfies(config_data, CONFIG_SCHEMA, strict=True, _errors=errors)
        if not is_valid:
            for error in errors:
                print(ERROR_PREFIX, str(error))
            system.exit(0)

        self.MAX_THREADS = config_data['max_threads']
        self.MAX_HEADER_SIZE = config_data['max_header_size']
        self.MAX_BODY_SIZE = config_data['max_body_size']
        self.SERVERS = []
        for entry in config_data['server']:
            normalized_entry = dict(entry)
            normalized_entry['host'] = _normalize_host_entries(normalized_entry.get('host', ''))
            if normalized_entry['SSL']:
                cert_path = normalized_entry.get('cert_path', '')
                key_path = normalized_entry.get('key_path', '')
                host_entries = normalized_entry['host']
                if not host_entries and (not cert_path or not key_path):
                    print(ERROR_PREFIX, "SSL server requires 'cert_path' and 'key_path' when no host list is provided.")
                    system.exit(0)
                if host_entries and (not cert_path or not key_path):
                    first_host = host_entries[0]
                    normalized_entry['cert_path'] = first_host['cert_path']
                    normalized_entry['key_path'] = first_host['key_path']
            else:
                normalized_entry['cert_path'] = normalized_entry.get('cert_path', '')
                normalized_entry['key_path'] = normalized_entry.get('key_path', '')
            if normalized_entry.get('max_threads') is None:
                normalized_entry['max_threads'] = self.MAX_THREADS
            normalized_entry['https-redirect'] = bool(normalized_entry.get('https-redirect', False))
            normalized_entry['https-redirect-escape-paths'] = list(normalized_entry.get('https-redirect-escape-paths', []))
            normalized_entry['update-cert-state'] = bool(normalized_entry.get('update-cert-state', False))
            self.SERVERS.append(normalized_entry)

    def _get_server_value(self, key):
        if not self.SERVERS:
            return None
        return self.SERVERS[0].get(key)

    def _set_server_value(self, key, value):
        if not self.SERVERS:
            return
        self.SERVERS[0][key] = value

    @property
    def SERVER_IP(self):
        return self._get_server_value('ip')

    @SERVER_IP.setter
    def SERVER_IP(self, value):
        self._set_server_value('ip', value)

    @property
    def SERVER_PORT(self):
        return self._get_server_value('port')

    @SERVER_PORT.setter
    def SERVER_PORT(self, value):
        self._set_server_value('port', value)

    @property
    def QUE_SIZE(self):
        return self._get_server_value('queue_size')

    @QUE_SIZE.setter
    def QUE_SIZE(self, value):
        self._set_server_value('queue_size', value)

    @property
    def SSL(self):
        return self._get_server_value('SSL')

    @SSL.setter
    def SSL(self, value):
        self._set_server_value('SSL', value)

    @property
    def HOST(self):
        return self._get_server_value('host')

    @HOST.setter
    def HOST(self, value):
        self._set_server_value('host', _normalize_host_entries(value))

    @property
    def CERT_PATH(self):
        return self._get_server_value('cert_path')

    @CERT_PATH.setter
    def CERT_PATH(self, value):
        self._set_server_value('cert_path', value)

    @property
    def KEY_PATH(self):
        return self._get_server_value('key_path')

    @KEY_PATH.setter
    def KEY_PATH(self, value):
        self._set_server_value('key_path', value)

    @property
    def SERVER_MAX_THREADS(self):
        return self._get_server_value('max_threads')

    @SERVER_MAX_THREADS.setter
    def SERVER_MAX_THREADS(self, value):
        self._set_server_value('max_threads', value)

    @property
    def HTTPS_REDIRECT(self):
        return self._get_server_value('https-redirect')

    @HTTPS_REDIRECT.setter
    def HTTPS_REDIRECT(self, value):
        self._set_server_value('https-redirect', bool(value))

    @property
    def HTTPS_REDIRECT_ESCAPE_PATHS(self):
        return self._get_server_value('https-redirect-escape-paths')

    @HTTPS_REDIRECT_ESCAPE_PATHS.setter
    def HTTPS_REDIRECT_ESCAPE_PATHS(self, value):
        paths = list(value) if isinstance(value, list) else []
        self._set_server_value('https-redirect-escape-paths', paths)

    @property
    def UPDATE_CERT_STATE(self):
        return self._get_server_value('update-cert-state')

    @UPDATE_CERT_STATE.setter
    def UPDATE_CERT_STATE(self, value):
        self._set_server_value('update-cert-state', bool(value))
