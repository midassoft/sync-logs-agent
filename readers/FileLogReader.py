import time
import os
from readers.BaseLogReader import BaseLogReader

class FileLogReader(BaseLogReader):
    def __init__(self, file_path):
        super(FileLogReader, self).__init__(file_path)
        self._file = None
        self._position = 0
        self._inode = None
        self._size = 0

    def _open_file(self):
        try:
            current_inode = os.stat(self.resource).st_ino
            if self._file is None or self._file.closed or current_inode != self._inode:
                if self._file and not self._file.closed:
                    self._file.close()
                self._file = open(self.resource, 'r')
                self._inode = current_inode
                # Solo seek si es el mismo archivo (no rotado)
                if current_inode == self._inode:
                    self._file.seek(self._position)
        except (IOError, OSError) as e:
            print("Error opening file:", str(e))
            time.sleep(1)
            return False
        return True

    def read(self, max_lines=None, timeout=None):
        if not self._open_file():
            return None

        lines = []
        start_time = time.time()

        while True:
            line = self._file.readline()
            if line:
                lines.append(line.strip())
                self._position = self._file.tell()
                if max_lines and len(lines) >= max_lines:
                    break
            else:
                current_size = os.stat(self.resource).st_size
                if current_size < self._position:  # Log truncado/rotado
                    self._position = 0
                    self._file.seek(0)
                elif timeout and (time.time() - start_time) > timeout:
                    break
                time.sleep(0.1)

        return lines or []