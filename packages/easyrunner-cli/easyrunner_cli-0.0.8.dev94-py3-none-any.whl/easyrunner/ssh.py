import functools
import logging
import os
import socket
import time
from typing import Callable, List, Optional, Self, Type, TypeVar

import paramiko
from fabric import Connection, Result

from .commands.runnable_command_string import RunnableCommandString  # fabfile.org

T = TypeVar("T")


def with_ssh_retry(
    max_attempts: int = 5,
    initial_wait: float = 10.0,
    backoff_factor: float = 2.0,
    max_wait: float = 120.0,
    retryable_exceptions: Optional[List[Type[Exception]]] = None,
):
    """
    Decorator for SSH operations with exponential backoff retry logic.

    Designed to handle resource starvation on small servers during operations
    like package installations or system updates that can cause SSH connections
    to fail with "Error reading SSH protocol banner" and similar transient errors.

    Args:
        max_attempts: Maximum number of retry attempts (default: 5)
        initial_wait: Initial wait time in seconds before first retry (default: 10.0)
        backoff_factor: Multiplier for wait time on each retry (default: 2.0)
        max_wait: Maximum wait time between retries in seconds (default: 120.0)
        retryable_exceptions: List of exception types to retry on. If None, uses default set.

    Returns:
        Decorated function that will retry on transient SSH connection failures

    Example:
        @with_ssh_retry(max_attempts=3, initial_wait=5.0)
        def connect_and_execute():
            with Ssh(...) as ssh:
                # SSH operations
                pass
    """
    if retryable_exceptions is None:
        retryable_exceptions = [
            paramiko.SSHException,  # "Error reading SSH protocol banner"
            EOFError,  # Connection dropped mid-handshake
            ConnectionError,  # General connection failures
            socket.timeout,  # Socket timeout during connection
            OSError,  # "Resource temporarily unavailable"
        ]

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            logger = logging.getLogger(__name__)
            current_wait = initial_wait

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except tuple(retryable_exceptions) as e:
                    if attempt == max_attempts - 1:  # Last attempt
                        logger.error(
                            f"Final SSH retry attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}"
                        )
                        # Provide more context for common resource starvation errors
                        if "Error reading SSH protocol banner" in str(
                            e
                        ) or "EOFError" in str(type(e).__name__):
                            raise ConnectionError(
                                f"Server appears to be resource-starved and cannot handle SSH connections. "
                                f"Consider using a larger server instance, waiting for current operations to complete, "
                                f"or running the command later when the server is less busy. Original error: {e}"
                            ) from e
                        raise

                    # Log retry attempt with context
                    error_context = ""
                    if "Error reading SSH protocol banner" in str(e):
                        error_context = " (server appears resource-starved)"
                    elif "EOFError" in str(type(e).__name__):
                        error_context = " (connection dropped during handshake)"

                    logger.warning(
                        f"SSH operation {func.__name__} failed on attempt {attempt + 1}/{max_attempts}{error_context}. "
                        f"Retrying in {current_wait:.1f} seconds... Error: {e}"
                    )

                    time.sleep(current_wait)
                    current_wait = min(current_wait * backoff_factor, max_wait)

                except Exception as e:
                    # Non-retryable exception, fail immediately
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise

            # Should never reach here due to the range loop structure
            raise RuntimeError(f"Unexpected end of retry loop for {func.__name__}")

        return wrapper

    return decorator


