#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import logging
import json
import traceback # Para un logging de errores más detallado

# --- INICIO: Determinar la ruta raíz del agente y el path por defecto para state.json ---
try:
    # __file__ es la ruta del script actual (main.py)
    # os.path.abspath asegura que sea una ruta absoluta
    # os.path.dirname obtiene el directorio de esa ruta
    AGENT_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError: 
    # Fallback si __file__ no está definido (ej. intérprete interactivo, cx_Freeze)
    # sys.argv[0] es el script que se está ejecutando
    AGENT_ROOT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))

DEFAULT_STATE_FILENAME = 'state.json' # Solo el nombre del archivo por defecto
# --- FIN: Determinación de Rutas Base ---

# Configuración básica de logging (como la tenías)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def resolve_state_file_path():
    """
    Determina la ruta absoluta para el state_file.
    Prioridad:
    1. Variable de entorno STATE_FILE (si es absoluta, se usa tal cual).
    2. Variable de entorno STATE_FILE (si es relativa, se une a AGENT_ROOT_DIR).
    3. Default: AGENT_ROOT_DIR / DEFAULT_STATE_FILENAME.
    Devuelve la ruta absoluta.
    """
    state_file_env = os.getenv('STATE_FILE')
    
    if state_file_env:
        if os.path.isabs(state_file_env):
            logger.debug("STATE_FILE es una ruta absoluta desde el entorno: %s", state_file_env)
            return state_file_env
        else: # Ruta relativa en .env (ej. "state.json" o "data/state.json")
            resolved_path = os.path.join(AGENT_ROOT_DIR, state_file_env)
            logger.debug("STATE_FILE es una ruta relativa desde el entorno ('%s'), resuelta a: %s", state_file_env, resolved_path)
            return resolved_path
    else: # No está en .env, usar el default construido con AGENT_ROOT_DIR
        resolved_path = os.path.join(AGENT_ROOT_DIR, DEFAULT_STATE_FILENAME)
        logger.debug("STATE_FILE no configurado en el entorno, usando default: %s", resolved_path)
        return resolved_path

def initialize_environment(current_resolved_state_file_path):
    """
    Verificar y preparar el entorno de ejecución usando la ruta de estado ya resuelta.
    """
    logger.debug("Inicializando entorno con archivo de estado: %s", current_resolved_state_file_path)
    state_dir = os.path.dirname(current_resolved_state_file_path)

    # Crear directorio de estado si no existe (solo si state_dir no es el directorio actual)
    # Si current_resolved_state_file_path es AGENT_ROOT_DIR/state.json, state_dir será AGENT_ROOT_DIR, que ya existe.
    # Esto es más para casos donde state.json podría estar en una subcarpeta como AGENT_ROOT_DIR/data/state.json
    if state_dir and not os.path.exists(state_dir):
        try:
            os.makedirs(state_dir)
            logger.info("Directorio de estado creado: %s", state_dir)
        except OSError as e:
            logger.error("CRÍTICO: No se pudo crear el directorio de estado %s. Error: %s", state_dir, e)
            sys.exit(1)

    # Crear archivo de estado inicial si no existe
    if not os.path.exists(current_resolved_state_file_path):
        try:
            with open(current_resolved_state_file_path, 'w') as f:
                json.dump({'last_position': 0, 'pending_batches': []}, f)
            logger.info("Archivo de estado inicializado: %s", current_resolved_state_file_path)
        except IOError as e:
            logger.error("CRÍTICO: No se pudo crear el archivo de estado inicial %s. Error: %s", current_resolved_state_file_path, e)
            sys.exit(1)

    # Verificar archivo de log (sin cambios respecto a tu versión)
    log_file = os.getenv('LOG_FILE')
    if not log_file:
        logger.error("CRÍTICO: La variable de entorno LOG_FILE no está configurada.")
        sys.exit(1)
    if not os.path.exists(log_file): # LOG_FILE puede ser una ruta absoluta o relativa desde donde ejecutas
        logger.error("CRÍTICO: El archivo de log %s no existe.", log_file)
        sys.exit(1)
    if not os.access(log_file, os.R_OK):
        logger.error("CRÍTICO: Sin permisos de lectura para el archivo de log %s.", log_file)
        sys.exit(1)

