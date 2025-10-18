import subprocess
import sys
import shutil
from pathlib import Path
import pytest
import glob

PROJECT_ROOT = Path(__file__).parent.parent
DIST_PATH = PROJECT_ROOT / "dist"
BUILD_PYPI_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "build_pypi.py"

@pytest.fixture(scope="module")
def build_pypi_packages():
    """
    Fixture to build the PyPI source distribution and wheel.
    """
    # Ensure dist directory is clean
    if DIST_PATH.exists():
        shutil.rmtree(DIST_PATH)
    DIST_PATH.mkdir(exist_ok=True)

    # 1. Build the PyPI package
    print(f"Building PyPI package using: {sys.executable} {BUILD_PYPI_SCRIPT_PATH}")
    build_process = subprocess.run(
        [sys.executable, str(BUILD_PYPI_SCRIPT_PATH)],
        capture_output=True,
        text=True,
        check=False
    )
    print(f"Build stdout:\n{build_process.stdout}")
    print(f"Build stderr:\n{build_process.stderr}")
    assert build_process.returncode == 0, f"PyPI build script failed: {build_process.stderr}"

    whl_files = glob.glob(str(DIST_PATH / "*.whl"))
    sdist_files = glob.glob(str(DIST_PATH / "*.tar.gz"))

    assert len(whl_files) == 1, "Expected exactly one wheel file."
    assert len(sdist_files) == 1, "Expected exactly one sdist file."

    wheel_file = whl_files[0]
    sdist_file = sdist_files[0]

    yield wheel_file, sdist_file

    # Teardown: Clean up dist directory
    print("Cleaning up PyPI build artifacts.")
    if DIST_PATH.exists():
        shutil.rmtree(DIST_PATH)

def install_and_test_cli(package_file: Path, package_type: str):
    """
    Helper function to install a package in a temporary venv and test its CLI.
    """
    venv_path = PROJECT_ROOT / f".venv-pypi-test-{package_type}"

    # Clean up previous venv if it exists
    if venv_path.exists():
        shutil.rmtree(venv_path)
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)

    # Determine the correct pip executable path within the venv
    pip_executable = venv_path / "bin" / "pip"
    if sys.platform == "win32":
        pip_executable = venv_path / "Scripts" / "pip.exe"

    # Install the built package into the venv
    print(f"Installing {package_type} package into venv using: {pip_executable} install --force-reinstall {package_file}")
    install_process = subprocess.run(
        [str(pip_executable), "install", "--force-reinstall", str(package_file)],
        capture_output=True,
        text=True,
        check=False
    )
    print(f"Install stdout:\n{install_process.stdout}")
    print(f"Install stderr:\n{install_process.stderr}")
    assert install_process.returncode == 0, f"Package installation failed for {package_type}: {install_process.stderr}"

    # Determine the correct ocr-my-mess executable path within the venv
    ocr_my_mess_executable = venv_path / "bin" / "ocr-my-mess"
    if sys.platform == "win32":
        ocr_my_mess_executable = venv_path / "Scripts" / "ocr-my-mess.exe"

    # Check if the executable exists
    assert ocr_my_mess_executable.exists(), f"Executable not found for {package_type} at {ocr_my_mess_executable}"

    print(f"Running installed {package_type} package: {ocr_my_mess_executable} --help")
    run_process = subprocess.run(
        [str(ocr_my_mess_executable), "--help"],
        capture_output=True,
        text=True,
        check=False
    )
    print(f"Run stdout:\n{run_process.stdout}")
    print(f"Run stderr:\n{run_process.stderr}")
    assert run_process.returncode == 0, f"Installed {package_type} package failed to run: {run_process.stderr}"
    assert "Usage: ocr-my-mess" in run_process.stdout

    # Teardown: Clean up venv
    print(f"Cleaning up {package_type} test venv.")
    if venv_path.exists():
        shutil.rmtree(venv_path)

def test_pypi_package_cli_help_from_wheel(build_pypi_packages):
    """
    Tests if the installed PyPI package's CLI runs with --help when installed from wheel.
    """
    wheel_file, _ = build_pypi_packages
    install_and_test_cli(Path(wheel_file), "wheel")

def test_pypi_package_cli_help_from_sdist(build_pypi_packages):
    """
    Tests if the installed PyPI package's CLI runs with --help when installed from sdist.
    """
    _, sdist_file = build_pypi_packages
    install_and_test_cli(Path(sdist_file), "sdist")