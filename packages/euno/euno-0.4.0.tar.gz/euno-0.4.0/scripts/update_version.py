#!/usr/bin/env python3
"""
Version update script for Euno SDK releases.

Usage:
    python scripts/update_version.py 0.2.0
"""

import sys
import os
import re


def update_version_file(version):
    """Update version in euno/version.py"""
    version_file = "euno/version.py"
    if os.path.exists(version_file):
        with open(version_file, "r") as f:
            content = f.read()

        # Replace the version line
        new_content = re.sub(r'__version__ = "[^"]*"', f'__version__ = "{version}"', content)

        with open(version_file, "w") as f:
            f.write(new_content)

        print(f"✅ Updated {version_file} to version {version}")
    else:
        print(f"❌ Version file not found: {version_file}")


def update_setup_file(version):
    """Update fallback version in setup.py"""
    setup_file = "setup.py"
    if os.path.exists(setup_file):
        with open(setup_file, "r") as f:
            content = f.read()

        # Replace the fallback version
        new_content = re.sub(r"return '[^']*'", f"return '{version}'", content)

        with open(setup_file, "w") as f:
            f.write(new_content)

        print(f"✅ Updated {setup_file} fallback version to {version}")
    else:
        print(f"❌ Setup file not found: {setup_file}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/update_version.py <version>")
        print("Example: python scripts/update_version.py 0.2.0")
        sys.exit(1)

    version = sys.argv[1]

    # Validate version format (basic check)
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        print("❌ Invalid version format. Use semantic versioning (e.g., 0.2.0)")
        sys.exit(1)

    print(f"🔄 Updating version to {version}...")

    update_version_file(version)
    update_setup_file(version)

    print(f"\n🎉 Version updated to {version}!")
    print("\nNext steps:")
    print("1. git add .")
    print('2. git commit -m "Release version {version}"')
    print("3. git push origin main")
    print("4. Create GitHub release with tag v{version}")


if __name__ == "__main__":
    main()
