import logging
import os
from typing import Optional, Self

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from .types.ssh_key_type import SshKeyType

logger = logging.getLogger(__name__)


class SshKey:
    """A class to generate and manage ED25519 type key pairs in OpenSSH format."""
    _private_key: ed25519.Ed25519PrivateKey | None = None
    _public_key: ed25519.Ed25519PublicKey | None = None
    _load_error: str | None = None

    def __init__(
        self,
        email: str,
        name: str,
        passphrase: Optional[str] = None,
        ssh_key_dir: Optional[str] = None,
        regenerate_if_exists: Optional[bool] = False,
    ):
        """
        Creates a new SSH key management instance for ED25519 keys.

        The constructor only loads existing keys if they are found on disk.
        To generate new keys, explicitly call generate_ed25519_keypair().
        To save keys, explicitly call save_private_key() and/or save_public_key().

        Args:
            email (str): The email address to associate with the SSH key.
            name (str): The name of the SSH key file with no extension. Defaults to "id_ed25519".
            passphrase (Optional[str]): The passphrase to encrypt the SSH key. Defaults to None.
            ssh_key_dir (Optional[str]): The directory to save the SSH key. Defaults to ~/.ssh.
            regenerate_if_exists (Optional[bool]): If True, regenerates and overwrites the key if it already exists. Defaults to False.
        """
        self.name: str = name
        self.email: str = email
        self._regenerate_if_exists: bool | None = regenerate_if_exists
        self._passphrase: str | None = passphrase
        self.key_type: SshKeyType = SshKeyType.ED25519

        _ssh_dir: str = os.path.expanduser(ssh_key_dir or "~/.ssh")
        self.key_path: str = os.path.join(_ssh_dir, name)
        """Path to the private key file, e.g. ~/.ssh/id_ed25519"""

        # Ensure .ssh directory exists with correct permissions
        os.makedirs(_ssh_dir, mode=0o700, exist_ok=True)

        # Check key file existence
        self.private_key_exists: bool = os.path.exists(self.key_path)
        self.public_key_exists: bool = os.path.exists(f"{self.key_path}.pub")

        self.keys_exists: bool = self.private_key_exists or self.public_key_exists
        """Keys exist if either private or public key file exists"""

        self._encryption_algorithm = serialization.NoEncryption()
        if self._passphrase:
            self._encryption_algorithm = serialization.BestAvailableEncryption(
                self._passphrase.encode()
            )

        # Load existing keys if they exist (no automatic generation)
        load_success = self.load_existing_keys()

        # If key files exist but loading failed, handle based on regenerate_if_exists
        if not load_success and self.keys_exists:
            if self._regenerate_if_exists:
                logger.warning(
                    f"Failed to load existing keys, will regenerate: {self._load_error}"
                )
                self.generate_ed25519_keypair()
                self.save_private_key()
                self.save_public_key()
            else:
                raise RuntimeError(
                    f"Failed to load existing SSH keys: {self._load_error}"
                )

        # If no keys exist and regenerate_if_exists is True, generate them
        elif not load_success and not self.keys_exists and self._regenerate_if_exists:
            self.generate_ed25519_keypair()
            self.save_private_key()
            self.save_public_key()

    def load_existing_keys(self: Self) -> bool:
        """
        Load existing SSH keys from disk if they exist.

        Loading strategy depends on gen_location and which files exist:
        - Always prefer loading private key if available (can derive public key)
        - Fall back to loading only public key if that's all we have
        - Consider context (server vs client) for determining what "exists" means

        Returns:
            bool: True if any keys were successfully loaded, False otherwise

        Raises:
            RuntimeError: If key files exist but cannot be loaded due to format/permission issues
        """
        keys_loaded = False
        self._load_error = None

        try:
            # Try to load private key first (preferred, can derive public key)
            if self.private_key_exists:
                logger.debug(f"Attempting to load private key from {self.key_path}")

                try:
                    with open(self.key_path, "rb") as f:
                        private_key_data = f.read()

                    if not private_key_data:
                        self._load_error = f"Private key file {self.key_path} is empty"
                        return False

                    # Load the private key with or without passphrase
                    if self._passphrase:
                        loaded_private_key = serialization.load_ssh_private_key(
                            private_key_data,
                            password=self._passphrase.encode(),
                        )
                    else:
                        loaded_private_key = serialization.load_ssh_private_key(
                            private_key_data, password=None
                        )

                    # Ensure it's an ED25519 key
                    if isinstance(loaded_private_key, ed25519.Ed25519PrivateKey):
                        self._private_key = loaded_private_key
                        # Derive the public key from the private key
                        self._public_key = self._private_key.public_key()
                        keys_loaded = True
                        logger.debug(
                            f"Successfully loaded private key from {self.key_path}"
                        )
                    else:
                        self._load_error = f"Private key at {self.key_path} is not an ED25519 key (found {type(loaded_private_key)})"
                        return False

                except PermissionError as e:
                    self._load_error = (
                        f"Permission denied reading private key {self.key_path}: {e}"
                    )
                    return False
                except Exception as e:
                    self._load_error = (
                        f"Failed to load private key from {self.key_path}: {e}"
                    )
                    return False

            # If we don't have private key loaded but public key file exists, load it
            if not keys_loaded and self.public_key_exists:
                logger.debug(f"Attempting to load public key from {self.key_path}.pub")

                try:
                    with open(f"{self.key_path}.pub", "rb") as f:
                        public_key_data = f.read()

                    if not public_key_data:
                        self._load_error = (
                            f"Public key file {self.key_path}.pub is empty"
                        )
                        return False

                    loaded_public_key = serialization.load_ssh_public_key(
                        public_key_data
                    )

                    # Ensure it's an ED25519 public key
                    if isinstance(loaded_public_key, ed25519.Ed25519PublicKey):
                        self._public_key = loaded_public_key
                        # Note: _private_key remains None in this case
                        keys_loaded = True
                        logger.debug(
                            f"Successfully loaded public key from {self.key_path}.pub"
                        )
                    else:
                        self._load_error = f"Public key at {self.key_path}.pub is not an ED25519 key (found {type(loaded_public_key)})"
                        return False

                except PermissionError as e:
                    self._load_error = (
                        f"Permission denied reading public key {self.key_path}.pub: {e}"
                    )
                    return False
                except Exception as e:
                    self._load_error = (
                        f"Failed to load public key from {self.key_path}.pub: {e}"
                    )
                    return False

        except Exception as e:
            # Unexpected error during key loading process
            self._load_error = f"Unexpected error during key loading: {e}"
            logger.error(self._load_error)
            return False

        return keys_loaded

    def has_private_key(self: Self) -> bool:
        """Returns True if a private key is loaded in memory"""
        return self._private_key is not None

    def has_public_key(self: Self) -> bool:
        """Returns True if a public key is loaded in memory"""
        return self._public_key is not None

    def has_load_error(self: Self) -> bool:
        """Returns True if there was an error loading keys"""
        return self._load_error is not None

    def get_load_error(self: Self) -> str | None:
        """Returns the load error message if any"""
        return self._load_error

    def key_status(self: Self) -> dict[str, bool | str | None]:
        """
        Returns detailed status of key availability

        Returns:
            dict with keys: private_file_exists, public_file_exists,
            private_key_loaded, public_key_loaded, has_load_error, load_error
        """
        return {
            "private_file_exists": self.private_key_exists,
            "public_file_exists": self.public_key_exists,
            "private_key_loaded": self.has_private_key(),
            "public_key_loaded": self.has_public_key(),
            "has_load_error": self.has_load_error(),
            "load_error": self.get_load_error(),
        }

    def generate_ed25519_keypair(
        self: Self,
    ) -> None:
        """
        Generate a new ED25519 key pair in memory.

        This will overwrite existing keys in memory if regenerate_if_exists is True,
        or skip generation if keys exist and regenerate_if_exists is False.

        To save the generated keys to disk, call save_private_key() and/or save_public_key().
        To add to SSH agent, call add_to_ssh_agent().
        """
        # Clear any previous load error since we're generating new keys
        self._load_error = None

        # If keys exist and we don't want to regenerate, skip generation
        if self.keys_exists and not self._regenerate_if_exists:
            # But ensure we have valid keys loaded
            if not self.has_public_key():
                raise RuntimeError(
                    f"Key files exist but no valid keys are loaded. "
                    f"Load error: {self._load_error}. "
                    f"Set regenerate_if_exists=True to force regeneration."
                )
            return

        # Generate key pair based on key type
        match self.key_type:
            case SshKeyType.ED25519:
                self._private_key = ed25519.Ed25519PrivateKey.generate()
                self._public_key = self._private_key.public_key()
                logger.debug(f"Generated new ED25519 key pair for {self.name}")
            case _:
                raise ValueError(f"Unsupported key type: {self.key_type}")

    def private_key_as_bytes(self: Self) -> bytes:
        """Returns the private key as bytes in OpenSSH format"""
        if self._private_key is None:
            return b""
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.OpenSSH,
            encryption_algorithm=self._encryption_algorithm,
        )

    def public_key_as_bytes(self: Self) -> bytes:
        """Returns the public key as bytes in OpenSSH format"""
        if self._public_key is None:
            return b""
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        )

    def private_key_as_string(self: Self) -> str:
        """Returns the private key as a string in OpenSSH format"""
        if self._private_key is None:
            if self._load_error:
                raise RuntimeError(
                    f"No private key available due to load error: {self._load_error}"
                )
            else:
                raise RuntimeError(
                    "No private key available. Call generate_ed25519_keypair() first."
                )
        return self.private_key_as_bytes().decode()

    def public_key_as_string(self: Self) -> str:
        """Returns the public key as a string in OpenSSH format"""
        if self._public_key is None:
            if self._load_error:
                raise RuntimeError(
                    f"No public key available due to load error: {self._load_error}"
                )
            else:
                raise RuntimeError(
                    "No public key available. Call generate_ed25519_keypair() first."
                )
        return self.public_key_as_bytes().decode()

    def save_private_key(self: Self) -> None:
        """Save the private key to the default key path"""
        if self.private_key_as_bytes() == b"":
            return None
        with open(self.key_path, "wb") as f:
            f.write(self.private_key_as_bytes())
        # Set correct permissions
        os.chmod(self.key_path, 0o600)

    def save_public_key(self: Self) -> None:
        """Save the public key to the default key path"""
        if self.public_key_as_bytes() == b"":
            return None
        with open(f"{self.key_path}.pub", "wb") as f:
            f.write(self.public_key_as_bytes())
        # Set correct permissions
        os.chmod(f"{self.key_path}.pub", 0o644)

    def add_to_ssh_agent(self: Self) -> None:
        """Add the private key to the SSH agent"""
        import subprocess

        subprocess.run(["ssh-add", self.key_path])
