from dotenv import load_dotenv
from mysql import connector
#import sqlite3
import secrets
import random
import string
import os

#db = sqlite3.connect('database.db')
#db_cur = db.cursor()

load_dotenv('.env')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')

db = connector.connect(
    host = DB_HOST,
    database = DB_NAME,
    username = DB_USERNAME,
    password = DB_PASSWORD
    )
db_cur = db.cursor()

db_cur.execute("""ALTER TABLE abonne ADD gestionnaire BOOLEAN DEFAULT 0""")
db.commit()
