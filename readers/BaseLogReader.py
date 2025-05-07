from abc import ABCMeta, abstractmethod

class BaseLogReader:
    __metaclass__ = ABCMeta
    def __init__(self, resource):
        self.resource = resource

    @abstractmethod
    def read(self):
        """
        Read data from the resource and return it.
        
        :return: the read data
        :rtype: object
        """
        pass