#
# flavor/packaging/orchestrator.py
#
"Core logic for building Flavor packages by orchestrating the Go packager CLI."

import os
from pathlib import Path
from typing import Any

from provide.foundation import logger
from provide.foundation.errors import log_only_error_context
from provide.foundation.file import temp_dir
from provide.foundation.file.formats import write_json
from provide.foundation.platform import get_platform_string, is_windows
from provide.foundation.process import run

from flavor.exceptions import BuildError
from flavor.ingredients.manager import IngredientManager
from flavor.packaging.orchestrator_ingredients import (
    create_builder_manifest,
    create_python_builder_metadata,
    create_python_slot_tarballs,
    find_builder_executable,
    find_launcher_executable,
    write_manifest_file,
)
from flavor.packaging.python.packager import PythonPackager
from flavor.psp.metadata.paths import validate_metadata_dict


class PackagingOrchestrator:
    DEFAULT_PYTHON_VERSION = "3.11"

    def __init__(
        self,
        package_integrity_key_path: str | None,
        public_key_path: str | None,
        output_flavor_path: str,
        build_config: dict[str, Any],
        manifest_dir: Path,
        package_name: str,
        version: str,
        entry_point: str,
        python_version: str | None = None,
        launcher_bin: str | None = None,
        builder_bin: str | None = None,
        strip_binaries: bool = False,
        show_progress: bool = False,
        key_seed: str | None = None,
        manifest_type: str = "toml",
    ) -> None:
        self.package_integrity_key_path = package_integrity_key_path
        self.public_key_path = public_key_path
        self.output_flavor_path = output_flavor_path
        self.package_name = package_name
        self.version = version
        self.entry_point = entry_point
        self.build_config = build_config
        self.manifest_dir = manifest_dir
        self.python_version = python_version or self.DEFAULT_PYTHON_VERSION
        self.launcher_bin = launcher_bin
        self.builder_bin = builder_bin
        self.strip_binaries = strip_binaries
        self.show_progress = show_progress
        self.key_seed = key_seed
        self.manifest_type = manifest_type

        # Use IngredientManager for finding helpers
        self.helper_manager = IngredientManager()
        self.platform = get_platform_string()

    @log_only_error_context(
        context_provider=lambda: {"operation": "detect_launcher_type"},
        log_level="trace",
    )
    def _detect_launcher_type(self, launcher_path: Path) -> str:
        """Detect launcher type by running the binary with --version."""
        logger.debug("🔍🚀📋 Detecting launcher type", path=str(launcher_path))
        try:
            result = run(
                [str(launcher_path), "--version"],
                capture_output=True,
                check=False,
                timeout=5,
            )
        except Exception as e:
            raise BuildError(f"Failed to execute command: {e}") from e

        output = result.stdout.lower()
        logger.trace("🔍📤📋 Launcher version output", output=result.stdout.strip())

        if "flavor-rs-launcher" in output or "rust" in output:
            logger.debug("🦀🔍✅ Detected Rust launcher")
            return "rust"
        if "flavor-go-launcher" in output or "go version" in output:
            logger.debug("🐹🔍✅ Detected Go launcher")
            return "go"

        logger.warning(
            "🔍❓⚠️ Could not determine launcher type from output",
            output=result.stdout,
        )
        return "rust"

    @log_only_error_context(
        context_provider=lambda: {"operation": "build_package"},
        log_level="debug",
        log_success=True,
    )
    def build_package(self) -> None:
        logger.info("🎯🏗️🚀 Orchestrator starting build process")
        logger.debug(
            "📦🔍📋 Package details",
            name=self.package_name,
            version=self.version,
            output=self.output_flavor_path,
            python_version=self.python_version,
            platform=self.platform,
            manifest_type=self.manifest_type,
        )
        logger.trace(
            "🔧🔍📋 Build configuration",
            launcher_bin=self.launcher_bin,
            builder_bin=self.builder_bin,
            strip_binaries=self.strip_binaries,
            key_seed=bool(self.key_seed),
            has_keys=bool(self.package_integrity_key_path),
        )

        # Check launcher availability early
        logger.info("🔍🚀 Checking launcher binary availability...")
        launcher_path = find_launcher_executable(self.launcher_bin)
        if not launcher_path.exists():
            raise BuildError(f"Launcher binary not found: {launcher_path}")
        if not os.access(launcher_path, os.X_OK):
            raise BuildError(f"Launcher binary not executable: {launcher_path}")

        # Check for platform mismatch
        if self.platform not in launcher_path.name and "any" not in launcher_path.name:
            logger.warning(
                "Launcher platform mismatch",
                expected=self.platform,
                found=launcher_path.name,
            )
        logger.info(f"✅ Launcher found and executable: {launcher_path}")

        # Store for later use
        self._launcher_path = launcher_path

        if self.builder_bin or os.environ.get("FLAVOR_BUILDER_BIN"):
            logger.info("🔨🌍🚀 Using external builder binary")
            logger.debug(
                "🔨📍📋 Builder path",
                builder=self.builder_bin or os.environ.get("FLAVOR_BUILDER_BIN"),
            )
            self._build_with_external_builder()
        else:
            logger.info("🐍🏗️🚀 Using internal Python builder (default)")
            self._build_with_python_builder()

    @log_only_error_context(
        context_provider=lambda: {"operation": "build_with_python_builder"},
        log_level="debug",
    )
    def _build_with_python_builder(self) -> None:
        """Build package using the internal Python PSPF builder."""
        logger.info("🐍🔨🚀 Building package with internal Python builder")
        logger.debug(
            "🐍🔍📋 Python builder configuration",
            python_version=self.python_version,
            manifest_dir=str(self.manifest_dir),
            entry_point=self.entry_point,
        )
        from flavor.psp.format_2025.pspf_builder import PSPFBuilder

        python_packager = PythonPackager(
            manifest_dir=self.manifest_dir,
            package_name=self.package_name,
            entry_point=self.entry_point,
            build_config=self.build_config,
            python_version=self.python_version,
        )

        with temp_dir(prefix="flavor_build_") as build_temp_dir:
            logger.info("Preparing Python artifacts...")
            artifacts = python_packager.prepare_artifacts(build_temp_dir)

            logger.info("Creating slot tarballs...")
            uv_tarball, python_tarball, wheels_tarball = create_python_slot_tarballs(build_temp_dir, artifacts)

            launcher_path = self._launcher_path
            launcher_type = self._detect_launcher_type(launcher_path)
            logger.info(f"Detected launcher type: {launcher_type}")

            is_windows()
            metadata = create_python_builder_metadata(self.package_name, self.version, self.build_config)
            metadata = validate_metadata_dict(metadata)

            builder = (
                PSPFBuilder.create()
                .metadata(**metadata)
                .add_slot(
                    id="uv",
                    data=uv_tarball,
                    operations="gzip",
                    purpose="tool",
                    lifecycle="runtime",
                    target="bin/uv",
                    permissions="0700",
                )
                .add_slot(
                    id="python",
                    data=python_tarball,
                    operations="tgz",
                    purpose="runtime",
                    lifecycle="runtime",
                    target="{workenv}",
                )
                .add_slot(
                    id="wheels",
                    data=wheels_tarball,
                    operations="tgz",
                    purpose="payload",
                    lifecycle="cache",
                    target="wheels",
                )
                .with_options(
                    launcher_bin=launcher_path,
                    strip_binaries=self.strip_binaries,
                    enable_mmap=True,
                    page_aligned=True,
                )
            )

            if self.key_seed:
                builder = builder.with_keys(seed=self.key_seed)
            elif self.package_integrity_key_path and self.public_key_path:
                from flavor.packaging.keys import (
                    load_private_key_raw,
                    load_public_key_raw,
                )

                private_key = load_private_key_raw(Path(self.package_integrity_key_path))
                public_key = load_public_key_raw(Path(self.public_key_path))
                builder = builder.with_keys(private=private_key, public=public_key)

            result = builder.build(Path(self.output_flavor_path))

            if not result.success:
                raise BuildError(f"Package build failed: {'; '.join(result.errors)}")

            # Always show completion message, detailed info only with progress flag
            final_size = Path(self.output_flavor_path).stat().st_size / (1024 * 1024)
            logger.info(f"✅ Package built successfully: {final_size:.1f} MB")
            if self.show_progress and result.metadata and "duration_seconds" in result.metadata:
                logger.info(f"⏱️  Build time: {result.metadata['duration_seconds']:.2f}s")

    @log_only_error_context(
        context_provider=lambda: {"operation": "build_with_external_builder"},
        log_level="debug",
    )
    def _build_with_external_builder(self) -> None:
        """Build package using an external builder binary (Go/Rust)."""
        logger.info("Building package with external builder...")
        from flavor.packaging.orchestrator_ingredients import create_slot_tarballs

        # If we have a JSON manifest, we can use it directly with external builders
        if self.manifest_type == "json":
            self._build_with_json_manifest()
            return

        python_packager = PythonPackager(
            manifest_dir=self.manifest_dir,
            package_name=self.package_name,
            entry_point=self.entry_point,
            build_config=self.build_config,
            python_version=self.python_version,
        )

        with temp_dir(prefix="flavor_build_") as build_temp_dir:
            logger.info("Preparing Python artifacts...")
            artifacts = python_packager.prepare_artifacts(build_temp_dir)

            logger.info("Creating slot tarballs...")
            slots = create_slot_tarballs(build_temp_dir, artifacts)

            key_paths = {
                "private": self.package_integrity_key_path,
                "public": self.public_key_path,
            }
            manifest = create_builder_manifest(
                self.package_name, self.version, self.build_config, slots, key_paths
            )

            manifest_path = write_manifest_file(manifest, build_temp_dir)
            packager_executable = find_builder_executable(self.builder_bin)
            launcher_executable = self._launcher_path

            detected_launcher_type = self._detect_launcher_type(launcher_executable)
            logger.info(f"Detected launcher type: {detected_launcher_type}")

            build_cmd_args = [
                str(packager_executable),
                "--manifest",
                str(manifest_path),
                "--output",
                self.output_flavor_path,
                "--launcher-bin",
                str(launcher_executable),
            ]

            if self.key_seed:
                build_cmd_args.extend(["--key-seed", self.key_seed])
            elif self.package_integrity_key_path:
                build_cmd_args.extend(["--private-key", self.package_integrity_key_path])
                if self.public_key_path:
                    build_cmd_args.extend(["--public-key", self.public_key_path])

            logger.info("Building flavor pack...")
            run(build_cmd_args, check=True, capture_output=True)

            # Always show completion message
            final_size = Path(self.output_flavor_path).stat().st_size / (1024 * 1024)
            logger.info(f"✅ Package built successfully: {final_size:.1f} MB")

    def _build_with_json_manifest(self) -> None:
        """Build package using a JSON manifest directly with external builders."""
        logger.info("Building package with JSON manifest and external builder...")

        # Write the manifest to a temporary file
        with temp_dir(prefix="flavor_json_build_") as build_temp_dir:
            # Transform nested JSON manifest to flat structure expected by external builders
            flat_manifest = {
                "name": self.build_config.get("package", {}).get("name", self.package_name),
                "version": self.build_config.get("package", {}).get("version", self.version),
                "command": self.build_config.get("execution", {}).get("command", self.entry_point),
                "slots": self.build_config.get("slots", []),  # Default to empty slots array
            }

            # Add optional fields if present
            if "environment" in self.build_config.get("execution", {}):
                flat_manifest["env"] = self.build_config["execution"]["environment"]

            # Write manifest directly to file
            manifest_path = build_temp_dir / "manifest.json"
            write_json(manifest_path, flat_manifest, indent=2)
            logger.info(f"Using JSON manifest at: {manifest_path}")

            # Find executables
            packager_executable = find_builder_executable(self.builder_bin)
            launcher_executable = self._launcher_path

            detected_launcher_type = self._detect_launcher_type(launcher_executable)
            logger.info(f"Detected launcher type: {detected_launcher_type}")

            # Build command
            build_cmd_args = [
                str(packager_executable),
                "--manifest",
                str(manifest_path),
                "--output",
                self.output_flavor_path,
                "--launcher-bin",
                str(launcher_executable),
            ]

            if self.key_seed:
                build_cmd_args.extend(["--key-seed", self.key_seed])
            elif self.package_integrity_key_path:
                build_cmd_args.extend(["--private-key", self.package_integrity_key_path])
                if self.public_key_path:
                    build_cmd_args.extend(["--public-key", self.public_key_path])

            logger.info("Building package...")
            run(build_cmd_args, check=True, capture_output=True)

            # Always show completion message
            final_size = Path(self.output_flavor_path).stat().st_size / (1024 * 1024)
            logger.info(f"✅ Package built successfully: {final_size:.1f} MB")
