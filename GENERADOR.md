# Generador de Logs de Prueba

Este script genera logs simulados en formato JSON con diferentes tipos de eventos (recargas, errores de API, accesos, etc.) para propósitos de prueba. Es útil para:

- Probar sistemas de monitoreo de logs
- Evaluar el rendimiento de agentes de log
- Simular cargas de trabajo realistas
- Desarrollar dashboards de visualización

### Características
- Genera 15 tipos diferentes de logs con frecuencias realistas
- Configuración flexible de intervalos entre logs
- Estructura de logs consistente con timestamp, servicio, nivel y contexto
- Soporte para interrupción limpia con `Ctrl+C`

### Configuración Básica
**# Cambiar frecuencia de generación**
Modifica la variable `WRITE_INTERVAL_SECONDS` al inicio del archivo:


**# Intervalo en segundos entre cada log**
WRITE_INTERVAL_SECONDS = 0.3  `Actualizar este valor`

Ejemplos de configuración:

| **Logs por segundo** | **Valor a usar** | **Descripción** |
| --- | --- | --- |
| 1 log/s | **`1.0`** | Intervalo de 1 segundo |
| 2 logs/s | **`0.5`** | Medio segundo entre logs |
| 5 logs/s | **`0.2`** | 200ms entre logs |
| 10 logs/s | **`0.1`** | 100ms entre logs |

### **Archivo de salida**

Por defecto los logs se escriben en **`prueba_de_carga.log`**.
En el repositorio hay un archivo llamado **`prueba_de_carga.log.example`** que se puede usar para probar el agente. solo borra el .example para usarlo.

## **Tipos de Logs Generados**

El script incluye 15 plantillas diferentes:

1. Recargas exitosas (más frecuentes)
2. Accesos HTTP (más frecuentes)
3. Pagos exitosos
4. Errores de API
5. Fallos de autenticación
6. Alertas de base de datos
7. Advertencias de recursos
8. Backups del sistema
9. Alertas de seguridad
10. Errores de conexión a BD
11. Límites de rate
12. Cache misses
13. Notificaciones enviadas
14. Mantenimientos programados

## **Uso Básico**

1. Ejecutar el script:
    ```
    python generador_logs.py
    ```
    
2. Verá la salida en consola con el conteo de logs generados
3. Los logs se escriben en el archivo configurado
4. Presione **`Ctrl+C`** para detener la generación