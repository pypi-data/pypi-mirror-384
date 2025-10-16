import subprocess
import sys

def test_main_entrypoint():
    result = subprocess.run(
        [sys.executable, "-m", "weathergrabber", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Weathergrabber" in result.stdout