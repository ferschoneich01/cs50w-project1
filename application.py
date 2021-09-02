import os
import re
import requests
import json
from flask import Flask, session, render_template, url_for, request, flash, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from funciones import login_required
from werkzeug.security import check_password_hash, generate_password_hash

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
@login_required
def index():
    books=[]
    characters = "('),"
    #seleccion del top 5 libros
    libros = db.execute("SELECT isbn FROM books ORDER BY isbn LIMIT 5").fetchall()
    for libro in libros:
        print(libro)
        isbn = libro
        isbn = re.sub("\!|\'|\?|\(|\(|\,","",isbn)  
        print(isbn)      
        res = requests.get("https://www.googleapis.com/books/v1/volumes?q=isbn:"+isbn)
        data = res.json()
        items = data["items"]
        encoded = json.dumps(items)
        decode = json.loads(encoded)

        print("llego")
        books.append([decode[0]["volumeInfo"]["title"],decode[0]["volumeInfo"]["imageLinks"]["smallThumbnail"],decode[0]["volumeInfo"]["authors"],decode[0]["volumeInfo"]["averageRating"]])
        #book = decode[0]["volumeInfo"]
        
        #categories = decode[0]["volumeInfo"]["categories"]
    for book in books:
        print(book[0])    
    #Obtencion del nombre de usuario
    idUser=session.get("id_user")
    id=str(idUser)
    user = db.execute("SELECT * FROM Users WHERE id_user = "+id).fetchall()
    
    return render_template('books.html',username = user[0]["username"],books=books)

#Cerrar sesion

@app.route("/logout", methods=["GET","POST"])
def logout():
    session.clear()
    return redirect("/")

@app.route("/login", methods=["POST","GET"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return "Ingrese un nombre de usuario"

        # Ensure password was submitted
        elif not request.form.get("password"):
            return "Ingrese una contraseña"

        #nomrbre de usuario ingresado
        username = request.form.get("username")
        
        # Query database for username
        rows = db.execute("SELECT * FROM Users WHERE Username = '"+username+"'").fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return "Contraseña Incorrecta"


        # Remember which user has logged in
        session["id_user"] = rows[0]["id_user"]
        
        # Redirect user to home page
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/register", methods=["POST","GET"])
def register():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return "Ingrese un nombre de usuario"

        # Ensure password was submitted
        elif not request.form.get("password"):
            return "Ingrese una contraseña"

        elif not request.form.get("Correo"):
            return "Ingrese un correo"

        #nomrbre de usuario ingresado
        username = request.form.get("username")
        password = generate_password_hash(request.form.get("password"))
        email = request.form.get("Correo")
        
        # Query database for username
        db.execute("INSERT INTO Users (username,password,email) VALUES ('"+str(username)+"','"+str(password)+"','"+str(email)+"')")
        db.commit()
        print("USUARIO REGISTRADO")
        # Redirect user to home page
        
        return redirect("/")
    else:
        return render_template("register.html")