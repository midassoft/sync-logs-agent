# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import, unicode_literals
import time
import os
import logging
from readers.BaseLogReader import BaseLogReader
import io

logger = logging.getLogger(__name__)

class FileLogReader(BaseLogReader):
    def __init__(self, file_path):
        super(FileLogReader, self).__init__(file_path) 
        self._file = None # Archivo de log
        self._position = 0 # Posición en el archivo
        self._inode = None # Inode del archivo

    def _open_file(self):
        """
        Abre el archivo de log si es necesario y devuelve True si tiene exito.
        Si el archivo no existe o no se puede abrir, devuelve False.
        """
        try:
            if not os.path.exists(self.resource):
                logger.warning(u"FileLogReader: El archivo de log %s no existe.", self.resource)
                if self._file and not self._file.closed:
                    self._file.close()
                    self._file = None 
                self._inode = None 
                return False

            current_inode = os.stat(self.resource).st_ino
            if self._file is None or self._file.closed or current_inode != self._inode:
                if self._file and not self._file.closed:
                    self._file.close()
                
                logger.debug(u"FileLogReader: Abriendo archivo %s. Inode actual: %s, Inode previo: %s", self.resource, current_inode, self._inode)
                self._file = io.open(self.resource, 'r', encoding='utf-8', errors='ignore')
                self._inode = current_inode
                
                logger.debug(u"FileLogReader: Aplicando seek a la posición %s", self._position)
                self._file.seek(self._position)

        except (IOError, OSError) as e:
            logger.error(u"FileLogReader: Error al abrir/stat el archivo %s: %s", self.resource, str(e))
            if self._file and not self._file.closed:
                self._file.close()
            self._file = None
            self._inode = None 
            time.sleep(1) 
            return False
        return True

    def read(self, max_lines=None, timeout=None):
        if not self._open_file():
            return [] 

        lines = []
        start_time = time.time()

        while True:
            try:
                line = self._file.readline()
            except IOError as e:
                logger.error(u"FileLogReader: Error al leer línea del archivo %s: %s. Intentando reabrir.", self.resource, e)
                if self._file: self._file.close() 
                self._file = None
                self._inode = None 
                return lines 
            
            if line:
                lines.append(line.strip())
                self._position = self._file.tell()
                if max_lines and len(lines) >= max_lines: 
                    break
            else: 
                try:
                    if os.path.exists(self.resource): 
                        current_stat = os.stat(self.resource)
                        current_size = current_stat.st_size
                        current_inode = current_stat.st_ino

                        if current_inode != self._inode: 
                            logger.info(u"FileLogReader: Rotación de log detectada (cambio de inode) para %s. Reseteando posición a 0.", self.resource)
                            self._position = 0
                            if self._file: self._file.close()
                            self._file = None 
                            break 
                        elif current_size < self._position:  
                            logger.info(u"FileLogReader: Truncamiento de log detectado para %s (tamaño actual %s < posición %s). Reseteando posición a 0.", self.resource, current_size, self._position)
                            self._position = 0
                            if self._file: self._file.seek(0) 
                    else: 
                        logger.warning(u"FileLogReader: El archivo de log %s ha desaparecido.", self.resource)
                        if self._file and not self._file.closed:
                            self._file.close()
                        self._file = None
                        self._inode = None
                        break 
                except OSError as e:
                    logger.warning(u"FileLogReader: Error al hacer stat del archivo %s: %s", self.resource, e)
                if timeout is not None and (time.time() - start_time) > timeout:
                    break
                time.sleep(0.1) 
        return lines 
    
    def get_current_position(self):
        return self._position
    
    def set_initial_position(self, position):
        """Establece la posición inicial. Usado por el agente antes de la primera lectura."""
        logger.info(u"FileLogReader: Estableciendo posición inicial a %s para %s", position, self.resource)
        self._position = position
        # Si el archivo ya está abierto y es el mismo inode, aplicar el seek.
        # De lo contrario, _open_file() lo manejará al abrir/reabrir.
        if self._file and not self._file.closed:
            try:
                # Verificar inode antes de hacer seek, por si acaso.
                if self._inode == os.stat(self.resource).st_ino:
                    self._file.seek(self._position)
                else:
                    logger.warning(u"FileLogReader: Inode cambió antes de set_initial_position seek. Se aplicará al reabrir.")
            except (IOError, OSError) as e:
                logger.error(u"FileLogReader: Error al hacer seek a la posición %s en set_initial_position: %s", self._position, e)

    def seek_to_end_and_get_position(self):
        """Abre el archivo si es necesario, se posiciona al final y devuelve esa posición."""
        if not self._open_file(): # Asegura que el archivo esté abierto y _inode sea correcto
            logger.warning(u"FileLogReader: No se pudo abrir el archivo %s para posicionar al final.", self.resource)
            return self._position # Devuelve la posición actual (probablemente 0 o la última conocida)
        try:
            self._file.seek(0, os.SEEK_END)
            self._position = self._file.tell()
            logger.info(u"FileLogReader: Posicionado al final del archivo %s en %s.", self.resource, self._position)
        except (IOError, OSError) as e:
            logger.error(u"FileLogReader: Error al intentar posicionar al final del archivo %s: %s", self.resource, e)
        return self._position