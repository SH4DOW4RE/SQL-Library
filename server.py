from flask import Flask, render_template, request, session, abort, redirect
from dotenv import load_dotenv
from mysql import connector
from waitress import serve
from datetime import datetime
import argparse
import secrets
import sys
import os


app = Flask(__name__)
app.secret_key = secrets.token_hex(32)


load_dotenv('.env')
IP = os.getenv('IP')
PORT = os.getenv('PORT')
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

argParser = argparse.ArgumentParser()
argParser.add_argument("-p", "--prod", help="Enable production mode", action='store_true')


@app.route('/<lang>')
@app.route('/')
def index(lang = ''):
    if lang == 'fr':
        return render_template('fr/index.html')
    else:
        return render_template('en/index.html')

@app.route('/<lang>/account')
@app.route('/account')
def account(lang = ''):
    firstname = None
    try: firstname = session['firstname']
    except: pass
    if lang == 'fr':
        if firstname != None:
            return render_template('fr/account.html')
        else:
            return redirect('/fr/connect')
    else:
        if firstname != None:
            return render_template('en/account.html')
        else:
            return redirect('/connect')

@app.route('/<lang>/connect')
@app.route('/connect')
def connect(lang = ''):
    if lang == 'fr':
        return render_template('fr/connect.html')
    else:
        return render_template('en/connect.html')

@app.route('/<lang>/connect', methods=['POST'])
@app.route('/connect', methods=['POST'])
def connect_post(lang = ''):
    c_type = request.form['c_type']
    if c_type == 'login':
        email = request.form['email']
        password = request.form['password']
        
    elif c_type == 'register':
        email = request.form['email']
        password = request.form['password']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        birthday = request.form['birthday']
        address = request.form['address']
        zipcode = request.form['zipcode']
        city = request.form['city']

@app.route('/<lang>/search', methods=['POST'])
@app.route('/search', methods=['POST'])
def search(lang = ''):
    name = request.form['query']
    while '"' in name: name = name.replace('"', '')
    try: author = request.form["author"]
    except: author = None
    try: editor = request.form['editor']
    except: editor = None
    try:
        if request.form['available'] == 'true':
            available = True
        elif request.form['available'] == 'false':
            available = False
        else:
            available = None
    except: available = None
    
    try: curr_page = int(request.form['page'])
    except: curr_page = 0
    print(curr_page)
    
    rf = [
        '<tr><td class="result-title">',
        '</td><td class="result-author">',
        '</td><td class="result-editor">',
        '</td>',
        '</td></tr>'
    ]
    
    af = [
        '<td class="result-available">',
        '<td class="result-notavailable">'
    ]
    
    query = f"""
        SELECT
            livre.titre,
            auteur.nom,
            editeur.nom,
            CASE
                WHEN EXISTS (
                    SELECT 1
                    FROM emprunt
                    WHERE emprunt.id_livre = livre.id AND emprunt.date_retour IS NULL
                ) THEN 'Available'
                ELSE 'Not Available'
            END AS availability_status
        FROM
            livre
        JOIN
            auteur ON livre.id_auteur = auteur.id
        JOIN
            editeur ON livre.id_editeur = editeur.id
        WHERE
            LOWER(livre.titre) LIKE '%{name.lower()}%'
    """
    if author != None and author != '':
        query += f"""        AND LOWER(auteur.nom) LIKE '%{author.lower()}%'"""
    if editor != None and editor != '':
        query += f"""        AND LOWER(editeur.nom) LIKE '%{editor.lower()}%'"""
    if available != None:
        prefix = 'EXISTS' if available else 'NOT EXISTS'
        query += f"""
            AND {prefix} (
                SELECT 1
                FROM emprunt
                WHERE emprunt.id_livre = livre.id AND emprunt.date_retour IS NULL
            )
        """
    
    offset = str(curr_page * 20 if curr_page != None else 0)
    max_per_page = '20'
    query += f'LIMIT {offset}, {max_per_page};'
    
    db_cur.execute(query)
    results = db_cur.fetchall()
    db.commit()
    
    for i in range(len(results)):
        if str(results[i][3]) == 'Available' :
            cond = True
        elif str(results[i][3]) == 'Not Available' :
            cond = False
        else:
            cond = results[i][3]
        results[i] = [results[i][0], results[i][1], results[i][2], cond ]
    
    for i in range(len(results)):
        results[i] = rf[0] + results[i][0] + rf[1] + results[i][1] + rf[2] + results[i][2] + rf[3] + ((af[0] + 'Available') if results[i][3] else (af[1] + 'Not Available')) + rf[4]
    
    if len(results) <= 0:
        results = '</table>'
    else:
        results = ''.join(results) + '</table>'
    
    avy_checked = 'checked' if (available and available != None) else ''
    avn_checked = 'checked' if (not available and available != None) else ''
    author = author if author != None else ''
    editor = editor if editor != None else ''
    
    if lang == 'fr':
        return render_template('fr/results.html', query=name, author=author, editor=editor, avy_checked=avy_checked, avn_checked=avn_checked, results=results, curr_page=curr_page, cursor=curr_page+1)
    else:
        return render_template('en/results.html', query=name, author=author, editor=editor, avy_checked=avy_checked, avn_checked=avn_checked, results=results, curr_page=curr_page, cursor=curr_page+1)


if __name__ == '__main__':
    args = argParser.parse_args()
    prod = args.prod
    
    if prod:
        serve(app, host=IP, port=PORT)
        sys.exit()
    else:
        app.run(host=IP, port=PORT, debug=True)
        sys.exit()
