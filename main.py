#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import, unicode_literals
import sys
import os
import json
import logging
import io


# configuracion de rutas para imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(PROJECT_ROOT, 'lib')
sys.path.insert(0, LIB_DIR)

import six
from six.moves.urllib import request, error

# Configuración básica de logging compatible con Python 2
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_environment():
    """
    Verificar y preparar el entorno de ejecución (Python 2 compatible)
    """
    state_file = os.getenv('STATE_FILE', '/tmp/log_agent.state')
    state_dir = os.path.dirname(state_file)

    # Crear el directorio de estado si no existe
    if state_dir and not os.path.exists(state_dir):
        try:
            os.makedirs(state_dir)
        except OSError as e:
            logger.error("Error creating state directory: %s", str(e))
            sys.exit(1)

    # Crear el archivo de estado si no existe
    if not os.path.exists(state_file):
        try:
            with io.open(state_file, 'w', encoding='utf-8') as f:
                # Inicializar el archivo de estado
                json.dump({'last_position': 0, 'pending_batches': []}, f)
        except IOError as e:
            logger.error("Error creating state file: %s", str(e))

    # Verificar el archivo de log
    log_file = os.getenv('LOG_FILE')
    if not log_file:
        logger.error("LOG_FILE environment variable not set")
        sys.exit(1)

    # Verificar el acceso al archivo de log
    if not os.path.exists(log_file):
        logger.error("Log file %s does not exist" % log_file)
        sys.exit(1)

    # Verificar el acceso de lectura al archivo de log
    if not os.access(log_file, os.R_OK):
        logger.error("No read permissions for log file %s" % log_file)
        sys.exit(1)

def load_env(filepath='.env'):
    """
    Load environment variables from a .env file
    Args: 
        filepath (str): The path to the .env file

    Raises:
        IOError: If file cannot be opened
        ValueError: for malformed lines
    """
    try:
        with io.open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        key, value = parts
                        os.environ[key.strip()] = value.strip()
                    else:
                        logger.warning("Invalid line in .env file (missing '='): %s", line)
    except IOError:
        logger.error("Error: .env file not found at %s" % filepath)

def main():
    logger.info("==> INICIO DEL SCRIPT")

    try:
        # importaciones locales (despues de la configuracion de sys.path)
        from config import load_config
        from agents.LogAgent import LogAgent

        logger.info("Starting Log Agent")

        # Cargar variables de entorno desde .env
        load_env()
        logger.info("==> .env cargado")

        # Inicializar entorno
        initialize_environment()
        logger.info("==> Entorno inicializado")

        # Cargar configuración
        config = load_config()
        logger.info("==> Configuración cargada")

        # Inicializar y ejecutar LogAgent
        agent = LogAgent(config)
        logger.info("==> LogAgent inicializado. Ejecutando...")
        agent.run()

    except KeyboardInterrupt:
        logger.info("Log Agent stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Fatal error: %s" % str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()