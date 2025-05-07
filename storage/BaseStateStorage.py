from abc import ABCMeta, abstractmethod

class BaseStateStorage:
    __metaclass__ = ABCMeta

    @abstractmethod
    def save(self, state):
        """
        Save the state to the storage.
        """
        pass

    @abstractmethod
    def load(self):
        """
        Load the state from the storage.
        """
        pass