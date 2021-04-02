"""
Utility methods for PyUpdaterWxDemo.
"""
import socket


def get_ephemeral_port():
    """
    Return an unused ephemeral port.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port
