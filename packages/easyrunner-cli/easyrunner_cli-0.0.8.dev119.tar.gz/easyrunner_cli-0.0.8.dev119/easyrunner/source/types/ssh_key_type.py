from enum import Enum


class SshKeyType(Enum):
    ED25519 = "ed25519"
    RSA = "rsa"
    ECDSA = "ecdsa"
