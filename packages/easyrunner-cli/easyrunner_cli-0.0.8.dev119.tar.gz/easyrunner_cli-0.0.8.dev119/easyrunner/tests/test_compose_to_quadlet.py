"""Tests for Podman compose_to_quadlet conversion."""

from easyrunner.source.resources.os_resources.podman import Podman
from easyrunner.source.types.compose_project.compose_project import ComposeProject


class TestComposeToQuadlet:
    """Test suite for compose_to_quadlet conversion."""

    def test_basic_service_conversion(self):
        """Test conversion of a basic service with minimal configuration."""
        compose_yaml = """
name: test-project
services:
  web:
    image: nginx:latest
    ports:
      - "8080:80"
networks:
  default:
    driver: bridge
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        result = Podman.compose_to_quadlet(project)

        # Should have container, network, and no volumes
        assert "web.container" in result
        assert "default.network" in result
        assert len([k for k in result.keys() if k.endswith(".volume")]) == 0

        # Check container unit content
        container_unit = result["web.container"]
        assert "Image=nginx:latest" in container_unit
        assert "PublishPort=8080:80" in container_unit
        assert "[Container]" in container_unit
        assert "[Install]" in container_unit
        assert "WantedBy=default.target" in container_unit

    def test_service_with_none_environment(self):
        """Test that services with environment: (no value) don't cause errors."""
        compose_yaml = """
name: test-project
services:
  caddy:
    image: caddy:2-alpine
    ports:
      - "8080:80"
    environment:
networks:
  default:
    driver: bridge
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        # Should not raise TypeError
        result = Podman.compose_to_quadlet(project)

        assert "caddy.container" in result
        container_unit = result["caddy.container"]
        # Should not contain any Environment= lines
        assert "Environment=" not in container_unit

    def test_service_with_none_labels(self):
        """Test that services with labels: (no value) don't cause errors."""
        compose_yaml = """
name: test-project
services:
  app:
    image: myapp:latest
    labels:
networks:
  default:
    driver: bridge
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        # Should not raise TypeError
        result = Podman.compose_to_quadlet(project)

        assert "app.container" in result
        container_unit = result["app.container"]
        # Should not contain any Label= lines
        assert "Label=" not in container_unit

    def test_service_with_environment_dict(self):
        """Test service with environment variables as dict."""
        compose_yaml = """
name: test-project
services:
  app:
    image: myapp:latest
    environment:
      DATABASE_URL: postgres://localhost/db
      DEBUG: "true"
      PORT: "3000"
networks:
  default:
    driver: bridge
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        result = Podman.compose_to_quadlet(project)

        container_unit = result["app.container"]
        assert "Environment=DATABASE_URL=postgres://localhost/db" in container_unit
        assert "Environment=DEBUG=true" in container_unit
        assert "Environment=PORT=3000" in container_unit

    def test_service_with_environment_list(self):
        """Test service with environment variables as list."""
        compose_yaml = """
name: test-project
services:
  app:
    image: myapp:latest
    environment:
      - DATABASE_URL=postgres://localhost/db
      - DEBUG=true
      - PORT=3000
networks:
  default:
    driver: bridge
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        result = Podman.compose_to_quadlet(project)

        container_unit = result["app.container"]
        assert "Environment=DATABASE_URL=postgres://localhost/db" in container_unit
        assert "Environment=DEBUG=true" in container_unit
        assert "Environment=PORT=3000" in container_unit

    def test_service_with_labels_dict(self):
        """Test service with labels as dict."""
        compose_yaml = """
name: test-project
services:
  app:
    image: myapp:latest
    labels:
      easyrunner.domain: myapp.example.com
      easyrunner.enabled: true
      easyrunner.port: 3000
