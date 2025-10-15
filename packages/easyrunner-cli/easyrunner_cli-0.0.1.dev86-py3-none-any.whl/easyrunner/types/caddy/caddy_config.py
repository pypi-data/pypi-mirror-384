"""Caddy configuration.

This class is a sparse representation of the Caddy configuration. It's not intended to represent everything that possible. Just this bits we need.
"""

from dataclasses import dataclass

from ...types.caddy.caddy_site import CaddySite


@dataclass
class CaddyConfig:
    """Represents the Caddy configuration.
    
    See https://caddyserver.com/docs/json/
    """
      
    sites: list[CaddySite] = []
    
