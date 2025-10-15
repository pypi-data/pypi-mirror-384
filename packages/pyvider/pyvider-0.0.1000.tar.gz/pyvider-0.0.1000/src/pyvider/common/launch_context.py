"""
Launch context detection for Pyvider.

This module detects how Pyvider was launched and provides context information
about the execution environment.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
import os
from pathlib import Path
import sys
from typing import Any


class LaunchMethod(Enum):
    """Different ways Pyvider can be launched."""

    PSPF_PACKAGE = "pspf_package"
    SCRIPT_MODULE = "script_module"
    SCRIPT_DIRECT = "script_direct"
    EDITABLE_INSTALL = "editable_install"
    UNKNOWN = "unknown"


@dataclass
class LaunchContext:
    """Context information about how Pyvider was launched."""

    method: LaunchMethod
    executable_path: str
    python_executable: str
    working_directory: str
    environment_info: dict[str, Any]
    is_terraform_invoked: bool
    details: dict[str, Any]

    def __str__(self) -> str:
        """Human-readable representation of launch context."""
        lines = [
            "🚀 Pyvider Launch Context:",
            f"   Method: {self.method.value}",
            f"   Executable: {self.executable_path}",
            f"   Python: {self.python_executable}",
            f"   Working Dir: {self.working_directory}",
            f"   Terraform Invoked: {self.is_terraform_invoked}",
        ]

        if self.details:
            lines.append("   Details:")
            for key, value in self.details.items():
                lines.append(f"     {key}: {value}")

        return "\n".join(lines)


def detect_launch_context() -> LaunchContext:
    """
    Detect how Pyvider was launched and return context information.

    Returns:
        LaunchContext with details about the execution environment
    """
    executable_path = sys.argv[0] if sys.argv else ""
    python_executable = sys.executable
    working_directory = str(Path.cwd())
    is_terraform_invoked = bool(os.environ.get("TF_PLUGIN_MAGIC_COOKIE"))

    # Gather environment information
    environment_info = {
        "python_version": sys.version,
        "platform": sys.platform,
        "argv": sys.argv,
        "path_entries": len(sys.path),
        "terraform_cookie_present": is_terraform_invoked,
    }

    # Add PSPF-specific environment variables if present
    pspf_env_vars = {}
    for key in os.environ:
        if key.startswith("PSPF_") or "pspf" in key.lower():
            pspf_env_vars[key] = os.environ[key]
    if pspf_env_vars:
        environment_info["pspf_env_vars"] = pspf_env_vars

    # Detect launch method and gather details
    method, details = _detect_launch_method(executable_path, python_executable)

    return LaunchContext(
        method=method,
        executable_path=executable_path,
        python_executable=python_executable,
        working_directory=working_directory,
        environment_info=environment_info,
        is_terraform_invoked=is_terraform_invoked,
        details=details,
    )


def _detect_launch_method(executable_path: str, python_executable: str) -> tuple[LaunchMethod, dict[str, Any]]:
    """
    Detect the specific launch method based on executable path and environment.

    Returns:
        Tuple of (LaunchMethod, details_dict)
    """
    details = {}

    # Check if we're running from a PSPF package
    if _is_pspf_launch(executable_path, python_executable):
        details.update(_get_pspf_details())
        return LaunchMethod.PSPF_PACKAGE, details

    # Check if we're running as a Python module
    if _is_module_launch():
        details["module_name"] = _get_module_name()
        details["launch_command"] = " ".join(sys.argv)
        return LaunchMethod.SCRIPT_MODULE, details

    # Check if we're running from an editable install
    if _is_editable_install(executable_path):
        details.update(_get_editable_install_details(executable_path))
        return LaunchMethod.EDITABLE_INSTALL, details

    # Check if we're running as a direct script
    if _is_direct_script_launch(executable_path):
        details["script_path"] = executable_path
        details["is_symlink"] = Path(executable_path).is_symlink()
        return LaunchMethod.SCRIPT_DIRECT, details

    # Unknown launch method
    details["reason"] = "Could not determine launch method"
    details["executable_analysis"] = _analyze_executable(executable_path)
    return LaunchMethod.UNKNOWN, details


def _is_pspf_launch(executable_path: str, python_executable: str) -> bool:
    """Check if we're running from a PSPF package."""
    # PSPF packages typically have a cache directory structure
    cache_indicators = ["/.cache/pspf/", "/cache/bin/python", "/pspf_", "terraform-provider-"]

    # Check if Python is running from a cache-like directory
    for indicator in cache_indicators:
        if indicator in python_executable.lower():
            return True

    # Check if executable path suggests PSPF
    if any(indicator in executable_path.lower() for indicator in ["terraform-provider-", "pspf"]):
        # Additional check: see if we're in a temporary/cache directory structure
        python_path = Path(python_executable)
        if any(part in str(python_path) for part in [".cache", "cache", "temp"]):
            return True

    return False


