from pathlib import Path
from time import sleep


def create_folder(folder_name, wait_until_success=True):
    """
    Membuat folder.
    Membuat folder secara recursive dengan permission.

    ```py
    create_folder("contoh_membuat_folder")
    create_folder("contoh/membuat/folder/recursive")
    create_folder("./contoh_membuat_folder/secara/recursive")
    ```
    """
    p = Path(folder_name)
    p.mkdir(parents=True, exist_ok=True)
    if wait_until_success:
        while not p.exists():
            sleep(0.1)

