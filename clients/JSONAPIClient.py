#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import json
import socket
import logging
from clients.BaseApiClient import BaseApiClient

# Cada módulo define su propio logger. Es una buena práctica.
logger = logging.getLogger(__name__)

class JSONAPIClient(BaseApiClient):
    def __init__(self, endpoint, auth_handler=None):
        """
        Constructor.

        :param endpoint: la URL base de la API sin trailing slash
        :type endpoint: str
        :param auth_handler: manejador de autenticación (opcional)
        :type auth_handler: BaseAuth
        :param timeout: timeout de la conexión en segundos (opcional, por defecto 10)
        :type timeout: int
        """
        self.endpoint = endpoint.rstrip('/')
        self.auth_handler = auth_handler
        self.timeout = 10

    def send(self, endpoint, data):
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'LogAgent/1.0'
        }

        if self.auth_handler:
            headers = self.auth_handler.authenticate(headers)
        
        try:
            body = json.dumps(data)
            req = urllib2.Request(self.endpoint, body, headers)
            response = urllib2.urlopen(req, timeout=self.timeout)
            
            status = response.getcode()
            content = response.read()

            logger.info("✅ API Response: Status Code %s", status)
            if content:
                logger.debug("📦 API Response content: %s", content)

            return status in (200, 201, 204)

        except urllib2.HTTPError as e:
            error_reason = e.reason if hasattr(e, 'reason') else 'Unknown Error'
            logger.error("❌ HTTP Error: %s (%s)", e.code, error_reason)

        except urllib2.URLError as e:
            reason = e.reason if hasattr(e, 'reason') else str(e)
            logger.error("❌ URL Error: %s", reason)

        except socket.timeout:
            logger.error("⏰ Timeout after %s seconds", self.timeout)

        except Exception as e:
            logger.error("⚠️ Unhandled error: %s", str(e))

        return False