# Agente de Recolección de Logs

**Versión 1.0.0**

## 1. Resumen

Este agente es una solución ligera y robusta para la recolección y reenvío de logs desde servidores a un endpoint de API centralizado. Su principal característica es que está desarrollado en **Python 2.6** para garantizar la máxima compatibilidad con sistemas operativos legacy (como CentOS 6) que ya no cuentan con soporte oficial, así como con sistemas más modernos que tengan esta versión de Python disponible. Se puede ejecutar en entornos de Python `2.6` y `3.x`.

El agente monitorea un archivo de log en tiempo real, procesa las nuevas entradas en lotes (batches) y los envía de forma segura a una API. Incluye persistencia de estado para evitar la duplicación de logs tras reinicios y un sistema de reintentos para manejar fallos temporales de conexión.

## 2. Características Principales

- **Alta Compatibilidad**: Diseñado para ejecutarse en entornos con Python `2.6`, lo que garantiza la compatibilidad con sistemas operativos legacy. y compatibilidad con Python `3.x`.
- **Persistencia de Estado**: Guarda la última posición de lectura del archivo de log. Si el agente se detiene y reinicia, continuará desde el punto exacto donde se quedó, sin enviar datos duplicados.
- **Procesamiento por Lotes (Batching)**: Agrupa múltiples líneas de log en una sola solicitud para optimizar el rendimiento de la red.
- **Reintentos Automáticos**: Si falla el envío a la API (por problemas de red o del servidor), el agente reintentará el envío varias veces antes de descartar el lote.
- **Configuración Centralizada**: Toda la configuración se maneja a través de un archivo `.env`, facilitando el despliegue en diferentes entornos sin modificar el código.
- **Herramienta de Diagnóstico**: Incluye un script para verificar la conectividad y la configuración antes de la ejecución.

## 3. Requisitos

- **Python 2.6** o una versión compatible de la rama 2.x.
- **Python 3** se trabaja para la compatibilidad con esta version.
- Acceso de lectura al archivo de log que se desea monitorear.
- Conectividad de red hacia el endpoint de la API.

