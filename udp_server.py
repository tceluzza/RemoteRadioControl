import json
import socket
import threading
from typing import Callable, Tuple, Optional


class UdpServer:
    """
    A simple UDP server that listens for text-based commands and allows replies.

    The server configuration (host and port) is read from `server_config.json`.
    Incoming messages trigger a user-defined callback, which receives the
    message text and the client's address (host, port).

    Example
    -------
    >>> def handle_command(cmd, addr):
    ...     print(f"Received {cmd} from {addr}")
    ...
    >>> server = UdpServer(callback=handle_command)
    >>> server.start()
    """

    def __init__(self, config_path: str = "server_config.json",
                 callback: Optional[Callable[[str, Tuple[str, int]], None]] = None) -> None:
        """
        Initialize the UDP server.

        Parameters
        ----------
        config_path : str
            Path to the JSON configuration file containing 'host' and 'port'.
        callback : Callable[[str, Tuple[str, int]], None], optional
            Function to call when a command is received. It should take the
            message text and the client address as parameters.
        """
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        self.host: str = config.get("host", "0.0.0.0")
        self.port: int = config.get("port", 6435)
        self.callback = callback

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self._listening = False
        self._thread: Optional[threading.Thread] = None

    def _listen(self) -> None:
        """Internal thread loop that listens for incoming UDP messages."""
        while self._listening:
            try:
                data, addr = self.sock.recvfrom(4096)
                message = data.decode("utf-8").strip()
                if self.callback:
                    self.callback(message, addr)
            except Exception as e:
                print(f"UDP receive error: {e}")

    def start(self) -> None:
        """Start listening for incoming UDP commands in a background thread."""
        if not self._listening:
            self._listening = True
            self._thread = threading.Thread(target=self._listen, daemon=True)
            self._thread.start()
            print(f"UDP server listening on {self.host}:{self.port}")

    def stop(self) -> None:
        """Stop listening for new messages and close the socket."""
        self._listening = False
        if self.sock:
            self.sock.close()
        print("UDP server stopped.")

    def send_reply(self, message: str, addr: Tuple[str, int]) -> None:
        """
        Send a reply to a client.

        Parameters
        ----------
        message : str
            The message to send.
        addr : Tuple[str, int]
            The client's address (host, port) to send to.
        """
        try:
            self.sock.sendto(message.encode("utf-8"), addr)
        except Exception as e:
            print(f"Error sending reply: {e}")

if __name__ == "__main__":
    def example_callback(cmd: str, addr: Tuple[str, int]) -> None:
        print(f"Received command: '{cmd}' from {addr}")
        server.send_reply(f"ACK: {cmd}", addr)

    server = UdpServer(callback=example_callback)
    server.start()

    try:
        while True:
            pass  # Keep the main thread alive
    except KeyboardInterrupt:
        server.stop()