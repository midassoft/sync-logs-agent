# -*- coding: utf-8 -*-
import json
import os
from storage.BaseStateStorage import BaseStateStorage

class FileStateStorage(BaseStateStorage):
    def __init__(self, file_path):
        self.file_path = file_path

    def save(self, data):
        temp_file_path = self.file_path + ".tmp"
        try:
            with open(temp_file_path, 'w') as f:
                json.dump(data, f) # Puedes añadir indent=4 para legibilidad si depuras el archivo manualmente
            os.rename(temp_file_path, self.file_path)
        except (IOError, OSError, TypeError) as e: # TypeError si data no es serializable
            self.logger.error("FileStateStorage: ERROR al guardar estado en %s: %s" % (self.file_path, e))
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except OSError as remove_err:
                    self.logger.error("FileStateStorage: Error al eliminar archivo temporal %s: %s" % (temp_file_path, remove_err))
            # Considerar relanzar la excepción o manejarla de alguna forma crítica

    def load(self):
        """
        Load the state from the storage.

        :return: the stored data or None if there is no data stored
        :rtype: object
        """
        if not os.path.exists(self.file_path):
            return None
        with open(self.file_path, 'r') as f:
            return json.load(f)