from flask import Flask, render_template, url_for, request, make_response
from pymongo import MongoClient
from datetime import datetime
import bcrypt
import os

from werkzeug.utils import redirect

app = Flask(__name__)

host = os.environ.get('MONGODB_URI')
salt = os.environ.get('SECRET')
client = MongoClient()
db = client.get_database('charity-tracker')
users = db.users
charities = db.charities

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login/', methods=['GET','POST'])
def login():
    if (request.method == 'POST'):
        user = {
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'email': request.form.get('email'),
            'password': bcrypt.hashpw(request.form.get('first_name')),
            'created_at': datetime.now(),
        }
        users.insert_one(user)
        response = make_response(redirect('/dashboard/'))
        response.set_cookie('_id', users.find_one({'email': request.form.get('email'), 'password': bcrypt.hashpw(request.form.get('first_name'))})._id)
        return response
    else:
        return render_template('login.html')
    

@app.route('/register/', methods=['GET',])
def register():
    return render_template('register.html')

@app.route('/dashboard/')
def dashboard():
    if '_id' in request.cookies:
        _id = request.cookies.get('_id')
    else:
        redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)