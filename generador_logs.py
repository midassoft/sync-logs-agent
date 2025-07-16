import json
import time
import random
import datetime
import uuid
import socket
import sys
import os

# --- CONFIGURACIÓN ---
LOG_FILE_PATH = 'prueba_de_carga.log'
# Intervalo en segundos entre cada escritura de log.
WRITE_INTERVAL_SECONDS = 0.3

# --- DATOS DE CONFIGURACIÓN ---
SERVICES = [
    'api5-prod01', 'api5-prod02', 'web-server-01', 'web-server-02',
    'nginx-lb', 'mysql-master', 'mysql-slave', 'redis-cache',
    'MidasPos Beta-Test', 'MidasPos Prod', 'auth-service',
    'payment-gateway', 'notification-service', 'backup-service',
    'monitoring-service'
]

IPS = [
    '192.168.1.100', '192.168.1.101', '10.0.0.5', '10.0.0.6',
    '201.229.162.15', '201.229.162.16', '172.16.0.10', '172.16.0.11'
]

USERS = ['operador1', 'admin', 'user123', 'supervisor', 'cliente001', 'api_user']

# --- PLANTILLAS PARA GENERAR LOGS ---

def create_recharge_log():
    """Genera un log de recarga exitosa."""
    providers = ['claro', 'altice', 'viva']
    levels = ['info', 'informacion', 'inf', 'information']
    return {
        "timestamp": datetime.datetime.now().isoformat(sep=' ', timespec='seconds'),
        "service": "MidasPos Beta-Test",
        "level": random.choice(levels),
        "message": f"Transacción de recarga exitosa para {random.choice(providers)}",
        "context": {
            "method": "POST", "url": "api/v1/transactions/recharge",
            "input": {"provider": random.choice(providers), "number": f"8{random.choice(['09','29','49'])}{random.randint(1000000, 9999999)}", "amount": random.choice([100, 200, 500])},
            "response": {"cod": "00", "auth_code": str(random.randint(10000000, 99999999)), "transaction_id": str(uuid.uuid4())}
        }
    }

def create_api_error_log():
    """Genera un log de error en una API."""
    error_levels = ['error', 'err', 'failure', 'fail', 'critical', 'crit', 'fatal']
    return {
        "timestamp": datetime.datetime.now().isoformat(sep=' ', timespec='seconds'),
        "service": random.choice(SERVICES),
        "level": random.choice(error_levels),
        "message": "Error en consulta de planes: Número no encontrado",
        "context": {
            "method": "POST", "endpoint": "api/data/get_plans",
            "error": {"cod": "05", "message": "Número no encontrado"}, 
            "response_time": f"{random.uniform(0.5, 2.5):.2f}",
            "ip": random.choice(IPS)
        }
    }

def create_auth_failure_log():
    """Genera un log de autenticación fallida."""
    error_levels = ['error', 'err', 'failure', 'fallo', 'error_auth']
    return {
        "timestamp": datetime.datetime.now().isoformat(sep=' ', timespec='seconds'),
        "service": random.choice(SERVICES),
        "level": random.choice(error_levels),
        "message": f"Autenticación fallida para el usuario '{random.choice(USERS)}'",
        "context": {
            "method": "POST", "endpoint": "api/auth/login",
            "input": {"username": random.choice(USERS), "password": "*******"}, 
            "error": {"cod": "401", "message": "Credenciales inválidas"},
            "ip": random.choice(IPS)
        }
    }

def create_database_warning_log():
    """Genera un log de advertencia de base de datos."""
    warning_levels = ['warning', 'warn', 'war', 'advertencia', 'alerta', 'caution']
    return {
        "timestamp": datetime.datetime.now().isoformat(sep=' ', timespec='seconds'),
        "service": random.choice(['mysql-master', 'mysql-slave', 'redis-cache']),
        "level": random.choice(warning_levels),
        "message": "Conexión a base de datos lenta detectada",
        "context": {
            "query_time": f"{random.uniform(2.0, 5.0):.2f}s",
            "query": "SELECT * FROM transactions WHERE date > ?",
            "connection_pool": f"{random.randint(15, 20)}/20",
            "database": "production_db"
        }
    }

def create_nginx_access_log():
    """Genera un log de acceso de nginx."""
    methods = ['GET', 'POST', 'PUT', 'DELETE']
    status_codes = [200, 201, 400, 401, 403, 404, 500, 502, 503]
    info_levels = ['info', 'access', 'acceso', 'information']
    
    return {
        "timestamp": datetime.datetime.now().isoformat(sep=' ', timespec='seconds'),
        "service": "nginx-lb",
        "level": random.choice(info_levels),
        "message": f"Solicitud HTTP procesada",
        "context": {
            "method": random.choice(methods),
            "url": f"/api/v1/{random.choice(['users', 'transactions', 'reports', 'auth'])}",
            "status": random.choice(status_codes),
            "response_time": f"{random.uniform(0.1, 3.0):.3f}s",
            "user_agent": "Mozilla/5.0 (compatible; API-Client/1.0)",
            "ip": random.choice(IPS),
            "bytes_sent": random.randint(500, 5000)
        }
    }

