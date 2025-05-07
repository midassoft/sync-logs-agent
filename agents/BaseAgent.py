import abc
import signal

class BaseAgent(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.__stop_event = False
        signal.signal(signal.SIGINT, self.graceful_shutdown)
        signal.signal(signal.SIGTERM, self.graceful_shutdown)

    @abc.abstractmethod
    def initialize(self):
        """
        Initialize necessary resources.
        """
        pass

    @abc.abstractmethod
    def execute(self):
        """"
        Principal logic of execution.
        """
        pass

    @abc.abstractmethod
    def cleanup(self):
        """
        Cleanup resources.
        """
        pass

    def graceful_shutdown(self, signum, frame):
        """
        Handle graceful shutdown.
        """
        self.__stop_event = True

    def run(self):
        """"
        Execution flow
        """
        self.initialize()
        try:
            while not self.__stop_event:
                self.execute()
        finally:
            self.cleanup()