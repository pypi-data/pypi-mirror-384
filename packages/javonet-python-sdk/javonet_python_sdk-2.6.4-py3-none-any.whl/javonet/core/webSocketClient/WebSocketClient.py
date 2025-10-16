from websockets.protocol import State
from websockets.sync.client import connect
from websockets.exceptions import WebSocketException

# cache of clients keyed by URI
_clients: dict[str, "WebSocketClient"] = {}


class WebSocketClient:

    def __init__(self, uri: str):
        self.uri = uri
        # disable frame size limit
        self.ws = connect(uri=uri, max_size=None)

    @staticmethod
    def add_or_get_client(uri: str) -> "WebSocketClient":
        client = _clients.get(uri)
        if client is not None:
            if client.ws is None or client.ws.protocol.state != State.OPEN:
                client.close()
                client = WebSocketClient(uri)
                _clients[uri] = client
        else:
            client = WebSocketClient(uri)
            _clients[uri] = client
        return client

    @staticmethod
    def send_message(uri: str, message: bytes) -> bytes:
        client = WebSocketClient.add_or_get_client(uri)
        try:
            client.send_byte_array(message)
            return client.receive_byte_array()
        except (WebSocketException, OSError, RuntimeError):
            # Reconnect and retry once
            client = WebSocketClient._recreate_client(uri, client)
            client.send_byte_array(message)
            return client.receive_byte_array()

    @staticmethod
    def _recreate_client(uri: str, client: "WebSocketClient") -> "WebSocketClient":
        try:
            if client is not None:
                client.close()
        except Exception:
            pass
        new_client = WebSocketClient(uri)
        _clients[uri] = new_client
        return new_client

    def send_byte_array(self, message: bytes) -> None:
        if self.ws is None:
            raise RuntimeError("WebSocket is not opened")
        self.ws.send(message)

    def receive_byte_array(self) -> bytes:
        if self.ws is None:
            raise RuntimeError("WebSocket is not opened")
        response = self.ws.recv()
        if isinstance(response, str):
            response = response.encode("utf-8")
        return response

    def close(self) -> None:
        if self.ws is not None:
            try:
                self.ws.close()
            finally:
                self.ws = None

    # Helpers to mirror C# API
    @staticmethod
    def close_client(uri: str) -> None:
        client = _clients.pop(uri, None)
        if client is not None:
            client.close()

    @staticmethod
    def get_state(uri: str):
        client = _clients.get(uri)
        if client is None or client.ws is None:
            return None
        return client.ws.protocol.state
