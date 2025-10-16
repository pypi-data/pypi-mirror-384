import pathlib
import subprocess
import time

from .print_colorize import print_colorize


def auto_reload(filename):
    """
    Menjalankan file python secara berulang.
    Dengan tujuan untuk melihat perubahan secara langsung.
    Pastikan kode aman untuk dijalankan.
    Jalankan kode ini di terminal console.

    ```py
    auto_reload("file_name.py")
    ```

    or run in terminal

    ```
    pypipr auto_reload
    ```
    """

    def filemtime(file):
        return pathlib.Path(file).stat().st_mtime

    mtime = filemtime(filename)
    last_mtime = 0

    try:
        print_colorize("Start")
        while True:
            last_mtime = mtime
            subprocess.run(f"python {filename}")
            while mtime == last_mtime:
                time.sleep(1)
                mtime = filemtime(filename)
            print_colorize("Reload")
    except KeyboardInterrupt:
        print_colorize("Stop")
