# Changelog

All notable changes to versionIO will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-15

### Added
- Initial release
- Drop-in replacement for `open()` function
- Automatic file versioning with timestamps
- `VersionedFile` high-level interface
- Configurable retention policies (max_versions)
- Cross-platform file locking
- Full test suite with pytest
- Examples and documentation

### Features
- Automatic backup creation before write operations
- Version listing and restoration
- Support for text and binary files
- Context manager support
- Configurable versioning policies

### Known Limitations
- Compression not yet implemented
- Diff-based storage not yet implemented
- CLI not yet available
```

### src/versionio/py.typed
```
# Marker file for PEP 561
# This package supports type hints