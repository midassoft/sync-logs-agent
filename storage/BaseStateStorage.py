
from __future__ import print_function, division, absolute_import, unicode_literals
import abc
from lib import six

@six.add_metaclass(abc.ABCMeta)
class BaseStateStorage:

    @abc.abstractmethod
    def save(self, state):
        """
        Save the state to the storage.
        """
        pass

    @abc.abstractmethod
    def load(self):
        """
        Load the state from the storage.
        """
        pass