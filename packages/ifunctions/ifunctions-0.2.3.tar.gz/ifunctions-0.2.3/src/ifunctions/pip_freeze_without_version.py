import subprocess
import sys


def pip_freeze_without_version(filename=None):
    """
    Memberikan list dari dependencies yang terinstall tanpa version.
    Bertujuan untuk menggunakan Batteries Included Python.

    ```py
    print(pip_freeze_without_version())
    ```
    """
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--format=freeze"],
        capture_output=True,
        text=True,
    )
    packages = [line.split("=")[0] for line in result.stdout.splitlines()]
    res = "\n".join(sorted(packages))
    if filename:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(res)
        return filename
    return res
