import subprocess
import sys

# Run the manual test
result = subprocess.run(
    [sys.executable, "tests/test_discovery_manual.py"],
    capture_output=True,
    text=True
)

print("STDOUT:")
print(result.stdout)
if result.stderr:
    print("\nSTDERR:")
    print(result.stderr)
print(f"\nReturn code: {result.returncode}")
