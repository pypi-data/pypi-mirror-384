import os
import tarfile
from pathlib import Path


def create_templates_archive():
    """Create a compressed archive of template files during package installation."""
    templates_dir = Path(".server-config")
    if not templates_dir.exists():
        print("Templates directory not found, skipping archive creation")
        return

    archive_name = "server-config.tar.gz"
    with tarfile.open(archive_name, "w:gz") as tar:
        # Add each directory in .server-config to the archive
        for item in templates_dir.iterdir():
            if item.is_dir():
                tar.add(item, arcname=item.name)

    # Move the archive to the artefacts directory
    archive_dir = Path("source/artefacts")
    archive_dir.mkdir(exist_ok=True)
    os.rename(archive_name, archive_dir / archive_name)

if __name__ == "__main__":
    create_templates_archive()
