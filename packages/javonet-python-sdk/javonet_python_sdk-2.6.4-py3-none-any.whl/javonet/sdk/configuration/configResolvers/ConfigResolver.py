from javonet.utils.RuntimeNameHandler import RuntimeNameHandler
from javonet.utils.connectionData.InMemoryConnectionData import InMemoryConnectionData
from javonet.utils.connectionData.WsConnectionData import WsConnectionData
from javonet.utils.connectionData.TcpConnectionData import TcpConnectionData

class ConfigResolver:

    @staticmethod
    def try_parse_runtime(runtime):
        if not runtime or runtime.strip() == "":
            raise ValueError("Runtime string cannot be null or whitespace.")
        runtime = runtime.strip().lower()
        return RuntimeNameHandler.get_runtime(runtime)

    @staticmethod
    def build_connection_data(host_value):
        if not host_value or host_value.strip() == "":
            return InMemoryConnectionData()
        hv = host_value.strip()
        lower = hv.lower()

        if lower in ("inmemory", "in-memory"):
            return InMemoryConnectionData()

        if lower.startswith("ws://") or lower.startswith("wss://"):
            return WsConnectionData(hv)

        if lower.startswith("tcp://"):
            try:
                return ConfigResolver.parse_tcp(hv[6:])
            except Exception:
                return InMemoryConnectionData()

        colon = hv.find(":")
        if colon > 0 and colon < len(hv) - 1:
            port_part = hv[colon + 1:]
            slash = port_part.find("/")
            if slash >= 0:
                port_part = port_part[:slash]
            try:
                port = int(port_part)
                host_only = hv[:colon]
                if host_only.strip():
                    try:
                        return TcpConnectionData(host_only, port)
                    except Exception:
                        return InMemoryConnectionData()
            except Exception:
                pass

        return InMemoryConnectionData()

    @staticmethod
    def parse_tcp(address):
        slash = address.find("/")
        host_port = address[:slash] if slash >= 0 else address
        colon = host_port.rfind(":")
        if colon <= 0 or colon >= len(host_port) - 1:
            raise ValueError("Invalid tcp:// format.")
        host = host_port[:colon]
        port_str = host_port[colon + 1:]
        try:
            port = int(port_str)
        except Exception:
            raise ValueError("Invalid port in tcp:// address.")
        return TcpConnectionData(host, port)
