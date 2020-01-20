import os
import requests
import urllib.parse
import csv
import secrets

from flask import redirect, render_template, request, session
from functools import wraps
from time import gmtime, strftime
from cs50 import SQL

dbz = SQL("sqlite:///plane-side.db")

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def checkvote(uid, aid):
    d = dbz.execute(f"SELECT * FROM votes WHERE userid={uid} AND id={aid};")
    print (d)
    if d == []:  
        return False
    elif d[0]["userid"] is uid and d[0]["id"] is aid:
        return True
    else: 
        return False

def sidechar(side):
    if side == 1:
        return "Left"
    elif side == 2: 
        return "Right"
    else:
        return "Invalid Side Server Error"

def bestside(aid):
    d = dbz.execute(f"SELECT * FROM votes WHERE id ={aid};")

    if d == []:
        return None
    else: 
        left = int(dbz.execute(f"SELECT count(*) FROM votes WHERE id={aid} AND side=1")[0]['count(*)'])
        right = int(dbz.execute(f"SELECT count(*) FROM votes WHERE id={aid} AND side=2")[0]['count(*)'])

        print (left, "=================================", right)

        if left > right:
            return 1
        elif left < right:
            return 2
        elif left == right:
            return 3
        else:
            return 4

def tuplemaker(): #automate tuple making for choices in Country form. 
    air = {}

    with open("airports.csv") as airports: 
        csv_reader = csv.reader(airports, delimiter=',')
        for row in csv_reader: 
            key = row[1]
            if key not in air: 
                air[key] = []
                air[key].append([row[3], row[1]])
            else: 
                air[key].append([row[3], row[1]])
    
    d = []
    for key, value in air.items():
        d.append((key, key))

    return tuple(d)

def apikeymaker(uid):
    d = int(dbz.execute(f"SELECT count(*) FROM API WHERE uid={uid}")[0]['count(*)'])

    if d > 0:
        return None
    else:
        key = str(secrets.token_urlsafe(32))
        dbz.execute (f"INSERT INTO API(uid, key, requests) VALUES ({uid}, '{key}', 500);")
        return key

def checkkey(key):
    check = dbz.execute(f"SELECT * FROM API WHERE key='{key}';")

    if check == []:
        return 3 # Code for Invalid Key 
        
    check = int(check[0]["requests"])

    if check > 0:
        return 1 # Code for Valid Key with Available Requests 
    if check == 0:
        return 2 # Code for Valid Key with no Available Requests 

def checkairport(iata):
    check = dbz.execute(f"SELECT * FROM Country WHERE iata='{iata}';")
    if check == []:

        return False
    else: 
        return True