def _is_module_launch() -> bool:
    """Check if we're running as 'python -m pyvider'."""
    # Check if we're running via __main__.py (indicates module execution)
    if len(sys.argv) >= 1 and sys.argv[0].endswith("__main__.py"):
        return True

    # Check if -m is in the original command line
    # This is tricky because sys.argv doesn't contain the -m flag
    # But we can infer it from the executable path structure
    if len(sys.argv) >= 1:
        # If argv[0] ends with __main__.py, it's almost certainly python -m
        if "__main__.py" in sys.argv[0]:
            return True

        # If the first argument is just "pyvider" or similar module name
        # and we're running from a __main__.py, it's likely python -m
        first_arg = Path(sys.argv[0]).name
        if first_arg in ["pyvider", "__main__.py"] or first_arg.endswith("__main__.py"):
            return True

    return False


def _is_editable_install(executable_path: str) -> bool:
    """Check if we're running from an editable install."""
    exe_path = Path(executable_path)

    # Look for .egg-link files or site-packages with -e installs
    try:
        # Check if the executable is in a venv/conda env
        if any(env_dir in str(exe_path) for env_dir in [".venv", "venv", "conda", "anaconda"]):
            return True

        # Check if we can find pyvider in development mode
        import pyvider

        pyvider_path = Path(pyvider.__file__).parent.parent.parent
        if pyvider_path.name == "src":  # typical editable install structure
            return True

    except (ImportError, AttributeError):
        pass

    return False


def _is_direct_script_launch(executable_path: str) -> bool:
    """Check if we're running as a direct script."""
    return executable_path.endswith((".py", ".pyz")) or "python" in executable_path


def _get_pspf_details() -> dict[str, Any]:
    """Get details specific to PSPF launches."""
    details: dict[str, Any] = {}

    # Try to find PSPF cache information
    python_path = Path(sys.executable)
    details["python_cache_path"] = str(python_path.parent.parent)
    details["cache_structure"] = _analyze_cache_structure(python_path)

    # Look for PSPF metadata
    cache_dir = python_path.parent.parent
    metadata_paths = [
        cache_dir / "metadata",
        cache_dir / "cache" / "metadata",
    ]

    for metadata_path in metadata_paths:
        if metadata_path.exists():
            details["metadata_path"] = str(metadata_path)
            break

    return details


def _get_module_name() -> str:
    """Get the module name being executed."""
    # For python -m execution, the module name might not be in sys.argv
    # but we can infer it from the path structure
    if len(sys.argv) >= 1:
        argv0 = sys.argv[0]
        if "__main__.py" in argv0:
            # Try to extract module name from path
            # e.g., /path/to/pyvider/src/pyvider/__main__.py -> pyvider
            path_parts = Path(argv0).parts
            for i, part in enumerate(reversed(path_parts)):
                if part == "__main__.py" and i + 1 < len(path_parts):
                    module_name = path_parts[-(i + 2)]  # Get the parent directory
                    if module_name != "src":  # Skip src directory
                        return module_name

    # Fallback: check if -m is explicitly in sys.argv (rare but possible)
    if "-m" in sys.argv:
        try:
            m_index = sys.argv.index("-m")
            if m_index + 1 < len(sys.argv):
                return sys.argv[m_index + 1]
        except (ValueError, IndexError):
            pass

    return "pyvider"  # Default assumption


def _get_editable_install_details(executable_path: str) -> dict[str, Any]:
    """Get details for editable installs."""
    details: dict[str, Any] = {"executable_path": executable_path}

    try:
        import pyvider

        details["pyvider_location"] = str(Path(pyvider.__file__).parent.parent)
        details["is_development_mode"] = "src" in str(pyvider.__path__[0])
    except (ImportError, AttributeError):
        details["pyvider_import_error"] = "Could not import pyvider"

    return details


def _analyze_executable(executable_path: str) -> dict[str, Any]:
    """Analyze the executable for debugging unknown launch methods."""
    exe_path = Path(executable_path)

    return {
        "exists": exe_path.exists(),
        "is_file": exe_path.is_file() if exe_path.exists() else False,
        "is_symlink": exe_path.is_symlink() if exe_path.exists() else False,
        "suffix": exe_path.suffix,
        "parent": str(exe_path.parent),
        "name": exe_path.name,
    }


def _analyze_cache_structure(python_path: Path) -> dict[str, Any]:
    """Analyze the cache directory structure for PSPF packages."""
    cache_dir = python_path.parent.parent

    structure = {
        "python_bin_dir": str(python_path.parent),
        "cache_root": str(cache_dir),
        "contents": [],
    }

    try:
        if cache_dir.exists():
            structure["contents"] = [item.name for item in cache_dir.iterdir() if item.is_dir()][
                :10
            ]  # Limit to 10 items
    except (OSError, PermissionError):
        structure["contents"] = ["<access_denied>"]

    return structure


def log_launch_context(logger_func: Callable[[str], None] | None = None) -> LaunchContext:
    """
    Detect and log the launch context.

    Args:
        logger_func: Optional logger function to use. If None, uses print.

    Returns:
        The detected LaunchContext
    """
    context = detect_launch_context()

    log_func = logger_func or print
    log_func(str(context))

    return context
