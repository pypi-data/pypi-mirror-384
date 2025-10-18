from dataclasses import dataclass, field


@dataclass(slots=True)
class DbConfig:
    """
    Configuration for SQLite database connection.

    Attributes:
        dir (str): Directory where the database files are stored.
        connection_pool_size (int): Number of connections in the pool.
        cached_statements (int): Number of statements to cache.
        timeout_ms (int): Busy/connection
            timeout in milliseconds. Otherwise SQLite will return busy immediately.
    """

    dir: str = field(default="~/.local/share/easyrunner/db")

    connection_pool_size: int = field(default=10)

    cached_statements: int = field(default=128)
    """Number of statements to cache"""

    timeout_ms: int = field(default=5000)
    """Busy/connection timeout in milliseconds. Otherwise SQLite will return busy immediately."""
