
from flask import Flask, flash, request, redirect, sessions, url_for, render_template, request, session, abort, make_response
from numpy import product
from pandas.core.frame import DataFrame
from werkzeug.utils import secure_filename
import pymongo
import certifi
import pyodbc
#from pymongo import MongoClient
import bcrypt
# from pymongo import Connection
from bson.objectid import ObjectId
#from pymongo import ObjectId
from gridfs import GridFS
from gridfs.errors import NoFile
from io import StringIO
import os
from werkzeug.wrappers import response
import pandas as pd
import json
ALLOWED_EXTENSIONS = set(['csv'])

UPLOAD_FOLDER = 'static\\uploads\\'

session_dict = {
    "first_name": "",
    "last_name": "",
    "email": "",
    "username": "",
    "file_name": "",
    "word_count": "",
    "total_path": ""

}

download_path = "x"


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__)
app.secret_key = "Sessiontest"
#app.config['MONGO_DBNAME'] = 'readfilecount'
app.config['MONGO_URI'] = 'mongodb+srv://root:cloud123@ccfpusers.fk9romi.mongodb.net/test'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#mongo = pymongo(app)
mongo = pymongo.MongoClient(
    "mongodb+srv://root:cloud123@ccfpusers.fk9romi.mongodb.net/test", tlsCAFile=certifi.where())
db = mongo.ccfpusers
fs = GridFS(db)
#db = mongo.get_database('readwords')
record = db.users


# Database Connection
connection = pyodbc.connect(
    Driver='{ODBC Driver 13 for SQL Server};Server=tcp:ccfp.database.windows.net,1433;Database=ccfp;Uid=CloudSA148bc47e;Pwd=ThisSucks!;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
)  # Creating Cursor
cursor = connection.cursor()


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/index')
def index():
    if 'username' in session:
        return render_template('index.html', user_name=session['username'])
    return render_template('home.html')


@app.route("/login", methods=["POST", "GET"])
def login():
    message = 'Please login to your account'
    if "username" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        session.permanent = False
        username = request.form.get("username")
        password = request.form.get("password")

        user_found = record.find_one({"username": username})
        print(user_found)
        if user_found:
            user_val = user_found['username']
            passwordcheck = user_found['password']
            session_dict['firstName'] = user_found['firstName']
            session_dict['lastName'] = user_found['lastName']
            session_dict['email'] = user_found['email']
            session_dict['username'] = user_found['username']
            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):

                session["username"] = user_val
                return redirect(url_for('index'))
            else:
                if "username" in session:

                    return redirect(url_for("index"))

                message = 'Wrong password'
                return render_template('login.html', message=message)
        else:
            message = 'Email not found'
            return render_template('login.html', message=message)
    return render_template('login.html', message=message)


@app.route('/registration/', methods=['POST', 'GET'])
def registration():
    if "username" in session:
        return render_template('index.html')

    error_message = ""
    if request.method == 'POST':
        db = mongo.ccfpusers
        users = db.users
        existing_user = users.find_one({'username': request.form['username']})
        existing_email = users.find_one({'email': request.form['email']})

        if existing_user is None and existing_email is None:
            if request.form['password'] != request.form['confirm_password']:
                flash("Passwords Doesn't Match!")
                return render_template('registration.html')

            hashpass = bcrypt.hashpw(
                request.form['password'].encode('utf-8'), bcrypt.gensalt())
            users.insert_one({
                'firstName': request.form['firstName'],
                'lastName': request.form['lastName'],
                'email': request.form['email'],
                'username': request.form['username'],
                'password': hashpass
            })

            return redirect(url_for('login'))
        #error_message="That username already exists!"
        flash("That username already exists!")
        return render_template('registration.html')

    return render_template('registration.html')


# @app.route('/index/upload/', methods=['GET', 'POST'])
# def upload_file():
#     if request.method == 'POST':
#         file = request.files['file']
#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             user_dir = os.path.join(
#                 app.config['UPLOAD_FOLDER'], session['username'])
#             if os.path.exists(user_dir):
#                 # path where the file is stored
#                 file.save(os.path.join(user_dir, filename))

