# -*- coding: utf-8 -*-

import time
import json
import sys
import logging
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

        # estado del agente, esto lo que hace es que guarda el estado del agente
        # en un archivo de estado.
        self.state_manager = StateManager(
            FileStateStorage(config['state_file'])
        )

        # reader, lee el archivo de log.
        self.log_reader = FileLogReader(config['log_file'])

        # client, envia los logs a la api.
        self.api_client = JSONAPIClient(
            endpoint=config['api_url'],
            auth_handler=ApiKeyAuth(config['api_token'])
        )

        # Inicial configuration, cargar de configuración.
        self.batch_interval = config.get('batch_interval', 0.5)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 5)

    def initialize(self):
        logger.info("LogAgent: Inicializando...")
        # Cargar last_position del estado, usando .get() para seguridad
        last_pos_from_state = self.state_manager.state.get('last_position')

        if last_pos_from_state is not None and last_pos_from_state > 0: # Considerar 0 como no válido o inicio
            logger.info("LogAgent: Se encontró last_position %s en el estado. Aplicando al lector.", last_pos_from_state)
            self.log_reader.set_initial_position(last_pos_from_state)
        else:
            logger.info("LogAgent: No se encontró last_position válida en el estado. Posicionando lector al final del archivo de log.")
            # Mover al final del archivo y obtener esa posición
            end_position = self.log_reader.seek_to_end_and_get_position()
            # Actualizar el estado inmediatamente con esta nueva posición final.
            # Así, si el agente se detiene antes de procesar nada, ya sabe dónde empezar.
            self.state_manager.update_position(end_position)
            logger.info("LogAgent: Estado actualizado con la posición final del log: %s", end_position)
    
    def execute(self):
        # 1. Process batches
        self._process_pending_batches()

        # 2. read new batches
        batch = self.log_reader.read(timeout=self.batch_interval)
        if batch:
            # 3. try to send the batch inmediately
            if not self._send_batch(batch):
                # if failed, add to pending batches
                batch_id = md5(json.dumps(batch).encode('utf-8')).hexdigest()
                self.state_manager.add_pending_batch({
                    'id': batch_id,
                    'data': batch,
                    'timestamp': time.time(),
                    'retry_count': 0
                })
            # 4. update last position
            self.state_manager.update_position(self.log_reader._position)
    
    def _process_pending_batches(self):
        # Iterar sobre una copia para poder modificar la original de forma segura
        for batch_info in list(self.state_manager.state.get('pending_batches', [])):
            if self._send_batch(batch_info['data']):
                logger.info("Batch pendiente ID %s enviado exitosamente. Eliminando.", batch_info.get('id'))
                self.state_manager.remove_pending_batch(batch_info.get('id'))
            else:
                batch_id = batch_info.get('id')
                logger.warn("Fallo al enviar batch pendiente ID %s.", batch_id)

                # Usar el nuevo método del StateManager
                new_retry_count = self.state_manager.increment_batch_retry(batch_id)

                if new_retry_count != -1: # Si el batch fue encontrado y actualizado
                    logger.info("Batch ID %s: contador de reintentos actualizado a %s.", batch_id, new_retry_count)
                    if new_retry_count > self.max_retries:
                        logger.warn("Batch ID %s eliminado después de %s reintentos.", batch_id, new_retry_count)
                        self.state_manager.remove_pending_batch(batch_id)
                else:
                    logger.error("Batch ID %s no encontrado en el estado para incrementar reintentos. Esto no debería suceder.", batch_id)

                time.sleep(self.retry_delay)
                # El 'break' significa que solo se procesa un batch pendiente por llamada a _process_pending_batches.
                # Esto es una estrategia para no sobrecargar si hay muchos fallos. Es aceptable.
                break 

    def _send_batch(self, batch):
        try:
            # Asegúrate que batch sea una lista/dict válida
            if not isinstance(batch, (list, dict)):
                batch = list(batch) if hasattr(batch, '__iter__') else [batch]
                
            payload = {
                'logs': batch if isinstance(batch, list) else [batch],
                'timestamp': time.time(),
                'source': self.config.get('source', 'unknown')
            }
            
            # Debug: verifica el payload
            logger.debug("Payload a enviar:", payload)
            
            return self.api_client.send('logs', payload)
        except Exception as e:
            sys.stderr.write("Error sending batch: %s\n" % str(e))
            return False
        
    def cleanup(self):
        """
        Cleanup resources.
        """
        if hasattr(self.log_reader, '_file') and self.log_reader._file:
            self.log_reader._file.close()
        self.state_manager.save()