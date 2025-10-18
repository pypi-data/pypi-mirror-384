import os
from dataclasses import dataclass


@dataclass
class SshConfigData:
    """Configuration data for SSH connections and key management."""

    key_dir: str = os.path.expanduser("~/.ssh/easyrunner_keys")
    """local dir for EasyRunner ssh keys"""

    username: str = "easyrunner"

# Default configuration
ssh_config = SshConfigData()


def _sanitise_hostname_or_ipv4(hostname_or_ipv4: str) -> str:
    """Sanitises the hostname or IPv4 address for use in file paths."""
    return hostname_or_ipv4.replace(".", "_").replace(":", "_")


def build_private_key_filename(hostname_or_ipv4: str) -> str:
    """
    Generates the private key filename based on the hostname or IPv4 address for EasyRunner managed servers.
    """
    return f"{_sanitise_hostname_or_ipv4(hostname_or_ipv4)}_id_ed25519"


def build_public_key_filename(hostname_or_ipv4: str) -> str:
    """
    Generates the public key filename based on the hostname or IPv4 address  for EasyRunner managed servers.
    """
    return f"{_sanitise_hostname_or_ipv4(hostname_or_ipv4)}_id_ed25519.pub"


def build_private_key_path(hostname_or_ipv4: str) -> str:
    """
    Generates the private key path based on the hostname or IPv4 address for EasyRunner managed servers.
    """
    return f"{ssh_config.key_dir}/{build_private_key_filename(hostname_or_ipv4)}"


def build_public_key_path(hostname_or_ipv4: str) -> str:
    """
    Generates the public key path based on the hostname or IPv4 address for EasyRunner managed servers.
    """
    return f"{ssh_config.key_dir}/{build_public_key_filename(hostname_or_ipv4)}"


def build_github_private_key_filename(hostname_or_ipv4: str) -> str:
    """
    Generates the GitHub private key filename based on the hostname or IPv4 address for EasyRunner managed servers.
    """
    return f"github_{_sanitise_hostname_or_ipv4(hostname_or_ipv4)}_id_ed25519"


def build_github_public_key_filename(hostname_or_ipv4: str) -> str:
    """
    Generates the GitHub public key filename based on the hostname or IPv4 address for EasyRunner managed servers.
    """
    return f"github_{_sanitise_hostname_or_ipv4(hostname_or_ipv4)}_id_ed25519.pub"


def build_github_private_key_path(hostname_or_ipv4: str) -> str:
    """
    Generates the GitHub private key path based on the hostname or IPv4 address for EasyRunner managed servers.
    """
    return f"{ssh_config.key_dir}/{build_github_private_key_filename(hostname_or_ipv4)}"


def build_github_public_key_path(hostname_or_ipv4: str) -> str:
    """
    Generates the GitHub public key path based on the hostname or IPv4 address for EasyRunner managed servers.
    """
    return f"{ssh_config.key_dir}/{build_github_public_key_filename(hostname_or_ipv4)}"
