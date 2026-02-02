from __future__ import print_function, division, absolute_import, unicode_literals
import os
import re
import io

def load_env_file():
    """Carga manualmente un archivo .env"""
    try:
        with io.open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"\'')
    except IOError:
        pass  # El archivo .env no existe, usaremos valores por defecto
    except UnicodeDecodeError:
        pass  # No se pudo decodificar el archivo .env


def load_config():
    load_env_file()  # Cargar variables primero
    
    # Determine the project root directory (where this config.py file lives)
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # State file is always relative to the agent installation directory
    # This is an internal implementation detail, not user configuration
    state_file_path = os.path.join(project_root, 'state', 'agent.state')
    
    return {
        'source': os.getenv('SOURCE'),
        'log_file': os.getenv('LOG_FILE', '/var/log/syslog'),
        'api_url': os.getenv('API_URL', 'http://localhost:8000/api/logs'),
        'secret_token': os.getenv('SECRET_TOKEN', 'default-key'),
        'batch_interval': float(os.getenv('BATCH_INTERVAL', '0.5')),
        'state_file': state_file_path,
        'max_retries': int(os.getenv('MAX_RETRIES', '3')),
        'retry_delay': int(os.getenv('RETRY_DELAY', '5')),
        'ssl_cert_file': os.getenv('SSL_CERT_FILE', None)
    }