#             else:
#                 os.mkdir(user_dir)
#                 file.save(os.path.join(user_dir, filename))
#                 print("File Saved 2")
#             file_dir = os.path.join(user_dir, filename)
#             file_dir = file_dir.replace('\\', '?')

#             return redirect(url_for('viewfilecount', file_name=file_dir))
#         else:
#             flash("Invalid Extension")
#             return render_template('index.html')
#     flash("No file Loaded!")
#     return render_template('index.html')


@app.route('/result/<file_name>/')
def viewfilecount(file_name):
    file_name = file_name.replace('?', '/')
    session['file_name'] = file_name
    #file_name = file_name.replace('\\', '/')
    if "username" not in session:
        return redirect(url_for("home"))
    if os.path.exists(file_name):
        print("File Exists")
        print(file_name)

        with open(file_name, 'r', encoding='utf-8') as f:
            content = f.read()
            contents_split = content.split()
            wordcount = len(contents_split)
            print(wordcount)
            split_file_name = file_name.split('/')
            session_dict['file_name'] = split_file_name[-1]
            session_dict['word_count'] = wordcount
            session_dict['total_path'] = file_name
            download_path = file_name
            print(download_path)
            print(session_dict)
    return render_template('result.html', session_dict=session_dict, filename=download_path, user_name=session['username'])


@app.route("/download/")
def download_file():
    print("Hello " + session_dict['total_path'])
    return send_file(session_dict['total_path'], as_attachment=True, environ=request.environ)


@app.route("/logout", methods=["POST", "GET"])
def logout():
    if "username" in session:
        session.pop("username", None)
        return render_template("login.html")
    else:
        return render_template('index.html')


@app.route("/CustomerEngagement")
def customerengagement():
    return render_template('customerEngagement.html')


@app.route("/index/search")
def searchpage():
    return render_template("searchhshd.html")


@app.route("/index/upload")
def uploadpage():
    return render_template("uploaddata.html")


@app.route("/index/searchnumber", methods=["GET", "POST"])
def searchhshd():
    if request.method == 'POST':
        HshdNumber = request.form['hshd']
        #sqlSearchQuery = 'select a.[HSHD_NUM],b.[BASKETNUM],b.[PURCHASE],b.[PRODUCT_NUM],c.[DEPARTMENT],c.[COMMODITY],b.[SPEND],b.[UNITS],b.[STORE_R],b.[WEEK_NUM],b.[YEAR_NUM],a.[L], a.[AGE_RANGE],a.[MARITAL],a.[INCOME_RANGE],a.[HOMEOWNER],a.[HSHD_COMPOSITION],a.[HH_SIZE],a.[CHILDREN] from Households as a inner join Transactions as b inner join Products as c on a.[HSHD_NUM]=b.[HSHD_NUM] and b.[PRODUCT_NUM]=c.[PRODUCT_NUM]'
        #print(sqlSearchQuery)
        #cursor.execute(sqlSearchQuery)
        #data = cursor.fetchall()
        cursor.execute("""SELECT DISTINCT a.HSHD_NUM, b.BASKET_NUM, b.PURCHASE_, b.PRODUCT_NUM, c.DEPARTMENT, c.COMMODITY, b.SPEND, b.UNITS, b.STORE_R, b.WEEEK_NUM, b.YEAR, a.L, a.AGE_RANGE, a.MARITAL, a.INCOME_RANGE, a.HOMEOWNER, a.HSHD_COMPOSITION, a.HH_SIZE, a.CHILDREN
                        FROM Households AS a
                        INNER JOIN Transactions AS b ON (a.HSHD_NUM = b.HSHD_NUM)
                        INNER JOIN Products AS c ON (b.PRODUCT_NUM = c.PRODUCT_NUM)
	                    WHERE a.HSHD_NUM = """+HshdNumber+" ORDER BY a.HSHD_NUM, b.BASKET_NUM, b.PURCHASE_, b.PRODUCT_NUM, c.DEPARTMENT, c.COMMODITY;");
        data = cursor.fetchall()
        connection.commit()

    return render_template('searchhshd.html', data=data)


