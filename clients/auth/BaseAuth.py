# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import, unicode_literals
import abc
from lib import six

@six.add_metaclass(abc.ABCMeta)
class BaseAuth(object):

    @abc.abstractmethod
    def authenticate(self, request):
        """Añade autenticación a la petición HTTP.
        :param request: Dict con los datos de la petición (headers, body, etc.)
        :return: Dict modificado
        """
        pass