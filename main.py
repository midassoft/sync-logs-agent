#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import, unicode_literals
import sys
import codecs
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
# 1. Obtener el logger RAÍZ. Todos los demás loggers heredarán de este.
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# 2. Crear un handler que escriba en la consola (stdout)
handler = logging.StreamHandler(sys.stdout)

# 3. Envolver el stream del handler con un codificador UTF-8.
utf8_writer = codecs.getwriter('utf-8')
if six.PY2:
    handler.stream = utf8_writer(handler.stream, 'strict')
else:
    handler.stream = utf8_writer(handler.stream)

# 4. Definir el formato del mensaje para este handler
formatter = logging.Formatter('%(asctime)s - %(name)s - [%(levelname)s] %(message)s')
handler.setFormatter(formatter)

# 5. Limpiar cualquier handler preexistente (muy importante) y añadir el nuestro.
if root_logger.handlers:
    root_logger.handlers = []
root_logger.addHandler(handler)

# logger para el propio main.py (ahora heredará la configuración correcta)
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
            logger.error(u"Error creating state directory: %s", str(e))
            sys.exit(1)

    # Crear el archivo de estado si no existe
    if not os.path.exists(state_file):
        logger.info(u"Archivo de estado %s no encontrado. Creando...", state_file)
        try:
            # 1. Definir el estado inicial
            inicial_state = {
                'last_position': 0,
                'pending_batches': []
            }
             # 2. Serializar una cadena de texto JSON
            json_string = json.dumps(inicial_state)
            
            # 3. Abrir en modo binario y escribir los bytes codigi==ficados en UTF-8
            with io.open(state_file, 'wb') as f:
                f.write(json_string.encode('utf-8'))

            logger.info(u"Archivo de estado %s creado exitosamente.", state_file)

        except IOError as e:
            logger.error(u"Error creating state file: %s", str(e))

    # Verificar el archivo de log
    log_file = os.getenv('LOG_FILE')
    if not log_file:
        logger.error(u"LOG_FILE environment variable not set")
        sys.exit(1)

    # Verificar el acceso al archivo de log
    if not os.path.exists(log_file):
        logger.error("Log file %s does not exist" % log_file)
        sys.exit(1)

    # Verificar el acceso de lectura al archivo de log
    if not os.access(log_file, os.R_OK):
        logger.error(u"No read permissions for log file %s" % log_file)
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
        logger.error(u"Error: .env file not found at %s" % filepath)

def main():
    logger.info(u"==> INICIO DEL SCRIPT")

    try:
        # importaciones locales (despues de la configuracion de sys.path)
        from config import load_config
        from agents.LogAgent import LogAgent

        logger.info(u"Starting Log Agent")

        # Cargar variables de entorno desde .env
        load_env()
        logger.info(u"==> .env cargado")

        # Inicializar entorno
        initialize_environment()
        logger.info(u"==> Entorno inicializado")

        # Cargar configuración
        config = load_config()
        logger.info(u"==> Configuración cargada")

        # Inicializar y ejecutar LogAgent
        agent = LogAgent(config)
        logger.info(u"==> LogAgent inicializado. Ejecutando...")
        agent.run()

    except KeyboardInterrupt:
        logger.info(u"Log Agent stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(u"Fatal error: %s" % str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()