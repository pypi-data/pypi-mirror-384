import os
import shutil
from datetime import datetime


def sqlite_backup(db):
    # db = os.path.abspath(db)
    if not os.path.isfile(db):
        raise FileNotFoundError(f"File '{db}' tidak ditemukan.")

    ff, ext = os.path.splitext(os.path.basename(db))

    fdb = os.path.join(os.path.dirname(db), ff)
    os.makedirs(fdb, exist_ok=True)

    nff = f"{ff}_{datetime.now():%Y%m%d_%H%M%S}{ext}"
    ndb = os.path.join(fdb, nff)

    shutil.copy2(db, ndb)
    return ndb
