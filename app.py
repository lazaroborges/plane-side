import os
import csv

from cs50 import SQL
from flask_sqlalchemy import SQLAlchemy 
from flask import Flask, flash, jsonify, redirect, render_template, request, session, safe_join, abort
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm 
from wtforms import SelectField

from helpers import apology, login_required, checkvote, sidechar, bestside, tuplemaker, apikeymaker, checkkey, checkairport

# Configure application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///plane-side.db'
app.config['SECRET_KEY'] = 'secret'

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
dbz = SQL("sqlite:///plane-side.db") # CS50 SQLite Flavor COnnection 
db = SQLAlchemy(app) # Standard SQLite Alchemy Connection

class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(20))
    name = db.Column(db.String(50))
    iata = db.Column(db.String(3))

class Form(FlaskForm):

    country = SelectField('country', choices=tuplemaker()) # it passes a list of tuples 
    airport = SelectField('airport', choices=[])
    iata = SelectField('iata', choices=[])

@app.route("/vote", methods=["GET", "POST"])
@login_required
def vote():
    form = Form()
    form.airport.choices = [(airport.id, airport.name) for airport in Country.query.filter_by(country='Afghanistan').all()]

    if request.method == 'POST':
        airport = Country.query.filter_by(id=form.airport.data).first()
        side = int(request.form.get("side")) #1 for left, 2 for right
        uid = session.get("user_id") #get that userID
        aid = airport.id #airport id 
        print ("----------------------------", airport.id, airport.iata, request.form.get("side"), type(request.form.get("side")))

        if checkvote(uid, aid) is True: 
            return '<h1>You already voted on {} @ {}</h1>'.format(airport.name, form.country.data)
        else:
            dbz.execute (f"INSERT INTO votes(userid, id, side) VALUES ({uid}, {aid}, {side});")
            return '<h1>You successfully voted on {} @ {} as {}</h1>'.format(airport.name, form.country.data, sidechar(side))

    return render_template("report.html", form=form)


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    form = Form()
    form.airport.choices = [(airport.id, airport.name) for airport in Country.query.filter_by(country='Afghanistan').all()]


    if request.method == 'POST':
        airport = Country.query.filter_by(id=form.airport.data).first()
        aid = airport.id #airport id
        best = bestside(aid)
        
        if best == 1: 
            return '<h1>The best side is the left side</h1>'
        elif best == 2: 
            return '<h1>The best side is the right side</h1>'
        
    return render_template("search.html", form=form)

 

@app.route('/airport/<country>')
def airport(country):
    airports = Country.query.filter_by(country=country).all()

    airportArray = []

    for airport in airports:
        airportObj = {}
        airportObj['id'] = airport.id
        airportObj['name'] = airport.name
        airportArray.append(airportObj)

    return jsonify({'airports' : airportArray})

@app.route('/api/', methods=["GET"])
def apirequest():
    key = request.args.get('key')
    iata = request.args.get('iata')
    checkedkey = checkkey(key)
    
    if checkedkey is 3:        
        return jsonify(str("Invalid Key."))
    elif checkedkey is 2: 
        return jsonify(str("No more requests available."))
    else: 
        if checkairport(iata) == False:
            return jsonify({f"{iata}": "Airport Not Found"}), 422
        else: 
            best = bestside(dbz.execute(f"SELECT (id) FROM Country WHERE iata='{iata}';")[0]["id"])

            requests = int(dbz.execute(f"SELECT requests FROM API WHERE key='{key}';")[0]["requests"]) - 1
            dbz.execute(f"UPDATE API SET requests={requests} WHERE key='{key}';")

            if best == 1: 
                return jsonify({f"{iata}": "Left"})
            elif best == 2: 
                return jsonify({f"{iata}": "Right"})
            elif best == 3: 
                return jsonify({f"{iata}": "tie"})
            else: 
                return jsonify({f"{iata}": "no votes available yet!"}), 422

    

@app.route("/api-key", methods=["GET", "POST"])
@login_required
def apikey():
    if request.method == 'GET':
        return render_template("api-key.html")

    if request.method == 'POST':
        uid = session.get("user_id") #get that userID
        d = apikeymaker(uid)
        if d is None: 
            key = dbz.execute (f"SELECT * FROM API WHERE uid={uid};")
            key = key[0]
            print ("\n", key, "\n")
            return render_template("api-key2.html", key=key)
        else: 
            key = dbz.execute (f"SELECT * FROM API WHERE uid={uid};")
            key = key[0]
            print ("\n", key, "\n")
            return render_template("api-key2.html", key=key)



@app.route("/")
@login_required
def index():    
    return redirect ("/vote")



@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    return jsonify("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = dbz.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            email = request.form.get("email")
            confirmation = request.form.get("confirmation")

            ## Query DB for userlist name and append them to a list (because this library )
            usernameSquery = dbz.execute (f"SELECT username FROM users;")
            usernameslist = list()
            for x in usernameSquery:
                usernameslist.append(x["username"])

            if request.form.get("password") != request.form.get("confirmation"):
                return apology ("Type Same Password!", 400)
            elif username == "":
                return apology ("Empty Username!", 400)
            elif password == "" or confirmation == "":
                return apology ("Empty Password!", 400)
            elif username in usernameslist:
                return apology ("Username already in use", 400)
            else:
                hashed = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

                dbz.execute("INSERT INTO users(username, hash, email) VALUES (:user, :hashd, :email)", user=username, hashd=hashed, email=email)

                return redirect ("/login")
    else:
        return render_template("register.html"), 200


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
