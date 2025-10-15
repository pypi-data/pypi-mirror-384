from enum import Enum


class PodmanNetworkDriver(Enum):
  """Podman network driver types aka network modes."""
  BRIDGE = "bridge"
  HOST = "host"
  NONE = "none"