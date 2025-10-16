from pathlib import Path


def dirpath(path=".", indeks=-1, abs_path=None):
    """
    Mengembalikan bagian direktori dari sebuah path berdasarkan indeks.
    Tanpa trailing slash di akhir.

    Args:
        path (str): Path lengkap ke file atau direktori.
        indeks (int): Indeks negatif untuk menentukan seberapa jauh naik ke atas direktori.
        abs_path (bool | None):
            - True untuk path absolut,
            - False untuk path relatif terhadap cwd,
            - None untuk path sesuai pemotongan manual.

    Returns:
        str: Path direktori hasil ekstraksi.

    Contoh:
        dirpath("/a/b/c/d/e.txt", -2) -> "a/b/c"
    """

    path_obj = Path(path)
    parts = path_obj.parts
    new_parts = parts[:indeks]

    new_path = Path(*new_parts)
    if abs_path is None:
        return str(new_path)

    resolved_path = new_path.resolve()
    if abs_path:
        return str(resolved_path)
    return str(resolved_path.relative_to(Path.cwd()))
