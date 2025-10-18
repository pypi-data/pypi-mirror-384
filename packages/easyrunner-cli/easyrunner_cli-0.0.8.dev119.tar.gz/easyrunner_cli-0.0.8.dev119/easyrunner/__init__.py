import logging


# Configure library-wide logger but overridable by the root logger in the consuming code.
logger = logging.getLogger(__name__)
logger.propagate = True  # Allow log messages to propagate to root logger

from .source import commands  # noqa
from .source.commands import base  # noqa
from .source.ssh import Ssh  # noqa
from .source.ssh_key import SshKey  # noqa
from .source import store  # noqa

__all__ = ["Ssh", "SshKey", "commands", "base", "store"]
