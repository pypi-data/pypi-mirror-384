
import toml
import sys

def bump_patch_version(version_str):
    major, minor, patch = map(int, version_str.split('.'))
    patch += 1
    return f"{major}.{minor}.{patch}"

if __name__ == "__main__":
    pyproject_path = "pyproject.toml"
    pyproject_data = toml.load(pyproject_path)
    old_version = pyproject_data["project"]["version"]
    new_version = bump_patch_version(old_version)
    pyproject_data["project"]["version"] = new_version
    with open(pyproject_path, "w") as f:
        toml.dump(pyproject_data, f)
    print(new_version)
