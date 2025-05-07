# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod

class BaseAuth(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def authenticate(self, request):
        """Añade autenticación a la petición HTTP.
        :param request: Dict con los datos de la petición (headers, body, etc.)
        :return: Dict modificado
        """
        pass