networks:
  default:
    driver: bridge
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        result = Podman.compose_to_quadlet(project)

        container_unit = result["app.container"]
        assert "Label=easyrunner.domain=myapp.example.com" in container_unit
        assert "Label=easyrunner.enabled=True" in container_unit
        assert "Label=easyrunner.port=3000" in container_unit

    def test_service_with_labels_list(self):
        """Test service with labels as list."""
        compose_yaml = """
name: test-project
services:
  app:
    image: myapp:latest
    labels:
      - easyrunner.domain=myapp.example.com
      - easyrunner.enabled=true
networks:
  default:
    driver: bridge
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        result = Podman.compose_to_quadlet(project)

        container_unit = result["app.container"]
        assert "Label=easyrunner.domain=myapp.example.com" in container_unit
        assert "Label=easyrunner.enabled=true" in container_unit

    def test_service_with_volumes(self):
        """Test service with volume mounts."""
        compose_yaml = """
name: test-project
services:
  app:
    image: myapp:latest
    volumes:
      - /host/path:/container/path
      - named_volume:/data
      - /another/path:/mount:ro
networks:
  default:
    driver: bridge
volumes:
  named_volume:
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        result = Podman.compose_to_quadlet(project)

        container_unit = result["app.container"]
        assert "Volume=/host/path:/container/path" in container_unit
        assert "Volume=named_volume:/data" in container_unit
        assert "Volume=/another/path:/mount:ro" in container_unit

        # Check volume unit
        assert "named_volume.volume" in result
        volume_unit = result["named_volume.volume"]
        assert "[Volume]" in volume_unit
        assert "Description=named_volume volume" in volume_unit

    def test_service_with_networks(self):
        """Test service with multiple networks."""
        compose_yaml = """
name: test-project
services:
  app:
    image: myapp:latest
    networks:
      - frontend
      - backend
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        result = Podman.compose_to_quadlet(project)

        container_unit = result["app.container"]
        # Should reference systemd network names
        assert "Network=systemd-test-project__frontend" in container_unit
        assert "Network=systemd-test-project__backend" in container_unit

        # Should have network units
        assert "frontend.network" in result
        assert "backend.network" in result

    def test_service_with_depends_on(self):
        """Test service dependencies."""
        compose_yaml = """
name: test-project
services:
  db:
    image: postgres:latest
  app:
    image: myapp:latest
    depends_on:
      - db
networks:
  default:
    driver: bridge
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        result = Podman.compose_to_quadlet(project)

        app_unit = result["app.container"]
        # Should have systemd dependencies
        assert "After=test-project__db.service" in app_unit
        assert "Requires=test-project__db.service" in app_unit

    def test_service_with_network_and_service_dependencies(self):
        """Test service with both network and service dependencies."""
        compose_yaml = """
name: test-project
services:
  db:
    image: postgres:latest
    networks:
      - backend
  app:
    image: myapp:latest
    depends_on:
      - db
    networks:
      - backend
networks:
  backend:
    driver: bridge
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        result = Podman.compose_to_quadlet(project)

        app_unit = result["app.container"]
        # Should have both network and service dependencies
        assert "After=test-project__backend-network.service test-project__db.service" in app_unit
        assert "Requires=test-project__backend-network.service test-project__db.service" in app_unit

    def test_service_with_user(self):
        """Test service with user specification."""
        compose_yaml = """
name: test-project
services:
  app:
    image: myapp:latest
    user: "1000:1000"
networks:
  default:
    driver: bridge
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        result = Podman.compose_to_quadlet(project)

        container_unit = result["app.container"]
        assert "User=1000:1000" in container_unit

    def test_ignore_ports_flag(self):
        """Test that ignore_ports flag prevents port publishing."""
        compose_yaml = """
name: test-project
services:
  app:
    image: myapp:latest
    ports:
      - "8080:80"
      - "8443:443"
networks:
  default:
    driver: bridge
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        result = Podman.compose_to_quadlet(project, ignore_ports=True)

        container_unit = result["app.container"]
        # Should not contain any PublishPort lines
        assert "PublishPort=" not in container_unit

    def test_external_network(self):
        """Test service with external network."""
        compose_yaml = """
name: test-project
services:
  app:
    image: myapp:latest
    networks:
      - external_net
