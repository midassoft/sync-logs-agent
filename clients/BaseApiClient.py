from abc import ABCMeta, abstractmethod


class BaseApiClient:
    __metaclass__ = ABCMeta

    @abstractmethod
    def send(self, data):
        pass