import os
import sqlite3
import urllib.request

CHINOOK_DB_URL = "https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"
DB_PATH = "chinook.db"

def download_chinook_db():
    if not os.path.exists(DB_PATH):
        print("Downloading Chinook database...")
        urllib.request.urlretrieve(CHINOOK_DB_URL, DB_PATH)
        print("Download complete.")
    else:
        print("Chinook database already exists.")

def verify_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in the database:")
    for table in tables:
        print("-", table[0])
    conn.close()

if __name__ == "__main__":
    download_chinook_db()
    verify_db()
