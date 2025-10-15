from openobd_protocol.Messages import Empty_pb2 as grpcEmpty

import threading
import logging

from openobd.core.session import OpenOBDSession
from openobd.core.exceptions import OpenOBDException
from openobd.core.stream_handler import StreamHandler
from openobd.core.exceptions import OpenOBDStreamStoppedException

class SessionTokenHandler:

    def __init__(self, openobd_session: OpenOBDSession):
        """
        Authenticates the given openOBD session and starts a thread to keep the session active by periodically updating
        its session token.

        :param openobd_session: a newly created OpenOBDSession that should remain active.
        """
        self.openobd_session = openobd_session
        self._authenticate()
        self.refresh_session_token_thread = threading.Thread(target=self._refresh_session_token, daemon=True)
        self.refresh_session_token_thread.start()

    def _authenticate(self):
        # Authenticating the openOBD session
        new_token = self.openobd_session.authenticate(request=grpcEmpty.EmptyMessage())
        self.openobd_session.update_session_token(new_token.value)

        # Start refreshing session tokens
        self.session_token_manager = StreamHandler(self.openobd_session.open_session_token_stream)

    def _refresh_session_token(self):
        try:
            while True:
                new_token = self.session_token_manager.receive()
                self.openobd_session.update_session_token(new_token.value)
        except OpenOBDStreamStoppedException:
            pass
        except OpenOBDException:
            if self.openobd_session.active:
                logging.exception(f" [!] Stopped refreshing session tokens for session [{self.openobd_session.id()}] due to an exception.")
            else:
                # An exception occurs, but the session is already finished. It does not make sense to refresh tokens for
                # finished sessions, so we show a nice message.
                # An example for this scenario is running a no-op script. The tokens are refreshed in a separate thread. The main
                # thread may have finished the session already, causing the refreshToken call to fail with an exception.
                logging.info(f" [!] Stopped refreshing session tokens for session [{self.openobd_session.id()}]. Session has already finished.")
        finally:
            self.session_token_manager.stop_stream()
