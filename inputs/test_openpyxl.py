import sys
print(f"Python: {sys.executable}")
print(f"Python version: {sys.version}")

try:
    import openpyxl
    print(f"✓ openpyxl {openpyxl.__version__} is installed")
except ImportError as e:
    print(f"✗ openpyxl is NOT installed: {e}")
    sys.exit(1)


