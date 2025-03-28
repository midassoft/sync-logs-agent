#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import json
import time
from datetime import datetime

class LogForwarder:
    def __init__(self, log_file, api_url, timeout=10):
        self.log_file = log_file
        self.api_url = api_url
        self.timeout = timeout

    def read_last_lines(self):
        """Lee nuevas líneas del archivo de log"""
        try:
            with open(self.log_file, 'r') as f:
                f.seek(0, 2)  # Ir al final del archivo
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    yield line
        except IOError as e:
            self.log_error("Error leyendo archivo: %s" % str(e))
            raise

    def send_log(self, log_data):
        """Envía un log al servidor API (módulo central)"""
        try:
            request = urllib2.Request(
                url=self.api_url,
                data=json.dumps(log_data),
                headers={'Content-Type': 'application/json'}
            )
            urllib2.urlopen(request, timeout=2)
            return True
        except Exception as e:
            self.log_error("Error enviando log: %s" % str(e))
            return False

    def process_log_line(self, line):
        """Procesa una línea de log antes de enviarla"""
        return {
            'timestamp': datetime.now().isoformat(),
            'message': line.strip(),
            'source': 'centos6_server'
        }

