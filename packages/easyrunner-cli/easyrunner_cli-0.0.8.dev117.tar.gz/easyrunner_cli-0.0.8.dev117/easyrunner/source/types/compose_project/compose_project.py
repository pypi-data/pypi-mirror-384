import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional

from .compose_network import ComposeNetwork
from .compose_service import ComposeService
from .compose_volume import ComposeVolume


@dataclass
class ComposeProject:
    """Data class for a Docker Compose project in the Compose Specification format which supersedes the versioned format.
    
    Represents a complete Docker Compose configuration including services,
    networks, and volumes.
    
    Attributes:
        name (str): Name of the compose project.
        services (Dict[str, ComposeService]): Dictionary of services keyed by service name.
        networks (Dict[str, ComposeNetwork]): Dictionary of networks keyed by network name.
        volumes (Dict[str, ComposeVolume]): Dictionary of volumes keyed by volume name.
    """

    name: str = field()
    """Name of the compose project."""

    services: Dict[str, ComposeService] = field(default_factory=dict)
    """Dictionary of services keyed by service name."""

    networks: Dict[str, ComposeNetwork] = field(default_factory=dict)
    """Dictionary of networks keyed by network name."""

    volumes: Dict[str, ComposeVolume] = field(default_factory=dict)
    """Dictionary of volumes keyed by volume name."""

    def systemd_container_name(self, service: ComposeService) -> str:
        """build the systemd container name

        Args:
            service: The service instance.

        Returns:
            str: The systemd generated container name for the service.
        """
        return f"systemd-{self.name}__{service.name}"

    @classmethod
    def from_compose_yaml(cls, compose_yaml: str, project_name: Optional[str] = None) -> "ComposeProject":
        """Create a ComposeProject from a Docker Compose YAML string.
        
        Args:
            compose_yaml: The Docker Compose YAML content as a string.
            project_name: Optional project name override.
            
        Returns:
            ComposeProject: A new ComposeProject instance.
        """
        import yaml

        compose_data = yaml.safe_load(compose_yaml)

        # Extract project name
        name = project_name or compose_data.get(
            "name", f"unnamed-project-{uuid.uuid4().hex[:8]}"
        )

        # Convert services
        services = {}
        for service_name, service_data in compose_data.get("services", {}).items():
            # Handle labels - normalize both list and dict formats to Dict[str, str]
            raw_labels = service_data.get("labels", {})
            normalized_labels = {}

            if isinstance(raw_labels, dict):
                # Already in dict format {"key": value} - preserve YAML types in as corresponding Python types
                normalized_labels = raw_labels
            elif isinstance(raw_labels, list):
                # Convert list format ["key=value"] to dict format
                for label in raw_labels:
                    if "=" in label:
                        key, value = label.split("=", 1)  # Split only on first =
                        normalized_labels[key] = value
                    else:
                        # Handle labels without values (just keys)
                        normalized_labels[label] = ""

            services[service_name] = ComposeService(
                name=service_name,
                image=service_data.get("image", ""),
                ports=service_data.get("ports", []),
                environment=service_data.get("environment", []),
                volumes=service_data.get("volumes", []),
                networks=service_data.get("networks", []),
                labels=normalized_labels,
                restart=service_data.get("restart"),
                user=service_data.get("user"),
                command=service_data.get("command"),
                depends_on=service_data.get("depends_on", []),
            )

        # Convert networks
        networks = {}
        for network_name, network_data in compose_data.get("networks", {}).items():
            networks[network_name] = ComposeNetwork(
                name=network_name,
                project_name=name,
                driver=network_data.get("driver") if isinstance(network_data, dict) else None,
                external=network_data.get("external", False) if isinstance(network_data, dict) else False,
                driver_opts=network_data.get("driver_opts", {}) if isinstance(network_data, dict) else {},
                ipam=network_data.get("ipam") if isinstance(network_data, dict) else None
            )

        # Convert volumes
        volumes = {}
        for volume_name, volume_data in compose_data.get("volumes", {}).items():
            volumes[volume_name] = ComposeVolume(
                name=volume_name,
                driver=volume_data.get("driver") if isinstance(volume_data, dict) else None,
                driver_opts=volume_data.get("driver_opts", {}) if isinstance(volume_data, dict) else {},
                external=volume_data.get("external", False) if isinstance(volume_data, dict) else False
            )

        return cls(
            name=name,
            services=services,
            networks=networks,
            volumes=volumes
        )
