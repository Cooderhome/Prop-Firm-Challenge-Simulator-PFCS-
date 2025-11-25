import subprocess
import sys

with open('app_output.txt', 'w') as f:
    try:
        subprocess.run([sys.executable, 'app.py'], stdout=f, stderr=f, check=True)
    except subprocess.CalledProcessError as e:
        print(f"App failed with exit code {e.returncode}")