class Ssh:
    _conn: Connection | None = None
    _hide: bool | str = "out"

    def __init__(
        self,
        hostname_or_ipv4: str,
        username: str,
        port: int = 22,
        key_filename: Optional[str] = None,
        key_content: Optional[str] = None,
        passphrase: Optional[str] = None,
        debug: bool = False,
        silent: bool = True,
    ):
        # setup logger for this class with correct logger namespace hierarchy
        self._logger: logging.Logger = logging.getLogger(__name__)
        # Critical for libs to prevent log messages from propagating to the root logger and causing dup logs and config issues.
        self._logger.addHandler(logging.NullHandler())

        self.hostname: str = hostname_or_ipv4
        self.port: int = port
        self.username: str = username
        self.debug: bool = debug
        self.silent: bool = silent
        if key_filename is not None:
            self.key_filename: str = os.path.expanduser(key_filename)
        elif key_content is not None:
            raise NotImplementedError("Key as content is not implemented yet")
        self._passphrase: str | None = passphrase

        # this controls the behaviour of for copying the subprocess’ stdout and stderr to the controlling terminal.
        if self.debug:
            # if debug is enabled, we want to see everything
            self._hide = False
        elif self.silent:
            # if silent is enabled, we want to hide everything (both stdout and stderr)
            self._hide = "both"
        else:
            # if debug and silent are disabled, we want to hide only stderr
            # self._hide = False
            self._hide = "both"

        self.connect()

    def connect(self) -> None:
        """Initialise a connection object which is access through the connection property.
        Despite the name, this method does not actually establish the connection by calling open().
        The run() and run_sudo() methods will implicitly call open() if the connection is not already open.
        """
        # Ref see https://docs.fabfile.org/en/latest/api/connection.html
        if self._conn is None:

            def _internal_create_paramiko_transport(
                self_arg=None, **kwargs
            ) -> paramiko.Transport:
                transport = paramiko.Transport((self.hostname, self.port))
                transport.use_compression(True)
                return transport

            self._conn = Connection(
                host=self.hostname,
                port=self.port,
                user=self.username,
                connect_timeout=15,
                connect_kwargs={
                    "key_filename": self.key_filename,
                    "passphrase": self._passphrase,
                    # Add Paramiko transport options
                    "disabled_algorithms": None,  # Enable all algorithms
                    "transport_factory": _internal_create_paramiko_transport,
                },
            )

        # Configure keepalive on the underlying transport
        if self._conn.transport:
            self._conn.transport.set_keepalive(
                interval=20
            )  # Send keepalive every 20 seconds

        try:
            self._conn.open()
        except paramiko.SSHException as ssh_err:
            self._logger.error(
                "SSH protocol error while opening connection: %s", str(ssh_err)
            )
            raise ConnectionError("SSH protocol error: ", ssh_err) from ssh_err
        except socket.timeout as timeout_err:
            self._logger.error(
                "Connection timed out while trying to reach %s:%d",
                self.hostname,
                self.port,
            )
            raise ConnectionError(
                f"Connection timed out to {self.hostname}:{self.port}.", timeout_err
            ) from timeout_err
        except socket.gaierror as dns_err:
            self._logger.error(
                "DNS resolution failed for host %s. Error: %s", self.hostname, dns_err
            )

            raise ConnectionError("DNS resolution failed.", dns_err) from dns_err
        except FileNotFoundError as key_err:
            self._logger.error(
                "SSH key file not found: %s. Please check the key filename.", key_err
            )
            raise ConnectionError("SSH key file not found.", key_err) from key_err

        except Exception as e:
            self._logger.critical(
                "Failed to open connection. Make sure you have network connectivity to the host, port 22 open into the host, SSH correctly running on the host, and the host is generally in a healthy state. Error: %s",
                e,
            )
            raise ConnectionError(
                "Failed to open connection. Make sure you have network connectivity to the host, port 22 open into the host, SSH correctly running on the host, and the host is generally in a healthy state",
                e,
            )

    @property
    def connection(self) -> Connection:
        if self._conn is None:
            self.connect()
        if self._conn is None:
            raise RuntimeError(
                "Failed to obtain a connection object for remote server: %s. Note at this point we haven't tried to open a connection to the remote host.",
                self.hostname,
            )
        return self._conn

    def run(self, command: RunnableCommandString) -> Result:
        """Run a shell command on the remote server, without sudo"""
        return self._run(command, False)

    def run_sudo(self, command: RunnableCommandString) -> Result:
        """Run a shell command on the remote server with sudo"""
        return self._run(command, True)

    def _run(self: Self, command: RunnableCommandString, sudo: bool) -> Result:
        # see https://docs.pyinvoke.org/en/latest/api/runners.html#invoke.runners.Runner.run

        # when warn=True, it will not raise an exception if the command exit code is none zero.
        # hide – Allows the caller to disable run’s default behavior of **copying** the subprocess’ stdout and stderr **to the controlling terminal**. Specify hide='out' (or 'stdout') to hide only the stdout stream, hide='err' (or 'stderr') to hide only stderr, or hide='both' (or True) to hide both streams. The default value is None, meaning to print everything; False will also disable hiding.
        # A Result object is always populated hence will be returned with the exit code and stderr set

        try:
            # sudo and run implicitly call connection.open() if it is not already open
            # for now stick with that behavior.
            # if we need to test connectivity then we might want to call open explicitly.
            if sudo:
                return self.connection.sudo(
                    command=command.command, env=command.env, hide=self._hide, warn=True
                )
            else:
                return self.connection.run(
                    command=command.command, env=command.env, hide=self._hide, warn=True
                )
        except Exception as e:
            # when warn=True, it will not raise an exception if the command reaches any exit code.
            # Otherwise this exception will always fire.
            # Anything that prevents a command from actually getting to “exited with an exit code” ignores 'warn' flag.
            self._logger.error(
                "Command didn't reach an exit code. Command: %s", command.command
            )
            raise e

    def close(self) -> None:
        """Close the SSH connection."""
        self.connection.close()

    def __enter__(self) -> Self:
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the runtime context related to this object and close the connection."""
        self.close()
