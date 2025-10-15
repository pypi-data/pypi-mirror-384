from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS
from ..runnable_command_string import RunnableCommandString
from .command_base import CommandBase


class UserCommands(CommandBase):
    """Base class for user management commands common across Unix/Linux distributions."""

    def __init__(self, os: OS, cpu_arch: CpuArch):
        # User management commands are typically part of the base system
        super().__init__(os=os, cpu_arch=cpu_arch, command_name="useradd", pkg_name="no pkg")

    def create_user(
        self, 
        username: str, 
        create_home: bool = True, 
        shell: str = "/bin/bash"
    ) -> RunnableCommandString:
        """Generate command to create a new user.
        
        Args:
            username: The username for the new user
            create_home: Whether to create a home directory for the user
            shell: The default shell for the user
            
        Returns:
            RunnableCommandString: Command to create the user
        """
        options = ["-s", shell]
        if create_home:
            options.extend(["-m"])
        
        # Create a user group with the same name as the user
        # This ensures the user has their own primary group
        options.extend(["-U"])

        command = f"useradd {' '.join(options)} {username}"
        return RunnableCommandString(command=command, sudo=True)

    def check_user_exists(self, username: str) -> RunnableCommandString:
        """Generate command to check if a user exists.
        
        Args:
            username: The username to check
            
        Returns:
            RunnableCommandString: Command to check user existence
        """
        return RunnableCommandString(command=f"id {username}", sudo=False)

    def set_password(self, username: str, password: str) -> RunnableCommandString:
        """Generate command to set user password using chpasswd.
        
        Args:
            username: The username
            password: The password to set
            
        Returns:
            RunnableCommandString: Command to set password
        """
        command = f"echo '{username}:{password}' | chpasswd"
        return RunnableCommandString(command=command, sudo=True)

    def add_user_to_group(self, username: str, group: str) -> RunnableCommandString:
        """Generate command to add user to a group.
        
        Args:
            username: The username
            group: The group name to add user to
            
        Returns:
            RunnableCommandString: Command to add user to group
        """
        command = f"usermod -a -G {group} {username}"
        return RunnableCommandString(command=command, sudo=True)

    def get_user_home_directory(self, username: str) -> RunnableCommandString:
        """Generate command to get user's home directory.
        
        Args:
            username: The username
            
        Returns:
            RunnableCommandString: Command to get home directory
        """
        command = f"getent passwd {username} | cut -d: -f6"
        return RunnableCommandString(command=command, sudo=False)

    def delete_user(self, username: str, remove_home: bool = False) -> RunnableCommandString:
        """Generate command to delete a user.
        
        Args:
            username: The username to delete
            remove_home: Whether to remove the user's home directory
            
        Returns:
            RunnableCommandString: Command to delete user
        """
        options = []
        if remove_home:
            options.append("-r")

        command = f"userdel {' '.join(options)} {username}"
        return RunnableCommandString(command=command, sudo=True)

    def add_user_to_sudoers_nopasswd(self, username: str) -> RunnableCommandString:
        """Generate command to add user to sudoers with passwordless sudo access.

        Args:
            username: The username to add to sudoers

        Returns:
            RunnableCommandString: Command to add user to sudoers with NOPASSWD
        """
        command = f'echo "{username} ALL=(ALL) NOPASSWD:ALL" | tee /etc/sudoers.d/{username} && chmod 440 /etc/sudoers.d/{username}'
        return RunnableCommandString(command=command, sudo=True)

    def check_user_has_sudo_access(self, username: str) -> RunnableCommandString:
        """Generate command to check if a user has sudo access.

        Args:
            username: The username to check

        Returns:
            RunnableCommandString: Command to check if user has sudo access
        """
        # Check if the sudoers file exists for the user
        command = f"test -f /etc/sudoers.d/{username}"
        return RunnableCommandString(command=command, sudo=False)

    def version(self) -> RunnableCommandString:
        """Get version information for useradd command."""
        return RunnableCommandString(command="useradd --version", sudo=False)
