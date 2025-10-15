from abc import abstractmethod

from openobd.communication.response_exceptions import ResponseException
import logging

class Socket:

    def __init__(self):
        self.socket_finished = False
        self.__enter__()

    def __enter__(self):
        return self

    def __del__(self):
        self.__exit__(None, None, None)

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            if isinstance(exc_type, ResponseException):
                logging.error(f'Request failed: {exc_value}')
            else:
                pass

        # Make sure we stop the socket once
        if self.socket_finished:
            return

        self.socket_finished = True

        # Finally stop the socket stream
        self.stop_stream()

    @abstractmethod
    def stop_stream(self) -> None:
        pass
