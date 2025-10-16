from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import pickle


with open(r'ml_models\model.pkl', 'rb') as f:
    model_18_21 = pickle.load(f)

with open(r'ml_models\xgb_model .pkl', 'rb') as f:
      model_22_60  = pickle.load(f)


app = Flask(__name__)
app.secret_key = "my_secret_key"

# Database config (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Mental_Stress.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(30), nullable=False)
    gender = db.Column(db.String(3))
    age = db.Column(db.Integer)
    occupation = db.Column(db.String(50))

    # Quiz answers + prediction
    q1 = db.Column(db.Integer)
    q2 = db.Column(db.Integer)
    q3 = db.Column(db.Integer)
    
    prediction = db.Column(db.String(50))


with app.app_context():
    db.create_all()



# Test prediction with fake data
sample_input = [[0]*20]  # 195 zeros to match model features
  # 20 zeros as placeholder
  # replace with correct number of features
print("18-21 model prediction:", model_18_21.predict(sample_input))
# print("22-60 model prediction:", model_22_60.predict(sample_input))