def create_system_resource_warning():
    """Genera un log de advertencia de recursos del sistema."""
    warning_levels = ['warning', 'warn', 'alerta', 'advertencia', 'caution']
    resource_types = ['CPU', 'Memory', 'Disk', 'Network']
    
    return {
        "timestamp": datetime.datetime.now().isoformat(sep=' ', timespec='seconds'),
        "service": "monitoring-service",
        "level": random.choice(warning_levels),
        "message": f"Uso alto de {random.choice(resource_types)} detectado",
        "context": {
            "cpu_usage": f"{random.uniform(75, 95):.1f}%",
            "memory_usage": f"{random.uniform(70, 90):.1f}%",
            "disk_usage": f"{random.uniform(80, 95):.1f}%",
            "server": random.choice(['web-server-01', 'web-server-02', 'api5-prod01']),
            "threshold": "80%"
        }
    }

def create_payment_success_log():
    """Genera un log de pago exitoso."""
    info_levels = ['info', 'success', 'exitoso', 'informacion', 'information']
    return {
        "timestamp": datetime.datetime.now().isoformat(sep=' ', timespec='seconds'),
        "service": "payment-gateway",
        "level": random.choice(info_levels),
        "message": "Pago procesado exitosamente",
        "context": {
            "transaction_id": str(uuid.uuid4()),
            "amount": random.choice([50, 100, 200, 500, 1000]),
            "currency": "DOP",
            "payment_method": random.choice(['credit_card', 'debit_card', 'transfer']),
            "merchant": "MidasPos",
            "customer_id": f"customer_{random.randint(1000, 9999)}",
            "processing_time": f"{random.uniform(0.5, 2.0):.2f}s"
        }
    }

def create_backup_log():
    """Genera un log de backup del sistema."""
    levels = ['info', 'informacion', 'backup_info', 'information']
    return {
        "timestamp": datetime.datetime.now().isoformat(sep=' ', timespec='seconds'),
        "service": "backup-service",
        "level": random.choice(levels),
        "message": "Backup automático completado",
        "context": {
            "backup_type": random.choice(['full', 'incremental', 'differential']),
            "size": f"{random.uniform(1.5, 10.0):.1f}GB",
            "duration": f"{random.uniform(5, 30):.1f}min",
            "destination": "/backups/daily/",
            "files_count": random.randint(1000, 10000),
            "compression": "gzip"
        }
    }

def create_security_alert_log():
    """Genera un log de alerta de seguridad."""
    error_levels = ['error', 'critical', 'alert', 'security', 'critico', 'alerta_seguridad']
    return {
        "timestamp": datetime.datetime.now().isoformat(sep=' ', timespec='seconds'),
        "service": "auth-service",
        "level": random.choice(error_levels),
        "message": "Intento de acceso sospechoso detectado",
        "context": {
            "ip": random.choice(IPS),
            "attempts": random.randint(5, 20),
            "username": random.choice(USERS),
            "time_window": "5min",
            "action": "IP_BLOCKED",
            "geo_location": random.choice(['Santo Domingo', 'Santiago', 'Unknown']),
            "user_agent": "automated-bot/1.0"
        }
    }

def create_database_connection_error():
    """Genera un log de error de conexión a base de datos."""
    error_levels = ['error', 'critical', 'fatal', 'err', 'critico', 'fallo']
    return {
        "timestamp": datetime.datetime.now().isoformat(sep=' ', timespec='seconds'),
        "service": random.choice(['mysql-master', 'mysql-slave']),
        "level": random.choice(error_levels),
        "message": "Error de conexión a base de datos",
        "context": {
            "error_code": random.choice(['2006', '2013', '1045', '1049']),
            "error_message": random.choice([
                "MySQL server has gone away",
                "Lost connection to MySQL server",
                "Access denied for user",
                "Unknown database"
            ]),
            "host": "localhost",
            "port": 3306,
            "database": "production_db",
            "retry_count": random.randint(1, 5)
        }
    }

