from ...commands.base.ip_tables_persistent_commands import IpTablesPersistentCommands
from ...types.cpu_arch_types import CpuArch
from ...types.os_type import OS


class IpTablesPersistentCommandsUbuntu(IpTablesPersistentCommands):
    def __init__(self,cpu_arch: CpuArch) -> None:
        super().__init__(os= OS.UBUNTU, cpu_arch=cpu_arch, command_name="iptables-save")
    