@app.route("/uploadfiles/", methods=["GET", "POST"])
def uploaddata():
    if request.method == "POST":
        householdfile = request.files['householdfile']
        transactionfile = request.files['transactionfile']
        productsfile = request.files['productsfile']
        if householdfile and allowed_file(householdfile.filename) and transactionfile and allowed_file(transactionfile.filename) and productsfile and allowed_file(productsfile.filename):
            householddata = pd.read_csv(householdfile)
            transactiondata = pd.read_csv(transactionfile)
            productsdata = pd.read_csv(productsfile)

            householddf = pd.DataFrame(householddata)
            transactiondf = pd.DataFrame(transactiondata)
            productsdf = pd.DataFrame(productsdata)
            
            for row in householddf.itertuples():
                    cursor.execute(
                    """INSERT INTO households (HSHD_NUM,L,AGE_RANGE,MARITAL,INCOME_RANGE,HOMEOWNER,HSHD_COMPOSITION,HH_SIZE,CHILDREN) VALUES (?,?,?,?,?,?,?,?,?)""",
                    (int(row.HSHD_NUM), str(row.L), str(row.AGE_RANGE), str(row.MARITAL),
                     str(row.INCOME_RANGE), str(row.HOMEOWNER), str(row.HSHD_COMPOSITION),
                     str(row.HH_SIZE), str(row.CHILDREN)))
              

            for row in transactiondf.itertuples():
                    cursor.execute(
                    """INSERT INTO transactions (BASKET_NUM,HSHD_NUM,PURCHASE_,PRODUCT_NUM,SPEND,UNITS,STORE_R,WEEEK_NUM,YEAR) VALUES (?,?,?,?,?,?,?,?,?)""",
                    (int(row.BASKET_NUM), int(row.HSHD_NUM), str(row.PURCHASE_),
                     int(row.PRODUCT_NUM), int(row.SPEND), int(row.UNITS), str(row.STORE_R),
                     int(row.WEEEK_NUM), int(row.YEAR)))

            for row in productsdf.itertuples():
                    cursor.execute("""INSERT INTO products (PRODUCT_NUM,DEPARTMENT,COMMODITY,BRAND_TY,NATURAL_ORGANIC_FLAG) VALUES (?,?,?,?,?)""",
                    (int(row.PRODUCT_NUM), str(row.DEPARTMENT), str(row.COMMODITY),str(row.BRAND_TY),
                     str(row.NATURAL_ORGANIC_FLAG)))

            return render_template("uploaddata.html")


@app.route("/sampledatapull")
def sampledatapull():
    cursor.execute("""SELECT DISTINCT a.HSHD_NUM, b.BASKET_NUM, b.PURCHASE_, b.PRODUCT_NUM, c.DEPARTMENT, c.COMMODITY, b.SPEND, b.UNITS, b.STORE_R, b.WEEEK_NUM, b.YEAR, a.L, a.AGE_RANGE, a.MARITAL, a.INCOME_RANGE, a.HOMEOWNER, a.HSHD_COMPOSITION, a.HH_SIZE, a.CHILDREN
                        FROM Households AS a
                        INNER JOIN Transactions AS b ON (a.HSHD_NUM = b.HSHD_NUM)
                        INNER JOIN Products AS c ON (b.PRODUCT_NUM = c.PRODUCT_NUM)
	                    WHERE a.HSHD_NUM LIKE '%0010%' ORDER BY a.HSHD_NUM, b.BASKET_NUM, b.PURCHASE_, b.PRODUCT_NUM, c.DEPARTMENT, c.COMMODITY;""")
    data = cursor.fetchall()
    connection.commit()

    return render_template('searchhshd.html', data=data)


app.run(debug=True, host="localhost")