def create_api_rate_limit_warning():
    """Genera un log de advertencia de límite de rate."""
    warning_levels = ['warning', 'warn', 'advertencia', 'limite', 'throttle']
    return {
        "timestamp": datetime.datetime.now().isoformat(sep=' ', timespec='seconds'),
        "service": random.choice(SERVICES),
        "level": random.choice(warning_levels),
        "message": "Límite de rate alcanzado para usuario",
        "context": {
            "user_id": f"user_{random.randint(100, 999)}",
            "ip": random.choice(IPS),
            "requests_per_minute": random.randint(100, 200),
            "limit": 100,
            "time_window": "1min",
            "action": "throttled",
            "endpoint": f"/api/v1/{random.choice(['users', 'transactions', 'reports'])}"
        }
    }

def create_cache_miss_log():
    """Genera un log de cache miss."""
    levels = ['debug', 'info', 'cache', 'depuracion', 'informacion']
    return {
        "timestamp": datetime.datetime.now().isoformat(sep=' ', timespec='seconds'),
        "service": "redis-cache",
        "level": random.choice(levels),
        "message": "Cache miss detectado",
        "context": {
            "key": f"user_data_{random.randint(1000, 9999)}",
            "cache_type": "redis",
            "ttl": random.randint(300, 3600),
            "hit_rate": f"{random.uniform(85, 95):.1f}%",
            "operation": "GET",
            "fallback": "database_query"
        }
    }

def create_notification_sent_log():
    """Genera un log de notificación enviada."""
    info_levels = ['info', 'sent', 'enviado', 'informacion', 'notification']
    return {
        "timestamp": datetime.datetime.now().isoformat(sep=' ', timespec='seconds'),
        "service": "notification-service",
        "level": random.choice(info_levels),
        "message": "Notificación enviada exitosamente",
        "context": {
            "notification_id": str(uuid.uuid4()),
            "type": random.choice(['email', 'sms', 'push', 'webhook']),
            "recipient": f"user_{random.randint(100, 999)}@example.com",
            "template": random.choice(['welcome', 'payment_confirm', 'alert', 'reminder']),
            "delivery_time": f"{random.uniform(0.1, 2.0):.2f}s",
            "status": "delivered"
        }
    }

def create_maintenance_log():
    """Genera un log de mantenimiento."""
    levels = ['info', 'maintenance', 'mantenimiento', 'informacion', 'scheduled']
    return {
        "timestamp": datetime.datetime.now().isoformat(sep=' ', timespec='seconds'),
        "service": random.choice(SERVICES),
        "level": random.choice(levels),
        "message": "Mantenimiento programado iniciado",
        "context": {
            "maintenance_type": random.choice(['update', 'restart', 'cleanup', 'optimization']),
            "estimated_duration": f"{random.randint(5, 30)}min",
            "affected_services": random.sample(SERVICES, random.randint(1, 3)),
            "maintenance_window": "02:00-04:00",
            "scheduled_by": "admin"
        }
    }

# Lista de funciones generadoras con diferentes pesos para simular frecuencia real
log_generators = [
    # Logs más frecuentes
    create_recharge_log,
    create_recharge_log,
    create_nginx_access_log,
    create_nginx_access_log,
    create_nginx_access_log,
    create_payment_success_log,
    create_payment_success_log,
    create_notification_sent_log,
    create_cache_miss_log,
    
    # Logs moderadamente frecuentes
    create_api_error_log,
    create_auth_failure_log,
    create_database_warning_log,
    create_api_rate_limit_warning,
    
    # Logs menos frecuentes
    create_system_resource_warning,
    create_backup_log,
    create_security_alert_log,
    create_database_connection_error,
    create_maintenance_log
]

def main():
    """Bucle principal que escribe los logs en el archivo."""
    print(f"✍️  Iniciando escritor de logs avanzado. Escribiendo en: {LOG_FILE_PATH}")
    print(f"📊  Tipos de logs disponibles: {len(set([func.__name__ for func in log_generators]))}")
    
    log_count = 0
    try:
        while True:
            try:
                # 1. Elige un generador de logs al azar y crea un objeto de log.
                generator_func = random.choice(log_generators)
                log_object = generator_func()
                
                # 2. Convierte el objeto de log (diccionario de Python) a un string JSON.
                json_string = json.dumps(log_object, ensure_ascii=False)
                
                # 3. Abre el archivo en modo 'append' ('a') y escribe el string JSON.
                with open(LOG_FILE_PATH, 'a', encoding='utf-8') as log_file:
                    log_file.write(json_string + '\n')
                
                log_count += 1
                print(f"[{log_count:04d}] {log_object['service']} | {log_object['level'].upper()} | {log_object['message'][:60]}...")

            
            except Exception as e:
                print(f"❌ Error al escribir en el archivo de logs: {e}")
                
            # 4. Espera antes de escribir el siguiente log.
            time.sleep(WRITE_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print(u"Generador de logs avanzado detenido por el usuario.")
        sys.exit(0)

if __name__ == "__main__":
    main()