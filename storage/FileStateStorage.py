# -*- coding: utf-8 -*-
import json
import os
import logging
import traceback # Para logging más detallado si es necesario

logger = logging.getLogger(__name__)

# from storage.BaseStateStorage import BaseStateStorage
# class FileStateStorage(BaseStateStorage):
class FileStateStorage(object): # Usar object si no tienes BaseStateStorage
    def __init__(self, file_path):
        self.file_path = file_path
        logger.debug("FileStateStorage inicializado con ruta: %s", self.file_path)

    def save(self, data):
        temp_file_path = self.file_path + ".tmp"
        operation_failed = False # Flag para saber si debemos relanzar una excepción específica
        original_exception = None

        logger.debug("FileStateStorage: Iniciando guardado de estado. Destino final: %s, Temporal: %s", self.file_path, temp_file_path)
        
        try:
            # 1. Escribir en el archivo temporal
            logger.debug("FileStateStorage: Escribiendo a archivo temporal %s", temp_file_path)
            with open(temp_file_path, 'w') as f:
                json.dump(data, f, indent=4) # indent=4 para legibilidad
            logger.debug("FileStateStorage: Escritura a %s completada.", temp_file_path)

            # 2. Eliminar el archivo de estado original (si existe) - NECESARIO PARA WINDOWS
            if os.path.exists(self.file_path):
                logger.debug("FileStateStorage: Archivo existente %s encontrado. Eliminando...", self.file_path)
                try:
                    os.remove(self.file_path)
                    logger.debug("FileStateStorage: Archivo existente %s eliminado.", self.file_path)
                except OSError as e_remove:
                    operation_failed = True
                    original_exception = e_remove
                    logger.error("FileStateStorage: CRÍTICO - No se pudo eliminar %s. Error: %s", self.file_path, repr(e_remove))
                    # No continuar si no se pudo eliminar el original, el rename fallaría o tendría efectos inesperados
            
            # 3. Renombrar el temporal al original (solo si el paso anterior no falló)
            if not operation_failed:
                logger.debug("FileStateStorage: Renombrando %s a %s", temp_file_path, self.file_path)
                os.rename(temp_file_path, self.file_path) # Puede levantar OSError
                logger.info("FileStateStorage: Estado guardado exitosamente en %s", self.file_path)

        except (IOError, OSError, TypeError) as e: # Captura errores de open, dump, o rename (si no fue el remove)
            operation_failed = True
            original_exception = e
            logger.error("FileStateStorage: ERROR CRÍTICO durante operación de guardado para %s. Excepción: %s", self.file_path, repr(e))
            # logger.debug("Traceback del error en save: %s", traceback.format_exc()) # Descomentar para debug profundo

        finally:
            # Limpiar el archivo temporal si la operación falló y el .tmp todavía existe
            if operation_failed and os.path.exists(temp_file_path):
                logger.debug("FileStateStorage: Operación de guardado falló. Intentando limpiar archivo temporal %s", temp_file_path)
                try:
                    os.remove(temp_file_path)
                    logger.debug("FileStateStorage: Archivo temporal %s eliminado tras error.", temp_file_path)
                except Exception as e_cleanup: 
                    logger.error("FileStateStorage: No se pudo eliminar el archivo temporal %s tras error. Excepción de limpieza: %s", temp_file_path, repr(e_cleanup))
            
            # Si cualquier parte de la operación crítica falló, relanzar la excepción original
            if operation_failed:
                if original_exception:
                    logger.debug("FileStateStorage: Relanzando excepción original: %s", repr(original_exception))
                    raise original_exception # Relanza la excepción específica que causó el fallo
                else:
                    # Esto no debería suceder si operation_failed es True, pero como fallback
                    logger.error("FileStateStorage: Operación de guardado falló pero no se capturó la excepción original. Levantando RuntimeError.")
                    raise RuntimeError("Fallo desconocido durante el guardado del estado en FileStateStorage.")

    def load(self):
        # (Mantén la versión de load que te di antes, que incluye renombrar .corrupt y devuelve None en error)
        logger.debug("FileStateStorage: Intentando cargar estado desde: %s", self.file_path)
        if not os.path.exists(self.file_path):
            logger.info("FileStateStorage: Archivo de estado %s no encontrado. Retornando estado vacío/default.", self.file_path)
            return None
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f) 
            logger.info("FileStateStorage: Estado cargado exitosamente desde %s", self.file_path)
            return data
        except (ValueError, IOError) as e:
            logger.error("FileStateStorage: ERROR al cargar/parsear estado desde %s. Excepción: %s. Retornando estado vacío/default.",
                         self.file_path, repr(e))
            try:
                timestamp = str(time.time()) # Necesitas importar time
                corrupt_file_path = self.file_path + ".corrupt." + timestamp
                os.rename(self.file_path, corrupt_file_path)
                logger.info("FileStateStorage: Archivo de estado corrupto renombrado a %s", corrupt_file_path)
            except Exception as e_rename_corrupt:
                logger.error("FileStateStorage: No se pudo renombrar el archivo de estado corrupto. Error: %s", repr(e_rename_corrupt))
            return None