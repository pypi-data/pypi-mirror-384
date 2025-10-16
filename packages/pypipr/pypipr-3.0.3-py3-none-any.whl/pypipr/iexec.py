import io
import sys


def iexec(python_syntax, import_pypipr=True):
    """
    improve exec() python function untuk mendapatkan outputnya

    ```python
    print(iexec('print(9*9)'))
    ```
    """
    if import_pypipr:
        python_syntax = f"from pypipr import *\n\n{python_syntax}"

    stdout_backup = sys.stdout

    sys.stdout = io.StringIO()
    exec(python_syntax)
    output = sys.stdout.getvalue()

    sys.stdout = stdout_backup

    return output
