from utils.pins import blink_led
from data import conf
from . import server_app as srv
from .core import HTMLResponse, Response


@srv.view('GET', '/')
def index_get(request):
    return HTMLResponse('templates/index.html')


@srv.view('POST', '/')
def index_post(request):
    print('{} pushed my button!!!'.format(request.address))
    blink_led()
    return index_get(request)


@srv.view('GET', '/error/')
def get_error(request):
    with open(conf.ERROR_LOG_FILENAME) as error_log:
        r = Response(200, error_log.read())

    return r
