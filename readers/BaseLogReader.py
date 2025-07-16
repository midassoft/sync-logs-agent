from __future__ import print_function, division, absolute_import, unicode_literals
import abc
from lib import six

@six.add_metaclass(abc.ABCMeta)
class BaseLogReader:

    def __init__(self, resource):
        self.resource = resource

    @abc.abstractmethod
    def read(self):
        """
        Read data from the resource and return it.
        
        :return: the read data
        :rtype: object
        """
        pass