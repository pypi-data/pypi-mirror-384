#
# This script installs IOCBio gel program to python virtual environment iocbio-gel
#

[CmdletBinding(PositionalBinding=$false)]
param(
    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [Alias('d')]
    [string]$SourceDir,

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [Alias('e')]
    [string]$EnvDir = "iocbio-gel",

    [Alias('h','?')]
    [switch]$Help
)

# Function to show usage and exit
function Show-Usage {
    param([string]$ErrorMessage)

    if ($ErrorMessage) {
        Write-Error $ErrorMessage
        Write-Output ""
    }

    Write-Output "Usage: .\install.ps1 [-SourceDir <path>] [-EnvDir <path>] [-Help]"
    Write-Output "  -SourceDir <path>  Install from checked out source code directory"
    Write-Output "                     (alias: -d)"
    Write-Output "  -EnvDir <path>     Directory for virtual environment (default: iocbio-gel)"
    Write-Output "                     (alias: -e)"
    Write-Output "  -Help              Show this help"
    exit 1
}

# Check for unknown parameters
if ($args.Count -gt 0) {
    Show-Usage "Unknown or invalid parameter(s): $args"
}

# Validate SourceDir if provided
if ($SourceDir -and -not (Test-Path $SourceDir -PathType Container)) {
    Show-Usage "SourceDir must be a valid directory path: $SourceDir"
}

if ($Help) {
    Write-Output "Usage: .\install.ps1 [-SourceDir <path>] [-EnvDir <path>] [-Help]"
    Write-Output "  -SourceDir <path>  Install from checked out source code directory"
    Write-Output "                     (alias: -d)"
    Write-Output "  -EnvDir <path>     Directory for virtual environment (default: iocbio-gel)"
    Write-Output "                     (alias: -e)"
    Write-Output "  -Help              Show this help"
    exit 0
}
# Allow overriding Python executable
$PYTHON = if ($env:PYTHON) { $env:PYTHON } else { "python.exe" }

# URLs
$ZEROC_ICE_WHEELS_URL = "https://gitlab.com/iocbio/gel/-/raw/main/packaging/zeroc-ice/zeroc-ice-wheels.json"
$REQUIREMENTS_URL = "https://gitlab.com/iocbio/gel/-/raw/main/requirements.txt"

# Set file paths based on source directory
if ($SourceDir) {
    $ZEROC_ICE_WHEELS_FILE = "$SourceDir\packaging\zeroc-ice\zeroc-ice-wheels.json"
    $REQUIREMENTS_FILE = "$SourceDir\requirements.txt"
} else {
    # Create temporary files
    $ZEROC_ICE_WHEELS_FILE = [System.IO.Path]::GetTempFileName()
    $REQUIREMENTS_FILE = [System.IO.Path]::GetTempFileName()
}

try {
    # Function to download URL to file
    function Download-File {
        param([string]$Url, [string]$Output)
        Write-Output "Downloading $Url to $Output"
        try {
            Invoke-WebRequest -Uri $Url -OutFile $Output -ErrorAction Stop
        } catch {
            Write-Error "Failed to download $Url"
            exit 1
        }
    }

    # Create virtual environment
    & $PYTHON -m venv $EnvDir
    Write-Output "Python virtual environment for $EnvDir created"
    Write-Output ""

    # Download files if not using source directory
    if (-not $SourceDir) {
        Download-File -Url $ZEROC_ICE_WHEELS_URL -Output $ZEROC_ICE_WHEELS_FILE
        Download-File -Url $REQUIREMENTS_URL -Output $REQUIREMENTS_FILE
    }

    # Determine platform (Windows x86_64)
    $PLATFORM = "win_x86_64"

    # Get Python version
    $PYTHON_VERSION = & $PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"

    # Extract ZeroC Ice URL
    $ZEROC_ICE_URL = & $PYTHON -c @"
import json
with open(r'$ZEROC_ICE_WHEELS_FILE', 'r') as f:
    config = json.load(f)
try:
    print(config['wheels']['$PLATFORM']['$PYTHON_VERSION'])
except KeyError:
    print('No ZeroC Ice wheel found for $PLATFORM $PYTHON_VERSION', file=__import__('sys').stderr)
    exit(1)
"@

    # Install ZeroC Ice
    & .\$EnvDir\Scripts\pip.exe install $ZEROC_ICE_URL

    # Install requirements
    & .\$EnvDir\Scripts\pip.exe install -r $REQUIREMENTS_FILE

    # Install iocbio.gel
    if ($SourceDir) {
        & .\$EnvDir\Scripts\pip.exe install $SourceDir
    } else {
        & .\$EnvDir\Scripts\pip.exe install iocbio.gel
    }

    Write-Output ""
    Write-Output "IOCBio-gel installed"
    Write-Output ""
    Write-Output "To run the program use following commands"
    Write-Output ".\$EnvDir\Scripts\Activate.ps1"
    Write-Output "iocbio-gel.exe"

} finally {
    # Clean up temporary files if not using source directory
    if (-not $SourceDir) {
        if (Test-Path $ZEROC_ICE_WHEELS_FILE) { Remove-Item $ZEROC_ICE_WHEELS_FILE }
        if (Test-Path $REQUIREMENTS_FILE) { Remove-Item $REQUIREMENTS_FILE }
    }
}
