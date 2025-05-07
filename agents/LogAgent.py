# -*- coding: utf-8 -*-

import time
import json
import sys
from hashlib import md5
from agents.BaseAgent import BaseAgent
from storage.StateManager import StateManager
from storage.FileStateStorage import FileStateStorage
from readers.FileLogReader import FileLogReader
from clients.JSONAPIClient import JSONAPIClient
from clients.auth.ApiKeyAuth import ApiKeyAuth

class LogAgent(BaseAgent):
    def __init__(self, config):
        super(LogAgent, self).__init__()
        self.config = config

        # dependecies injection
        self.state_manager = StateManager(
            FileStateStorage(config['state_file'])
        )
        self.log_reader = FileLogReader(config['log_file'])

        # client
        self.api_client = JSONAPIClient(
            endpoint=config['api_url'],
            auth_handler=ApiKeyAuth(config['api_token'])
        )
        

        # Inicial configuration
        self.batch_interval = config.get('batch_interval', 0.5)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 5)

    def initialize(self):
        if self.state_manager.state['last_position']:
            self.log_reader._position = self.state_manager.state['last_position']
    
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
        for batch in list(self.state_manager.state['pending_batches']):
            if self._send_batch(batch['data']):
                self.state_manager.remove_pending_batch(batch['id'])
            else:
                batch['retry_count'] += 1
                if batch['retry_count'] > self.max_retries:
                    self.state_manager.remove_pending_batch(batch['id'])
                time.sleep(self.retry_delay)
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
            print("Payload a enviar:", payload)
            
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