# Deploy CLI - Standalone Binary

Version: v1.0.1-jpmc-bec9ef6

## About

This package includes:
- **deploy-cli**: Standalone binary with embedded libraries
- **bin/**: Shared libraries (libTableauCppLibrary.so, libtableauhyperapi.so, hyperd)
- **config/**: Configuration files (embedded.yml)
- **deploy-cli.sh**: Wrapper script for manual library loading

## Quick Start

### Option 1: Automatic (Recommended)

The binary automatically extracts and loads libraries:

```bash
# Just run it directly
./deploy-cli --help

# Run a pipeline
./deploy-cli run <path-to-project> --project-id=XXX --pipeline-name=YYY
```

### Option 2: Manual (If automatic fails)

Use the wrapper script with pre-extracted libraries:

```bash
# Uses bin/ directory for libraries
./deploy-cli.sh --help

# Run a pipeline
./deploy-cli.sh run <path-to-project> --project-id=XXX --pipeline-name=YYY
```

### Option 3: Set LD_LIBRARY_PATH manually

```bash
export LD_LIBRARY_PATH=$(pwd)/bin:$LD_LIBRARY_PATH
export _DEPLOY_CLI_REEXEC=1  # Skip auto-extraction
./deploy-cli --help
```

## Installation

Add to your system PATH:

```bash
sudo cp deploy-cli /usr/local/bin/
deploy-cli --help
```

Or use it directly from the current directory:

```bash
./deploy-cli --help
```

## Build Information

- **Version**: v1.0.1-jpmc-bec9ef6
- **Git Commit**: bec9ef6
- **Build Time**: $(date -u +%Y-%m-%dT%H:%M:%SZ)
- **Go Version**: 1.24.7
- **Platform**: linux-amd64
- **Base OS**: Ubuntu 20.04 LTS (compatible with most Linux distributions)

## Features

- ✅ **Automatic mode**: Embedded libraries extracted at runtime
- ✅ **Manual mode**: Pre-extracted libraries in bin/ directory
- ✅ **Flexible**: Works in restricted environments
- ✅ **Portable**: Compatible across Linux distributions (glibc 2.31+)
- ✅ **No installation**: Run directly or use wrapper script

## Technical Details

### Automatic Mode (Default)
The binary uses Go's embed functionality to include all required shared libraries.
On first run, libraries are extracted to `/tmp/deploy-cli-libs-*` and the binary
re-executes itself with proper LD_LIBRARY_PATH.

### Manual Mode (Fallback)
If automatic extraction fails (e.g., restricted /tmp), use the wrapper script
which loads libraries from the included bin/ directory:
- libTableauCppLibrary.so
- libtableauhyperapi.so
- hyperd

## Troubleshooting

If you see "cannot open shared object file" errors:

1. Try the wrapper script: `./deploy-cli.sh --help`
2. Or set library path manually:
   ```bash
   export LD_LIBRARY_PATH=$(pwd)/bin:$LD_LIBRARY_PATH
   ./deploy-cli --help
   ```
3. Check diagnostics: `ldd ./deploy-cli`
