"""Build script gets called on uv/pip build."""

import os
import pathlib
import shutil
import subprocess
import sys

# Conditional import for hatchling (may not be available in all build environments)
try:
    from hatchling.builders.hooks.plugin.interface import BuildHookInterface
    HATCHLING_AVAILABLE = True
except ImportError:
    HATCHLING_AVAILABLE = False
    BuildHookInterface = object  # Dummy base class


class BuildError(Exception):
    """Custom exception for build failures"""

    pass


def run_subprocess(cmd: list[str], cwd: pathlib.Path) -> None:
    """
    Run a subprocess, allowing natural signal propagation.

    Args:
        cmd: Command and arguments as a list of strings
        cwd: Working directory for the subprocess
    """

    print(f"-- Running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def pnpm_install(project_root: pathlib.Path, pnpm_path: str):
    run_subprocess([pnpm_path, "install", "--frozen-lockfile"], project_root)


def pnpm_buildui(project_root: pathlib.Path, pnpm_path: str):
    run_subprocess([pnpm_path, "buildUi"], project_root)


def copy_directory(src: pathlib.Path, dst: pathlib.Path, description: str):
    """Copy directory with proper error handling"""
    print(f"Copying {description} from {src} to {dst}")
    try:
        if dst.exists():
            shutil.rmtree(dst)
        dst.mkdir(parents=True)
        shutil.copytree(src, dst, dirs_exist_ok=True)
    except KeyboardInterrupt:
        print("\nInterrupt received during copy operation...")
        # Clean up partial copies
        if dst.exists():
            shutil.rmtree(dst)
        raise
    except Exception as e:
        raise BuildError(f"Failed to copy {src} to {dst}: {e!s}")


def copy_frontend(project_root: pathlib.Path):
    """Copy the frontend dist directory to the backend for inclusion in the package."""
    backend_frontend_dir = project_root / "backend" / "chainlit" / "frontend" / "dist"
    frontend_dist = project_root / "frontend" / "dist"
    copy_directory(frontend_dist, backend_frontend_dir, "frontend assets")


def copy_copilot(project_root: pathlib.Path):
    """Copy the copilot dist directory to the backend for inclusion in the package."""
    backend_copilot_dir = project_root / "backend" / "chainlit" / "copilot" / "dist"
    copilot_dist = project_root / "libs" / "copilot" / "dist"
    copy_directory(copilot_dist, backend_copilot_dir, "copilot assets")


def copy_staged_assets(backend_dir: pathlib.Path, staged_assets_dir: pathlib.Path):
    """Copy pre-staged frontend assets to the backend for inclusion in the package."""
    print(f"Copying staged assets from {staged_assets_dir}")
    
    # Copy main frontend assets
    frontend_staged = staged_assets_dir / "frontend"
    if frontend_staged.exists():
        backend_frontend_dir = backend_dir / "chainlit" / "frontend" / "dist"
        copy_directory(frontend_staged, backend_frontend_dir, "staged frontend assets")
    
    # Copy copilot assets
    copilot_staged = staged_assets_dir / "copilot"
    if copilot_staged.exists():
        backend_copilot_dir = backend_dir / "chainlit" / "copilot" / "dist"
        copy_directory(copilot_staged, backend_copilot_dir, "staged copilot assets")
    
    print("Staged assets copied successfully")


def build():
    """Main build function with proper error handling"""

    # Check if frontend building should be skipped (assets already staged)
    skip_frontend = os.environ.get("BRAZIL_BUILD_SKIP_FRONTEND", "").lower() == "true"
    staged_assets_dir = os.environ.get("FRONTEND_ASSETS_STAGED_DIR", "")
    
    if skip_frontend:
        print("\n-- Skipping frontend build (BRAZIL_BUILD_SKIP_FRONTEND=true)")
        
        backend_dir = pathlib.Path(__file__).resolve().parent
        project_root = backend_dir.parent
        
        if staged_assets_dir:
            print(f"-- Using pre-staged frontend assets from: {staged_assets_dir}")
            try:
                copy_staged_assets(backend_dir, pathlib.Path(staged_assets_dir))
                return
            except Exception as e:
                print(f"Warning: Failed to copy staged assets: {e}")
                print("Falling back to in-place asset copy...")
        
        # Try to copy assets from their built locations (fallback when no staged assets)
        print("-- Looking for built frontend assets in source directory...")
        try:
            # Check if frontend/dist exists and copy it
            frontend_dist = project_root / "frontend" / "dist"
            if frontend_dist.exists():
                print(f"Found frontend assets at: {frontend_dist}")
                copy_frontend(project_root)
            else:
                print(f"No frontend dist found at: {frontend_dist}")
            
            # Check if copilot/dist exists and copy it  
            copilot_dist = project_root / "libs" / "copilot" / "dist"
            if copilot_dist.exists():
                print(f"Found copilot assets at: {copilot_dist}")
                copy_copilot(project_root)
            else:
                print(f"No copilot dist found at: {copilot_dist}")
                
            return  # Done with asset copying
            
        except Exception as e:
            print(f"Warning: Failed to copy in-place assets: {e}")
            print("No frontend assets will be included")
            return

    print(
        "\n-- Building frontend, this might take a while!\n\n"
        "   If you don't need to build the frontend and just want dependencies installed, use:\n"
        "   `uv sync --no-install-project --no-editable`\n"
    )

    try:
        # Find directory containing this file
        backend_dir = pathlib.Path(__file__).resolve().parent
        project_root = backend_dir.parent

        # Dirty hack to distinguish between building wheel from sdist and from source code
        if not (project_root / "package.json").exists():
            return

        pnpm = shutil.which("pnpm")
        if not pnpm:
            raise BuildError("pnpm not found!")

        pnpm_install(project_root, pnpm)
        pnpm_buildui(project_root, pnpm)
        copy_frontend(project_root)
        copy_copilot(project_root)

    except KeyboardInterrupt:
        print("\nBuild interrupted by user")
        sys.exit(1)
    except BuildError as e:
        print(f"\nBuild failed: {e!s}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e!s}")
        sys.exit(1)


if HATCHLING_AVAILABLE:
    class CustomBuildHook(BuildHookInterface):
        def initialize(self, _, __):
            build()
else:
    # Dummy class when hatchling is not available
    class CustomBuildHook:
        pass
