#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import, unicode_literals
import sys
import os
import json
import socket
import logging
import time
from clients.BaseApiClient import BaseApiClient
import ssl

# Configuración de imports para six (compatible con estructura de carpetas)
LIB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib')
sys.path.insert(0, LIB_DIR)
try:
    import six
    from six.moves.urllib import request, error
except ImportError as e:
    logging.error("Critical error: Could not import six library: %s", str(e))
    sys.exit(1)

logger = logging.getLogger(__name__)

class JSONAPIClient(BaseApiClient):
    def __init__(self, endpoint, auth_handler=None, timeout=10, ssl_cert_file=None):
        """
        Constructor mejorado.

        Args:
            endpoint (str): URL base de la API (sin trailing slash)
            auth_handler (BaseAuth, optional): Manejador de autenticación
            timeout (int, optional): Timeout en segundos. Default 10.
        """
        self.endpoint = endpoint.rstrip('/')
        self.auth_handler = auth_handler
        self.timeout = timeout
        self.retry_attempts = 3  # Nuevo: intentos de reintento
        self.retry_delay = 1     # Nuevo: delay entre reintentos (segundos)
        self.ssl_cert_file = ssl_cert_file

    def create_ssl_context(self):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # ¡Solo para desarrollo!
        return context

    def _prepare_request(self, data):
        """Prepara los headers y body de la request."""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'LogAgent/1.0',
            'Accept': 'application/json',
        }
        
        if self.auth_handler:
            headers = self.auth_handler.authenticate(headers)
        
        return headers, json.dumps(data).encode('utf-8')

    def _create_ssl_context(self):
        """Crea un contexto SSL que desactiva verificación para desarrollo local."""
        # Para desarrollo local con dominios .test o .local, desactivar verificación SSL
        if self._is_local_development():
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            logger.debug(u"Usando SSL sin verificación para desarrollo local")
            return ssl_context

        # Para producción, usar verificación SSL estricta
        return ssl.create_default_context()

    def _is_local_development(self):
        """Determina si la URL es de desarrollo local."""
        if not self.endpoint:
            return False

        local_domains = ['.test', '.local', 'localhost', '127.0.0.1']
        return any(domain in self.endpoint for domain in local_domains)

    def _handle_response(self, response):
        # intentar decodificar la respuesta como JSON
        """Maneja la respuesta de la API."""
        if not response:
            logger.error(u"Empty response received from API.")
            return False, None
        """Procesa la respuesta de la API."""
        status = response.getcode()
        logger.debug(u"Response status code: %s", status)
        content = response.read()
        
        logger.info(u"API Response [%s]", status)
        if content:
            try:
                # Intenta decodificar el contenido como JSON antes de parsear
                decoded_content = content.decode('utf-8')
                json_response = json.loads(content)
                logger.debug(u"Response content: %s", 
                           json.dumps(json_response, indent=2))
                return True, json_response
            except ValueError:
                logger.debug(u"Raw response: %s", content)
        
        return status in (200, 201, 204), None

    def send(self, endpoint, data):
        """
        Envía datos a la API con manejo de errores robusto.
        
        Args:
            endpoint (str): Endpoint específico (se une a self.endpoint)
            data (dict): Datos a enviar
            
        Returns:
            tuple: (success, response_data)
        """
        base_url = self.endpoint.rstrip('/')
        clean_endpoint = endpoint.lstrip('/')
        
        # Si la base_url ya termina con el endpoint que queremos enviar, no lo duplicamos
        # Verificamos que termine en "/endpoint" o que sea exactamente el endpoint
        if base_url.endswith('/' + clean_endpoint) or base_url == clean_endpoint:
            url = base_url
        else:
            url = base_url + '/' + clean_endpoint

        ssl_context = self.create_ssl_context()
        
        logger.debug(u"URL de destino: %s", url)
        
        for attempt in range(self.retry_attempts):
            try:
                headers, body = self._prepare_request(data)
                logger.debug(u"Request body: %s", body.decode('utf-8'))
                req = request.Request(url, body, headers)
                start_time = time.time()
                response = request.urlopen(req, timeout=self.timeout, context=ssl_context) #borrar
                latency = time.time() - start_time
                
                logger.debug(u"Request latency: %.2fs", latency)
                return self._handle_response(response)
                
            except error.HTTPError as e:
                error_reason = getattr(e, 'reason', 'Unknown Error')
                logger.error(u"HTTP Error %s: %s (Attempt %d/%d)", 
                            e.code, error_reason, attempt+1, self.retry_attempts)
                if attempt == self.retry_attempts - 1:
                    return False, {'error': error_reason, 'code': e.code}
                
            except error.URLError as e:
                reason = getattr(e, 'reason', str(e))
                logger.error(u"URL Error: %s (Attempt %d/%d)", 
                           reason, attempt+1, self.retry_attempts)
                if attempt == self.retry_attempts - 1:
                    return False, {'error': reason}
                
            except socket.timeout:
                logger.error(u"Timeout after %s seconds (Attempt %d/%d)", 
                           self.timeout, attempt+1, self.retry_attempts)
                if attempt == self.retry_attempts - 1:
                    return False, {'error': 'timeout'}
                
            except Exception as e:
                logger.error(u"Unhandled error: %s", str(e), exc_info=True)
                return False, {'error': str(e)}
            
            if attempt < self.retry_attempts - 1:
                time.sleep(self.retry_delay)
        
        return False, {'error': 'max retries exceeded'}