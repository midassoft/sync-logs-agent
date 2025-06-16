from __future__ import print_function, division, absolute_import, unicode_literals
import abc
from lib import six

@six.add_metaclass(abc.ABCMeta)
class BaseApiClient:

    @abc.abstractmethod
    def send(self, data):
        """
        Send the data to the API.

        :param data: data to send
        :return: True if the request was successful, False otherwise
        """
        pass