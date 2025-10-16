"""
PSPF/2025 Format Constants

All constants defined here match the authoritative specification.
These are the canonical values for the PSPF/2025 v0 format.
"""

# =================================
# Format Version and Magic
# =================================
from __future__ import annotations

PSPF_VERSION = 0x20250001  # PSPF/2025 v1 format identifier
FORMAT_VERSION_STRING = "2025.0.0"  # String version for JSON metadata

# Magic bytes for package trailer
TRAILER_START_MAGIC = bytes([0xF0, 0x9F, 0x93, 0xA6])  # 📦 emoji
TRAILER_END_MAGIC = bytes([0xF0, 0x9F, 0xAA, 0x84])  # 🪄 emoji

# =================================
# Binary Structure Sizes
# =================================
INDEX_BLOCK_SIZE = 8192  # Exactly 8192 bytes (8KB)
SLOT_DESCRIPTOR_SIZE = 64  # Exactly 64 bytes per slot
MAGIC_TRAILER_SIZE = 8200  # Start magic + index + end magic

# =================================
# Operation Definitions (v0 Required)
# =================================

# Core operations that MUST be supported in v0
OP_NONE = 0x00  # No operation

# Bundle operations (0x01-0x0F)
OP_TAR = 0x01  # POSIX TAR archive (REQUIRED)

# Compression operations (0x10-0x2F)
OP_GZIP = 0x10  # GZIP compression (REQUIRED)
OP_BZIP2 = 0x13  # BZIP2 compression (REQUIRED)
OP_XZ = 0x16  # XZ/LZMA2 compression (REQUIRED)
OP_ZSTD = 0x1B  # Zstandard compression (REQUIRED)

# v0 Required Operations Set
V0_REQUIRED_OPERATIONS = {
    OP_NONE,
    OP_TAR,
    OP_GZIP,
    OP_BZIP2,
    OP_XZ,
    OP_ZSTD,
}

# Common operation chains for v0
OPERATION_CHAINS = {
    # Raw data
    "raw": [],
    # Single operations
    "gzip": [OP_GZIP],
    "bzip2": [OP_BZIP2],
    "xz": [OP_XZ],
    "zstd": [OP_ZSTD],
    "tar": [OP_TAR],
    # Common compound operations
    "tar.gz": [OP_TAR, OP_GZIP],
    "tar.bz2": [OP_TAR, OP_BZIP2],
    "tar.xz": [OP_TAR, OP_XZ],
    "tar.zst": [OP_TAR, OP_ZSTD],
    # Alternative names
    "tgz": [OP_TAR, OP_GZIP],
    "tbz2": [OP_TAR, OP_BZIP2],
    "txz": [OP_TAR, OP_XZ],
}

# =================================
# Slot Purpose Types
# =================================
PURPOSE_CODE = 0  # Executable code
PURPOSE_DATA = 1  # Application data
PURPOSE_CONFIG = 2  # Configuration files
PURPOSE_MEDIA = 3  # Media/assets

PURPOSE_NAMES = {
    PURPOSE_CODE: "code",
    PURPOSE_DATA: "data",
    PURPOSE_CONFIG: "config",
    PURPOSE_MEDIA: "media",
}

PURPOSE_FROM_STRING = {
    "code": PURPOSE_CODE,
    "data": PURPOSE_DATA,
    "config": PURPOSE_CONFIG,
    "media": PURPOSE_MEDIA,
}

# =================================
# Slot Lifecycle Types (v0 only)
# =================================
LIFECYCLE_INIT = 0  # First run only, then removed
LIFECYCLE_STARTUP = 1  # Extract at every startup
LIFECYCLE_RUNTIME = 2  # Extract on first use (default)
LIFECYCLE_SHUTDOWN = 3  # Extract during cleanup
LIFECYCLE_CACHE = 4  # Performance cache, can regenerate
LIFECYCLE_TEMPORARY = 5  # Remove after session ends
LIFECYCLE_LAZY = 6  # Load on-demand
LIFECYCLE_EAGER = 7  # Load immediately on startup
LIFECYCLE_DEV = 8  # Development mode only
LIFECYCLE_CONFIG = 9  # User-modifiable config files
LIFECYCLE_PLATFORM = 10  # Platform/OS specific content

