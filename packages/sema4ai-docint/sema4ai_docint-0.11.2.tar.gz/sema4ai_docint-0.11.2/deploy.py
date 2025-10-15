#!/usr/bin/env python3
"""
Automated deployment script for libraries.

This script:
1. Builds the wheel using `uv build`
2. Copies the wheel to target directories
3. Updates package.yaml files to reference the new wheel
"""

import shutil
import subprocess
import sys
import tomllib
from datetime import datetime
from pathlib import Path


def generate_timestamped_filename(project_name: str, version: str) -> str:
    """Generate filename: project-name-$version.dev$timestamp.whl."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    wheel_base = project_name.replace("-", "_")
    return f"{wheel_base}-{version}-{timestamp}-py3-none-any.whl"


def get_project_info() -> tuple[str, str]:
    """Extract project name and version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found in current directory")

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})

    name = project.get("name")
    if not name:
        raise ValueError("Could not find project name in pyproject.toml")

    version = project.get("version")
    if not version:
        raise ValueError("Could not find project version in pyproject.toml")

    return name, version


def build_wheel() -> Path:
    """Build the wheel using uv build."""
    print("🔨 Building wheel with uv build...")

    result = subprocess.run(["uv", "build"], check=False, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Build failed: {result.stderr}")
        sys.exit(1)

    print("✅ Build completed successfully")

    # Find the built wheel
    dist_dir = Path("dist")
    if not dist_dir.exists():
        raise FileNotFoundError("dist directory not found after build")

    wheel_files = list(dist_dir.glob("*.whl"))
    if not wheel_files:
        raise FileNotFoundError("No wheel files found in dist directory")

    # Get the most recent wheel file
    wheel_file = max(wheel_files, key=lambda p: p.stat().st_mtime)
    print(f"📦 Built wheel: {wheel_file.name}")

    return wheel_file


def delete_old_wheels(target_dir: Path, project_name: str) -> None:
    """Delete old wheel files for this project from the target directory."""
    wheel_prefix = f"{project_name.replace('-', '_')}-"
    old_wheels = list(target_dir.glob(f"{wheel_prefix}*.whl"))

    if old_wheels:
        print(f"🗑️  Deleting {len(old_wheels)} old wheel(s) from {target_dir}")
        for old_wheel in old_wheels:
            old_wheel.unlink()
            print(f"   Deleted: {old_wheel.name}")
    else:
        print(f"ℹ️  No old wheels found to delete in {target_dir}")  # noqa: RUF001


def copy_wheel_to_targets(
    wheel_file: Path, target_dirs: list[str], project_name: str, version: str
) -> str:
    """Copy the wheel file to target directories with timestamped filename."""
    timestamped_filename = generate_timestamped_filename(project_name, version)

    for target_dir in target_dirs:
        target_path = Path(target_dir)
        if not target_path.exists():
            print(f"⚠️  Target directory does not exist: {target_path}")
            continue

        # Delete old wheels first
        delete_old_wheels(target_path, project_name)

        destination = target_path / timestamped_filename
        print(f"📋 Copying {wheel_file.name} to {target_path} as {timestamped_filename}")
        shutil.copy2(wheel_file, destination)
        print(f"✅ Copied to {destination}")

    return timestamped_filename


def update_package_yaml(package_yaml_path: Path, wheel_filename: str, project_name: str) -> None:
    """Update package.yaml to reference the new wheel file."""
    if not package_yaml_path.exists():
        print(f"⚠️  package.yaml not found: {package_yaml_path}")
        print("   Target directory may not exist or package.yaml not created yet")
        return

    print(f"📝 Updating {package_yaml_path}")

    # Read file as text to preserve comments and formatting
    with open(package_yaml_path) as f:
        content = f.read()

    # Find and update the wheel reference using regex
    import re

    wheel_prefix = f"./{project_name.replace('-', '_')}-"
    # Pattern that matches version numbers with dots, hyphens, and underscores
    pattern = rf"(\s*-\s*){re.escape(wheel_prefix)}[^/\s]*\.whl"

    if re.search(pattern, content):
        # Replace the wheel reference while preserving indentation
        new_content = re.sub(pattern, rf"\1./{wheel_filename}", content)

        # Write back the updated content with Unix line endings
        with open(package_yaml_path, "w", newline="\n") as f:
            f.write(new_content)

        print(f"✅ Updated {package_yaml_path}")
    else:
        print(f"⚠️  No wheel reference found to update in {package_yaml_path}")
        # Debug: show what wheel references exist in the file
        wheel_refs = re.findall(r"\s*-\s*\./[^-\s]*\.whl", content)
        if wheel_refs:
            print(f"🔍 Found wheel references: {wheel_refs}")
        else:
            print("🔍 No wheel references found in file")

        # Check if this project's wheel reference exists at all
        if wheel_prefix in content:
            print("   Found project prefix but no matching wheel reference")
        else:
            print(f"   No references to {project_name} found in package.yaml")


def main():
    """Main deployment function."""
    try:
        # Get project info
        project_name, version = get_project_info()
        print(f"🚀 Deploying {project_name} v{version}")

        # Target directories
        target_dirs = [
            "../actions/document-intelligence",
            "../actions/document-insights",
        ]

        # Build wheel
        wheel_file = build_wheel()

        # Copy wheel to target directories
        timestamped_filename = copy_wheel_to_targets(wheel_file, target_dirs, project_name, version)

        # Update package.yaml files
        for target_dir in target_dirs:
            package_yaml_path = Path(target_dir) / "package.yaml"
            update_package_yaml(package_yaml_path, timestamped_filename, project_name)

        print("✨ Deployment completed successfully!")

    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
