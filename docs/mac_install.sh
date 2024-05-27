#!/bin/bash

# Function to set SQLCipher paths
set_sqlcipher_paths() {
    SQLCIPHER_PATH=$(brew --prefix sqlcipher)
    export C_INCLUDE_PATH="$SQLCIPHER_PATH/include"
    export LIBRARY_PATH="$SQLCIPHER_PATH/lib"
    export PKG_CONFIG_PATH="$SQLCIPHER_PATH/lib/pkgconfig"
    echo "SQLCipher path: $SQLCIPHER_PATH"
    echo "C_INCLUDE_PATH: $C_INCLUDE_PATH"
    echo "LIBRARY_PATH: $LIBRARY_PATH"
    echo "PKG_CONFIG_PATH: $PKG_CONFIG_PATH"
}

# Function to create necessary symlinks for SQLCipher headers and libraries
create_symlinks() {
    SQLCIPHER_PATH=$(brew --prefix sqlcipher)
    if [[ "$(uname -m)" == "arm64" ]]; then
        echo "Creating symlinks for M1 Mac..."
         mkdir -p /usr/local/lib
         mkdir -p /usr/local/include
         ln -sf "$SQLCIPHER_PATH/lib/libsqlcipher.a" /usr/local/lib/libsqlcipher.a
         ln -sf "$SQLCIPHER_PATH/include/sqlcipher" /usr/local/include/sqlcipher
    fi
    if [ ! -d /usr/local/include/sqlcipher ]; then
        echo "Creating necessary symlinks for SQLCipher headers..."
         mkdir -p /usr/local/include
         ln -sf "$SQLCIPHER_PATH/include/sqlcipher" /usr/local/include/sqlcipher
    fi
}

# Function to build and install sqlcipher3 using pypa/build and pip
install_sqlcipher3() {
    if [ -d "sqlcipher3" ]; then
        echo "sqlcipher3 directory already exists. Pulling the latest changes..."
        git -C sqlcipher3 pull
    else
        echo "Cloning sqlcipher3 repository..."
        git clone https://github.com/coleifer/sqlcipher3.git
    fi

    cd sqlcipher3 || { echo "sqlcipher3 directory not found"; exit 1; }

    # Set environment paths
    set_sqlcipher_paths

    # Build and install the package
    python -m pip install build
    python -m build
    python -m pip install .

    cd ..
}

# Function to install pyrekordbox
install_pyrekordbox() {
    pip install pyrekordbox
    python -m pyrekordbox download-key
}

# Check for brew installation
if ! command -v brew &> /dev/null
then
    echo "Homebrew could not be found. Please install Homebrew first."
    exit 1
fi

# Check if SQLCipher is installed
if ! brew list sqlcipher &> /dev/null
then
    echo "SQLCipher is not installed. Installing SQLCipher..."
    brew install sqlcipher
fi

# Set SQLCipher paths
set_sqlcipher_paths

# Create necessary symlinks
create_symlinks

# Install sqlcipher3
install_sqlcipher3

# Install pyrekordbox
install_pyrekordbox

echo "pyrekordbox installation complete."