LIFECYCLE_NAMES = {
    LIFECYCLE_INIT: "init",
    LIFECYCLE_STARTUP: "startup",
    LIFECYCLE_RUNTIME: "runtime",
    LIFECYCLE_SHUTDOWN: "shutdown",
    LIFECYCLE_CACHE: "cache",
    LIFECYCLE_TEMPORARY: "temporary",
    LIFECYCLE_LAZY: "lazy",
    LIFECYCLE_EAGER: "eager",
    LIFECYCLE_DEV: "dev",
    LIFECYCLE_CONFIG: "config",
    LIFECYCLE_PLATFORM: "platform",
}

LIFECYCLE_FROM_STRING = {
    "init": LIFECYCLE_INIT,
    "startup": LIFECYCLE_STARTUP,
    "runtime": LIFECYCLE_RUNTIME,
    "shutdown": LIFECYCLE_SHUTDOWN,
    "cache": LIFECYCLE_CACHE,
    "temporary": LIFECYCLE_TEMPORARY,
    "lazy": LIFECYCLE_LAZY,
    "eager": LIFECYCLE_EAGER,
    "dev": LIFECYCLE_DEV,
    "config": LIFECYCLE_CONFIG,
    "platform": LIFECYCLE_PLATFORM,
}

# =================================
# Platform Identifiers
# =================================
PLATFORM_ANY = 0
PLATFORM_LINUX = 1
PLATFORM_MACOS = 2
PLATFORM_WINDOWS = 3

PLATFORM_NAMES = {
    PLATFORM_ANY: "any",
    PLATFORM_LINUX: "linux",
    PLATFORM_MACOS: "darwin",
    PLATFORM_WINDOWS: "windows",
}

# =================================
# Default Values
# =================================

DEFAULT_ALIGNMENT = 8  # 8-byte alignment
DEFAULT_PAGE_SIZE = 4096  # 4KB pages (Linux/Windows default)

DEFAULT_MAX_MEMORY = 128 * 1024 * 1024  # 128MB
DEFAULT_MIN_MEMORY = 8 * 1024 * 1024  # 8MB
DEFAULT_CHUNK_SIZE = 64 * 1024  # 64KB

# =================================
# Package Flags
# =================================
FLAG_MEMORY_MAPPED = 1 << 0  # Package supports memory mapping
FLAG_SIGNED = 1 << 1  # Package is digitally signed
FLAG_COMPRESSED = 1 << 2  # Package uses compression
FLAG_ENCRYPTED = 1 << 3  # Package has encrypted slots

# =================================
# Validation Limits
# =================================
MAX_SLOT_COUNT = 65535  # Maximum slots per package
MAX_PACKAGE_SIZE = 2**63 - 1  # Maximum package size (64-bit)
MAX_SLOT_SIZE = 2**32 - 1  # Maximum slot size (32-bit for v0)
MAX_OPERATION_CHAIN_LENGTH = 8  # Maximum operations in chain

# String limits
MAX_PACKAGE_NAME_LENGTH = 255
MAX_SLOT_NAME_LENGTH = 255
MAX_PATH_LENGTH = 4096

# =================================
# Error Codes
# =================================
ERROR_INVALID_MAGIC = 1
ERROR_INVALID_VERSION = 2
ERROR_INVALID_CHECKSUM = 3
ERROR_INVALID_SIGNATURE = 4
ERROR_UNSUPPORTED_OPERATION = 5
ERROR_INVALID_SLOT_ID = 6
ERROR_CORRUPT_DATA = 7

# =================================
# Metadata Schema
# =================================
METADATA_REQUIRED_FIELDS = [
    "format_version",
    "package",
    "slots",
]

SLOT_REQUIRED_FIELDS = [
    "id",
    "name",
    "purpose",
    "lifecycle",
    "operations",
    "size",
    "checksum",
]

# =================================
# Debugging and Development
# =================================
PSPF_FILE_EXTENSION = ".pspf"
PSPF_MIME_TYPE = "application/vnd.pspf"

# Debug constants removed - use FLAVOR_VALIDATION environment variable instead
