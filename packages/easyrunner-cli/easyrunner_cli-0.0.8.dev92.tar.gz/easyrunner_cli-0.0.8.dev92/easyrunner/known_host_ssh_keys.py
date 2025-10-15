"""
List of known host keys for SSH connections. Example: for github.com
We need to add these to the known_hosts file to avoid MITM attacks and avoid being prompted to verify on first connection.
This is a dictionary where the key is the hostname and the value is a list of known host keys
The keys are in the format "<hostname> <key_type> <key_value>" which is the format of the known_hosts file
These can be added to the known_hosts file directly. We do this to mitigate MITM attacks.
if host only publishes the fingerprints then use:
Get the keys for the host and save to a temp file `ssh-keyscan <hostname> > <hostname>_sshkey.txt`
Generate the fingerprints for them `ssh-keygen -lf <hostname>_sshkey.txt -E sha256` (make sure -E matches the hash algorithm used in the fingerprint by the respective host)
manually check the fingerprints of the downloaded keys match the host's published fingerprints.
if the fingerprints match, run `cat <hostname>_sshkey.txt` to get the keys, then add them to the list below.
"""
from typing import List

KNOWN_HOST_SSH_KEYS: dict[str, List[str]] = {
    "github.com": [
        "github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl",
        "github.com ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBEmKSENjQEezOmxkZMy7opKgwFB9nkt5YRrYMjNuG5N87uRgg6CLrbo5wAdT/y6v0mKV0U2w0WZ2YB/++Tpockg=",
        "github.com ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCj7ndNxQowgcQnjshcLrqPEiiphnt+VTTvDP6mHBL9j1aNUkY4Ue1gvwnGLVlOhGeYrnZaMgRK6+PKCUXaDbC7qtbW8gIkhL7aGCsOr/C56SJMy/BCZfxd1nWzAOxSDPgVsmerOBYfNqltV9/hWCqBywINIR+5dIg6JTJ72pcEpEjcYgXkE2YEFXV1JHnsKgbLWNlhScqb2UmyRkQyytRLtL+38TGxkxCflmO+5Z8CSSNY7GidjMIZ7Q4zMjA2n1nGrlTDkzwDCsw+wqFPGQA179cnfGWOWRVruj16z6XyvxvjJwbz0wQZ75XK5tKSb7FNyeIEs4TT4jk+S4dhPeAUC5y+bDYirYgM4GC7uEnztnZyaVWQ7B381AK4Qdrwt51ZqExKbQpTUNn+EjqoTwvqNj4kqx5QUCI0ThS/YkOxJCXmPUWZbhjpCg56i+2aB6CmK2JGhn57K5mj0MNdBXA4/WnwH6XoPWJzK5Nyu2zB3nAZp+S5hpQs+p1vN1/wsjk=",
    ]
}