def load_env(base_dir):
    """
    Carga variables de un archivo .env ubicado en base_dir.
    """
    filepath = os.path.join(base_dir, '.env')
    try:
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip() # strip() cualquier espacio extra
        logger.info("Variables de entorno cargadas desde %s (si existió).", filepath)
    except IOError:
        logger.warn("Archivo .env no encontrado en %s. Se usarán variables de entorno existentes o valores por defecto.", filepath)

def main():
    print("==> INICIO DEL SCRIPT")
    exit_code = 0 

    try:
        from config import load_config # Asumiendo que tienes config.py
        from agents.LogAgent import LogAgent

        logger.info("Iniciando Log Agent...")
        logger.debug("Raíz del agente detectada: %s", AGENT_ROOT_DIR)

        # Cargar .env desde la raíz del agente
        load_env(AGENT_ROOT_DIR) 
        
        # 1. Resolver la ruta del state_file ANTES de hacer cualquier otra cosa con ella
        final_state_file_path = resolve_state_file_path()
        
        # 2. IMPORTANTE: Establecer la variable de entorno 'STATE_FILE' a la ruta resuelta.
        # Esto asegura que initialize_environment (si la usara directamente) y load_config()
        # obtengan esta ruta definitiva.
        os.environ['STATE_FILE'] = final_state_file_path
        logger.debug("Variable de entorno 'STATE_FILE' establecida para esta ejecución a: %s", final_state_file_path)

        # 3. Inicializar entorno (pasándole la ruta resuelta)
        initialize_environment(final_state_file_path)

        # 4. Cargar configuración (debería usar os.getenv('STATE_FILE') que ahora es la ruta correcta)
        config = load_config() # Tu config.py debería hacer os.getenv('STATE_FILE') sin un default problemático
        
        # Verificar que la config tenga la ruta correcta para el state_file
        if config.get('state_file') != final_state_file_path:
            logger.warn("Posible discrepancia en state_file: main.py resolvió '%s' pero config.py cargó '%s'. "
                        "Asegúrate que config.py usa os.getenv('STATE_FILE') y no otro default conflictivo.",
                        final_state_file_path, config.get('state_file'))
            # Forzar la ruta correcta si es necesario, aunque es mejor que config.py la tome bien.
            # config['state_file'] = final_state_file_path

        logger.info("Configuración cargada. Fuente: %s, Archivo Log: %s, Archivo Estado: %s", 
                    config.get('source', 'N/A'), 
                    config.get('log_file', 'N/A'),
                    config.get('state_file', 'N/A')) # Debería ser final_state_file_path
        logger.debug("Configuración detallada final: %s", config)

        agent = LogAgent(config)
        logger.info("LogAgent inicializado. Ejecutando el agente...")
        agent.run()
        logger.info("Log Agent finalizó su ejecución principal normalmente.")

    except KeyboardInterrupt:
        logger.info("Log Agent interrumpido por el usuario (KeyboardInterrupt detectada en main). El agente debería estar limpiando...")
        exit_code = 130 
    
    except IOError as e:
        if hasattr(e, 'errno') and e.errno == 4: # EINTR
            logger.info("Log Agent: Operación de IO interrumpida (EINTR). Esto puede ocurrir durante el cierre por señal.")
            exit_code = 0 
        else:
            logger.error("CRÍTICO: Error fatal de IO no manejado: %s", str(e))
            logger.error("Traceback:\n%s", traceback.format_exc())
            exit_code = 1
            
    except Exception as e:
        logger.error("CRÍTICO: Error fatal genérico no manejado: %s", str(e))
        logger.error("Traceback:\n%s", traceback.format_exc())
        exit_code = 1
        
    finally:
        logger.info("==> FIN DEL SCRIPT (Código de salida: %s)", exit_code)
        sys.exit(exit_code)

if __name__ == '__main__':
    main()