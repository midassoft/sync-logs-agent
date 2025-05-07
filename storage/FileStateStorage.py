import json
import os
from storage.BaseStateStorage import BaseStateStorage

class FileStateStorage(BaseStateStorage):
    def __init__(self, file_path):
        self.file_path = file_path

    def save(self, data):
        """
        Save the state to the storage.

        :param data: the data to store
        :type data: object
        """
        with open(self.file_path, 'w') as f:
            json.dump(data, f)

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