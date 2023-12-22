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
        pass
    else:
        if email != None and password != None:
            firstname = ''
            lastname = ''
            db_cur.execute(f"""SELECT prenom, nom, date_naissance, adresse, code_postal, ville, date_inscription, date_fin_abo, email, mot_de_passe, gestionnaire FROM abonne WHERE email = "{email}" AND mot_de_passe = "{password}";""")
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
            admin = True if results[0][10] == 1 else False
            
            return render_template('en/account.html', firstname=firstname, lastname=lastname, endsub2=endsub2, email=email, password=password, birthday=birthday, address=address, zipcode=zipcode, city=city, regdate=regdate, endsub=endsub, admin=admin)
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
    email = request.form['email']
    password = request.form['password']
    
    db_cur.execute(f"""SELECT prenom, nom, email, mot_de_passe FROM abonne WHERE email = "{email}" AND mot_de_passe = "{password}";""")
    results = db_cur.fetchall()
    db.commit()
    
    if len(results) < 1:
        if lang == 'fr':
            return connect(lang, 'Email ou Mot de Passe incorrect.')
        else:
            return connect(lang, 'Wrong email or password.')
    else:
        session['email'] = email
        session['password'] = password
        
        if lang == 'fr':
            return index(lang, f"Bienvenue {results[0][0]} {results[0][1].upper()}")
        else:
            return index(lang, f"Welcome {results[0][0]} {results[0][1].upper()}")
            

@app.route('/<lang>/search', methods=['POST'])
@app.route('/search', methods=['POST'])
def search(lang = ''):
    name = request.form['query']
    while '"' in name: name = name.replace('"', '')
    try:
        author = request.form["author"]
        while '"' in author: author = author.replace('"', '')
    except: author = None
    try: 
        editor = request.form['editor']
        while '"' in editor: editor = editor.replace('"', '')
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
    
    rf = [
        '<tr><td class="result-title">',
        '</td><td class="result-author">',
        '</td><td class="result-editor">',
        '</td><td class="result-last-borrow">',
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
            (
                SELECT MAX(emprunt.date_emprunt)
                FROM emprunt
                WHERE emprunt.id_livre = livre.id
            ),
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
        if str(results[i][4]) == 'Available' :
            cond = True
        elif str(results[i][4]) == 'Not Available' :
            cond = False
        else:
            cond = results[i][4]
        results[i] = [results[i][0], results[i][1], results[i][2], results[i][3], cond ]
    
    
        
    
    for i in range(len(results)):
        if lang == 'fr':
            availability = (af[0] + 'Disponible') if results[i][4] else (af[1] + 'Non Disponible')
        else:
            availability = (af[0] + 'Available') if results[i][4] else (af[1] + 'Not Available')
        
        results[i] = rf[0] + results[i][0] + rf[1] + results[i][1] + rf[2] + results[i][2] + rf[3] + results[i][3].strftime('%d/%m/%Y') + rf[4] + availability + rf[5]
    
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

@app.route('/<lang>/search/sub')
@app.route('/search/sub')
def search_sub(lang = ''):
    results = '</table>'
    if lang == 'fr':
        return render_template('fr/search-sub.html', results=results, cursor=0)
    else:
        return render_template('en/search-sub.html', results=results, cursor=0)

@app.route('/<lang>/search/sub', methods=['POST'])
@app.route('/search/sub', methods=['POST'])
def search_sub_post(lang = ''):
    firstname = request.form['firstname']
    while '"' in firstname: firstname = firstname.replace('"', '')
    try:
        lastname = request.form["lastname"]
        while '"' in lastname: lastname = lastname.replace('"', '')
    except: lastname = None
    try: 
        city = request.form['city']
        while '"' in city: city = city.replace('"', '')
    except: city = None
    if request.form.get('expired'):
        expired = True
    else:
        expired = False
    
    try: curr_page = int(request.form['page'])
    except: curr_page = 0
    
    rf = [
        '<tr><td class="result-lastname">',
        '</td><td class="result-firstname">',
        '</td><td class="result-city">',
        '</td><td class="result-birthday">',
        '</td><td class="result-end-sub">',
        '</td></tr>'
    ]
    
    query = f"""
        SELECT
            nom,
            prenom,
            ville,
            date_naissance,
            date_fin_abo
        FROM
            abonne
        WHERE
            LOWER(nom) LIKE '%{lastname.lower()}%'
    """

    if firstname != None and firstname != '':
        query += f"""        AND LOWER(prenom) LIKE '%{firstname.lower()}%'"""
    if city != None and city != '':
        query += f"""        AND LOWER(ville) LIKE '%{city.lower()}%'"""
    if expired:
        query += f"""        AND (date_fin_abo IS NULL OR date_fin_abo < CURDATE())"""

    offset = str(curr_page * 20 if curr_page != None else 0)
    max_per_page = '20'
    query += f'LIMIT {offset}, {max_per_page};'
    
    db_cur.execute(query)
    results = db_cur.fetchall()
    db.commit()
    
    for i in range(len(results)):
        results[i] = rf[0] + results[i][0] + rf[1] + results[i][1] + rf[2] + results[i][2] + rf[3] + results[i][3].strftime('%d/%m/%Y') + rf[4] + results[i][4].strftime('%d/%m/%Y') + rf[5]
    
    if len(results) <= 0:
        results = '</table>'
    else:
        results = ''.join(results) + '</table>'
    
    if expired:
        expired = 'checked'
    else:
        expired = ''
    lastname = lastname if lastname != None else ''
    firstname = firstname if firstname != None else ''
    city = city if city != None else ''
    
    if lang == 'fr':
        return render_template('fr/search-sub.html', results=results, lastname=lastname, firstname=firstname, city=city, expired=expired, curr_page=curr_page, cursor=curr_page+1, cp="changePage('p')", cn="changePage('n')")
    else:
        return render_template('en/search-sub.html', results=results, lastname=lastname, firstname=firstname, city=city, expired=expired, curr_page=curr_page, cursor=curr_page+1, cp="changePage('p')", cn="changePage('n')")

@app.route('/<lang>/disconnect')
@app.route('/disconnect')
def disconnect(lang = ''):
    session.clear()
    if lang == 'fr':
        return redirect('/fr')
    else:
        return redirect('/')


if __name__ == '__main__':
    args = argParser.parse_args()
    prod = args.prod
    
    if prod:
        serve(app, host=IP, port=PORT)
        sys.exit()
    else:
        app.run(host=IP, port=PORT, debug=True)
        sys.exit()
