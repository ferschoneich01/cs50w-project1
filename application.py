import os
import requests
import json
from flask import Flask, session, render_template, url_for, request, flash, redirect,jsonify
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
    isbn=[]
    #seleccion del top 12 libros
    libros = ["1451648537","1442468351","0446679097","0385339097",
    "0812995341","1423121309","0061053562","0345379063",
    "0765326264","0446611212","0345519515","1423108760"]
    #Impresion de los libros
    for libro in libros:
        isbn = libro;
        res = requests.get("https://www.googleapis.com/books/v1/volumes?q="+isbn)
        data = res.json()
        items = data["items"]
        encoded = json.dumps(items) 
        decode = json.loads(encoded)
        try:
                rate = decode[0]["volumeInfo"]["averageRating"]       
        except Exception:
                rate = "0"
        books.append([decode[0]["volumeInfo"]["title"],decode[0]["volumeInfo"]["imageLinks"]["smallThumbnail"],rate])
        
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
            flash('Ingrese un nombre de usuario')
            return redirect("/login")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash('Ingrese una contraseña')
            return redirect("/login")

        #nomrbre de usuario ingresado
        username = request.form.get("username")
        
        # Query database for username
        rows = db.execute("SELECT * FROM Users WHERE Username = '"+username+"'").fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            flash('Contraseña Incorrecta')
            return redirect("/login")


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
            flash("Ingrese un nombre de usuario")
            

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Ingrese una contraseña")

        elif not request.form.get("Correo"):
            flash("Ingrese un correo")

        #nomrbre de usuario ingresado
        username = request.form.get("username")
        password = generate_password_hash(request.form.get("password"))
        email = request.form.get("Correo")
        
        # Query database for username
        db.execute("INSERT INTO Users (username,password,email) VALUES ('"+str(username)+"','"+str(password)+"','"+str(email)+"')")
        db.commit()
        # Redirect user to home page
        
        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/search", methods=["GET","POST"])
@login_required
def search():
    return render_template('search.html')

@app.route("/searchResult", methods=["POST"])
@login_required
def searchResult():
    flag = True
    #books=[]
    value = request.form.get("search")
    book = db.execute("SELECT * FROM books WHERE isbn = '"+str(value)+"'").fetchall()
    if len(book) != 0:
        res = requests.get("https://www.googleapis.com/books/v1/volumes?q="+str(value))
        data = res.json()
        items = data["items"]
        encoded = json.dumps(items)
        
        decode = json.loads(encoded)

        autor = decode[0]["volumeInfo"]["authors"]
        titulo = decode[0]["volumeInfo"]["title"]
        linkImg=decode[0]["volumeInfo"]["imageLinks"]["smallThumbnail"]
        categoria = decode[0]["volumeInfo"]["categories"]
        try:
            descripcion = decode[0]["volumeInfo"]["description"]
            if len(descripcion) > 400:
                descripcion = descripcion[0:400]+"..."
                   
        except Exception:
            descripcion = "Not description"

        try:
            rate = decode[0]["volumeInfo"]["averageRating"]       
        except Exception:
            rate = "0"
        rates_commits = db.execute("SELECT * FROM user_rate WHERE id_book = '"+str(value)+"'").fetchall()
        return render_template('searchResult.html',isbn=value,titulo=titulo,linkImg=linkImg,autor=autor,categoria=categoria,descripcion=descripcion,rate=rate,rates_commits=rates_commits)
    else:
        isbn = db.execute("SELECT isbn FROM books WHERE title = '"+str(value)+"'").fetchall()
        if len(isbn) != 0:
            res = requests.get("https://www.googleapis.com/books/v1/volumes?q="+str(isbn))
            data = res.json()
            items = data["items"]
            encoded = json.dumps(items)
            
            decode = json.loads(encoded)

            autor = decode[0]["volumeInfo"]["authors"]
            titulo = decode[0]["volumeInfo"]["title"]
            linkImg=decode[0]["volumeInfo"]["imageLinks"]["smallThumbnail"]
            categoria = decode[0]["volumeInfo"]["categories"]
            try:
                descripcion = decode[0]["volumeInfo"]["description"]
                if len(descripcion) > 400:
                    descripcion = descripcion[0:400]+"..."      
            except Exception:
                descripcion = "Not description"

            try:
                rate = decode[0]["volumeInfo"]["averageRating"]       
            except Exception:
                rate = "0"
            #extraemos valoraciones y comentarios
            rates_commits = db.execute("SELECT * FROM user_rate WHERE id_book = '"+str(isbn)+"'").fetchall()
            return render_template('searchResult.html',isbn=isbn,titulo=titulo,linkImg=linkImg,autor=autor,categoria=categoria,descripcion=descripcion,rate=rate,rates_commits=rates_commits)
        else:
            flash('No se encontro el libro')
            return redirect("/search")
             
@app.route("/addComment/<isbn>", methods=["POST"])
@login_required
def addComment(isbn):
        rate = request.form.get("rate")
        comment = request.form.get("comment")
        username = db.execute("SELECT username FROM Users WHERE id_user = "+str(session["id_user"])+"").fetchall()
        username = f"%{username}%"
        print(username)        
        # Query database for username
        #db.execute("INSERT INTO user_rate (rate,comment,id_user,id_book,username) VALUES ("+str(rate)+",'"+str(comment)+"',"+str(session["id_user"])+",'"+str(isbn)+"','"+str(username)+"')")
        #db.commit()
        return redirect("/search")