import re
from typing import Dict, List, Optional

from .... import logger
from ...command_executor import CommandExecutor
from ...commands.base.ssh_agent_commands import SshAgentCommands
from ...types.exec_result import ExecResult
from .os_resource_base import OsResourceBase


class SshAgent(OsResourceBase):
    """Represents an SSH agent service for managing SSH keys in memory.
    
    This resource provides functionality to start/stop ssh-agent, check if it's running,
    and manage SSH keys by adding them to the agent for authentication.
    """
    
    SSH_AUTH_SOCK_ENV_VAR = "SSH_AUTH_SOCK"
    """Name of the environment variable for the SSH authentication socket."""
    SSH_AGENT_PID_ENV_VAR = "SSH_AGENT_PID"
    """Name of the environment variable for the SSH agent process ID."""

    

    def __init__(
        self,
        executor: CommandExecutor,
        commands: SshAgentCommands,
        socket_path: str = "$HOME/.ssh/ssh_agent_er.sock",
    ) -> None:
        """Initialize an SSH agent resource.

        Args:
            executor: CommandExecutor instance for executing commands
            commands: SshAgentCommands instance for ssh-agent operations  
            socket_path: Optional path for the SSH agent socket
        """
        super().__init__(commands=commands, executor=executor)
        self.socket_path = socket_path
        self._commands: SshAgentCommands = commands
        self._agent_pid: Optional[str] = None

    def is_running(self) -> bool:
        """Check if ssh-agent is currently running.
        
        Returns:
            bool: True if ssh-agent is running and accessible, False otherwise
        """
        try:
            from ...commands.runnable_command_string import RunnableCommandString
            
            # Directly test the configured socket path with ssh-add -l
            test_cmd = RunnableCommandString(command="ssh-add -l")
            test_cmd.env = {self.SSH_AUTH_SOCK_ENV_VAR: self.socket_path}
            
            result = self.executor.execute(command=test_cmd)
            
            # ssh-add -l returns:
            # - 0: agent running with keys loaded
            # - 1: agent running but no keys loaded  
            # - 2: agent not running or no authentication socket
            is_running = result.return_code in [0, 1]
            logger.debug(f"SSH agent running status: {is_running} (return code: {result.return_code})")
            return is_running
        except Exception as e:
            logger.error(f"Error checking ssh-agent status: {e}")
            return False

    def start(self) -> ExecResult[Dict[str, str]]:
        """Start ssh-agent in background mode.
        
        Returns:
            ExecResult[Dict[str, str]]: Result containing environment variables 
                                     (SSH_AUTH_SOCK, SSH_AGENT_PID) if successful
        """
        if self.is_running():
            logger.debug("SSH agent is already running")
            # Try to get existing environment variables
            env_vars = self._get_current_env_vars()
            result = ExecResult[Dict[str, str]](
                success=True,
                return_code=0,
                stdout="SSH agent already running",
                stderr=""
            )
            result.result = env_vars
            return result

        try:
            start_cmd = self._commands.start_background(self.socket_path)
            result = self.executor.execute(command=start_cmd)

            if result.success and result.stdout:
                # Parse the output to extract environment variables
                env_vars = self._parse_agent_output(result.stdout)
                
                if env_vars:
                    self._auth_sock = env_vars.get(self.SSH_AUTH_SOCK_ENV_VAR)
                    self._agent_pid = env_vars.get(self.SSH_AGENT_PID_ENV_VAR)

                    logger.debug(f"SSH agent started successfully. PID: {self._agent_pid}, Socket: {self._auth_sock}")
                    
                    typed_result = ExecResult[Dict[str, str]](
                        success=True,
                        return_code=result.return_code,
                        stdout=result.stdout,
                        stderr=result.stderr
                    )
                    typed_result.result = env_vars
                    return typed_result
                else:
                    error_msg = "Failed to parse ssh-agent output for environment variables"
                    logger.error(error_msg)
                    typed_result = ExecResult[Dict[str, str]](
                        success=False,
                        return_code=1,
                        stdout="",
                        stderr=error_msg
                    )
                    typed_result.result = {}
                    return typed_result
            else:
                error_msg = f"Failed to start ssh-agent: {result.stderr}"
                logger.error(error_msg)
                typed_result = ExecResult[Dict[str, str]](
                    success=False,
                    return_code=result.return_code,
                    stdout=result.stdout or "",
                    stderr=result.stderr or error_msg
                )
                typed_result.result = {}
                return typed_result

        except Exception as e:
            error_msg = f"Exception starting ssh-agent: {str(e)}"
            logger.error(error_msg)
            typed_result = ExecResult[Dict[str, str]](
                success=False,
                return_code=1,
                stdout="",
                stderr=error_msg
            )
            typed_result.result = {}
            return typed_result

    def stop(self) -> ExecResult:
        """Stop the ssh-agent process.
        
        Returns:
            ExecResult: Result of the stop operation
        """
        if not self.is_running():
            logger.debug("SSH agent is not running")
            return ExecResult(
                success=True,
                return_code=0,
                stdout="SSH agent is not running",
                stderr=""
            )

        try:
            kill_cmd = self._commands.kill(self._agent_pid)
            result = self.executor.execute(command=kill_cmd)

            if result.success:
                logger.debug("SSH agent stopped successfully")
                self._agent_pid = None
            else:
                logger.error(f"Failed to stop ssh-agent: {result.stderr}")

            return result

        except Exception as e:
            error_msg = f"Exception stopping ssh-agent: {str(e)}"
            logger.error(error_msg)
            return ExecResult(
                success=False,
                return_code=1,
                stdout="",
                stderr=error_msg
            )

    def add_key_from_content(self, private_key_content: str, comment_content: Optional[str] = None) -> ExecResult:
        """Add a private key to ssh-agent from content.
        
        Args:
            private_key_content: The content of the private key to add
        
        Returns:
            ExecResult: Result of the add key operation
        """
        if not self.is_running():
            error_msg = "SSH agent is not running. Start it first."
            logger.error(error_msg)
            return ExecResult(
                success=False,
                return_code=1,
                stdout="",
                stderr=error_msg
            )

        try:
            add_cmd = self._commands.add_key_from_content(private_key_content, comment_content)
            # Set the socket environment variable so the command uses our specific agent
            add_cmd.env = {self.SSH_AUTH_SOCK_ENV_VAR: self.socket_path}
            result = self.executor.execute(command=add_cmd)

            if result.success:
                logger.debug("Successfully added private key to ssh-agent")
            else:
                logger.error(f"Failed to add private key to ssh-agent: {result.stderr}")

            return result

        except Exception as e:
            error_msg = f"Exception adding key to ssh-agent: {str(e)}"
            logger.error(error_msg)
            return ExecResult(
                success=False,
                return_code=1,
                stdout="",
                stderr=error_msg
            )

    def add_key_from_file(self, key_file_path: str) -> ExecResult:
        """Add a private key to ssh-agent from file.
        
        Args:
            key_file_path: Path to the private key file
        
        Returns:
            ExecResult: Result of the add key operation
        """
        if not self.is_running():
            error_msg = "SSH agent is not running. Start it first."
            logger.error(error_msg)
            return ExecResult(
                success=False,
                return_code=1,
                stdout="",
                stderr=error_msg
            )

        try:
            add_cmd = self._commands.add_key_from_file(key_file_path)
            # Set the socket environment variable so the command uses our specific agent
            add_cmd.env = {self.SSH_AUTH_SOCK_ENV_VAR: self.socket_path}
            result = self.executor.execute(command=add_cmd)

            if result.success:
                logger.debug(f"Successfully added key file {key_file_path} to ssh-agent")
            else:
                logger.error(f"Failed to add key file to ssh-agent: {result.stderr}")

            return result

        except Exception as e:
            error_msg = f"Exception adding key file to ssh-agent: {str(e)}"
            logger.error(error_msg)
            return ExecResult(
                success=False,
                return_code=1,
                stdout="",
                stderr=error_msg
            )

    def list_keys(self) -> ExecResult[List[str]]:
        """List all keys currently loaded in ssh-agent.
        
        Returns:
            ExecResult[List[str]]: Result containing list of key fingerprints if successful
        """
        if not self.is_running():
            error_msg = "SSH agent is not running. Start it first."
            logger.error(error_msg)
            typed_result = ExecResult[List[str]](
                success=False,
                return_code=1,
                stdout="",
                stderr=error_msg
            )
            typed_result.result = []
            return typed_result

        try:
            from ...commands.runnable_command_string import RunnableCommandString
            
            # Use direct ssh-add command with our socket
            list_cmd = RunnableCommandString(command="ssh-add -l")
            list_cmd.env = {self.SSH_AUTH_SOCK_ENV_VAR: self.socket_path}
            
            result = self.executor.execute(command=list_cmd)

            if result.success and result.stdout:
                # Parse the key list output
                keys = self._parse_key_list(result.stdout)
                logger.debug(f"SSH agent has {len(keys)} keys loaded")
                
                typed_result = ExecResult[List[str]](
                    success=True,
                    return_code=result.return_code,
                    stdout=result.stdout,
                    stderr=result.stderr
                )
                typed_result.result = keys
                return typed_result
            else:
                # No keys loaded or agent not accessible
                typed_result = ExecResult[List[str]](
                    success=result.return_code == 1,  # Return code 1 means no keys loaded (but agent running)
                    return_code=result.return_code,
                    stdout=result.stdout or "",
                    stderr=result.stderr or ""
                )
                typed_result.result = []
                return typed_result

        except Exception as e:
            error_msg = f"Exception listing keys from ssh-agent: {str(e)}"
            logger.error(error_msg)
            typed_result = ExecResult[List[str]](
                success=False,
                return_code=1,
                stdout="",
                stderr=error_msg
            )
            typed_result.result = []
            return typed_result

    def remove_all_keys(self) -> ExecResult:
        """Remove all keys from ssh-agent.
        
        Returns:
            ExecResult: Result of the remove operation
        """
        if not self.is_running():
            error_msg = "SSH agent is not running. Start it first."
            logger.error(error_msg)
            return ExecResult(
                success=False,
                return_code=1,
                stdout="",
                stderr=error_msg
            )

        try:
            from ...commands.runnable_command_string import RunnableCommandString
            
            # Use direct ssh-add command with our socket
            remove_cmd = RunnableCommandString(command="ssh-add -D")
            remove_cmd.env = {self.SSH_AUTH_SOCK_ENV_VAR: self.socket_path}
            
            result = self.executor.execute(command=remove_cmd)

            if result.success:
                logger.debug("Successfully removed all keys from ssh-agent")
            else:
                logger.error(f"Failed to remove keys from ssh-agent: {result.stderr}")

            return result

        except Exception as e:
            error_msg = f"Exception removing keys from ssh-agent: {str(e)}"
            logger.error(error_msg)
            return ExecResult(
                success=False,
                return_code=1,
                stdout="",
                stderr=error_msg
            )

    def get_setup_env_vars(self) -> Dict[str, str]:
        """Get the environment variables needed to set up the SSH agent in the shell session.
        
        Use this to set the `RunnableCommandString.env` property when executing commands that need
        access to the SSH agent. For example: Git commands need to this to access SSH keys.

        Returns:
            Dict[str, str]: Dictionary containing SSH_AUTH_SOCK and SSH_AGENT_PID
        """
        env_vars: Dict[str, str] = {}
        env_vars[self.SSH_AUTH_SOCK_ENV_VAR] = self.socket_path
        env_vars[self.SSH_AGENT_PID_ENV_VAR] = self._agent_pid or ""
        return env_vars

    def _parse_agent_output(self, output: str) -> Dict[str, str]:
        """Parse ssh-agent output to extract environment variables.
        
        Args:
            output: Output from ssh-agent -s command
            
        Returns:
            Dict[str, str]: Dictionary containing SSH_AUTH_SOCK and SSH_AGENT_PID
        """
        env_vars = {}
        
        # Parse SSH_AUTH_SOCK
        auth_sock_match = re.search(r'SSH_AUTH_SOCK=([^;]+);', output)
        if auth_sock_match:
            env_vars[self.SSH_AUTH_SOCK_ENV_VAR] = auth_sock_match.group(1)
        
        # Parse SSH_AGENT_PID
        agent_pid_match = re.search(r'SSH_AGENT_PID=([^;]+);', output)
        if agent_pid_match:
            env_vars[self.SSH_AGENT_PID_ENV_VAR] = agent_pid_match.group(1)
            
        return env_vars

    def _parse_key_list(self, output: str) -> List[str]:
        """Parse ssh-add -l output to extract key fingerprints.
        
        Args:
            output: Output from ssh-add -l command
            
        Returns:
            List[str]: List of key information strings
        """
        if not output.strip():
            return []
            
        lines = output.strip().split('\n')
        keys = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('The agent has no identities'):
                keys.append(line)
                
        return keys

    def _get_current_env_vars(self) -> Dict[str, str]:
        """Get current SSH agent environment variables.
        
        Returns:
            Dict[str, str]: Dictionary containing current SSH_AUTH_SOCK and SSH_AGENT_PID
        """
        env_vars = {}
        
        # Try to get SSH_AUTH_SOCK from environment
        try:
            from ...commands.runnable_command_string import RunnableCommandString
            sock_result = self.executor.execute(
                command=RunnableCommandString(command=f"echo ${self.SSH_AUTH_SOCK_ENV_VAR}")
            )
            if sock_result.success and sock_result.stdout:
                sock_value = sock_result.stdout.strip()
                if sock_value and sock_value != f"${self.SSH_AUTH_SOCK_ENV_VAR}":
                    env_vars[self.SSH_AUTH_SOCK_ENV_VAR] = sock_value
        except Exception:
            pass
            
        # Try to get SSH_AGENT_PID from environment
        try:
            from ...commands.runnable_command_string import RunnableCommandString
            pid_result = self.executor.execute(
                command=RunnableCommandString(command=f"echo ${self.SSH_AGENT_PID_ENV_VAR}")
            )
            if pid_result.success and pid_result.stdout:
                pid_value = pid_result.stdout.strip()
                if pid_value and pid_value != f"${self.SSH_AGENT_PID_ENV_VAR}":
                    env_vars[self.SSH_AGENT_PID_ENV_VAR] = pid_value
        except Exception:
            pass
            
        return env_vars

    @property
    def agent_pid(self) -> Optional[str]:
        """Get the SSH agent process ID.
        
        Returns:
            Optional[str]: The SSH agent PID if known, None otherwise
        """
        return self._agent_pid

    @property
    def auth_sock(self) -> Optional[str]:
        """Get the SSH agent authentication socket path.
        
        Returns:
            Optional[str]: The SSH agent socket path if known, None otherwise
        """
        return self.socket_path

    def get_agent_info(self) -> Dict[str, Optional[str]]:
        """Get comprehensive information about the SSH agent.
        
        Returns:
            Dict[str, Optional[str]]: Dictionary containing agent information including:
                - pid: The SSH agent process ID
                - socket_path: The authentication socket path
                - is_running: Whether the agent is currently running
                - num_keys: Number of keys currently loaded (if agent is running)
        """
        info = {
            "pid": self._agent_pid,
            "socket_path": self.socket_path,
            "is_running": str(self.is_running()),
            "num_keys": None
        }
        
        # If agent is running, try to get the number of loaded keys
        if self.is_running():
            try:
                keys_result = self.list_keys()
                if keys_result.success and keys_result.result is not None:
                    info["num_keys"] = str(len(keys_result.result))
                else:
                    info["num_keys"] = "0"
            except Exception as e:
                logger.debug(f"Could not get key count: {e}")
                info["num_keys"] = "unknown"
        else:
            info["num_keys"] = "0"
        
        return info

    def get_process_info(self) -> ExecResult[Dict[str, str]]:
        """Get detailed process information about the SSH agent.
        
        Returns:
            ExecResult[Dict[str, str]]: Result containing process details if successful:
                - pid: Process ID
                - ppid: Parent process ID  
                - command: Full command line
                - status: Process status
                - memory: Memory usage
                - cpu_time: CPU time used
        """
        if not self.is_running():
            error_msg = "SSH agent is not running"
            logger.error(error_msg)
            typed_result = ExecResult[Dict[str, str]](
                success=False,
                return_code=1,
                stdout="",
                stderr=error_msg
            )
            typed_result.result = {}
            return typed_result

        try:
            from ...commands.runnable_command_string import RunnableCommandString
            
            process_info = {}
            
            # Get basic process info using ps if we have a PID
            if self._agent_pid:
                ps_cmd = RunnableCommandString(
                    command=f"ps -p {self._agent_pid} -o pid,ppid,command,stat,rss,time --no-headers"
                )
                ps_result = self.executor.execute(ps_cmd)
                
                if ps_result.success and ps_result.stdout:
                    # Parse ps output
                    ps_fields = ps_result.stdout.strip().split(None, 5)
                    if len(ps_fields) >= 6:
                        process_info.update({
                            "pid": ps_fields[0],
                            "ppid": ps_fields[1], 
                            "command": ps_fields[2],
                            "status": ps_fields[3],
                            "memory_kb": ps_fields[4],
                            "cpu_time": ps_fields[5]
                        })
            
            # Get socket information if we have a socket path
            if self.socket_path:
                # Check if socket file exists and get its info
                socket_cmd = RunnableCommandString(
                    command=f"ls -la {self.socket_path}"
                )
                socket_result = self.executor.execute(socket_cmd)
                
                if socket_result.success and socket_result.stdout:
                    process_info["socket_info"] = socket_result.stdout.strip()
                else:
                    process_info["socket_info"] = "Socket file not found"
            
            # Get environment variables related to SSH agent
            env_cmd = RunnableCommandString(
                command="env | grep SSH_"
            )
            env_result = self.executor.execute(env_cmd)
            
            if env_result.success and env_result.stdout:
                process_info["ssh_env_vars"] = env_result.stdout.strip()
            else:
                process_info["ssh_env_vars"] = "No SSH environment variables found"
                
            typed_result = ExecResult[Dict[str, str]](
                success=True,
                return_code=0,
                stdout="Process information retrieved successfully",
                stderr=""
            )
            typed_result.result = process_info
            return typed_result

        except Exception as e:
            error_msg = f"Exception getting process info: {str(e)}"
            logger.error(error_msg)
            typed_result = ExecResult[Dict[str, str]](
                success=False,
                return_code=1,
                stdout="",
                stderr=error_msg
            )
            typed_result.result = {}
            return typed_result

    def refresh_agent_info(self) -> ExecResult[Dict[str, Optional[str]]]:
        """Refresh and get current SSH agent information from the system.
        
        This method queries the system to get the current SSH agent PID and socket path,
        updating the internal state if an agent is found.
        
        Returns:
            ExecResult[Dict[str, Optional[str]]]: Result containing updated agent info
        """
        try:
            agent_info = {}
            
            # Try to get PID from system
            pid_cmd = self._commands.get_agent_pid()
            pid_result = self.executor.execute(pid_cmd)
            
            if pid_result.success and pid_result.stdout:
                pid_value = pid_result.stdout.strip()
                if pid_value and pid_value != "" and pid_value.isdigit():
                    agent_info["pid"] = pid_value
                    self._agent_pid = pid_value
                else:
                    agent_info["pid"] = None
                    self._agent_pid = None
            
            # Try to get socket path from system
            socket_cmd = self._commands.get_socket_path()
            socket_result = self.executor.execute(socket_cmd)
            
            if socket_result.success and socket_result.stdout:
                socket_value = socket_result.stdout.strip()
                if socket_value and socket_value != "" and socket_value != f"${self.SSH_AUTH_SOCK_ENV_VAR}":
                    agent_info["socket_path"] = socket_value
                    self._auth_sock = socket_value
                else:
                    agent_info["socket_path"] = None
                    self._auth_sock = None
            
            # Update running status
            agent_info["is_running"] = str(self.is_running())
            
            # Get key count if running
            if self.is_running():
                keys_result = self.list_keys()
                if keys_result.success and keys_result.result is not None:
                    agent_info["num_keys"] = str(len(keys_result.result))
                else:
                    agent_info["num_keys"] = "0"
            else:
                agent_info["num_keys"] = "0"
            
            logger.debug(f"Refreshed SSH agent info: {agent_info}")
            
            typed_result = ExecResult[Dict[str, Optional[str]]](
                success=True,
                return_code=0,
                stdout="SSH agent info refreshed successfully",
                stderr=""
            )
            typed_result.result = agent_info
            return typed_result

        except Exception as e:
            error_msg = f"Exception refreshing agent info: {str(e)}"
            logger.error(error_msg)
            typed_result = ExecResult[Dict[str, Optional[str]]](
                success=False,
                return_code=1,
                stdout="",
                stderr=error_msg
            )
            typed_result.result = {}
            return typed_result

    def kill_all_agents(self) -> ExecResult:
        """Kill all SSH agent processes for the current user.
        
        This is useful for cleanup when multiple agents might be running.
        
        Returns:
            ExecResult: Result of killing all SSH agent processes
        """
        try:
            kill_all_cmd = self._commands.kill_all_agents()
            result = self.executor.execute(kill_all_cmd)
            
            if result.success or result.return_code == 1:  # pkill returns 1 if no processes found
                logger.debug("Successfully killed all SSH agent processes")
                # Reset internal state since all agents are killed
                self._agent_pid = None
                self._auth_sock = None
                
                # Return success even if no processes were found to kill
                return ExecResult(
                    success=True,
                    return_code=0,
                    stdout="All SSH agent processes killed",
                    stderr=""
                )
            else:
                logger.error(f"Failed to kill SSH agent processes: {result.stderr}")
                return result

        except Exception as e:
            error_msg = f"Exception killing SSH agent processes: {str(e)}"
            logger.error(error_msg)
            return ExecResult(
                success=False,
                return_code=1,
                stdout="",
                stderr=error_msg
            )
