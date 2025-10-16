#!/usr/bin/env python3
"""Cache management for Flavor packages."""

import contextlib
import os
from pathlib import Path
import time

from provide.foundation.file import temp_dir
from provide.foundation.file.directory import ensure_dir, safe_rmtree
from provide.foundation.file.formats import read_json
from provide.foundation.utils.environment import get_str


def get_cache_dir() -> Path:
    """Get the cache directory for Flavor packages."""
    cache_dir = get_str("FLAVOR_CACHE")
    if cache_dir:
        return Path(cache_dir)

    # Default cache locations
    if os.name == "posix":
        if "darwin" in os.uname().sysname.lower():
            # macOS
            base = Path(get_str("TMPDIR", default="/var/folders"))
            return base / "pspf" / "workenv"
        else:
            # Linux
            return temp_dir().parent / "pspf" / "workenv"
    else:
        # Windows
        return temp_dir().parent / "pspf" / "workenv"


class CacheManager:
    """Manages the Flavor package cache."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialize cache manager.

        Args:
            cache_dir: Override cache directory (defaults to system cache)
        """
        self.cache_dir = cache_dir or get_cache_dir()
        ensure_dir(self.cache_dir)

    def list_cached(self) -> list[dict]:
        """List all cached packages.

        Returns:
            List of cached package information
        """
        cached = []

        for entry in self.cache_dir.iterdir():
            if not entry.is_dir() or entry.name.startswith("."):
                continue

            instance_metadata_dir = self.cache_dir / f".{entry.name}.pspf"
            if not instance_metadata_dir.is_dir():
                continue

            # Check for the modern completion marker
            completion_marker = instance_metadata_dir / "instance" / "extract" / "complete"
            if not completion_marker.exists():
                continue

            info = {
                "id": entry.name,
                "path": str(entry),
                "size": self._get_dir_size(entry),
                "modified": entry.stat().st_mtime,
                "metadata_type": "instance",
            }

            # Read metadata from the standard location
            metadata_file = instance_metadata_dir / "package" / "psp.json"
            if metadata_file.exists():
                try:
                    metadata = read_json(metadata_file)
                    pkg = metadata.get("package", metadata)
                    info["name"] = pkg.get("name", "unknown")
                    info["version"] = pkg.get("version", "unknown")
                except (OSError, KeyError):
                    info["name"] = "unknown"
                    info["version"] = "unknown"
            else:
                info["name"] = "unknown"
                info["version"] = "unknown"

            cached.append(info)

        return sorted(cached, key=lambda x: x["modified"], reverse=True)

    def get_cache_size(self) -> int:
        """Get total size of cache in bytes.

        Returns:
            Total cache size in bytes
        """
        total = 0
        for entry in self.cache_dir.iterdir():
            if entry.is_dir():
                total += self._get_dir_size(entry)
        return total

    def clean(self, max_age_days: int | None = None) -> list[str]:
        """Clean old packages from cache.

        Args:
            max_age_days: Remove packages older than this many days (None = remove all)

        Returns:
            List of removed package IDs
        """
        removed = []
        current_time = time.time()

        for entry in self.cache_dir.iterdir():
            if not entry.is_dir():
                continue

            should_remove = False

            # If max_age_days specified, check age
            if max_age_days is not None:
                age_seconds = current_time - entry.stat().st_mtime
                age_days = age_seconds / 86400
                if age_days > max_age_days:
                    should_remove = True
            else:
                # No age specified, remove all
                should_remove = True

            if should_remove:
                # Remove the directory
                try:
                    safe_rmtree(entry)
                    removed.append(entry.name)
                except OSError:
                    pass

        return removed

    def inspect_workenv(self, workenv_name: str) -> dict:
        """Inspect a specific workenv.

        Args:
            workenv_name: Name of the workenv to inspect

        Returns:
            Detailed inspection information
        """
        workenv_dir = self.cache_dir / workenv_name
        instance_metadata_dir = self.cache_dir / f".{workenv_name}.pspf"

        info = {
            "name": workenv_name,
            "content_dir": str(workenv_dir),
            "exists": workenv_dir.exists(),
            "metadata_type": None,
            "metadata_dir": None,
            "checksum": None,
            "extraction_complete": False,
            "package_info": {},
        }

        if not workenv_dir.exists() or not instance_metadata_dir.is_dir():
            return info

        info["metadata_type"] = "instance"
        info["metadata_dir"] = str(instance_metadata_dir)

        # Read checksum from the standard location
        checksum_file = instance_metadata_dir / "instance" / "package.checksum"
        if checksum_file.exists():
            with contextlib.suppress(IOError):
                info["checksum"] = checksum_file.read_text().strip()

        # Check for the modern completion marker
        completion_marker = instance_metadata_dir / "instance" / "extract" / "complete"
        info["extraction_complete"] = completion_marker.exists()

        # Read package metadata from the standard location
        metadata_file = instance_metadata_dir / "package" / "psp.json"
        if metadata_file.exists():
            try:
                metadata = read_json(metadata_file)
                pkg = metadata.get("package", metadata)
                info["package_info"] = {
                    "name": pkg.get("name"),
                    "version": pkg.get("version"),
                    "builder": metadata.get("build", {}).get("builder"),
                }
            except OSError:
                pass

        return info

    def remove(self, package_id: str) -> bool:
        """Remove a specific cached package.

        Args:
            package_id: ID of the package to remove

        Returns:
            True if removed, False if not found
        """
        package_dir = self.cache_dir / package_id
        if package_dir.exists() and package_dir.is_dir():
            try:
                safe_rmtree(package_dir)
                return True
            except OSError:
                return False
        return False

    def _get_dir_size(self, path: Path) -> int:
        """Get total size of a directory.

        Args:
            path: Directory path

        Returns:
            Total size in bytes
        """
        total = 0
        for root, _dirs, files in os.walk(path):
            for file in files:
                filepath = Path(root) / file
                with contextlib.suppress(OSError):
                    total += filepath.stat().st_size
        return total
