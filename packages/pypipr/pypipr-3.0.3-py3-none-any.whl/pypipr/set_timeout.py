import threading


def set_timeout(interval, func, args=None, kwargs=None):
    """
    Menjalankan fungsi ketika sudah sekian detik.
    Apabila timeout masih berjalan tapi kode sudah selesai dieksekusi semua, maka
    program tidak akan berhenti sampai timeout selesai, kemudian fungsi dijalankan,
    kemudian program dihentikan.

    ```python
    set_timeout(3, lambda: print("Timeout 3"))
    x = set_timeout(7, print, args=["Timeout 7"])
    print(x)
    print("menghentikan timeout 7")
    x.cancel()
    ```
    """
    t = threading.Timer(interval=interval, function=func, args=args, kwargs=kwargs)
    t.start()
    # t.cancel() untuk menghentikan timer sebelum waktu habis
    return t
