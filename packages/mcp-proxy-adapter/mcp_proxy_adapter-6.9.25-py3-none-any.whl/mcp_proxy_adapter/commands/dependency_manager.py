"""
Dependency management system for remote plugins.

This module handles automatic installation and verification of plugin dependencies
using pip and other package management tools.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
import sys
import importlib
from typing import List, Dict, Any, Tuple
from pathlib import Path

try:  # Python 3.8+
    from importlib import metadata as importlib_metadata  # type: ignore
except Exception:  # pragma: no cover - very old Python fallback
    import importlib_metadata  # type: ignore

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version, InvalidVersion

from mcp_proxy_adapter.core.logging import get_global_logger


class DependencyManager:
    """
    Manages plugin dependencies installation and verification.
    """

    def __init__(self):
        """Initialize dependency manager."""
        self._installed_packages: Dict[str, str] = {}
        self._load_installed_packages()

    def _load_installed_packages(self) -> None:
        """Load list of currently installed packages."""
        try:
            self._installed_packages.clear()
            for dist in importlib_metadata.distributions():
                try:
                    name = dist.metadata.get("Name") or dist.metadata.get("name")
                    version = dist.version
                    if name and version:
                        self._installed_packages[name.lower()] = version
                except Exception:
                    continue
        except Exception as e:
            get_global_logger().warning(f"Failed to load installed packages: {e}")

    def check_dependencies(
        self, dependencies: List[str]
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Check if dependencies are satisfied.

        Args:
            dependencies: List of dependency names

        Returns:
            Tuple of (all_satisfied, missing_deps, installed_deps)
        """
        if not dependencies:
            return True, [], []

        missing_deps = []
        installed_deps = []

        for dep in dependencies:
            if self._is_dependency_satisfied(dep):
                installed_deps.append(dep)
            else:
                missing_deps.append(dep)

        all_satisfied = len(missing_deps) == 0
        return all_satisfied, missing_deps, installed_deps

    def _is_dependency_satisfied(self, dependency: str) -> bool:
        """
        Check if a single dependency is satisfied.

        Args:
            dependency: Dependency name or spec

        Returns:
            True if dependency is satisfied, False otherwise
        """
        # Parse requirement (handles version specifiers)
        try:
            req = Requirement(dependency)
        except Exception:
            # Fallback: treat as importable module name
            try:
                importlib.import_module(dependency)
                return True
            except ImportError:
                return False

        # Check installation by distribution name
        try:
            installed_version = importlib_metadata.version(req.name)
        except importlib_metadata.PackageNotFoundError:
            return False

        # If no specifier, any installed version satisfies
        if not req.specifier:
            return True

        try:
            return Version(installed_version) in req.specifier
        except InvalidVersion:
            # If version parsing fails, fallback to string comparison via specifier
            return req.specifier.contains(installed_version, prereleases=True)

    def install_dependencies(
        self, dependencies: List[str], user_install: bool = False
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Install dependencies using pip.

        Args:
            dependencies: List of dependency names to install
            user_install: Whether to install for current user only

        Returns:
            Tuple of (success, installed_deps, failed_deps)
        """
        if not dependencies:
            return True, [], []

        installed_deps = []
        failed_deps = []

        for dep in dependencies:
            try:
                if self._install_single_dependency(dep, user_install):
                    installed_deps.append(dep)
                    get_global_logger().info(f"Successfully installed dependency: {dep}")
                else:
                    failed_deps.append(dep)
                    get_global_logger().error(f"Failed to install dependency: {dep}")
            except Exception as e:
                failed_deps.append(dep)
                get_global_logger().error(f"Error installing dependency {dep}: {e}")

        success = len(failed_deps) == 0

        # Reload installed packages cache
        if success:
            self._load_installed_packages()

        return success, installed_deps, failed_deps

    def _install_single_dependency(
        self, dependency: str, user_install: bool = False
    ) -> bool:
        """
        Install a single dependency using pip.

        Args:
            dependency: Dependency name or spec
            user_install: Whether to install for current user only

        Returns:
            True if installation successful, False otherwise
        """
        try:
            # Build pip command
            cmd = [sys.executable, "-m", "pip", "install"]

            if user_install:
                cmd.append("--user")

            # Add quiet flag to reduce output
            cmd.append("--quiet")

            # Add dependency
            cmd.append(dependency)

            get_global_logger().debug(f"Installing dependency: {' '.join(cmd)}")

            # Run pip install
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300  # 5 minutes timeout
            )

            if result.returncode == 0:
                get_global_logger().debug(f"Successfully installed {dependency}")
                return True
            else:
                get_global_logger().error(f"Failed to install {dependency}: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            get_global_logger().error(f"Timeout while installing {dependency}")
            return False
        except Exception as e:
            get_global_logger().error(f"Error installing {dependency}: {e}")
            return False

    def verify_installation(self, dependencies: List[str]) -> Tuple[bool, List[str]]:
        """
        Verify that dependencies are properly installed.

        Args:
            dependencies: List of dependencies to verify

        Returns:
            Tuple of (all_verified, failed_verifications)
        """
        if not dependencies:
            return True, []

        failed_verifications = []

        for dep in dependencies:
            if not self._is_dependency_satisfied(dep):
                failed_verifications.append(dep)

        all_verified = len(failed_verifications) == 0
        return all_verified, failed_verifications

    def get_dependency_info(self, dependency: str) -> Dict[str, Any]:
        """
        Get information about a dependency.

        Args:
            dependency: Dependency name

        Returns:
            Dictionary with dependency information
        """
        info: Dict[str, Any] = {
            "name": dependency,
            "installed": False,
            "version": None,
            "importable": False,
        }

        # Check if it's installed
        try:
            version = importlib_metadata.version(dependency)
            info["installed"] = True
            info["version"] = version
        except importlib_metadata.PackageNotFoundError:
            pass

        # Check if it's importable
        try:
            importlib.import_module(dependency)
            info["importable"] = True
        except ImportError:
            pass

        return info

    def list_installed_dependencies(self) -> Dict[str, str]:
        """
        Get list of all installed packages.

        Returns:
            Dictionary mapping package names to versions
        """
        return self._installed_packages.copy()


# Global instance
dependency_manager = DependencyManager()
