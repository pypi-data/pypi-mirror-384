
#################################################
# HolAdo (Holistic Automation do)
#
# (C) Copyright 2021-2025 by Eric Klumpp
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# The Software is provided “as is”, without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealings in the Software.
#################################################

import logging
from holado_rest.api.rest.rest_client import RestClient
import socket
import urllib.parse
import re
from holado_rest.api.rest.rest_manager import RestManager
from holado.common.handlers.undefined import undefined_argument, undefined_value
import os
from holado_core.common.tools.converters.converter import Converter
from holado_core.common.exceptions.technical_exception import TechnicalException

logger = logging.getLogger(__name__)


class TestServerClient(RestClient):

    @classmethod
    def new_client(cls, use_localhost=undefined_argument, **kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = None
        if 'url' not in kwargs:
            if use_localhost is undefined_argument:
                env_use = os.getenv("HOLADO_USE_LOCALHOST", False)
                use_localhost = Converter.is_boolean(env_use) and Converter.to_boolean(env_use)
            
            url = os.getenv("HOLADO_TEST_SERVER_URL", undefined_value)
            if url is undefined_value:
                scheme = kwargs.get('scheme', undefined_value)
                if scheme is undefined_value:
                    scheme = os.getenv("HOLADO_TEST_SERVER_SCHEME", "http")
                host = kwargs.get('host', undefined_value)
                if host is undefined_value:
                    host = "localhost" if use_localhost else os.getenv("HOLADO_TEST_SERVER_HOST", "holado_test_server")
                port = kwargs.get('port', undefined_value)
                if port is undefined_value:
                    port = os.getenv("HOLADO_TEST_SERVER_PORT", 51232)
                
                if port is None:
                    url = f"{scheme}://{host}"
                else:
                    url = f"{scheme}://{host}:{port}"
            kwargs['url'] = url
        
        manager = RestManager(default_client_class=cls)
        res = manager.new_client(**kwargs)
        
        return res
    
    
    def __init__(self, name, url, headers=None):
        super().__init__(name, url, headers)
        
        self.__is_available = None
    
    @property
    def is_available(self):
        if self.__is_available is None:
            self.__is_available = self.ping()
            logger.info(f"Test server is {'not ' if not self.__is_available else ''}available")
        return self.__is_available
    
    def ping(self):
        url_parsed = urllib.parse.urlparse(self.url)
        netloc_pattern = r"(?P<host>.*?)(?::(?P<port>\d+))?$"
        m = re.match(netloc_pattern, url_parsed.netloc)
        host = m.group('host')
        if m.group('port') is not None:
            port = Converter.to_integer(m.group('port'))
        elif url_parsed.scheme == "http":
            port = 80
        elif url_parsed.scheme == "https":
            port = 443
        else:
            raise TechnicalException(f"Unable to define port used by test-server (URL: '{self.url}')")
        
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            sock.connect((host,port))
        except Exception as exc:
            logger.debug(f"Ping of test server failed for ({host}, {port}): {str(exc)}")
            return False
        else:
            sock.close()
            logger.debug(f"Ping of test server succeeded for ({host}, {port})")
            return True
        
    
    # Manage campaigns actions
    
    def update_stored_campaigns(self):
        response = self.put(f"campaign/update")
        return self.response_result(response, status_ok=[200, 204])
    
    def get_scenario_history(self, scenario_name=None, size=None):
        data = {}
        if scenario_name is not None:
            data['scenario_name'] = scenario_name
        if size is not None:
            data['size'] = size
            
        if data:
            response = self.get(f"campaign/scenario/history", json=data)
        else:
            response = self.get(f"campaign/scenario/history", json=data)
        
        return self.response_result(response, status_ok=[200, 204])
    
    
    
    
    
