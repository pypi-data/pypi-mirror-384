import pathlib


def iscandir(
    folder_name=".",
    glob_pattern="*",
    recursive=True,
    scan_file=True,
    scan_folder=True,
):
    """
    Mempermudah scandir untuk mengumpulkan folder dan file.

    ```python
    print(iscandir())
    print(list(iscandir("./", recursive=False, scan_file=False)))
    ```
    """
    path_obj = pathlib.Path(folder_name)
    if recursive:
        path_obj = path_obj.rglob(glob_pattern)
    else:
        path_obj = path_obj.glob(glob_pattern)

    for i in path_obj:
        if scan_folder and i.is_dir():
            yield i
        if scan_file and i.is_file():
            yield i
