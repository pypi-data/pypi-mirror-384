import logging
import platform
from typing import Optional

import keyring

logger = logging.getLogger(__name__)


class HetznerApiKeyManager:
    """
    Manages Hetzner API keys with secure storage per project.

    Uses the system keyring for secure API key storage. On macOS, this automatically
    configures the keychain item to require password authentication on every access
    using the Security Framework. On other platforms, uses standard keyring storage.
    
    Supports multiple Hetzner projects, each with their own API key.
    """

    def __init__(self, project_name: str = "default") -> None:
        """Initialize manager for a specific Hetzner project.
        
        Args:
            project_name: Name of the Hetzner project (default: "default")
        """
        self.project_name = project_name
        self.keychain_service: str = "easyrunner.hetzner"
        self.keychain_account: str = f"api_key.{project_name}"
        self.is_macos: bool = platform.system() == "Darwin"

    def store_api_key(self, api_key: str) -> bool:
        """Store Hetzner API key in system keyring with password challenge on macOS."""
        if self.is_macos:
            return self._store_api_key_macos_secure(api_key)
        else:
            return self._store_api_key_standard(api_key)

    def get_api_key(self) -> Optional[str]:
        """Retrieve Hetzner API key from system keyring (will prompt for password on macOS)."""
        if self.is_macos:
            return self._get_api_key_macos_secure()
        else:
            return self._get_api_key_standard()

    def delete_api_key(self) -> bool:
        """Delete Hetzner API key from keyring."""
        if self.is_macos:
            return self._delete_api_key_macos_secure()
        else:
            return self._delete_api_key_standard()
    
    @staticmethod
    def list_projects() -> list[str]:
        """List all Hetzner projects that have stored API keys.
        
        Note: Due to keyring library limitations, this method cannot enumerate
        all stored projects. Users must remember their project names.
        
        Returns:
            Empty list (not supported by keyring library)
        """
        # The keyring library doesn't provide a cross-platform way to enumerate
        # all accounts for a given service. Users must track their project names.
        logger.debug("Project enumeration not supported by keyring library")
        return []

    def _store_api_key_standard(self, api_key: str) -> bool:
        """Store API key using standard keyring (non-macOS platforms)."""
        try:
            keyring.set_password(self.keychain_service, self.keychain_account, api_key)
            return True
        except Exception as e:
            logger.error(f"Failed to store API key in keyring: {e}")
            return False

    def _get_api_key_standard(self) -> Optional[str]:
        """Retrieve API key using standard keyring (non-macOS platforms)."""
        try:
            return keyring.get_password(self.keychain_service, self.keychain_account)
        except Exception as e:
            logger.error(f"Failed to retrieve API key from keyring: {e}")
            return None

    def _delete_api_key_standard(self) -> bool:
        """Delete API key using standard keyring (non-macOS platforms)."""
        try:
            keyring.delete_password(self.keychain_service, self.keychain_account)
            return True
        except Exception as e:
            logger.error(f"Failed to delete API key from keyring: {e}")
            return False

    def _store_api_key_macos_secure(self, api_key: str) -> bool:
        """Store API key with password challenge requirement on macOS."""
        try:
            from Foundation import NSData  # type: ignore
            from Security import (  # type: ignore
                SecAccessControlCreateWithFlags,  # type: ignore
                SecItemAdd,  # type: ignore
                SecItemDelete,  # type: ignore
                errSecSuccess,  # type: ignore
                kSecAttrAccessControl,  # type: ignore
                kSecAttrAccessibleWhenUnlockedThisDeviceOnly,  # type: ignore
                kSecAttrAccount,  # type: ignore
                kSecAttrService,  # type: ignore
                kSecClass,  # type: ignore
                kSecClassGenericPassword,  # type: ignore
                kSecValueData,  # type: ignore
            )
        except ImportError as import_error:
            logger.info(
                f"PyObjC frameworks not available ({import_error}), using standard keyring"
            )
            return self._store_api_key_standard(api_key)

        try:
            # Delete any existing item first
            query = {
                kSecClass: kSecClassGenericPassword,
                kSecAttrService: self.keychain_service,
                kSecAttrAccount: self.keychain_account,
            }
            SecItemDelete(query)

            # Create access control requiring user interaction (password/TouchID)
            # Using kSecAccessControlUserPresence which requires authentication
            error = None
            access_control = SecAccessControlCreateWithFlags(
                None,  # allocator
                kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
                0x40000000,  # kSecAccessControlUserPresence
                error,
            )

            if not access_control:
                logger.warning(
                    "Failed to create access control, falling back to standard keyring"
                )
                return self._store_api_key_standard(api_key)

            # Configure keychain item with password requirement
            query = {
                kSecClass: kSecClassGenericPassword,
                kSecAttrService: self.keychain_service,
                kSecAttrAccount: self.keychain_account,
                kSecValueData: NSData.dataWithBytes_length_(
                    api_key.encode("utf-8"), len(api_key.encode("utf-8"))
                ),
                kSecAttrAccessControl: access_control,
            }

            status = SecItemAdd(query, None)
            if status == errSecSuccess:
                logger.debug("API key stored with password challenge requirement")
                return True
            else:
                logger.warning(
                    f"Failed to store secure API key (status: {status}), falling back to standard keyring"
                )
                return self._store_api_key_standard(api_key)

        except Exception as e:
            logger.warning(
                f"Failed to store secure API key: {e}, falling back to standard keyring"
            )
            return self._store_api_key_standard(api_key)

    def _get_api_key_macos_secure(self) -> Optional[str]:
        """Retrieve API key with password challenge on macOS."""
        try:
            from Security import (  # type: ignore
                SecItemCopyMatching,  # type: ignore
                errSecAuthFailed,  # type: ignore
                errSecItemNotFound,  # type: ignore
                errSecSuccess,  # type: ignore
                errSecUserCancel,  # type: ignore
                kSecAttrAccount,  # type: ignore
                kSecAttrService,  # type: ignore
                kSecClass,  # type: ignore
                kSecClassGenericPassword,  # type: ignore
                kSecReturnData,  # type: ignore
                kSecUseOperationPrompt,  # type: ignore
            )
        except ImportError as import_error:
            logger.debug(
                f"PyObjC Security framework not available ({import_error}), using standard keyring"
            )
            return self._get_api_key_standard()

        try:
            query = {
                kSecClass: kSecClassGenericPassword,
                kSecAttrService: self.keychain_service,
                kSecAttrAccount: self.keychain_account,
                kSecReturnData: True,
                kSecUseOperationPrompt: "Please authenticate to access Hetzner API key",
            }

            status, result = SecItemCopyMatching(query, None)

            if status == errSecSuccess:
                return result.bytes().decode("utf-8")
            elif status == errSecUserCancel:
                logger.info("User cancelled authentication")
                return None
            elif status == errSecAuthFailed:
                logger.error("Authentication failed")
                return None
            elif status == errSecItemNotFound:
                logger.debug("API key not found in keychain")
                return None
            else:
                logger.error(f"Keychain error: {status}")
                return self._get_api_key_standard()

        except Exception as e:
            logger.error(f"Failed to retrieve secure API key: {e}")
            return self._get_api_key_standard()

    def _delete_api_key_macos_secure(self) -> bool:
        """Delete secure API key from macOS keychain."""
        try:
            from Security import (  # type: ignore
                SecItemDelete,  # type: ignore
                errSecSuccess,  # type: ignore
                kSecAttrAccount,  # type: ignore
                kSecAttrService,  # type: ignore
                kSecClass,  # type: ignore
                kSecClassGenericPassword,  # type: ignore
            )
        except ImportError as import_error:
            logger.debug(
                f"PyObjC Security framework not available ({import_error}), using standard keyring"
            )
            return self._delete_api_key_standard()

        try:
            query = {
                kSecClass: kSecClassGenericPassword,
                kSecAttrService: self.keychain_service,
                kSecAttrAccount: self.keychain_account,
            }

            status = SecItemDelete(query)
            return status == errSecSuccess

        except Exception as e:
            logger.error(f"Failed to delete secure API key: {e}")
            return self._delete_api_key_standard()
