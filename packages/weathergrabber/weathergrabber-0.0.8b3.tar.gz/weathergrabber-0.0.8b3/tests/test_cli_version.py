import subprocess
import sys
import weathergrabber


def test_cli_version_flag_prints_version():
    result = subprocess.run([
        sys.executable, "-m", "weathergrabber", "-v"
    ], capture_output=True, text=True)
    assert result.returncode in (0, 2)
    output = (result.stdout or "") + (result.stderr or "")
    assert str(weathergrabber.__version__) in output
    assert "Weathergrabber" in output
