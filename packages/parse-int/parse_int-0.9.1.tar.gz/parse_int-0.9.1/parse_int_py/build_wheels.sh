#!/usr/bin/bash

# got to this scripts directory
# go to this script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR"

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
# The last 5 major CPython versions as of late 2025.
# Adjust this list if needed.
PYTHON_VERSIONS=("3.13" "3.12" "3.11" "3.10" "3.9")

# Your PyPI username and token/password.
# It's highly recommended to use an API token instead of your password.
# You can set these as environment variables for better security:
# export MATURIN_USERNAME="__token__"
# export MATURIN_PASSWORD="pypi-api-token-goes-here"
# If not set, maturin will prompt you.

# --- Step 1: Install uv if not present ---
echo "⚙️  Checking for uv..."
if ! command -v uv &> /dev/null
then
    echo "uv could not be found. Installing uv..."
    # You can choose your preferred installation method.
    # Using pipx is recommended for isolating tools.
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="/root/.local/bin:${PATH}"
else
    echo "✅ uv is already installed."
fi

rustc --version

echo "--------------------------------------------------"

# --- Step 2: Clean previous builds ---
echo "🧹 Cleaning previous builds..."
# Create a temporary virtual environment to run maturin clean.
cargo clean
# uv venv .venv_temp -p python3
# source .venv_temp/bin/activate
# uv pip install maturin
# #maturin clean
# deactivate
# rm -rf .venv_temp
echo "✅ Cleaned build artifacts."
echo "--------------------------------------------------"

# --- Step 3: Build for each Python version ---
echo "🏗️  Starting the build process for multiple Python versions..."
for version in "${PYTHON_VERSIONS[@]}"
do
    echo "--- Building for Python $version ---"
    VENV_NAME=".venv_py${version//.}" # e.g., .venv_py311
    
    echo "Creating virtual environment: $VENV_NAME with python$version"
    # Create a virtual environment with a specific Python version
    uv venv "$VENV_NAME" -p "python$version"
    
    echo "Activating environment and installing maturin..."
    # Activate the environment
    source "$VENV_NAME/bin/activate"
    
    # Install maturin in the new environment
    uv pip install maturin
    
    echo "Building wheel for python$version..."
    # Build the wheel for the current interpreter
    maturin build --release
    
    # Deactivate the environment
    deactivate
    echo "✅ Successfully built wheel for Python $version."
done
echo "--------------------------------------------------"

# --- Step 4: Publish to PyPI ---
echo "🚀 Publishing wheels to PyPI..."

# Create one final virtual environment just for the publish step
uv venv .venv_publish -p python3
source .venv_publish/bin/activate
uv pip install maturin

# The 'maturin publish' command finds all compatible wheels in the
# target/wheels/ directory and uploads them in a single batch.
# Ensure MATURIN_USERNAME and MATURIN_PASSWORD are set as environment variables.
maturin publish

deactivate
rm -rf .venv_publish

echo "🎉 All done! Your package has been published to PyPI."
