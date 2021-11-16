from flask import Flask, render_template, url_for, request, make_response, session
from pymongo import MongoClient
from datetime import datetime, timedelta
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
        return redirect('/dashboard/')
    else:
        return render_template('register.html')

@app.route('/dashboard/')
def dashboard():
    if session.get('email') and session.get('password'):
        email = session['email']
        password = session['password']
        user = users.find_one({"$and": [{'email': email}, {'password': password}]})
        if user:
            recent_donations = []
            for donation_id in user['donations']:
                donation = donations.find_one({'_id': donation_id})
                charity = charities.find_one({'_id': ObjectId(donation['charity_id'])})
                donation['total_impact'] = int(donation['amount']) * int(charity['impact_per_dollar'])
                recent_donations.append(
                    {
                        'donation': donation,
                        'charity': charity,
                    }
                )

            recent_donations.reverse()
            
            user['lifetime'] = 0
            for donation in recent_donations:
                user['lifetime'] += float(donation['donation']['amount'])
            
            user['year_to_date'] = 0
            for donation in recent_donations:
                now = datetime.now()
                one_year_ago = now - timedelta(days=365)
                if donation['donation']['created_at'] >= one_year_ago:
                    user['year_to_date'] += float(donation['donation']['amount'])

            user['month_to_date'] = 0
            for donation in recent_donations:
                now = datetime.now()
                one_month_ago = now - timedelta(days=31)
                if donation['donation']['created_at'] >= one_month_ago:
                    user['month_to_date'] += float(donation['donation']['amount'])

            return render_template('dashboard.html', user=user, recent_donations=recent_donations)
        else:
            return redirect('/login')
    else:
        return redirect('/login')

@app.route('/charity/<id>', methods=['GET'])
def get_charity(id):
    charity = charities.find_one({'_id': ObjectId(id)})
    email = session['email']
    password = session['password']
    user = users.find_one({"$and": [{'email': email}, {'password': password}]})
    return render_template('charity.html', charity=charity, user=user) 

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
    return redirect('/charity/' + str(charities.find_one({'created_at': charity['created_at']})['_id']))

@app.route('/charity/new', methods=['GET'])
def get_create_charity_form():
    return render_template('new_charity_form.html')

@app.route('/charities/', methods=['GET'])
def charitiesList():
    if request.method == 'GET':
        return render_template('charities.html', charities=charities.find())

@app.route('/donate/', methods=['POST'])
def donate():
    if request.method == 'POST':
        email = session['email']
        password = session['password']
        user = users.find_one({"$and": [{'email': email}, {'password': password}]})
        donation = {
            'charity_id': request.form.get('charity'),
            'user_id': user['_id'],
            'amount': request.form.get('amount'),
            'created_at': datetime.now(),
        }
        donations.insert_one(donation)
        donation = donations.find_one({'created_at': donation['created_at']})
        users.update_one(
            {'_id': user['_id']},
            {'$push': {'donations': donation['_id']}}
        )
        charities.update_one(
            {'_id': donation['charity_id']},
            {'$push': {'donations': donation['_id']}}
        )
        return redirect('/dashboard/')

@app.route('/logout/')
def logout():
    session['email'] = ''
    session['password'] = ''
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)