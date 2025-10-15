from openobd.core.stream_handler import StreamHandler
from openobd.core.session import OpenOBDSession
import logging


def set_bus_configuration(openobd_session: OpenOBDSession, bus_configs):
    # Open a configureBus stream, send the bus configurations, and close the stream
    bus_config_stream = StreamHandler(openobd_session.configure_bus)
    bus_config_stream.send_and_close(bus_configs)
    logging.debug("Buses have been configured.")

