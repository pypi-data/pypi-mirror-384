#!/bin/bash

# deploy-cli.sh - Wrapper script to run deploy-cli with proper library paths
# This script ensures the binary can find its required shared libraries

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set library path to include the bin/ directory
export LD_LIBRARY_PATH="${SCRIPT_DIR}/bin:${LD_LIBRARY_PATH}"

# Skip auto-extraction since we're providing libraries manually
export _DEPLOY_CLI_REEXEC=1

# Run the deploy-cli binary with all provided arguments
exec "${SCRIPT_DIR}/deploy-cli" "$@"
