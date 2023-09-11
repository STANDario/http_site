from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from threading import Thread
from pathlib import Path
from urllib import parse
import mimetypes
import logging
import socket
import json


BASE_DIR = Path()
HOST = socket.gethostname()
SOCKET_PORT = 5000


class HTTPHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        client_socket = socket.socket()
        client_socket.connect((HOST, SOCKET_PORT))
        client_socket.send(body)
        client_socket.close()
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def do_GET(self):
        url = parse.urlparse(self.path)
        match url.path:
            case "/":
                self.send_html("index.html")
            case "/message":
                self.send_html("message.html")
            case _:
                file = BASE_DIR / url.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html("error.html", 404)

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        with open(filename, "rb") as fn:
            self.wfile.write(fn.read())

    def send_static(self, filename):
        self.send_response(200)
        mt = mimetypes.guess_type(filename)
        if mt:
            self.send_header("Content-Type", mt[0])
        else:
            self.send_header("Content-Type", "text/plain")
        self.end_headers()
        with open(filename, "rb") as fn:
            self.wfile.write(fn.read())


def run(server=HTTPServer, handler=HTTPHandler):
    address = ("0.0.0.0", 3000) # Для того щоб пробросити назовні з контейнера краще ставити "0.0.0.0"
    http = server(address, handler)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def socket_main():

    while True:

        socket_server = socket.socket()
        socket_server.bind((HOST, SOCKET_PORT))
        socket_server.listen()

        conn, address = socket_server.accept()
        logging.info(f"Connection from: {address}")

        msg = conn.recv(1024)
        msg = parse.unquote_plus(msg.decode())
        msg = {key: value for key, value in [el.split("=") for el in msg.split("&")]}
        now = datetime.now()

        with open(BASE_DIR.joinpath("storage/data.json"), "r", encoding="utf-8") as bd:
            msg_in_data = json.load(bd)

        msg_in_data[str(now)] = msg

        with open(BASE_DIR.joinpath("storage/data.json"), "w", encoding="utf-8") as bd:
            json.dump(msg_in_data, bd, ensure_ascii=False)

        conn.close()
        socket_server.close()


if __name__ == "__main__":
    STORAGE_DIR = Path().joinpath("storage")
    FILE_STORAGE = STORAGE_DIR / "data.json"
    if not FILE_STORAGE.exists():
        with open(FILE_STORAGE, "w", encoding="utf-8") as bd:
            json.dump({}, bd, ensure_ascii=False)

    socket_thread = Thread(target=socket_main)
    http_thread = Thread(target=run)

    socket_thread.start()
    http_thread.start()
    socket_thread.join()
    http_thread.join()

    logging.info("End work!")

