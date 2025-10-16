import sqlite3


def sqlite_get_data_table(filename, tablename):
    """
    Perintah SQLite untuk menampilkan seluruh data
    pada tabel database
    """
    con = sqlite3.connect(filename)
    cur = con.cursor()
    cur.execute(f"SELECT * FROM {tablename}")
    rows = cur.fetchall()
    con.close()
    return rows
