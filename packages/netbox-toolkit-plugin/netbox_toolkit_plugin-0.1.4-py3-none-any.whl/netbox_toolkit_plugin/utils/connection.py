"""Connection management utilities for robust socket handling."""

import contextlib
import socket
import time
from typing import Any


def safe_socket_close(sock: socket.socket | None) -> None:
    """Safely close a socket with proper error handling."""
    if sock is None:
        return

    try:
        # Try graceful shutdown first
        with contextlib.suppress(OSError, AttributeError):
            # Socket might already be closed or not connected
            sock.shutdown(socket.SHUT_RDWR)

        # Then close the socket
        sock.close()

    except Exception:
        pass  # Socket cleanup error ignored


def is_socket_valid(sock: socket.socket | None) -> bool:
    """Check if a socket is valid and usable."""
    if sock is None:
        return False

    try:
        # Try to get socket peer name - this will fail if socket is closed
        sock.getpeername()
        return True
    except (OSError, AttributeError):
        return False


def cleanup_connection_resources(connection: Any) -> None:
    """Clean up all resources associated with a connection object."""
    if not connection:
        return

    try:
        # Handle Scrapli-specific cleanup
        if hasattr(connection, "channel") and connection.channel:
            try:
                # Close the channel
                if hasattr(connection.channel, "close"):
                    connection.channel.close()

                # Clean up the underlying socket if accessible
                if hasattr(connection.channel, "socket"):
                    safe_socket_close(connection.channel.socket)
                elif hasattr(connection.channel, "_socket"):
                    safe_socket_close(connection.channel._socket)

            except Exception:
                pass  # Channel cleanup error ignored

        # Handle transport cleanup
        if hasattr(connection, "transport") and connection.transport:
            try:
                if hasattr(connection.transport, "close"):
                    connection.transport.close()

                # Clean up transport socket if accessible
                if hasattr(connection.transport, "sock"):
                    safe_socket_close(connection.transport.sock)
                elif hasattr(connection.transport, "_socket"):
                    safe_socket_close(connection.transport._socket)

            except Exception:
                pass  # Transport cleanup error ignored

        # Try the main close method
        if hasattr(connection, "close"):
            with contextlib.suppress(Exception):
                # Connection close error ignored
                connection.close()

    except Exception:
        pass  # Connection cleanup error ignored


def validate_connection_health(connection: Any) -> bool:
    """Validate that a connection is healthy and usable."""
    if not connection:
        return False

    try:
        # Check if connection reports as alive
        if hasattr(connection, "isalive") and not connection.isalive():
            return False

        # Check underlying socket health if available
        if hasattr(connection, "channel") and connection.channel:
            if hasattr(connection.channel, "socket"):
                if not is_socket_valid(connection.channel.socket):
                    return False
            elif hasattr(connection.channel, "_socket") and not is_socket_valid(
                connection.channel._socket
            ):
                return False

        # Check transport socket health if available
        if hasattr(connection, "transport") and connection.transport:
            if hasattr(connection.transport, "sock"):
                if not is_socket_valid(connection.transport.sock):
                    return False
            elif hasattr(connection.transport, "_socket") and not is_socket_valid(
                connection.transport._socket
            ):
                return False

        return True

    except Exception:
        return False


def wait_for_socket_cleanup(timeout: float = 2.0) -> None:
    """Wait for socket cleanup to complete."""
    time.sleep(min(timeout, 2.0))
