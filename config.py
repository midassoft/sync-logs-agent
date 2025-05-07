import os
def load_config():
    return {
        'source': os.getenv('SOURCE'),
        'log_file': os.getenv('LOG_FILE', '/var/log/syslog'),
        'api_url': os.getenv('API_URL', 'http://localhost:8000/logs'),
        'api_token': os.getenv('API_TOKEN', 'default-key'),
        'batch_interval': float(os.getenv('BATCH_INTERVAL', '0.5')),
        'state_file': os.getenv('STATE_FILE', '/tmp/log_agent.state'),
        'max_retries': int(os.getenv('MAX_RETRIES', '3')),
        'retry_delay': int(os.getenv('RETRY_DELAY', '5'))
    }