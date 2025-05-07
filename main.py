#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import json

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
    if state_dir and not os.path.exists(state_dir):
        os.makedirs(state_dir)

    if not os.path.exists(state_file):
        with open(state_file, 'w') as f:
            json.dump({'last_position': 0, 'pending_batches': []}, f)

    log_file = os.getenv('LOG_FILE')
    if not log_file:
        logger.error("LOG_FILE environment variable not set")
        sys.exit(1)

    if not os.path.exists(log_file):
        logger.error("Log file %s does not exist" % log_file)
        sys.exit(1)

    if not os.access(log_file, os.R_OK):
        logger.error("No read permissions for log file %s" % log_file)
        sys.exit(1)

def load_env(filepath='.env'):
    try:
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    except IOError:
        print("Error: .env file not found at %s" % filepath)

def main():
    print("==> INICIO DEL SCRIPT")

    try:
        # Cargar módulos
        from config import load_config
        from agents.LogAgent import LogAgent

        logger.info("Starting Log Agent")

        # Cargar variables de entorno desde .env
        load_env()
        print("==> .env cargado")

        # Inicializar entorno
        initialize_environment()
        print("==> Entorno inicializado")

        # Cargar configuración
        config = load_config()
        print("==> Configuración cargada: %s" % str(config))
        logger.debug("Loaded configuration: %s" % config)

        # Inicializar y ejecutar LogAgent
        agent = LogAgent(config)
        print("==> LogAgent inicializado. Ejecutando...")
        agent.run()

    except KeyboardInterrupt:
        logger.info("Log Agent stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Fatal error: %s" % str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()
