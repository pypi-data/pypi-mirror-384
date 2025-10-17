"""
Tests for the User resource.

This file contains unit tests for the User resource to ensure it works correctly.
"""

from unittest.mock import Mock

from easyrunner.source.command_executor import CommandExecutor
from easyrunner.source.commands.ubuntu.user_commands_ubuntu import UserCommandsUbuntu
from easyrunner.source.resources.os_resources import User
from easyrunner.source.types.cpu_arch_types import CpuArch
from easyrunner.source.types.exec_result import ExecResult


class TestUser:
    """Test cases for the User resource."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_executor = Mock(spec=CommandExecutor)
        self.user_commands = UserCommandsUbuntu(cpu_arch=CpuArch.X86_64)
        self.username = "testuser"
        self.user = User(
            executor=self.mock_executor,
            commands=self.user_commands,
            username=self.username
        )

    def test_user_initialization(self):
        """Test that User resource initializes correctly."""
        assert self.user.username == self.username
        assert self.user._commands == self.user_commands
        assert self.user.executor == self.mock_executor

    def test_user_exists_true(self):
        """Test user exists check when user exists."""
        # Mock successful user existence check (id command returns 0)
        self.mock_executor.execute.return_value = ExecResult(
            success=True,
            return_code=0,
            stdout=f"uid=1001({self.username}) gid=1001({self.username}) groups=1001({self.username})",
            stderr=""
        )

        result = self.user.exists()
        assert result is True
        self.mock_executor.execute.assert_called_once()

    def test_user_exists_false(self):
        """Test user exists check when user does not exist."""
        # Mock failed user existence check (id command returns 1)
        self.mock_executor.execute.return_value = ExecResult(
            success=False,
            return_code=1,
            stdout="",
            stderr=f"id: '{self.username}': no such user"
        )

        result = self.user.exists()
        assert result is False
        self.mock_executor.execute.assert_called_once()

    def test_create_user_success(self):
        """Test successful user creation."""
        # Mock user doesn't exist initially
        self.mock_executor.execute.side_effect = [
            # First call: user existence check (returns False)
            ExecResult(success=False, return_code=1, stdout="", stderr="no such user"),
            # Second call: user creation (returns success)
            ExecResult(success=True, return_code=0, stdout="", stderr=""),
            # Third call: password setting (returns success)
            ExecResult(success=True, return_code=0, stdout="", stderr="")
        ]

        result = self.user.create(password="testpass", create_home=True, shell="/bin/bash")
        
        assert result.success is True
        assert result.return_code == 0
        # Should have called execute 3 times: exists check + create + set password
        assert self.mock_executor.execute.call_count == 3

    def test_create_user_already_exists(self):
        """Test user creation when user already exists."""
        # Mock user already exists
        self.mock_executor.execute.return_value = ExecResult(
            success=True,
            return_code=0,
            stdout=f"uid=1001({self.username})",
            stderr=""
        )

        result = self.user.create()
        
        assert result.success is True
        assert result.stdout is not None and "already exists" in result.stdout
        # Should only call execute once for the existence check
        self.mock_executor.execute.assert_called_once()

    def test_delete_user_success(self):
        """Test successful user deletion."""
        # Mock user exists, then successful deletion
        self.mock_executor.execute.side_effect = [
            # First call: user existence check (returns True)
            ExecResult(success=True, return_code=0, stdout=f"uid=1001({self.username})", stderr=""),
            # Second call: user deletion (returns success)
            ExecResult(success=True, return_code=0, stdout="", stderr="")
        ]

        result = self.user.delete(remove_home=True)
        
        assert result.success is True
        assert result.return_code == 0
        # Should have called execute twice: exists check + delete
        assert self.mock_executor.execute.call_count == 2

    def test_delete_user_not_exists(self):
        """Test user deletion when user doesn't exist."""
        # Mock user doesn't exist
        self.mock_executor.execute.return_value = ExecResult(
            success=False,
            return_code=1,
            stdout="",
            stderr="no such user"
        )

        result = self.user.delete()
        
        assert result.success is True
        assert result.stdout is not None and "does not exist" in result.stdout
        # Should only call execute once for the existence check
        self.mock_executor.execute.assert_called_once()

    def test_add_to_groups_success(self):
        """Test successfully adding user to groups."""
        groups = ["sudo", "docker"]
        
        # Mock user exists, then successful group additions
        self.mock_executor.execute.side_effect = [
            # First call: user existence check (returns True)
            ExecResult(success=True, return_code=0, stdout=f"uid=1001({self.username})", stderr=""),
            # Second call: add to sudo group (returns success)
            ExecResult(success=True, return_code=0, stdout="", stderr=""),
            # Third call: add to docker group (returns success)
            ExecResult(success=True, return_code=0, stdout="", stderr="")
        ]

        result = self.user.add_to_groups(groups)
        
        assert result.success is True
        assert result.stdout is not None and all(group in result.stdout for group in groups)
        # Should call execute 3 times: exists check + 2 group additions
        assert self.mock_executor.execute.call_count == 3

    def test_add_to_groups_user_not_exists(self):
        """Test adding user to groups when user doesn't exist."""
        # Mock user doesn't exist
        self.mock_executor.execute.return_value = ExecResult(
            success=False,
            return_code=1,
            stdout="",
            stderr="no such user"
        )

        result = self.user.add_to_groups(["sudo"])
        
        assert result.success is False
        assert result.stderr is not None and "does not exist" in result.stderr
        # Should only call execute once for the existence check
        self.mock_executor.execute.assert_called_once()

    def test_get_home_directory_success(self):
        """Test successfully getting user's home directory."""
        home_path = f"/home/{self.username}"
        
        # Mock user exists, then successful home directory retrieval
        self.mock_executor.execute.side_effect = [
            # First call: user existence check (returns True)
            ExecResult(success=True, return_code=0, stdout=f"uid=1001({self.username})", stderr=""),
            # Second call: get home directory (returns success)
            ExecResult(success=True, return_code=0, stdout=home_path, stderr="")
        ]

        result = self.user.get_home_directory()
        
        assert result.success is True
        assert result.result == home_path
        # Should call execute twice: exists check + get home directory
        assert self.mock_executor.execute.call_count == 2

    def test_get_home_directory_user_not_exists(self):
        """Test getting home directory when user doesn't exist."""
        # Mock user doesn't exist
        self.mock_executor.execute.return_value = ExecResult(
            success=False,
            return_code=1,
            stdout="",
            stderr="no such user"
        )

        result = self.user.get_home_directory()
        
        assert result.success is False
        assert result.stderr is not None and "does not exist" in result.stderr
        assert result.result is None
        # Should only call execute once for the existence check
        self.mock_executor.execute.assert_called_once()

    def test_set_password_success(self):
        """Test successfully setting user password."""
        # Mock user exists, then successful password setting
        self.mock_executor.execute.side_effect = [
            # First call: user existence check (returns True)
            ExecResult(success=True, return_code=0, stdout=f"uid=1001({self.username})", stderr=""),
            # Second call: set password (returns success)
            ExecResult(success=True, return_code=0, stdout="", stderr="")
        ]

        result = self.user.set_password("newpassword")
        
        assert result.success is True
        # Should call execute twice: exists check + set password
        assert self.mock_executor.execute.call_count == 2

    def test_set_password_user_not_exists(self):
        """Test setting password when user doesn't exist."""
        # Mock user doesn't exist
        self.mock_executor.execute.return_value = ExecResult(
            success=False,
            return_code=1,
            stdout="",
            stderr="no such user"
        )

        result = self.user.set_password("newpassword")
        
        assert result.success is False
        assert result.stderr is not None and "does not exist" in result.stderr
        # Should only call execute once for the existence check
        self.mock_executor.execute.assert_called_once()
