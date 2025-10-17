from dataclasses import dataclass

from ...types.json import JsonObject


@dataclass
class CaddySite:
    """Represents a Caddy site block in configuration."""
    
    name: str
    """The name key of the site."""
    
    config_json: JsonObject
    """The Caddy json configuration of the site block. i.e.: server section.
    See https://caddyserver.com/docs/json/apps/http/servers/
    """
