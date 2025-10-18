#!/usr/bin/env python3
"""
Utility script to update HomebrewFormula/vss-cli.rb with the latest version from PyPI.

This script:
1. Reads the current version from .bumpversion.cfg
2. Fetches package info from PyPI
3. Updates the Homebrew formula with new URL, SHA256, and wheel filename
"""

import configparser
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen


def get_current_version():
    """Read current version from .bumpversion.cfg"""
    config = configparser.ConfigParser()
    config.read('.bumpversion.cfg')
    return config['bumpversion']['current_version']


def fetch_pypi_info(package_name, version):
    """Fetch package information from PyPI"""
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        with urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        if version not in data['releases']:
            raise ValueError(f"Version {version} not found in PyPI releases")
            
        # Find the wheel file
        for file_info in data['releases'][version]:
            if file_info['filename'].endswith('.whl') and 'py2.py3-none-any' in file_info['filename']:
                return {
                    'url': file_info['url'],
                    'sha256': file_info['digests']['sha256'],
                    'filename': file_info['filename']
                }
        
        raise ValueError(f"No suitable wheel file found for version {version}")
        
    except HTTPError as e:
        raise RuntimeError(f"Failed to fetch PyPI data: {e}")


def update_homebrew_formula(pypi_info, version):
    """Update the Homebrew formula with new package information"""
    formula_path = Path('HomebrewFormula/vss-cli.rb')
    
    if not formula_path.exists():
        raise FileNotFoundError(f"Homebrew formula not found at {formula_path}")
    
    content = formula_path.read_text()
    
    # Update URL
    url_pattern = r'url\s+"[^"]*"'
    content = re.sub(url_pattern, f'url "{pypi_info["url"]}"', content)
    
    # Update SHA256
    sha256_pattern = r'sha256\s+"[^"]*"'
    content = re.sub(sha256_pattern, f'sha256 "{pypi_info["sha256"]}"', content)
    
    # The wheel filename is now dynamically extracted from URL, so no need to update it
    
    formula_path.write_text(content)
    print(f"Updated {formula_path} with version {version}")


def main():
    """Main function"""
    try:
        # Get current version from .bumpversion.cfg
        version = get_current_version()
        print(f"Current version: {version}")
        
        # Fetch PyPI information
        print("Fetching PyPI information...")
        pypi_info = fetch_pypi_info('vss-cli', version)
        
        print(f"Found wheel: {pypi_info['filename']}")
        print(f"URL: {pypi_info['url']}")
        print(f"SHA256: {pypi_info['sha256']}")
        
        # Update Homebrew formula
        update_homebrew_formula(pypi_info, version)
        print("Homebrew formula updated successfully!")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()