import logging

from openobd_protocol.Communication.Messages.Isotp_pb2 import IsotpChannel, IsotpMessage

from openobd.communication.socket import Socket
from openobd.communication.response_exceptions import *
from openobd.communication.uds_request_handler import UdsRequestHandler
from openobd.core.exceptions import OpenOBDStreamTimeoutException
from openobd.core.session import OpenOBDSession
from openobd.core.stream_handler import StreamHandler


class IsotpSocket(Socket):

    def __init__(self, openobd_session: OpenOBDSession, isotp_channel: IsotpChannel, timeout: float | None = 10):
        """
        Handles sending messages to the given channel and parsing incoming responses.

        :param openobd_session: an active OpenOBDSession with which to start the CAN stream.
        :param isotp_channel: the channel which to send messages to.
        :param timeout: time in seconds to wait for each response before raising a NoResponseException. None will wait forever.
        """
        super().__init__()
        self.stream_handler = StreamHandler(openobd_session.open_isotp_stream, outgoing_stream=True)
        self._channel = isotp_channel
        self.uds_request_handler = UdsRequestHandler(self.stream_handler, timeout)

        '''We send an empty message to the server to ensure that the channel is initialized, this also helps when we 
        want to just listen on a channel'''
        self.stream_handler.send(IsotpMessage(channel=self._channel, payload=""))

    def request(self, payload: str, timeout: float | None = None, silent: bool = False, tries: int = 1) -> str | None:
        """
        Sends the given payload and waits for the response. Raises the appropriate ResponseException when receiving a
        negative response.

        :param payload: the bytes to send to the channel.
        :param timeout: time in seconds to wait for a response before raising a NoResponseException. Will use self.timeout if None.
        :param silent: if True, will not raise any ResponseExceptions. Instead, returns the payload of negative responses or None for NoResponseExceptions.
        :param tries: how many times to send the payload until a positive response is received.
        :return: the payload of the received response.
        """
        try:
            message = IsotpMessage(channel=self._channel, payload=payload)
            logging.debug(f"Send [{message}]")
            return self.uds_request_handler.request(message, timeout, silent, tries)
        except ResponseException as e:
            # Add channel info to the exception before raising it
            e.request_id = self._channel.request_id
            e.response_id = self._channel.response_id
            raise e

    def send(self, payload: str):
        message = IsotpMessage(channel=self._channel, payload=payload)
        self.stream_handler.send(message, flush_incoming_messages=True)

    def receive(self, timeout: float):
        try:
            response = self.stream_handler.receive(timeout=timeout)     # type: IsotpMessage
        except OpenOBDStreamTimeoutException:
            raise NoResponseException(request="??", response=None, request_id=self._channel.request_id, response_id=self._channel.response_id)

        return response.payload.upper()

    def stop_stream(self) -> None:
        """
        Closes the gRPC stream if it is not already closed. A new Socket object will have to be created to start another
        stream.
        """
        self.uds_request_handler.stop_stream()
