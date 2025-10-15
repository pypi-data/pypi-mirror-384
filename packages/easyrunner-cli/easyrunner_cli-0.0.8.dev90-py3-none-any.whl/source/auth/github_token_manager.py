import logging
import platform
from typing import Optional

import keyring

logger = logging.getLogger(__name__)


class GitHubTokenManager:
    """
    Manages GitHub OAuth tokens with secure storage.

    Uses the system keyring for secure token storage. On macOS, this automatically
    configures the keychain item to require password authentication on every access
    using the Security Framework. On other platforms, uses standard keyring storage.
    """
    def __init__(self) -> None:
        self.keychain_service: str = "easyrunner.github"
        self.keychain_account: str = "oauth_token"
        self.is_macos: bool = platform.system() == "Darwin"

    def store_token(self, token: str) -> bool:
        """Store GitHub token in system keyring with password challenge on macOS."""
        if self.is_macos:
            return self._store_token_macos_secure(token)
        else:
            return self._store_token_standard(token)

    def get_token(self) -> Optional[str]:
        """Retrieve GitHub token from system keyring (will prompt for password on macOS)."""
        if self.is_macos:
            return self._get_token_macos_secure()
        else:
            return self._get_token_standard()

    def delete_token(self) -> bool:
        """Delete GitHub token from keyring."""
        if self.is_macos:
            return self._delete_token_macos_secure()
        else:
            return self._delete_token_standard()

    def _store_token_standard(self, token: str) -> bool:
        """Store token using standard keyring (non-macOS platforms)."""
        try:
            keyring.set_password(self.keychain_service, self.keychain_account, token)
            return True
        except Exception as e:
            logger.error(f"Failed to store token in keyring: {e}")
            return False

    def _get_token_standard(self) -> Optional[str]:
        """Retrieve token using standard keyring (non-macOS platforms)."""
        try:
            return keyring.get_password(self.keychain_service, self.keychain_account)
        except Exception as e:
            logger.error(f"Failed to retrieve token from keyring: {e}")
            return None

    def _delete_token_standard(self) -> bool:
        """Delete token using standard keyring (non-macOS platforms)."""
        try:
            keyring.delete_password(self.keychain_service, self.keychain_account)
            return True
        except Exception as e:
            logger.error(f"Failed to delete token from keyring: {e}")
            return False

    def _store_token_macos_secure(self, token: str) -> bool:
        """Store token with password challenge requirement on macOS."""
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
            return self._store_token_standard(token)

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
                return self._store_token_standard(token)

            # Configure keychain item with password requirement
            query = {
                kSecClass: kSecClassGenericPassword,
                kSecAttrService: self.keychain_service,
                kSecAttrAccount: self.keychain_account,
                kSecValueData: NSData.dataWithBytes_length_(
                    token.encode("utf-8"), len(token.encode("utf-8"))
                ),
                kSecAttrAccessControl: access_control,
            }

            status = SecItemAdd(query, None)
            if status == errSecSuccess:
                logger.debug("Token stored with password challenge requirement")
                return True
            else:
                logger.warning(
                    f"Failed to store secure token (status: {status}), falling back to standard keyring"
                )
                return self._store_token_standard(token)

        except Exception as e:
            logger.warning(
                f"Failed to store secure token: {e}, falling back to standard keyring"
            )
            return self._store_token_standard(token)

    def _get_token_macos_secure(self) -> Optional[str]:
        """Retrieve token with password challenge on macOS."""
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
            return self._get_token_standard()

        try:
            query = {
                kSecClass: kSecClassGenericPassword,
                kSecAttrService: self.keychain_service,
                kSecAttrAccount: self.keychain_account,
                kSecReturnData: True,
                kSecUseOperationPrompt: "Please authenticate to access GitHub token",
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
                logger.debug("Token not found in keychain")
                return None
            else:
                logger.error(f"Keychain error: {status}")
                return self._get_token_standard()

        except Exception as e:
            logger.error(f"Failed to retrieve secure token: {e}")
            return self._get_token_standard()

    def _delete_token_macos_secure(self) -> bool:
        """Delete secure token from macOS keychain."""
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
            return self._delete_token_standard()

        try:
            query = {
                kSecClass: kSecClassGenericPassword,
                kSecAttrService: self.keychain_service,
                kSecAttrAccount: self.keychain_account,
            }

            status = SecItemDelete(query)
            return status == errSecSuccess

        except Exception as e:
            logger.error(f"Failed to delete secure token: {e}")
            return self._delete_token_standard()
