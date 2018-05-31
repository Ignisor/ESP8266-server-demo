import sys
import machine

from data import conf
from .core import Server

server_app = Server()

from . import views  # initialize views after server initialisation


def serve():
    try:
        server_app.activate_server(lambda: True)
    except Exception as e:
        # write exception to file and restart a machine in case of error
        with open(conf.ERROR_LOG_FILENAME, 'w') as err_file:
            sys.print_exception(e, err_file)
        machine.reset()

