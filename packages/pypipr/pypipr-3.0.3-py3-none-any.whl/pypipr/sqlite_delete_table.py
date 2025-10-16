import sqlite3


def sqlite_delete_table(filename, tablename):
    """
    Perintah sederhana untuk menghapus tabel
    dari database SQLite.
    """
    con = sqlite3.connect(filename)
    cur = con.cursor()
    cur.execute(f"DROP TABLE IF EXISTS {tablename}")
    con.commit()
    con.close()
