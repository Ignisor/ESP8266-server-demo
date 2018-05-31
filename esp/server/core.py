import json
import socket

import time
from uerrno import EAGAIN, ETIMEDOUT
import gc

CODE_HEADERS = {
    200: 'OK',
    400: 'Bad Request',
    404: 'Not Found',
    500: 'Internal Server Error',
}


class Server(object):
    """ Class describing a simple HTTP server"""
    def __init__(self, port=80):
        self.host = ''  # works on all avaivable network interfaces
        self.views = {}
        self.port = port

        self.socket = None

    def activate_server(self, main_task):
        """ Attempts to aquire the socket and launch the server """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self._wait_for_connections(main_task)

    def view(self, method, url):
        """View decorator"""
        def view_decorator(func):
            def func_wrapper(request):
                try:
                    return func(request)
                except Exception as e:
                    return Response(500, "500 Server Error ({})".format(e))

            key = '{}:{}'.format(method.lower(), url.lower())
            self.views[key] = func_wrapper

            return func_wrapper
        return view_decorator

    def _wait_for_connections(self, main_task):
        """
        Main non blocking loop awaiting connections
        :param main_task: function to call in loop while waiting for connection
        """
        self.socket.listen(1)
        self.socket.setblocking(False)

        while True:
            if not main_task():
                break  # break the loop if main_tesk returned false

            s_data = dict(d.split('=') for d in str(self.socket).replace('>', '').split()[1:])

            if s_data.get('incoming', '0') != '0':
                try:
                    self._handle_connection()
                except OSError as e:
                    if e.args[0] != ETIMEDOUT:
                        raise e

            gc.collect()
            time.sleep(0.1)

    def _handle_connection(self):
        conn, addr = self.socket.accept()
        conn.settimeout(1)

        request = Request(conn, addr)

        view = self._get_view(request)
        response = view(request)
        server_response = response.encode()

        for chunk in server_response:
            conn.send(chunk)

        conn.close()

    def _get_view(self, request):
        key = '{}:{}'.format(request.method.lower(), request.url.lower())
        return self.views.get(key, lambda r: Response(404))


class Request(object):
    def __init__(self, connection, addr):
        self.conn = connection
        self.address = addr
        self.headers = self._get_headers()
        self.body = self._get_body()

    def _get_headers(self):
        while True:
            try:
                headers = self._receive_headers()
                break
            except OSError as e:
                if e.args[0] != EAGAIN:
                    raise e

        return self._process_headers(headers)

    def _receive_headers(self, chunk_size=1):
        data = b''
        while True:
            data += self.conn.recv(chunk_size)
            if data.endswith(b'\r\n\r\n'):
                return bytes.decode(data)

    def _process_headers(self, headers_str):
        headers = {}
        headers_list = list(filter(lambda i: bool(i), headers_str.split('\r\n')))

        starting_line = headers_list.pop(0)
        self.method, self.url, self.version = starting_line.split()

        for header in headers_list:
            key, value = header.split(': ')
            headers[key] = value

        return headers

    def _get_body(self):
        content_len = int(self.headers.get('content-length', 0))
        if content_len == 0:
            return None

        while True:
            try:
                body = self._receive_body(content_len)
                break
            except OSError as e:
                if e.args[0] != EAGAIN:
                    raise e

        if self.headers.get('Content-Type', '') == 'application/json':
            body = json.loads(body)

        return body

    def _receive_body(self, length, chunk_size=1):
        data = b''
        received_bytes = 0
        while True:
            chunk = self.conn.recv(chunk_size)
            data += chunk
            received_bytes += chunk_size

            if received_bytes >= length:
                return bytes.decode(data)


class Response(object):
    def __init__(self, code, content=None):
        self.code = code
        self.content = content
        self.headers = self._process_headers()

    def _gen_headers(self):
        """ Generates HTTP response Headers. Ommits the first line! """
        headers = []
        code_h = CODE_HEADERS[self.code]
        headers.append('HTTP/1.1 {code} {text}'.format(code=self.code, text=code_h))

        headers.append('Cache-Control: no-cache, no-store, must-revalidate')
        headers.append('Server: ESP-Python-HTTP-Server')
        headers.append('Connection: close')  # signal that the conection wil be closed after complting the request

        return headers

    def _process_headers(self):
        h = '\n'.join(self._gen_headers())
        h += '\n\n'
        return h

    def encode(self):
        yield self.headers.encode()
        if self.content:
            if type(self.content) == str:
                self.content = (self.content, )
            for part in self.content:
                yield part.encode()


class JSONResponse(Response):
    def _gen_headers(self):
        headers = super()._gen_headers()
        headers.append('Content-type: application/json')

        return headers

    def _process_content(self):
        return json.dumps(self.content)

    def encode(self):
        self.content = self._process_content()
        return super(JSONResponse, self).encode()


class HTMLResponse(Response):
    def __init__(self, file):
        super(HTMLResponse, self).__init__(200, open(file))