## 4. Instalación y Configuración
#### Primero configura u entorno de prueba local
Esto se hace siguiedo los pasos que estan en este documento [GENERADOR.md](https://github.com/midassoft/sync-logs-agent/blob/main/GENERADOR.md)

Sigue estos pasos para configurar el agente en un servidor:

**Paso 1: Clonar el Repositorio**

```
git clone https://github.com/midassoft/sync-logs-agent.git
cd sync-logs-agent

```

**Paso 2: Configurar el Entorno**

El agente utiliza un archivo `.env` para cargar sus configuraciones. Crea este archivo en la raíz del proyecto copiando el ejemplo:

```
cp .env.example .env

```

Ahora, edita el archivo `.env` con los valores correctos para tu entorno:

```
# (OBLIGATORIO) Identificador único del servidor desde donde se envían los logs.
# Ejemplo: servidor_produccion_db, maquina_centos_01
SOURCE=servidor_centos6

# (OBLIGATORIO) Ruta completa al archivo de log que se va a monitorear.
LOG_FILE=/var/log/mi_app.log

# (OBLIGATORIO) URL completa del endpoint de la API que recibirá los logs.
# URL del servicio centralizado de logs. El agente añade automáticamente '/logs' al final.
# Ejemplos: http://localhost:8000/api, https://logs.empresa.com/api, http://192.168.1.100:3000/api
API_URL=http://localhost:8000/api

# (OBLIGATORIO) Token de autenticación para la API.
# Este es el token es el que esta en el servidor que recibe los logs
SECRET_TOKEN=tu_api_key_secreta

# --- Configuración Avanzada (Valores por defecto recomendados) ---

# Intervalo (en segundos) en que el agente busca nuevas líneas en el log.
# Admite decimales. Ejemplo: 0.5 para 500 milisegundos.
BATCH_INTERVAL=0.5

# Número máximo de veces que el agente reintentará enviar un lote si falla.
MAX_RETRIES=5

# Tiempo de espera (en segundos) entre cada reintento fallido.
# Ayuda a no saturar la red o la API si esta está caída.
RETRY_DELAY=2

# Ruta completa al archivo de estado. El agente necesita permisos de escritura aquí.
# Guarda la última posición leída y los lotes pendientes.
STATE_FILE=/var/run/log_agent.state

```

## 4.3. Variables de Entorno - Referencia Completa

### Descripción Detallada de Cada Variable

A continuación se explica cada variable de entorno, su propósito, dónde obtener su valor y consideraciones importantes:

#### **Variables Obligatorias**

**`SOURCE`** - *Identificador único del servidor*
- **Propósito**: Identifica de forma única el servidor desde donde se envían los logs
- **Dónde obtenerlo**:
  - **Inventario de servidores**: Consultar con el equipo de infraestructura
  - **Convenciones de nombres**: Usar el hostname o un identificador estándar de la organización
  - **Ejemplos**: `web-server-01`, `database-prod-001`, `app-centos-legacy`
- **Importancia**: Crítica para el seguimiento y depuración de logs
- **Consideraciones**: Debe ser único en toda la infraestructura

**`LOG_FILE`** - *Ruta completa al archivo de log*
- **Propósito**: Especifica qué archivo de log será monitoreado
- **Dónde obtenerlo**:
  - **Documentación de la aplicación**: Revisar logs de la app que se va a monitorear
  - **Servidores existentes**: `ls /var/log/` para ver archivos disponibles
  - **Configuración del sistema**: Archivos como `/var/log/syslog`, `/var/log/messages`
- **Ejemplos**: `/var/log/nginx/access.log`, `/var/log/mysql/error.log`
- **Permisos**: El usuario que ejecute el agente debe tener permisos de lectura

**`API_URL`** - *URL del servicio centralizado de logs*
- **Propósito**: Endpoint HTTP donde se enviarán los logs
- **Dónde obtenerlo**:
  - **Equipo de desarrollo**: URL del servicio centralizado de logs
  - **Documentación del proyecto**: Buscar en la documentación del servicio de logs
  - **Configuración existente**: Si ya hay otros servidores enviando logs
- **Formato**: `http://dominio.com/api/logs` o `https://api.empresa.com/v1/logs`
- **Nota**: El agente automáticamente añade `/logs` al endpoint

**`SECRET_TOKEN`** - *Token de autenticación API*
- **Propósito**: Autentica las peticiones al servicio centralizado
- **Dónde obtenerlo**:
  - **Administrador del servicio**: Solicitar token al equipo que mantiene el servicio de logs
  - **Panel de administración**: Si el servicio tiene interfaz web
  - **Configuración del servicio**: Documentación del servicio centralizado
  - **Variables de entorno existentes**: Si ya hay servidores configurados
- **Seguridad**: Mantener secreto y rotar periódicamente
- **Formato**: Generalmente un string alfanumérico largo

#### **Variables Avanzadas (Opcionales)**

**`BATCH_INTERVAL`** - *Intervalo de lectura en segundos*
- **Propósito**: Controla cada cuánto tiempo revisa el agente el archivo de log
- **Valor por defecto**: `0.5` segundos
- **Rango recomendado**: `0.1` - `2.0` segundos
- **Consideraciones**:
  - Valores bajos = Mayor CPU, menor latencia
  - Valores altos = Menor CPU, mayor latencia
  - Ajustar según volumen de logs y recursos disponibles

**`MAX_RETRIES`** - *Número máximo de reintentos*
- **Propósito**: Cuántas veces reintenta enviar un lote si falla
- **Valor por defecto**: `3`
- **Rango recomendado**: `3` - `10`
- **Consideraciones**: Balance entre persistencia y rendimiento

**`RETRY_DELAY`** - *Tiempo de espera entre reintentos*
- **Propósito**: Segundos entre cada reintento fallido
- **Valor por defecto**: `5` segundos
- **Rango recomendado**: `2` - `30` segundos
- **Consideraciones**: Evitar saturar la red o el servicio API

**`STATE_FILE`** - *Archivo de persistencia de estado*
- **Propósito**: Guarda la posición de lectura y lotes pendientes
- **Dónde obtenerlo**:
  - **Permisos de escritura**: Directorio donde el agente pueda escribir
  - **Espacio disponible**: Verificar espacio en disco
  - **Copias de seguridad**: Considerar si debe incluirse en backups
- **Ubicaciones típicas**:
  - `/tmp/log_agent.state` (temporal)
  - `/var/run/log_agent.state` (runtime)
  - `/app/data/state.json` (aplicación)
- **Permisos**: El usuario del agente debe poder escribir

### Guía de Configuración por Entorno

#### **Entorno de Desarrollo**
```bash
SOURCE=dev-server-local
LOG_FILE=/var/log/syslog
API_URL=http://localhost:8000/api/logs
SECRET_TOKEN=dev-token-12345
STATE_FILE=/tmp/log_agent_dev.state
```

#### **Entorno de Producción**
```bash
SOURCE=web-prod-001
LOG_FILE=/var/log/nginx/access.log
API_URL=https://logs.empresa.com/api/logs
SECRET_TOKEN=sk-prod-abcdef123456
STATE_FILE=/var/run/log_agent.state
```

#### **Solución de Problemas Comunes**

**Error: "Variable de entorno no configurada"**
- Verificar que el archivo `.env` existe en la raíz del proyecto
- Revisar que no hay errores de sintaxis (espacios, caracteres especiales)
- Confirmar que las variables están exportadas: `source .env`

**Error: "No se puede acceder al archivo de log"**
- Verificar permisos: `ls -la /ruta/al/logfile`
- Probar acceso manual: `tail -f /ruta/al/logfile`
- Considerar ejecutar el agente con sudo si es necesario

**Error: "Conexión rechazada por el API"**
- Verificar que la URL sea correcta: `curl URL/api/logs`
- Confirmar que el SECRET_TOKEN sea válido
- Revisar conectividad de red: `ping dominio.com`

## 5. Uso del Agente

### Paso 5.1: Probar la Configuración

Antes de ejecutar el agente, es **altamente recomendable** usar el script de prueba para validar que la configuración es correcta. Este script verifica que:

1. El archivo `LOG_FILE` existe y es legible.
2. La conexión con `API_URL` es exitosa.
3. El `SECRET_TOKEN` es aceptado por el servidor (no devuelve error 401 o 403).

Ejecútalo con:

```
python3 test.py

```

**Salida Exitosa:**

```
--- Iniciando Pruebas de Sanidad del Agente ---
--> Probando: Acceso al archivo de logs...
 [OK]: Acceso al archivo de logs

--> Probando: Conectividad y Autenticacion API...
  -> Intentando enviar un payload de prueba a: http://localhost:8000/api/
 [OK]: Conectividad y Autenticacion API

  -> ¡Excelente! Todas las pruebas pasaron. El agente esta listo para ejecutarse.

```

**Salida con Errores:**

```
--- Iniciando Pruebas de Sanidad del Agente ---
--> Probando: Acceso al archivo de logs...
 [OK]: Acceso al archivo de logs

--> Probando: Conectividad y Autenticacion API...
  -> Intentando enviar un payload de prueba a: http://localhost:8000/api/

URL Error: [Errno 61] Connection refused (Attempt 1/3)
URL Error: [Errno 61] Connection refused (Attempt 2/3)
URL Error: [Errno 61] Connection refused (Attempt 3/3)
  [FALLO]: Conectividad y Autenticacion API

  -> Una o mas pruebas fallaron. Revisa la configuracion.

```

Si ves errores, revisa tu archivo `.env` y la conectividad de red.

### Paso 5.2: Ejecutar el Agente

Una vez que las pruebas pasan, puedes iniciar el agente. Se recomienda ejecutarlo como un proceso en segundo plano para que siga funcionando aunque cierres la terminal.

```
# Ejecuta el agente y redirige su salida a un archivo de log propio.
python main.py &

```

- `&`: Envía el proceso a segundo plano.
- Para detener el agente, busca su PID (`ps aux | grep main.py`) y usa `kill <PID>`.

## 6. Estructura del Proyecto

```
.
├── agents/
│   ├── LogAgent.py         # Orquestador principal del agente.
│   └── BaseAgent.py        # Clase base para agentes.
├── clients/
│   ├── JSONAPIClient.py    # Cliente para enviar datos a la API.
│   └── auth/
│       └── ApiKeyAuth.py   # Lógica de autenticación por API Key.
├── readers/
│   └── FileLogReader.py    # Lógica para leer el archivo de log.
├── storage/
│   ├── StateManager.py     # Gestiona el estado del agente.
│   └── FileStateStorage.py # Guarda y carga el estado desde un archivo.
├── .env.example            # Plantilla de configuración.
├── config.py               # Módulo para cargar la configuración desde .env.
├── test.py                 # Script de diagnóstico.
└── main.py                 # Punto de entrada para ejecutar el agente.

```
