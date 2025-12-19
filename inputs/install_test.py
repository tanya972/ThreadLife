#!/usr/bin/env python3
import subprocess
import sys

print("Attempting to install openpyxl...")
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "openpyxl"],
    capture_output=True,
    text=True
)

print(f"Return code: {result.returncode}")
print(f"STDOUT:\n{result.stdout}")
print(f"STDERR:\n{result.stderr}")

print("\n" + "="*50)
print("Testing import...")
try:
    import openpyxl
    print(f"SUCCESS: openpyxl {openpyxl.__version__} is installed!")
except ImportError as e:
    print(f"FAILED: {e}")
    sys.exit(1)


