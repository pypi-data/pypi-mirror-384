import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
DIST_PATH = PROJECT_ROOT / "dist"
BUILD_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "build.py"

@pytest.mark.pyinstaller_build
@pytest.mark.skipif(sys.platform == "win32", reason="Build script is for Linux/macOS")
def test_cli_build_and_run():
    """
    Tests if the CLI can be built and if the resulting executable runs.
    """
    executable_path = DIST_PATH / "ocr-my-mess"

    # 1. Run the build script
    build_process = subprocess.run([sys.executable, str(BUILD_SCRIPT_PATH)], capture_output=True, text=True, check=False)
    assert build_process.returncode == 0, f"Build script failed: {build_process.stderr}"

    # 2. Check if the executable exists
    assert executable_path.exists(), "CLI executable was not created."

    # 3. Run the executable with --help
    run_process = subprocess.run([str(executable_path), "--help"], capture_output=True, text=True, check=False)
    assert run_process.returncode == 0, f"Executable failed to run: {run_process.stderr}"
    assert "Usage: ocr-my-mess" in run_process.stdout

@pytest.mark.pyinstaller_build
@pytest.mark.skipif(sys.platform == "win32", reason="Build script is for Linux/macOS")
def test_gui_build_and_run():
    """
    Tests if the GUI can be built and runs without crashing immediately.
    """
    executable_path = DIST_PATH / "ocr-my-mess"

    # 1. Run the build script
    build_process = subprocess.run([sys.executable, str(BUILD_SCRIPT_PATH)], capture_output=True, text=True, check=False)
    assert build_process.returncode == 0, f"Build script failed: {build_process.stderr}"

    # 2. Check if the executable exists
    assert executable_path.exists(), "GUI executable was not created."

    # 3. Run the executable with a timeout to check for immediate crashes
    try:
        # For a GUI app, we expect it to run until the timeout, then we kill it.
        # If it crashes before the timeout, process.wait() will return a non-zero code.
        process = subprocess.Popen([str(executable_path)])
        process.wait(timeout=5)
        # If we are here, the process terminated quickly, which might be an error.
        if process.returncode != 0:
            stdout, stderr = process.communicate()
            pytest.fail(f"GUI executable crashed with code {process.returncode}.\nStderr: {stderr}")
    except subprocess.TimeoutExpired:
        # This is the success case: the app launched and is running.
        process.kill()
        pass