# **Documentación del Agente de Logs (LogAgent)**

## **Descripción**

El LogAgent es un agente de monitoreo de logs que lee archivos de log locales, envía los datos a un servidor remoto a través de una API REST, y mantiene un estado persistente para garantizar que no se pierdan datos incluso después de reinicios.

## **Características principales**

- Monitoreo continuo de archivos de log
- Detección automática de rotación y truncamiento de logs
- Envío por lotes con intervalo configurable
- Reintentos automáticos para fallos de red o del servidor
- Persistencia del estado (posición en el log y lotes pendientes)
- Autenticación por API Key
- Compatible con Python 2

## **Configuración**

El agente se configura mediante variables de entorno. Puedes crea un archivo **`.env`** en el directorio raíz con las siguientes variables:

### **Configuración mínima requerida**

```
SOURCE=nombre_del_agente
LOG_FILE=/ruta/al/archivo.log
API_URL=http://url.del.servidor/api/logs
API_TOKEN=tu_api_key_secreta
```

### **Configuración opcional**

```
# Intervalo en segundos entre lecturas de lotes (default: 0.5)
BATCH_INTERVAL=0.5

# Máximo número de reintentos para envíos fallidos (default: 3)
MAX_RETRIES=3

# Tiempo de espera entre reintentos en segundos (default: 5)
RETRY_DELAY=5

# Archivo donde se guarda el estado (default: /tmp/log_agent.state)
STATE_FILE=/ruta/estado/state.json
```

## **Instalación y Uso**

1. Clona el repositorio o copia los archivos del agente
2. Crea un archivo **`.env`** con tu configuración
3. Ejecuta el agente:

```
python main.py
```

## **Requisitos del sistema**

- Python 2.7
- Permisos de lectura en el archivo de log especificado
- Permisos de escritura en el directorio del archivo de estado
- Conexión a internet para enviar logs al servidor remoto

## **Comportamiento del Agente**

1. **Inicialización**:
    - Verifica que el archivo de log exista y sea legible
    - Carga la última posición conocida del archivo de estado
    - Si no hay estado previo, comienza desde el final del archivo
2. **Ejecución continua**:
    - Lee nuevas líneas del log en intervalos configurados
    - Envía los lotes al servidor remoto
    - Si falla el envío, guarda el lote como pendiente y reintenta más tarde
    - Actualiza la posición actual en el archivo de estado
3. **Manejo de errores**:
    - Reintenta enviar lotes fallidos hasta **`MAX_RETRIES`** veces
    - Detecta rotación/truncamiento de logs y ajusta la posición
    - Maneja pérdida temporal de conexión o indisponibilidad del servidor
4. **Cierre limpio**:
    - Guarda el estado actual al terminar
    - Cierra el archivo de log correctamente

## **Estructura del Proyecto**

```
logs-agent/
├── agents/
│   ├── BaseAgent.py
│   └── LogAgent.py         # Agente principal
├── clients/
│   ├── BaseApiClient.py
│   ├── JSONAPIClient.py    # Cliente HTTP para la API
│   └── auth/               # Módulos de autenticación
├── config.py               # Configuración
├── main.py                 # Punto de entrada
├── readers/                # Lectores de logs
├── storage/                # Manejo de estado persistente
└── .env.example            # Ejemplo de archivo de configuración
```

## **Notas**

- El agente no modifica ni borra los archivos de log originales
- El formato de los logs enviados al servidor incluye metadatos como timestamp y origen
- El estado se guarda de forma atómica para prevenir corrupción