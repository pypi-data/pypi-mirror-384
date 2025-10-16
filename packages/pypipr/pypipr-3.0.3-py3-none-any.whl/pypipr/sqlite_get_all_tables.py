import sqlite3


def sqlite_get_all_tables(filename):
    """
    Perintah SQLite untuk menampilkan seluruh tabel
    yang ada pada database.
    Hanya akan mengembalikan kolom nama tabel saja.
    """
    con = sqlite3.connect(filename)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' order by name;")
    tables = cur.fetchall()
    con.close()
    return tables
