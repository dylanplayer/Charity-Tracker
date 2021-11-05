from flask import Flask
from flask import Flask, render_template, url_for
from pymongo import MongoClient
import os

app = Flask(__name__)

host = os.environ.get('MONGODB_URI')
client = MongoClient()
db = client.get_database('charity-tracker')
users = db.users
charities = db.charities

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login/', methods=['GET',])
def login():
    return render_template('login.html')

@app.route('/register/', methods=['GET',])
def register():
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)