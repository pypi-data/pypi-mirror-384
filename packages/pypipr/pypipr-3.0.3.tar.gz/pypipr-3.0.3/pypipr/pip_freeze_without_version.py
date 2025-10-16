from subprocess import run

from .ijoin import ijoin
from .iopen import iopen


def pip_freeze_without_version(filename=None):
    """
    Memberikan list dari dependencies yang terinstall tanpa version.
    Bertujuan untuk menggunakan Batteries Included Python.

    ```py
    print(pip_freeze_without_version())
    ```
    """
    text = run("pip list --format=freeze", capture_output=True, text=True, shell=True).stdout
    res = ijoin((i.split("=")[0] for i in text.splitlines()), separator="\n")
    if filename:
        return iopen(filename, data=res)
    return res
