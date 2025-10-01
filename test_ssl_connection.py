#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
import io

# Configuración de rutas para imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(PROJECT_ROOT, 'lib')
sys.path.insert(0, LIB_DIR)

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def load_env(filepath='.env'):
    """Load environment variables from a .env file"""
    try:
        with io.open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        key, value = parts
                        os.environ[key.strip()] = value.strip()
    except IOError:
        logger.error("Error: .env file not found at %s" % filepath)

def test_ssl_connection():
    """Test SSL connection to the API"""
    logger.info("Testing SSL connection...")

    try:
        # Cargar variables de entorno
        load_env()

        # Importar después de configurar el path
        from config import load_config
        from clients.JSONAPIClient import JSONAPIClient
        from clients.auth.ApiKeyAuth import ApiKeyAuth

        # Cargar configuración
        config = load_config()

        logger.info("API URL: %s", config['api_url'])
        logger.info("API Token: %s", config['api_token'][:10] + "..." if len(config['api_token']) > 10 else config['api_token'])

        # Crear cliente API
        api_client = JSONAPIClient(
            endpoint=config['api_url'],
            auth_handler=ApiKeyAuth(config['api_token'])
        )

        # Datos de prueba
        test_data = {
            'logs': ['Test log message from SSL test'],
            'timestamp': __import__('time').time(),
            'source': config.get('source', 'test')
        }

        logger.info("Attempting to send test data...")

        # Intentar enviar
        success, response = api_client.send('logs', test_data)

        if success:
            logger.info("SUCCESS: SSL connection working!")
            logger.info("Response: %s", response)
        else:
            logger.error("FAILED: Could not connect to API")
            logger.error("Error: %s", response)

    except Exception as e:
        logger.error("Exception occurred: %s", str(e))
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_ssl_connection()