#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import, unicode_literals
import time
import json
import sys
import logging
import signal
from hashlib import md5
from agents.BaseAgent import BaseAgent
from storage.StateManager import StateManager
from storage.FileStateStorage import FileStateStorage
from readers.FileLogReader import FileLogReader
from clients.JSONAPIClient import JSONAPIClient
from clients.auth.ApiKeyAuth import ApiKeyAuth

logger = logging.getLogger(__name__)

class LogAgent(BaseAgent):
    def __init__(self, config):
        super(LogAgent, self).__init__()
        self.config = config
        
        # AJUSTADO: Límite mucho más conservador para considerar overhead de Laravel/Pusher
        self.MAX_BATCH_SIZE_BYTES = 7500   # Margen de seguridad de 2500 bytes
        self.SAFETY_BUFFER = 2500
        self.MAX_LINE_SIZE_BYTES = 6000    # Para truncar líneas individuales grandes
        
        # Control de interrupción
        self._shutdown_requested = False
        self._cleanup_done = False  # Evitar cleanup múltiple
        self._setup_signal_handlers()

        # estado del agente
        self.state_manager = StateManager(
            FileStateStorage(config['state_file'])
        )

        # reader, lee el archivo de log.
        self.log_reader = FileLogReader(config['log_file'])

        # client, envia los logs a la api.
        self.api_client = JSONAPIClient(
            endpoint=config['api_url'],
            auth_handler=ApiKeyAuth(config['secret_token']),
            ssl_cert_file=self.config.get('ssl_cert_file')
        )

        # Configuración
        self.batch_interval = config.get('batch_interval', 0.5)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 5)
        
    def _setup_signal_handlers(self):
        """Configura manejadores para Ctrl+C y otras señales"""
        def signal_handler(signum, frame):
            logger.info(u"Señal de interrupción recibida (%s). Iniciando shutdown...", signum)
            self._shutdown_requested = True
            
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Kill
        
    def _should_continue(self):
        """Verifica si el agente debe continuar ejecutándose"""
        return not self._shutdown_requested
        
    def initialize(self):
        logger.info(u"LogAgent: Inicializando...")
        
        # NUEVO: Limpiar batches pendientes que son demasiado grandes
        self._clean_oversized_pending_batches()
        
        # Cargar last_position del estado
        last_pos_from_state = self.state_manager.state.get('last_position')

        if last_pos_from_state is not None and last_pos_from_state > 0:
            logger.info(u"LogAgent: Se encontró last_position %s en el estado. Aplicando al lector.", last_pos_from_state)
            self.log_reader.set_initial_position(last_pos_from_state)
        else:
            logger.info(u"LogAgent: No se encontró last_position válida en el estado. Posicionando lector al final del archivo de log.")
            end_position = self.log_reader.seek_to_end_and_get_position()
            self.state_manager.update_position(end_position)
            logger.info(u"LogAgent: Estado actualizado con la posición final del log: %s", end_position)

    def run(self):
        """Loop principal del agente con manejo de shutdown limpio"""
        self.initialize()
        
        logger.info(u"Iniciando loop principal del LogAgent...")
        
        try:
            while self._should_continue():
                self.execute()
                
                # Pequeña pausa para evitar CPU alta cuando no hay datos
                if self._should_continue():
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            logger.info(u"KeyboardInterrupt recibido en LogAgent")
            self._shutdown_requested = True
        except Exception as e:
            logger.error(u"Error en loop principal de LogAgent: %s", str(e))
            self._shutdown_requested = True
        finally:
            # Cleanup una sola vez
            if not self._cleanup_done:
                logger.info(u"Realizando cleanup final...")
                self.cleanup()
                self._cleanup_done = True
            logger.info(u"LogAgent terminó correctamente")
    
    def execute(self):
        # Verificar shutdown al inicio
        if not self._should_continue():
            return
            
        # 1. Procesar batches pendientes (solo los de tamaño válido)
        self._process_pending_batches()

        # Verificar shutdown después de procesar pendientes
        if not self._should_continue():
            return

        # 2. NUEVA LÓGICA: Control granular por línea con interrupciones
        current_batch = []
        current_size_estimate = 0
        last_position = self.log_reader._position  # Guardar posición inicial
        
        # Calcular overhead base del JSON una vez (más conservador)
        base_overhead = len(json.dumps({
            'logs': [],
            'source': self.config.get('source', ''),
            'timestamp': int(time.time())
        }).encode('utf-8'))
        
        # Agregamos overhead adicional para Laravel/Pusher
        laravel_pusher_overhead = 1500  # Metadata adicional de Laravel + Pusher
        total_overhead = base_overhead + laravel_pusher_overhead
        
        for line in self.log_reader.read(timeout=self.batch_interval):
            # Verificar interrupción antes de procesar cada línea
            if not self._should_continue():
                logger.info(u"Interrupción detectada durante procesamiento. Guardando estado...")
                break
                
            try:
                # Convertir línea a string si es necesario
                if isinstance(line, str):
                    line_str = line
                else:
                    line_str = json.dumps(line)
                
                # Calcular tamaño real de la línea en el array JSON
                line_size = len(json.dumps(line_str).encode('utf-8'))
                
                # Manejar líneas individuales demasiado grandes
                if line_size > self.MAX_LINE_SIZE_BYTES:
                    logger.warning(u"Línea de log demasiado grande (%d bytes), truncando a %d bytes", 
                                 line_size, self.MAX_LINE_SIZE_BYTES)
                    line_str = line_str[:self.MAX_LINE_SIZE_BYTES-50] + "...[TRUNCATED]"
                    line_size = len(json.dumps(line_str).encode('utf-8'))
                
                # Estimar tamaño total del payload con esta línea (MÁS CONSERVADOR)
                estimated_payload_size = total_overhead + current_size_estimate + line_size
                if len(current_batch) > 0:
                    estimated_payload_size += len(current_batch) - 1  # Comas entre elementos
                
                # Control granular: ¿Cabe en el batch actual?
                if estimated_payload_size > self.MAX_BATCH_SIZE_BYTES:
                    # Enviar batch actual si tiene contenido
                    if current_batch:
                        if not self._should_continue():
                            logger.info(u"Interrupción detectada antes de envío. Guardando estado...")
                            break
                            
                        self._send_and_handle_batch(current_batch)
                        logger.debug(u"Batch enviado con %d líneas, estimado: %d bytes", 
                                   len(current_batch), total_overhead + current_size_estimate)
                    
                    # Iniciar nuevo batch con la línea actual
                    current_batch = [line_str]
                    current_size_estimate = line_size
                else:
                    # La línea cabe en el batch actual
                    current_batch.append(line_str)
                    current_size_estimate += line_size
                
                # Actualizar última posición conocida
                last_position = self.log_reader._position
                
            except Exception as e:
                logger.error(u"Error procesando línea de log: %s", str(e))
                continue
        
        # Enviar cualquier batch restante (si no hay interrupción)
        if current_batch and self._should_continue():
            self._send_and_handle_batch(current_batch)
            logger.debug(u"Batch final enviado con %d líneas, estimado: %d bytes", 
                       len(current_batch), total_overhead + current_size_estimate)
        
        # IMPORTANTE: Actualizar posición solo UNA VEZ al final
        if last_position != self.state_manager.state.get('last_position'):
            self.state_manager.update_position(last_position)
            
    def _clean_oversized_pending_batches(self):
        """Limpia batches pendientes que excedan el tamaño máximo"""
        pending_batches = self.state_manager.state.get('pending_batches', [])
        original_count = len(pending_batches)
        cleaned_batches = []
        
        for batch_info in pending_batches:
            batch_data = batch_info.get('data', [])
            batch_size = self._calculate_batch_size({'logs': batch_data, 'source': self.config.get('source', ''), 'timestamp': int(time.time())})
            
            if batch_size <= self.MAX_BATCH_SIZE_BYTES:
                cleaned_batches.append(batch_info)
            else:
                logger.warning(u"Eliminando batch pendiente demasiado grande: ID %s, tamaño %d bytes", 
                             batch_info.get('id', 'unknown'), batch_size)
        
        if len(cleaned_batches) != original_count:
            self.state_manager.state['pending_batches'] = cleaned_batches
            self.state_manager.save()
            logger.info(u"Limpieza completada: %d batches eliminados por tamaño excesivo", 
                       original_count - len(cleaned_batches))
            
    def _send_and_handle_batch(self, batch):
        """Envía un batch y maneja el resultado - MEJORADO"""
        # Verificación de seguridad antes de enviar
        payload = {
            'logs': [str(line) if not isinstance(line, str) else line for line in batch],
            'source': self.config.get('source', ''),
            'timestamp': int(time.time())
        }
        
        payload_size = self._calculate_batch_size(payload)
        
        if payload_size > self.MAX_BATCH_SIZE_BYTES:
            logger.error(u"CRÍTICO: Batch de %d bytes excede límite de %d bytes. Esto no debería ocurrir con la nueva lógica. Descartando batch.", 
                        payload_size, self.MAX_BATCH_SIZE_BYTES)
            return  # No enviar ni guardar en pending
        
        if not self._send_batch(batch):
            # Solo agregar a pending si falló por motivos de red, no por tamaño
            batch_id = md5(json.dumps(batch).encode('utf-8')).hexdigest()
            self.state_manager.add_pending_batch({
                'id': batch_id,
                'data': batch,
                'timestamp': time.time(),
                'retry_count': 0
            })
            logger.info(u"Batch agregado a pending por fallo de red: ID %s", batch_id)
    
    def _process_pending_batches(self):
        """Procesa batches pendientes - CON MANEJO DE INTERRUPCIONES"""
        for batch_info in list(self.state_manager.state.get('pending_batches', [])):
            # Verificar interrupción antes de procesar cada batch pendiente
            if not self._should_continue():
                logger.info(u"Interrupción detectada durante procesamiento de batches pendientes.")
                break
                
            if self._send_batch(batch_info['data']):
                logger.info(u"Batch pendiente ID %s enviado exitosamente. Eliminando.", batch_info.get('id'))
                self.state_manager.remove_pending_batch(batch_info.get('id'))
            else:
                batch_id = batch_info.get('id')
                logger.warning(u"Fallo al enviar batch pendiente ID %s.", batch_id)

                new_retry_count = self.state_manager.increment_batch_retry(batch_id)

                if new_retry_count != -1:
                    logger.info(u"Batch ID %s: contador de reintentos actualizado a %s.", batch_id, new_retry_count)
                    if new_retry_count > self.max_retries:
                        logger.warning(u"Batch ID %s eliminado después de %s reintentos.", batch_id, new_retry_count)
                        self.state_manager.remove_pending_batch(batch_id)
                else:
                    logger.error(u"Batch ID %s no encontrado en el estado para incrementar reintentos.", batch_id)

                # Respetar interrupción incluso durante el sleep
                for _ in range(int(self.retry_delay)):
                    if not self._should_continue():
                        logger.info(u"Interrupción detectada durante retry delay.")
                        return
                    time.sleep(1)
                break 

    def _send_batch(self, batch):
        """Envía batch - MEJORADO con mejor validación"""
        try:
            # Asegurar que batch sea una lista
            if not isinstance(batch, list):
                batch = [batch] if batch else []
                
            # Convertir cada línea de log a string si no lo está ya
            processed_logs = []
            for log_line in batch:
                if isinstance(log_line, (dict, list)):
                    processed_logs.append(json.dumps(log_line))
                else:
                    processed_logs.append(str(log_line))
            
            # Construir payload con estructura correcta
            payload = {
                'logs': processed_logs,
                'source': self.config.get('source', ''),
                'timestamp': int(time.time())
            }

            # Validación final de tamaño
            payload_size = self._calculate_batch_size(payload)
            if payload_size > self.MAX_BATCH_SIZE_BYTES:
                logger.error(u"El tamaño del payload (%s bytes) excede el máximo permitido (%s bytes). Batch rechazado definitivamente.", 
                           payload_size, self.MAX_BATCH_SIZE_BYTES)
                return False  # Esto causará que NO se agregue a pending
            
            logger.debug(u"Enviando batch de %d líneas, tamaño: %d bytes", len(processed_logs), payload_size)
            
            success, response = self.api_client.send('logs', payload)
            
            if success:
                logger.debug(u"Batch enviado exitosamente")
            else:
                logger.warning(u"Fallo al enviar batch: %s", response)
                
            return success
            
        except Exception as e:
            logger.error(u"Error sending batch: %s", str(e), exc_info=True)
            return False
        
    def _calculate_batch_size(self, batch):
        """Calcula el tamaño aproximado en bytes del batch serializado como JSON"""
        try:
            return len(json.dumps(batch).encode('utf-8'))
        except Exception as e:
            logger.error(u"Error calculando tamaño del batch: %s", str(e))
            return 0

    def cleanup(self):
        """Cleanup resources - MEJORADO para evitar múltiples ejecuciones"""
        if self._cleanup_done:
            return
            
        logger.info(u"Ejecutando cleanup del LogAgent...")
        try:
            if hasattr(self.log_reader, '_file') and self.log_reader._file:
                self.log_reader._file.close()
            self.state_manager.save()
            logger.info(u"Cleanup completado exitosamente")
        except Exception as e:
            logger.error(u"Error durante cleanup: %s", str(e))
        finally:
            self._cleanup_done = True