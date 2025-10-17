# Installation and Update

This document provides installation instructions for IOCBIO Gel software across different platforms. The easiest way to install is using the binary installation or automated installation scripts.

## Installation Overview

There are three main installation approaches:

1. **Binary Installation (Windows only, Recommended)** - Pre-packaged executable with all dependencies included
2. **Automated Installation Scripts** - One-command installation with automatic dependency handling
3. **Manual Python/pip Installation** - Install from source or PyPI (for advanced users)

## Releases

All releases are available at [Releases](https://gitlab.com/iocbio/gel/-/releases). Releases are distributed as:
- Pre-packaged executables (Windows)
- Python packages through PyPI (all platforms)

---

## Quick Installation (Recommended)

### Windows

**Option 1: Binary Installation (Recommended)**

This is the simplest installation method for Windows users as it includes all dependencies.

1. Go to [Releases](https://gitlab.com/iocbio/gel/-/releases)
2. Download the Windows executable (ZIP file)
3. Extract the ZIP to any location on your PC
4. Run `gel.bat` from the extracted folder

**Option 2: Automated Script Installation**

**Important:** Navigate to the directory where you want to create the virtual environment before running the script. The script will create a virtual environment folder (default: `iocbio-gel`) in your current directory. You can specify a custom directory using the `-EnvDir` parameter.

Open PowerShell as Administrator and run:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://gitlab.com/iocbio/gel/-/raw/main/install.ps1'))
```

Or download and run the script manually:
```powershell
# Download the script
Invoke-WebRequest -Uri "https://gitlab.com/iocbio/gel/-/raw/main/install.ps1" -OutFile "install.ps1"

# Run the script (use -EnvDir to specify custom virtual environment directory)
.\install.ps1
```

**What the script does:**

- Creates a Python virtual environment (default name: `iocbio-gel`)
- Automatically detects your Python version and platform
- Downloads and installs the correct ZeroC Ice wheel for your system
- Installs all required dependencies
- Installs the IOCBio Gel application

**To start the application:**
```powershell
.\iocbio-gel\Scripts\Activate.ps1
iocbio-gel.exe
```

or navigate to `.\iocbio-gel\Scripts` and double click on `iocbio-gel` (or use environment directory name if you specified non-default one).


### Linux/macOS

**Automated Script Installation**

**Important:** Navigate to the directory where you want to create the virtual environment before running the script. The script will create a virtual environment folder (default: `iocbio-gel`) in your current directory. You can specify a custom directory using the `-e` option.

```bash
curl https://gitlab.com/iocbio/gel/-/raw/main/install.sh | bash
```

or

```bash
wget -qO - https://gitlab.com/iocbio/gel/-/raw/main/install.sh | bash
```

Or download and run the script manually:
```bash
# Download the script
curl -O https://gitlab.com/iocbio/gel/-/raw/main/install.sh
# or
wget https://gitlab.com/iocbio/gel/-/raw/main/install.sh

# Make it executable and run (use -e to specify custom virtual environment directory)
chmod +x install.sh
./install.sh
```

**What the script does:**

- Creates a Python virtual environment (default name: `iocbio-gel`)
- Automatically detects your platform (Linux x86_64/aarch64, macOS universal2)
- Automatically detects your Python version
- Downloads and installs the correct ZeroC Ice wheel for your system
- Installs all required dependencies
- Installs the IOCBio Gel application

**To start the application:**
```bash
iocbio-gel/bin/iocbio-gel
```

---

## Advanced Installation Options

### Installing from Source Directory

If you have the source code checked out, you can install from the local directory.

**Important:** Navigate to a directory **outside** the source tree before running these commands. It is better to create the virtual environment outside the source code directory.

**Windows:**
```powershell
# Navigate to where you want the virtual environment
cd C:\desired\installation\path
# Run script pointing to source directory (use -EnvDir to specify custom virtual environment directory)
C:\path\to\gel\source\install.ps1 -SourceDir "C:\path\to\gel\source" [-EnvDir "custom-env-name"]
```

**Linux/macOS:**
```bash
# Navigate to where you want the virtual environment
cd /desired/installation/path
# Run script pointing to source directory (use -e to specify custom virtual environment directory)
/path/to/gel/source/install.sh -d /path/to/gel/source [-e custom-env-name]
```

### Prerequisites for Script Installation

**All Platforms:**

- Python 3.10-3.12 (recommended versions for best compatibility)
- Internet connection for downloading dependencies

**Python Version Notes:**

- The scripts automatically detect your Python version
- Supported versions: 3.8, 3.9, 3.10, 3.11, 3.12
- **Recommended:** Python 3.10-3.12 for optimal compatibility with all dependencies
- You can specify a specific Python executable using the `PYTHON` environment variable:
  ```bash
  # Linux/macOS
  PYTHON=python3.11 ./install.sh
  
  # Windows PowerShell
  $env:PYTHON="python3.11"; .\install.ps1
  ```

- Check available ZeroC Ice wheels for your Python version at the [ZeroC Ice wheels configuration](https://gitlab.com/iocbio/gel/-/raw/main/packaging/zeroc-ice/zeroc-ice-wheels.json)

**Important Virtual Environment Notes:**

- Virtual environments are created with fixed paths and **cannot be moved** after creation
- Choose your installation directory carefully before running the scripts
- The virtual environment folder (default: `iocbio-gel`) will be created in your current working directory
- You can specify a custom directory name using the `-e` (Linux/macOS) or `-EnvDir` (Windows) option

**Windows Additional Requirements:**

- Microsoft Visual C++ Redistributable for Visual Studio 2015, 2017, and 2019 ([download here](https://docs.microsoft.com/en-US/cpp/windows/latest-supported-vc-redist?view=msvc-160))
- PowerShell execution policy set to allow script execution

**Linux/macOS Additional Requirements:**

- `curl` or `wget` for downloading
- Standard development tools (usually pre-installed)

### Manual Python/pip Installation

If you prefer manual installation or the automated scripts don't work for your setup:

1. **Ensure pip is up to date:**
   ```bash
   python3 -m pip install --user --upgrade pip
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv iocbio-gel
   ```

3. **Install ZeroC Ice (see troubleshooting section for wheel URLs)**

4. **Install IOCBIO Gel:**
   ```bash
   # Activate virtual environment first
   # Linux/macOS:
   source iocbio-gel/bin/activate
   # Windows:
   # .\iocbio-gel\Scripts\Activate.ps1

   pip install -r https://gitlab.com/iocbio/gel/-/raw/main/requirements.txt
   pip install iocbio.gel
   ```

### Development Installation

For developers working with the source code:

```bash
# Create virtual environment and install ZeroC Ice first
python -m venv iocbio-gel
source iocbio-gel/bin/activate  # Linux/macOS
# .\iocbio-gel\Scripts\Activate.ps1  # Windows

# Install in development mode
pip install -e .
```

---

## Troubleshooting

### Script Installation Fails

If the automated installation scripts fail:

1. **Check Prerequisites:** Ensure Python 3.10-3.12 is installed and accessible
2. **Clean Up Failed Installation:** If the installation script failed and you want to retry with a different Python version using the `PYTHON` environment variable, delete the previously created virtual environment folder first. The script may continue using the old Python version from the existing environment. Remove the environment directory (default: iocbio-gel or your custom name) and run the installation again with your preferred Python version specified. Example: PYTHON=python3.12 ./install.sh (Linux/macOS) or $env:PYTHON="python3.12.exe"; .\install.ps1 (Windows).
3. **Check Internet Connection:** Scripts need to download dependencies
4. **Check Permissions:** 
   - Windows: Run PowerShell as Administrator
   - Linux/macOS: Ensure you have write permissions in the current directory
5. **Try Manual Installation:** Use the manual pip installation method described above

### ZeroC Ice Installation Issues

**Problem:** The automated script fails with ZeroC Ice-related errors.

**Background:** OMERO Python library requires ZeroC ICE version 3.6.5, which has compatibility issues with Python 3.11+ from the standard PyPI distribution. The scripts automatically handle this by using pre-built wheels from Glencoe Software.

**Manual ZeroC Ice Installation:**

If you need to install ZeroC Ice manually, visit [Glencoe Software ZeroC Ice page](https://www.glencoesoftware.com/blog/2023/12/08/ice-binaries-for-omero.html) to find the appropriate wheel for your platform and Python version.

**Examples:**

*Windows Python 3.12:*
```powershell
.\iocbio-gel\Scripts\pip install https://github.com/glencoesoftware/zeroc-ice-py-win-x86_64/releases/download/20240325/zeroc_ice-3.6.5-cp312-cp312-win_amd64.whl
```

*Linux Python 3.12 x86_64:*
```bash
iocbio-gel/bin/pip install https://github.com/glencoesoftware/zeroc-ice-py-linux-x86_64/releases/download/20240202/zeroc_ice-3.6.5-cp312-cp312-manylinux_2_28_x86_64.whl
```

*macOS Python 3.12 (universal2):*
```bash
iocbio-gel/bin/pip install https://github.com/glencoesoftware/zeroc-ice-py-macos-universal2/releases/download/20240131/zeroc_ice-3.6.5-cp312-cp312-macosx_11_0_universal2.whl
```

**Finding the Right ZeroC Ice Wheel:**

1. **Check supported versions:** Visit the [ZeroC Ice wheels configuration](https://gitlab.com/iocbio/gel/-/raw/main/packaging/zeroc-ice/zeroc-ice-wheels.json) to see supported Python versions and platforms
2. **Get wheel URLs:** Visit https://www.glencoesoftware.com/blog/2023/12/08/ice-binaries-for-omero.html
3. Find your operating system and Python version in the table
4. Click the link to go to the GitHub releases page
5. Copy the URL of the appropriate `.whl` file
6. Install using the virtual environment pip (e.g., `iocbio-gel/bin/pip install [wheel_URL]`)

**Supported Platforms and Python Versions:**

- **Windows:** x86_64 architecture, Python 3.8-3.12
- **Linux:** x86_64 and aarch64 architectures, Python 3.8-3.12
- **macOS:** Universal2 (Intel and Apple Silicon), Python 3.10-3.12

### PowerShell Execution Policy Issues (Windows)

If you get execution policy errors, run PowerShell as Administrator and set the policy:

```powershell
Set-ExecutionPolicy AllSigned
```
or for temporary bypass:
```powershell
Set-ExecutionPolicy Bypass -Scope Process
```

### Command Not Found After Installation

If `iocbio-gel` command is not found after installation:

**When using automated scripts:** Always use the full path as shown in the installation output:

- Windows: `.\[env-dir]\Scripts\Activate.ps1` then `iocbio-gel.exe` (replace `[env-dir]` with your virtual environment directory)
- Linux/macOS: `[env-dir]/bin/iocbio-gel` (replace `[env-dir]` with your virtual environment directory)

**For manual pip installations:**

- Linux/macOS: Ensure `~/.local/bin` is in your PATH
- Windows: Check that Python Scripts directory is in your PATH

### Platform-Specific Issues

- **Windows**: Ensure Visual C++ Redistributable is installed
- **macOS**: Use the universal2 wheels for better compatibility across Apple Silicon and Intel Macs
- **Linux**: The scripts support x86_64 and aarch64 architectures
- **Unsupported platforms**: For other architectures, try manual installation with platform-appropriate wheels

### Getting Help

For additional support:

1. Check the [project repository issues](https://gitlab.com/iocbio/gel/-/issues)
2. Ensure you're using a supported Python version (3.10-3.12 recommended)
3. Try the manual installation method if automated scripts fail
4. Contact the project maintainers with detailed error messages

---

## Summary

**Recommended Installation Path:**

1. **Use binary installation** (Windows only) if scripts fail
2. **Try automated scripts first** - They handle all dependencies automatically
3. **Manual installation** as last resort for troubleshooting

**Key Points:**

- Automated scripts create isolated virtual environments (customizable directory name)
- ZeroC Ice compatibility is handled automatically
- Virtual environments prevent package conflicts
- Manual installation may be needed for unsupported configurations

The automated installation scripts are designed to work out-of-the-box for most users and handle the complex ZeroC Ice dependency automatically.
