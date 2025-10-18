from enum import Enum


class CloudProviders(str, Enum):
    """Supported cloud providers for automated server creation."""
    #AZURE = "azure"
    #AWS = "aws"
    #DIGITAL_OCEAN = "digitalocean"
    #LINODE = "linode"
    #VULTR = "vultr"
    HETZNER = "hetzner"
    #GCP = "gcp"
    #OVH = "ovh"
    