networks:
  external_net:
    external: true
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        result = Podman.compose_to_quadlet(project)

        # Should still create network unit (Quadlet handles external networks)
        assert "external_net.network" in result

    def test_complex_service(self):
        """Test a complex service with multiple features."""
        compose_yaml = """
name: easyrunner
services:
  caddy:
    image: docker.io/library/caddy:2-alpine
    ports:
      - "8080:80"
      - "8443:443"
      - "127.0.0.1:2019:2019"
    restart: unless-stopped
    volumes:
      - /home/easyrunner/easyrunner-stack/infra/caddy/Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    networks:
      - easyrunner_proxy_network
    environment:
    command: caddy run --config /etc/caddy/Caddyfile --watch
networks:
  easyrunner_proxy_network:
    name: easyrunner_proxy_network
    external: true
volumes:
  caddy_data:
  caddy_config:
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        # This should not raise any errors (regression test for the bug)
        result = Podman.compose_to_quadlet(project)

        assert "caddy.container" in result
        assert "easyrunner_proxy_network.network" in result
        assert "caddy_data.volume" in result
        assert "caddy_config.volume" in result

        container_unit = result["caddy.container"]
        assert "Image=docker.io/library/caddy:2-alpine" in container_unit
        assert "PublishPort=8080:80" in container_unit
        assert "PublishPort=8443:443" in container_unit
        assert "PublishPort=127.0.0.1:2019:2019" in container_unit
        assert "Volume=/home/easyrunner/easyrunner-stack/infra/caddy/Caddyfile:/etc/caddy/Caddyfile" in container_unit
        assert "Volume=caddy_data:/data" in container_unit
        assert "Volume=caddy_config:/config" in container_unit
        assert "Network=systemd-easyrunner__easyrunner_proxy_network" in container_unit
        # Environment should be None and not cause errors
        assert "Environment=" not in container_unit

    def test_empty_project(self):
        """Test empty compose project."""
        compose_yaml = """
name: empty-project
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        result = Podman.compose_to_quadlet(project)

        # Should return empty dict
        assert result == {}

    def test_service_with_empty_environment_list(self):
        """Test service with empty environment list."""
        compose_yaml = """
name: test-project
services:
  app:
    image: myapp:latest
    environment: []
networks:
  default:
    driver: bridge
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        result = Podman.compose_to_quadlet(project)

        container_unit = result["app.container"]
        # Should not contain any Environment= lines
        assert "Environment=" not in container_unit

    def test_service_with_empty_labels_dict(self):
        """Test service with empty labels dict."""
        compose_yaml = """
name: test-project
services:
  app:
    image: myapp:latest
    labels: {}
networks:
  default:
    driver: bridge
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        result = Podman.compose_to_quadlet(project)

        container_unit = result["app.container"]
        # Should not contain any Label= lines
        assert "Label=" not in container_unit

    def test_network_with_driver(self):
        """Test network with driver specification."""
        compose_yaml = """
name: test-project
services:
  app:
    image: myapp:latest
    networks:
      - custom_net
networks:
  custom_net:
    driver: macvlan
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        result = Podman.compose_to_quadlet(project)

        network_unit = result["custom_net.network"]
        assert "Driver=macvlan" in network_unit

    def test_volume_external(self):
        """Test external volume."""
        compose_yaml = """
name: test-project
services:
  app:
    image: myapp:latest
    volumes:
      - external_vol:/data
networks:
  default:
    driver: bridge
volumes:
  external_vol:
    external: true
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        result = Podman.compose_to_quadlet(project)

        # Should still create volume unit
        assert "external_vol.volume" in result

    def test_systemd_unit_structure(self):
        """Test that generated units have correct systemd structure."""
        compose_yaml = """
name: test-project
services:
  app:
    image: myapp:latest
networks:
  default:
    driver: bridge
"""
        project = ComposeProject.from_compose_yaml(compose_yaml)
        result = Podman.compose_to_quadlet(project)

        container_unit = result["app.container"]
        # Check for proper sections
        assert "[Unit]" in container_unit
        assert "[Container]" in container_unit
        assert "[Install]" in container_unit
        
        # Check Install section content
        assert "WantedBy=default.target" in container_unit

        network_unit = result["default.network"]
        assert "[Unit]" in network_unit
        assert "[Network]" in network_unit
        assert "[Install]" in network_unit
