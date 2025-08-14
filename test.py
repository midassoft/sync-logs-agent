#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import, unicode_literals
import sys
import codecs
import logging
from config import load_config
from lib import six

# Importa las clases de tu agente que vamos a probar
from readers.FileLogReader import FileLogReader
from clients.JSONAPIClient import JSONAPIClient
from clients.auth.ApiKeyAuth import ApiKeyAuth

# Ahora vamos a configurar el logger del agente para que escriba en la consola sin errores de codificación
# 1. Obtener el logger que vamos a usar
logger = logging.getLogger('AgentTester')
logger.setLevel(logging.INFO)

# 2. Crear un handler que escriba en la consola (stdout)
handler = logging.StreamHandler(sys.stdout)

# 3. SOLO PARA PYTHON 2: Envolver el stream del handler con un codificador UTF-8
#    En python 3, el StreamHandler ya es UTF-8 por defecto
if six.PY2:
    utf8_writer = codecs.getwriter('utf-8')
    handler.stream = utf8_writer(handler.stream, 'strict')

# 4. Definir el formato del mensaje para este handler
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)

# 5. Limpiar cualquier handler preexistente y añadir el nuestro.
#    Esto previene configuraciones duplicadas o conflictivas.
if logger.handlers:
    logger.handlers = []
logger.addHandler(handler)

# 6. Evitar que el mensaje se pase a loggers de nivel superior
logger.propagate = False

class AgentTester(object):
    def __init__(self):
        """
        Carga la configuración e instancia los componentes clave del agente
        para usarlos en las pruebas.
        """
        self.config = load_config()
        
        self.log_reader = FileLogReader(self.config.get('log_file'))
        
        auth_handler = ApiKeyAuth(self.config.get('secret_token'))
        self.api_client = JSONAPIClient(
            endpoint=self.config.get('api_url'),
            auth_handler=auth_handler,
            ssl_cert_file=self.config.get('ssl_cert_file')
        )

    def test_all(self):
        """Ejecuta todas las pruebas en secuencia."""
        tests = [
            ('Acceso al archivo de logs', self.test_log_file_access),
            ('Conectividad y Autenticacion API', self.test_api_connectivity)
        ]
        
        # --- Emojis reemplazados por caracteres ASCII ---
        logger.info(u"--- Iniciando Pruebas de Sanidad del Agente ---")
        all_passed = True
        for name, test_func in tests:
            logger.info(u"--> Probando: %s...", name)
            if not test_func():
                logger.error(u"  [FALLO]: %s\n", name)
                all_passed = False
                break
            else:
                logger.info(u" [OK]: %s\n", name)
        
        if all_passed:
            logger.info(u"  -> ¡Excelente! Todas las pruebas pasaron. El agente esta listo para ejecutarse.")
            return True
        else:
            logger.error(u"  -> Una o mas pruebas fallaron. Revisa la configuracion.")
            return False

    def test_log_file_access(self):
        """
        Verifica que se puede acceder al archivo de logs usando la clase FileLogReader.
        """
        if not self.config.get('log_file'):
            logger.error(u"  -> Variable de entorno LOG_FILE no esta configurada.")
            return False
            
        return self.log_reader._open_file()

    def test_api_connectivity(self):
        """
        Prueba la conexión y autenticación con la API usando la clase JSONAPIClient.
        """
        if not self.config.get('api_url'):
            logger.error(u"  -> Variable de entorno API_URL no esta configurada.")
            return False
        if not self.config.get('secret_token'):
            logger.error(u"  -> Variable de entorno SECRET_TOKEN no esta configurada.")
            return False

        logger.info(u"  -> Intentando enviar un payload de prueba a: %s", self.config.get('api_url'))
        
        test_payload = {
            'test_run': True, 
            'message': 'Connection test from LogAgent'
        }
        success, _ = self.api_client.send('test', test_payload)
        return success


if __name__ == "__main__":
    tester = AgentTester()
    exit_code = 0 if tester.test_all() else 1
    exit(exit_code)