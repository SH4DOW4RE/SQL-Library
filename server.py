from flask import Flask, render_template, request, session, abort, redirect
from dotenv import load_dotenv
from mysql import connector
from waitress import serve
from datetime import datetime
from dateutil.relativedelta import relativedelta
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
def index(lang = '', flash = ''):
    flash = '"' + flash + '"'
    if lang == 'fr':
        return render_template('fr/index.html', flash=flash)
    else:
        return render_template('en/index.html', flash=flash)

@app.route('/<lang>/account')
@app.route('/account')
def account(lang = ''):
    email = None
    password = None
    try: email = session.get('email')
    except: pass
    try: password = session.get('password')
    except: pass
    if lang == 'fr':
        if email != None and password != None:
            firstname = ''
            lastname = ''
            db_cur.execute(f"""SELECT nom, prenom FROM abonne WHERE email = "{email}" AND mot_de_passe = "{password}";""")
            results = db_cur.fetchall()
            db.commit()

            if len(results) < 1:
                return redirect('/fr/connect')

            firstname = results[0][1]
            lastname = results[0][0]

            return render_template('fr/account.html', firstname=firstname, lastname=lastname)
        else:
            session.clear()
            return redirect('/fr/connect')
    else:
        if email != None and password != None:
            firstname = ''
            lastname = ''
            db_cur.execute(f"""SELECT prenom, nom, date_naissance, adresse, code_postal, ville, date_inscription, date_fin_abo, email, mot_de_passe FROM abonne WHERE email = "{email}" AND mot_de_passe = "{password}";""")
            results = db_cur.fetchall()
            db.commit()

            if len(results) < 1:
                return redirect('/connect')

            firstname = results[0][0]
            lastname = results[0][1].upper()
            endsub = results[0][7]
            endsub2 = results[0][7].strftime('%d/%m/%Y')
            birthday = results[0][2]
            address = results[0][3]
            zipcode = results[0][4]
            city = results[0][5]
            regdate = results[0][6]

            return render_template('en/account.html', firstname=firstname, lastname=lastname, endsub2=endsub2, email=email, password=password, birthday=birthday, address=address, zipcode=zipcode, city=city, regdate=regdate, endsub=endsub)
        else:
            session.clear()
            return redirect('/connect')

@app.route('/<lang>/connect')
@app.route('/connect')
def connect(lang = '', flash = ''):
    flash = '"' + flash + '"'
    if lang == 'fr':
        return render_template('fr/connect.html', flash=flash)
    else:
        return render_template('en/connect.html', flash=flash)

@app.route('/<lang>/connect', methods=['POST'])
@app.route('/connect', methods=['POST'])
def connect_post(lang = ''):
    c_type = request.form['c_type']
    if c_type == 'login':
        email = request.form['email']
        password = request.form['password']
        
        db_cur.execute(f"""SELECT prenom, nom, email, mot_de_passe FROM abonne WHERE email = "{email}" AND mot_de_passe = "{password}";""")
        results = db_cur.fetchall()
        db.commit()
        
        if len(results) < 1:
            return connect(lang, 'Wrong username or password.')
        else:
            session['email'] = email
            session['password'] = password
            
            return index(lang, f"Welcome {results[0][0]} {results[0][1].upper()}")
        
    elif c_type == 'register':
        email = request.form['email']
        while '"' in email: email = email.replace('"', '')
        password = request.form['password']
        while '"' in password: password = password.replace('"', '')
        firstname = request.form['firstname']
        while '"' in firstname: firstname = firstname.replace('"', '')
        lastname = request.form['lastname']
        while '"' in lastname: lastname = lastname.replace('"', '')
        birthday = request.form['birthday']
        while '"' in birthday: birthday = birthday.replace('"', '')
        address = request.form['address']
        while '"' in address: address = address.replace('"', '')
        zipcode = request.form['zipcode']
        while '"' in zipcode: zipcode = zipcode.replace('"', '')
        city = request.form['city']
        while '"' in city: city = city.replace('"', '')
        
        today = datetime.now().strftime('%Y-%m-%d')
        abo = (datetime.now() + relativedelta(years=1)).strftime('%Y-%m-%d')
        
        db_cur.execute(
            f"""
                INSERT INTO abonne (prenom, nom, date_naissance, adresse, code_postal, ville, date_inscription, date_fin_abo, email, mot_de_passe)
                VALUES ("{firstname.capitalize()}", "{lastname.capitalize()}", "{birthday}", "{address}", "{zipcode}", "{city.upper()}", "{today}", "{abo}", "{email}", "{password}")
            """)
        db.commit()
        
        return connect(lang, 'Successfuly registered, please login now.')

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
