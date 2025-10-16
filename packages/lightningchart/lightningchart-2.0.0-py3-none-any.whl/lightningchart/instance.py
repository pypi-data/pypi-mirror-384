from __future__ import annotations
import os
import queue
import sys
import threading
import time
import uuid
import json
import msgpack
import requests
import socket
import webbrowser
import pkgutil
from http.server import HTTPServer, BaseHTTPRequestHandler
from IPython import get_ipython
from IPython.display import IFrame, display
from flask import Flask, request, render_template, send_from_directory, Response
from flask_socketio import SocketIO, join_room

from lightningchart.utils.utils import NumpyEncoder, msgpack_default

LOCALHOST = 'localhost'
host_name = '0.0.0.0'
base_dir = '.'
if hasattr(sys, '_MEIPASS'):
    base_dir = os.path.join(sys._MEIPASS)


def get_free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((LOCALHOST, 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def display_html(html_content, notebook=False, width: int | str = '100%', height: int | str = 600):
    html_bytes = html_content.encode('utf-8')

    class Server(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html_bytes)

    server_address = (LOCALHOST, 0)
    server = HTTPServer(server_address, Server)
    server_thread = threading.Thread(target=server.handle_request)
    server_thread.daemon = False
    server_thread.start()
    if notebook:
        return display(
            IFrame(
                src=f'http://{LOCALHOST}:{server.server_port}',
                width=width,
                height=height,
            )
        )
    else:
        webbrowser.open(f'http://{LOCALHOST}:{server.server_port}')
    server_thread.join()


def js_functions():
    base_dir = '.'
    if hasattr(sys, '_MEIPASS'):
        base_dir = os.path.join(sys._MEIPASS)

    js_code = pkgutil.get_data(__name__, os.path.join(base_dir, 'static/lcpy.js')).decode()
    return js_code


def create_html(items):
    serialized_items = []
    for i in items:
        serialized_items.append(json.dumps(i, cls=NumpyEncoder))
    html = f"""<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="shortcut icon" href="#">
        <title>LightningChart Python</title>
        <script src="https://cdn.jsdelivr.net/npm/@lightningchart/lcjs@8.0.2/dist/lcjs.iife.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@lightningchart/lcjs-themes@6.0.0/dist/iife/lcjs-themes.iife.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/msgpack-lite@0.1.26/dist/msgpack.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/socket.io@4.8.1/client-dist/socket.io.min.js"></script>
        <style>
            body {{
                height: 100%;
                margin: 0;
            }}
        </style>
    </head>
    <body>
    <script>
        {js_functions()}
    </script>
    <script>
        lcpy.initStatic({serialized_items});
    </script>
    </body>
</html>
"""
    return html


class Instance:
    def __init__(self):
        self.id = str(uuid.uuid4()).split('-')[0]
        self.session = requests.Session()
        retry_adapter = requests.adapters.HTTPAdapter(max_retries=5)
        self.session.mount('http://', retry_adapter)
        self.items = list()
        self.pending_get_results = dict()
        self.connected_clients = dict()
        self.preserve_data = True
        self.server_is_open = False
        self.server_port = None
        self.send_method = 'http'
        self.seq_num = 0

        # Initialize Flask and SocketIO
        self.app = Flask(
            __name__,
            static_folder=os.path.join(base_dir, 'static'),
            template_folder=os.path.join(base_dir, 'static'),
        )
        self.app.config['SECRET_KEY'] = 'secret!'
        self.socketio = SocketIO(self.app, async_mode='gevent', ping_timeout=60)

        # HTTP routes
        self.app.route('/', methods=['GET'])(self._http_index)
        self.app.route('/send', methods=['POST'])(self._http_send)
        self.app.route('/get', methods=['POST'])(self._http_get)
        self.app.route('/storage', methods=['GET'])(self._http_storage)
        self.app.route('/resources/<path:path>', methods=['GET'])(self._http_resources)
        self.app.route('/static/<path:path>', methods=['GET'])(self._http_static)

        # SocketIO events
        self.socketio.on_event('connect', self._sio_connect)
        self.socketio.on_event('disconnect', self._sio_disconnect)
        self.socketio.on_event('join', self._sio_join)
        self.socketio.on_event('get_result', self._sio_get_result)

    # ----- Public methods -----

    def send(self, id: str, command: str, arguments: dict = None):
        data = {
            'seq': self.seq_num,
            'id': id,
            'command': command,
            'args': arguments,
        }
        self.seq_num += 1

        if not self.server_is_open:
            self.items.append(data)
        else:
            if self.send_method == 'http':
                self._send_http(data)
            else:
                self._send_direct(data)

    def get(self, id: str, command: str = None, arguments: dict = None):
        get_id = str(uuid.uuid4()).split('-')[0]
        data = {
            'get_id': get_id,
            'id': str(id),
            'command': command,
            'args': arguments or {},
        }
        if not self.server_is_open:
            try:
                if get_ipython().__class__.__name__ == 'ZMQInteractiveShell':
                    self._open_in_notebook()
                    for _ in range(20):
                        if self.id in self.connected_clients.values():
                            break
                        time.sleep(0.5)
                else:
                    self._open_in_browser()
            except Exception as e:
                raise Exception(f'Chart was not opened, and it failed to open automatically. Please open it manually.Error: {e}')
        binary_data = msgpack.packb(data, default=msgpack_default)
        try:
            response = self.session.post(
                f'http://{LOCALHOST}:{self.server_port}/get?room={self.id}&get_id={get_id}',
                data=binary_data,
                headers={'Content-Type': 'application/msgpack'},
            )
            if response.ok:
                data = msgpack.unpackb(response.content, raw=False)
                return data
            elif response.status_code == 400:
                raise Exception('Chart is not open, cannot execute command. Call open() method first.')
            elif response.status_code == 500:
                raise Exception('Unexpected error occurred, cannot execute command.')
        except requests.RequestException as e:
            print(e)

    def open(
        self,
        method: str = None,
        live: bool = False,
        width: int | str = '100%',
        height: int | str = 600,
    ):
        if method not in ('browser', 'notebook', 'link'):
            method = 'notebook' if get_ipython().__class__.__name__ == 'ZMQInteractiveShell' else 'browser'

        if (live or method == 'link') and not self.server_is_open:
            self._start_server()

        if method == 'notebook':
            return self._open_in_notebook(width=width, height=height)
        elif method == 'link':
            return f'http://{LOCALHOST}:{self.server_port}/?id={self.id}'
        else:
            self._open_in_browser()
            return None

    def close(self):
        if self.server_is_open:
            for client in self.connected_clients.keys():
                self.socketio.emit('shutdown', to=client)
            self.socketio.stop()
            self.server_is_open = False

    def set_data_preservation(self, enabled: bool):
        self.preserve_data = enabled
        return self

    # ----- Private methods -----

    def _send_http(self, data: dict):
        binary_data = msgpack.packb(data, default=msgpack_default)
        try:
            response = self.session.post(
                f'http://{LOCALHOST}:{self.server_port}/send?id={self.id}',
                data=binary_data,
                headers={'Content-Type': 'application/msgpack'},
            )
            if response.ok:
                return True
        except requests.RequestException as e:
            raise Exception(f'Error sending data: {e}')

    def _send_direct(self, data: dict):
        binary_data = msgpack.packb(data, default=msgpack_default)
        try:
            save = False
            if self.id in self.connected_clients.values():
                self.socketio.emit('item', binary_data, to=self.id)
            else:
                save = True

            if self.preserve_data or save:
                self.items.append(data)

            return True
        except Exception as e:
            raise Exception(f'Error sending data: {e}')

    def _start_server(self):
        try:
            self.server_port = get_free_port()
            server_thread = threading.Thread(
                target=lambda: self.socketio.run(
                    self.app,
                    host=host_name,
                    port=self.server_port,
                    debug=True,
                    log_output=False,
                    use_reloader=False,
                )
            )
            server_thread.start()
            self.server_is_open = True
        except Exception as e:
            raise Exception(f'The server could not be started: {e}')

    def _wait_for_get_result(self, get_id, timeout=5, poll_interval=0.5, max_polls=10):
        q = queue.Queue()
        self.pending_get_results[get_id] = q
        for _ in range(max_polls):
            if not q.empty():
                break
            self.socketio.sleep(poll_interval)
        try:
            result = q.get(timeout=timeout)
        except queue.Empty:
            result = None
        finally:
            del self.pending_get_results[get_id]
        return result

    def _open_static(self):
        html = create_html(self.items)
        display_html(html)

    def _open_in_browser(self):
        if self.server_is_open:
            webbrowser.open(f'http://{LOCALHOST}:{self.server_port}/?id={self.id}')
            try:
                timeout = 10
                interval = 0.1
                waited = 0
                while waited < timeout:
                    if self.id in self.connected_clients.values():
                        break
                    time.sleep(interval)
                    waited += interval
            except requests.exceptions.ConnectionError as e:
                print(e)
        else:
            self._open_static()

    def _open_in_notebook(self, width: int | str = '100%', height: int | str = 600):
        if self.server_is_open:
            return display(
                IFrame(
                    src=f'http://{LOCALHOST}:{self.server_port}/?id={self.id}',
                    width=width,
                    height=height,
                )
            )
        else:
            html = create_html(self.items)
            return display_html(html, notebook=True, width=width, height=height)

    # ----- HTTP Routes -----

    def _http_send(self):
        room = request.args.get('id')
        binary_data = request.data

        save = False
        if room in self.connected_clients.values():
            self.socketio.emit('item', binary_data, to=room)
        else:
            save = True

        if self.preserve_data or save:
            data = msgpack.unpackb(binary_data)
            self.items.append(data)

        return '', 200

    def _http_get(self):
        room = request.args.get('room')
        get_id = request.args.get('get_id')
        binary_data = request.data

        if room not in self.connected_clients.values():
            return Response('', status=400)

        self.socketio.emit('get_request', binary_data, to=room)
        result = self._wait_for_get_result(get_id)

        if result is None:
            return Response('', status=500)
        return Response(msgpack.packb(result), mimetype='application/msgpack')

    def _http_storage(self):
        room = request.args.get('id')
        if room not in self.connected_clients.values():
            return Response('Room not found', status=404)

        data = msgpack.packb(self.items)
        if not self.preserve_data:
            del self.items[:]

        return Response(data, mimetype='application/msgpack')

    def _http_resources(self, path):
        return send_from_directory('./static/resources', path)

    def _http_static(self, path):
        return send_from_directory('./static', path)

    def _http_index(self):
        room = request.args.get('id')
        return render_template('index.html', room=room)

    # ----- SocketIO Events -----

    def _sio_connect(self):
        self.connected_clients[request.sid] = 'default'

    def _sio_disconnect(self):
        del self.connected_clients[request.sid]

    def _sio_join(self, room):
        join_room(room)
        self.connected_clients[request.sid] = room
        self.socketio.emit('storage', to=room)

    def _sio_get_result(self, binary_data):
        data = msgpack.unpackb(binary_data)
        get_id = data['get_id']
        result = data['result']
        if get_id in self.pending_get_results:
            self.pending_get_results[get_id].put(result)
