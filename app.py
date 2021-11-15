from flask import Flask, render_template, url_for, request, make_response, session
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import bcrypt
import os

from werkzeug.utils import redirect

app = Flask(__name__)

app.secret_key = os.environ.get('SECRET')

host = os.environ.get('MONGODB_URI')
salt = os.environ.get('SECRET')
client = MongoClient(host=host)
db = client.get_database('charity-tracker')
users = db.users
charities = db.charities
donations = db.donations

@app.route('/')
def index():
    if session.get('email') and session.get('password'):
        return redirect('/dashboard')
    return render_template('index.html')

@app.route('/login/', methods=['GET','POST'])
def login():
    if (request.method == 'POST'):
        email = request.form.get('email')
        password = bcrypt.hashpw(request.form.get('password').encode('UTF-8'), salt.encode('UTF-8'))
        user = users.find_one({"$and": [{'email': email}, {'password': password}]})
        if user:
            session['email'] = user['email']
            session['password'] = user['password']
            return redirect('/dashboard')
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')

@app.route('/register/', methods=['GET','POST'])
def register():
    if (request.method == 'POST'):
        user = {
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'email': request.form.get('email'),
            'password': bcrypt.hashpw(request.form.get('password').encode('UTF-8'), salt.encode('UTF-8')),
            'donations': [],
            'created_at': datetime.now(),
        }
        users.insert_one(user)
        session['email'] = user['email']
        session['password'] = user['password']
        return redirect('/dashboard')
    else:
        return render_template('register.html')

@app.route('/dashboard/')
def dashboard():
    if session.get('email') and session.get('password'):
        email = session['email']
        password = session['password']
        user = users.find_one({"$and": [{'email': email}, {'password': password}]})
        recent_donations=[]
        if user:
            return render_template('dashboard.html', user=user, recent_donations=recent_donations)
        else:
            return redirect('/login')
    else:
        return redirect('/login')

@app.route('/charity/<id>', methods=['GET'])
def get_charity(id):
    charity = charities.find_one({'_id': ObjectId(id)})
    return render_template('charity.html', charity=charity) 

@app.route('/charity/', methods=['POST'])
def create_charity():
    charity = {
        'name': request.form.get('name'),
        'banner': request.form.get('banner'),
        'dollar_per_impact': request.form.get('dollar_per_impact'),
        'impact_per_dollar': request.form.get('impact_per_dollar'),
        'unit_of_impact': request.form.get('unit_of_impact'),
        'impact_sentance': request.form.get('impact_sentance'),
        'description': request.form.get('description'),
        'donations': [],
        'created_at': datetime.now(),
    }
    charities.insert_one(charity)
    return redirect('/charity/' + {charities.find_one({'created_at': charity['created_at']})._id})

@app.route('/charity/new', methods=['GET'])
def get_create_charity_form():
    return render_template('new_charity_form.html')

if __name__ == '__main__':
    app.run(debug=True)