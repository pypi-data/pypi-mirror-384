import subprocess
import sys
import os

def run_command(command, message):
    print(f"--- {message} ---")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Stderr: {result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/local_release.py <version>")
        sys.exit(1)
    new_version = sys.argv[1]
    print(f"--- Releasing version: {new_version} ---")

    # 2. Git operations
    print("\n--- Building distribution packages ---")
    run_command(["python", "-m", "build"], "Building packages")

    print("\n--- Uploading to PyPI ---")
    run_command(["twine", "upload", "dist/*"], "Uploading distribution packages to PyPI")

    print("\n--- PyPI release process completed locally ---")
    print("\nRemember to verify the release on PyPI.")

if __name__ == "__main__":
    main()
