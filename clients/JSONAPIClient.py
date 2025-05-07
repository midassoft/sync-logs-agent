#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import json
import socket
import logging
from clients.BaseApiClient import BaseApiClient

logger = logging.getLogger(__name__)

class JSONAPIClient(BaseApiClient):
    def __init__(self, endpoint, auth_handler=None):
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

            print("✅ Response code:", status)
            print("📦 Response content:", content)

            return status in (200, 201, 204)

        except urllib2.HTTPError as e:
            error_content = e.read()
            logger.error("HTTP Error: %s - %s" % (e.code, error_content))
            print("❌ HTTP Error:", e.code)
            print("🔻 Response content:", error_content)

        except urllib2.URLError as e:
            if hasattr(e, 'reason'):
                logger.error("URL Error: %s" % e.reason)
                print("❌ URL Error:", e.reason)
            else:
                logger.error("URL Error: %s" % str(e))
                print("❌ URL Error:", str(e))

        except socket.timeout:
            logger.error("Timeout after %s seconds" % self.timeout)
            print("⏰ Timeout after %s seconds" % self.timeout)

        except Exception as e:
            logger.error("Unhandled error: %s" % str(e))
            print("⚠️ Unhandled error:", str(e))

        return False
