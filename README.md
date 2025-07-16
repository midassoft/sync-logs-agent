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
Esto se hace siguiedo los pasos que estan en este documento [GENERADOR.md](empty)

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
# Esta es la url que se esta trabajando en local, puedes cambiarla, pero el servidor que recibe los logs recibe un POST en api/logs 
# Solo se necesita la url sin el `logs` ya que el agente se encarga de poner esto.
API_URL=http://host/api/ 

# (OBLIGATORIO) Token de autenticación para la API.
# Este es el token es el que esta en el servidor que recibe los logs
API_TOKEN=tu_api_key_secreta

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

## 5. Uso del Agente

### Paso 5.1: Probar la Configuración

Antes de ejecutar el agente, es **altamente recomendable** usar el script de prueba para validar que la configuración es correcta. Este script verifica que:

1. El archivo `LOG_FILE` existe y es legible.
2. La conexión con `API_URL` es exitosa.
3. El `API_TOKEN` es aceptado por el servidor (no devuelve error 401 o 403).

Ejecútalo con:

```
python3 connection_test.py

```

**Salida Exitosa:**

```
--- Iniciando Pruebas de Sanidad del Agente ---
--> Probando: Acceso al archivo de logs...
 [OK]: Acceso al archivo de logs

--> Probando: Conectividad y Autenticacion API...
  -> Intentando enviar un payload de prueba a: http://192.168.5.241:8000/api/
 [OK]: Conectividad y Autenticacion API

  -> ¡Excelente! Todas las pruebas pasaron. El agente esta listo para ejecutarse.

```

**Salida con Errores:**

```
--- Iniciando Pruebas de Sanidad del Agente ---
--> Probando: Acceso al archivo de logs...
 [OK]: Acceso al archivo de logs

--> Probando: Conectividad y Autenticacion API...
  -> Intentando enviar un payload de prueba a: http://192.168.5.241:8000/api/

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
├── connection_test.py      # Script de diagnóstico.
└── main.py                 # Punto de entrada para ejecutar el agente.

```
