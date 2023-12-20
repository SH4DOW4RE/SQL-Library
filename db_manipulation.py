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

providers = [
    '@gmail.com',
    '@hotmail.com',
    '@yahoo.com',
    '@outlook.com',
    '@outlook.fr',
    '@sfr.fr',
    '@orange.fr',
    '@bbox.fr',
    '@laposte.net'
]

letters = string.ascii_letters
digits = string.digits
special_chars = '!#$&*+,?;.-_<>=@'

alphabet = letters + digits + special_chars


db_cur.execute("SELECT prenom, nom FROM abonne")
names = db_cur.fetchall()


for i in range(len(names)):
    password = ''
    length = random.randint(5, 20)
    for j in range(length):
        password += ''.join(secrets.choice(alphabet))

    email = list(names[i][0].lower())[0] + '.' + names[i][1].lower() + random.choice(providers)

    print(i+9)
    db_cur.execute(f"""UPDATE abonne SET email = "{email}", mot_de_passe = "{password}" WHERE id = {i+9};""")
    db.commit()
