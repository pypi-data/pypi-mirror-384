#!/usr/bin/env bash

#
# This script installs IOCBio gel program to python virtual environment iocbio-gel
#

set -e

# Parse command line options
SOURCE_DIR=""
ENV_DIR="iocbio-gel"
while getopts "d:e:h" opt; do
  case $opt in
    d) SOURCE_DIR="$OPTARG" ;;
    e) ENV_DIR="$OPTARG" ;;
    h) echo "Usage: $0 [-d source_dir] [-e env_dir] [-h]"
        echo "  -d source_dir  Install from checked out source code directory"
        echo "  -e env_dir     Directory for virtual environment (default: iocbio-gel)"
        echo "  -h             Show this help"
        exit 0 ;;
    *) echo "Invalid option: -$OPTARG" >&2
       echo "Use -h for help" >&2
       exit 1 ;;
  esac
done

# Allow overriding Python executable
PYTHON=${PYTHON:-python3}

# URLs
ZEROC_ICE_WHEELS_URL="https://gitlab.com/iocbio/gel/-/raw/main/packaging/zeroc-ice/zeroc-ice-wheels.json"
REQUIREMENTS_URL="https://gitlab.com/iocbio/gel/-/raw/main/requirements.txt"

# Set file paths based on source directory
if [ -n "$SOURCE_DIR" ]; then
  ZEROC_ICE_WHEELS_FILE="$SOURCE_DIR/packaging/zeroc-ice/zeroc-ice-wheels.json"
  REQUIREMENTS_FILE="$SOURCE_DIR/requirements.txt"
else
  # Create temporary files
  ZEROC_ICE_WHEELS_FILE=$(mktemp)
  REQUIREMENTS_FILE=$(mktemp)

  # Clean up temporary files on exit
  trap 'rm -f "$ZEROC_ICE_WHEELS_FILE" "$REQUIREMENTS_FILE"' EXIT
fi

# Function to download URL to file, supports curl or wget, exits on error
download() {
  url=$1
  output=$2
  echo "Downloading $url"
  if command -v wget &> /dev/null; then
    wget -q -O "$output" "$url" || { echo "Failed to download $url" >&2; exit 1; }
  else
    curl -s -o "$output" "$url" || { echo "Failed to download $url" >&2; exit 1; }
  fi
}

# Create virtual environment
$PYTHON -m venv "$ENV_DIR"

# Activate virtual environment
source "$ENV_DIR/bin/activate"

# Download files if not using source directory
if [ -z "$SOURCE_DIR" ]; then
  # Download zeroc-ice-wheels.json
  download "$ZEROC_ICE_WHEELS_URL" "$ZEROC_ICE_WHEELS_FILE"

  # Download requirements.txt
  download "$REQUIREMENTS_URL" "$REQUIREMENTS_FILE"
fi

# Determine platform
OS=$(uname -s)
ARCH=$(uname -m)
if [[ "$OS" == "Linux" ]]; then
  if [[ "$ARCH" == "x86_64" ]]; then
    PLATFORM="linux_x86_64"
  elif [[ "$ARCH" == "aarch64" ]]; then
    PLATFORM="linux_aarch64"
  else
    echo "Unsupported architecture: $ARCH"
    exit 1
  fi
elif [[ "$OS" == "Darwin" ]]; then
  PLATFORM="darwin_universal2"
else
  echo "Unsupported OS: $OS"
  exit 1
fi

# Get Python version
PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

# Extract ZeroC Ice URL
ZEROC_ICE_URL=$(python -c "
import json
with open('$ZEROC_ICE_WHEELS_FILE') as f:
    config = json.load(f)
try:
    print(config['wheels']['$PLATFORM']['$PYTHON_VERSION'])
except KeyError:
    print('No ZeroC Ice wheel found for $PLATFORM $PYTHON_VERSION', file=__import__('sys').stderr)
    exit(1)
")

# Install ZeroC Ice
pip install "$ZEROC_ICE_URL"

# Install requirements
pip install -r "$REQUIREMENTS_FILE"

# Install iocbio.gel
if [ -n "$SOURCE_DIR" ]; then
  pip install "$SOURCE_DIR"
else
  pip install iocbio.gel
fi

echo "Start the program by running $ENV_DIR/bin/iocbio-gel"
