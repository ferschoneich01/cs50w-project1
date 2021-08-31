import os
import requests
import json
from flask import Flask, session, render_template, url_for, request, flash, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


    

@app.route("/")
def index():
    isbn='080213825X'
    res = requests.get("https://www.googleapis.com/books/v1/volumes?q=isbn:"+isbn)
    data = res.json()
    items = data["items"]
    encoded = json.dumps(items)
    decode = json.loads(encoded)

    return decode[0]["volumeInfo"]["title"]

@app.route("/login", methods=["POST","GET"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Ingrese un nombre de usuario")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Ingrese una contraseña")

        
        # Query database for username
        rows = db.execute("SELECT * FROM Users WHERE Username = :username",username=request.form.get("username")).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not rows[0]["password"] == request.form.get("password"):
            return "Contraseña Incorrecta"


        # Remember which user has logged in
        session["id_user"] = rows[0]["id_user"]

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("login.html")
