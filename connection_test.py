#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from config import load_config

# Importa las clases de tu agente que vamos a probar
from readers.FileLogReader import FileLogReader
from clients.JSONAPIClient import JSONAPIClient
from clients.auth.ApiKeyAuth import ApiKeyAuth

# Configuración básica del logger
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('ConnectionTester')

class ConnectionTester(object):
    def __init__(self):
        """
        Carga la configuración e instancia los componentes clave del agente
        para usarlos en las pruebas.
        """
        self.config = load_config()
        
        # 👉 Instanciamos los clientes que vamos a probar
        # 1. Lector de archivos de log
        self.log_reader = FileLogReader(self.config.get('log_file'))
        
        # 2. Cliente API con su manejador de autenticación
        auth_handler = ApiKeyAuth(self.config.get('api_token'))
        self.api_client = JSONAPIClient(
            endpoint=self.config.get('api_url'),
            auth_handler=auth_handler
        )

    def test_all(self):
        """Ejecuta todas las pruebas en secuencia."""
        tests = [
            # El orden es importante: primero el archivo, luego la conexión.
            ('Acceso al archivo de logs', self.test_log_file_access),
            ('Conectividad y Autenticación API', self.test_api_connectivity)
        ]
        
        logger.info("--- Iniciando Pruebas de Sanidad del Agente ---")
        all_passed = True
        for name, test_func in tests:
            logger.info("▶️  Probando: %s...", name)
            if not test_func():
                logger.error("❌ Falló: %s\n", name)
                all_passed = False
                break  # Detiene las pruebas al primer fallo
            else:
                logger.info("✅ Pasó: %s\n", name)
        
        if all_passed:
            logger.info("🎉 ¡Excelente! Todas las pruebas pasaron. El agente está listo para ejecutarse.")
            return True
        else:
            logger.error("🚨 Una o más pruebas fallaron. Revisa la configuración y los logs de error.")
            return False

    def test_log_file_access(self):
        """
        Verifica que se puede acceder al archivo de logs usando la clase FileLogReader.
        Esto prueba que el archivo existe y que hay permisos de lectura.
        """
        if not self.config.get('log_file'):
            logger.error("  → Variable de entorno LOG_FILE no está configurada.")
            return False
            
        # verificamos que se pueda abrir el archivo
        return self.log_reader._open_file()

    def test_api_connectivity(self):
        """
        Prueba la conexión y autenticación con la API usando la clase JSONAPIClient.
        Un solo envío exitoso confirma que la URL es correcta, el servidor responde
        y la API Key es válida.
        """
        if not self.config.get('api_url'):
            logger.error("  → Variable de entorno API_URL no está configurada.")
            return False
        if not self.config.get('api_token'):
            logger.error("  → Variable de entorno API_TOKEN no está configurada.")
            return False

        logger.info("  → Intentando enviar un payload de prueba a: %s", self.config.get('api_url'))
        
        # Prepear el payload
        test_payload = {
            'test_run': True, 
            'message': 'Connection test from LogAgent'
        }
        
        # Enviar el payload
        return self.api_client.send('test', test_payload)


if __name__ == "__main__":
    tester = ConnectionTester()
    # Salimos con código 0 si todo OK, 1 si hay error.
    # Esto es útil para scripts de automatización.
    exit_code = 0 if tester.test_all() else 1
    exit(exit_code)