# Log Forward Agent

![Python](https://img.shields.io/badge/python-2.6+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Un agente ligero para enviar logs en tiempo real a un servicio API remoto.

## Características principales

- ⏱ **Monitoreo en tiempo real** - Lee solo los nuevos logs que se escriben después de iniciar
- 🚀 **Configuración simple** - Interfaz interactiva para configurar múltiples agentes
- ⏳ **Modo prueba** - Opción para ejecutar por tiempo limitado (testing)
- 🔄 **Background** - Los agentes continúan ejecutándose independientemente
- 📦 **Sin dependencias** - Solo requiere Python estándar

## Requisitos

- Python 2.6+
- Acceso a los archivos de log
- Conexión al endpoint API de destino

## Instalación

1. Clona el repositorio o descarga el script:
    ```bash
        git clone https://github.com/tu-usuario/log-forward-agent.git
        cd log-forward-agent
    ```
2. Otorga permisos de ejecución:

    ```bash
        chmod +x log_forward.py
    ```
## Uso básico
Ejecuta el agente interactivamente:
```bash
    python sync-logs-agent.py
```
Sigue las instrucciones para configurar cada agente:

1. Ingresa la ruta del archivo de log

2. Proporciona la URL del API de destino

3. (Opcional) Especifica un tiempo de prueba en segundos

Ejemplo de flujo:

```bash
    === Log Sync Agent ===

    Configure new agent (leave empty to finish setup)
    Log file path: 'file path'
    API URL: 'API_URL' 
    Test duration in seconds (optional): 5
    Agent started (PID: 52) for /var/log/mi_app.log
    Test completed for /var/log/mi_app.log

    Configure new agent (leave empty to finish setup)
    Log file path: /var/log/otro_log.log
    API URL: http://logs-management-app-1:8000/api/logs
    Agent started (PID: 53) for /var/log/otro_log.log

    Configure new agent (leave empty to finish setup)
    Log file path: 

    Agents are running in background.
    To stop agents, use: kill <PID>

    # Aqui para salir al terminal hay que hacer un crtl+c, hasta ahora el sistema me esta mostrando un error en la consola luego del crtl+c, pero el agente sigue ejecutandose
```
## Manejo de agentes
* Listar agentes activos:
```bash
    ps aux | grep log_forward.py
```
* Detener un agente:
```bash
    kill <PID>
```
* Detener todos los agentes:

```bash
    pkill -f log_forward.py
```
Formato de los logs enviados
Cada entrada de log se envía como un objeto JSON con el formato:
```json
{
  "timestamp": "YYYY-MM-DD HH:MM:SS",
  "message": "Contenido completo de la línea de log",
  "source": "/ruta/al/archivo.log"
}
```