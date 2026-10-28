"""Authenticated loopback IPC, one connection/request at a time. No Revit API."""
import socket
import threading
from bimcode_mcp import protocol as p


class Ticket(object):
    def __init__(self, seconds=p.EXECUTION_SECONDS):
        self.deadline = p.monotonic() + seconds
        self.done = threading.Event()
        self.cancelled = threading.Event()
        self.response = None

    def alive(self):
        return not self.cancelled.is_set() and p.monotonic() < self.deadline

    def complete(self, response):
        if self.alive():
            self.response = response
            self.done.set()


class Listener(object):
    def __init__(self, dispatch):
        self.dispatch = dispatch
        self.token = p.secret()
        self.stopped = threading.Event()
        self.current = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(("127.0.0.1", 0))
        self.socket.listen(1)
        self.socket.settimeout(0.25)
        self.port = self.socket.getsockname()[1]
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True

    def start(self):
        self.thread.start()

    def stop(self):
        self.stopped.set()
        if self.current is not None:
            self.current.cancelled.set()
            self.current.done.set()
        self.socket.close()

    def _run(self):
        while not self.stopped.is_set():
            try:
                connection, address = self.socket.accept()
            except socket.timeout:
                continue
            except (socket.error, OSError):
                break
            try:
                self._serve(connection)
            except Exception:
                # Never log requests, credentials, model data or exception text.
                pass
            finally:
                connection.close()

    def _serve(self, connection):
        request = p.validate_request(p.receive(connection, p.MAX_REQUEST,
                                    p.monotonic() + 2.0), self.token)
        rid = request["request_id"]
        if request["operation"] == "ping":
            response = p.result(rid, {"read_only": True, "tools": list(p.TOOLS)})
        else:
            ticket = Ticket()
            self.current = ticket
            try:
                if self.stopped.is_set():
                    return
                self.dispatch(request, ticket)
                ticket.done.wait(max(0, ticket.deadline - p.monotonic()))
                response = ticket.response
                if response is None:
                    response = p.result(rid, error="REVIT_TIMEOUT")
            finally:
                ticket.cancelled.set()
                self.current = None
        try:
            raw = p.encode(response, p.MAX_RESPONSE)
        except Exception:
            raw = p.encode(p.result(rid, error="RESULT_TOO_LARGE"), p.MAX_RESPONSE)
        connection.settimeout(2.0)
        connection.sendall(raw)
