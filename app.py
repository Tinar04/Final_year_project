from flask import Flask, render_template,jsonify, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import pickle
import os
from advice_func import get_advice_18_21
import random
import numpy
import pandas as pd
# from catboost import CatBoostClassifier

# from advice_func import get_advice_18_21, get_advice_22_60



with open(r'ml_models\model.pkl', 'rb') as f:
    model_18_21 = pickle.load(f)

with open(r'ml_models\preprocess_pipeline.pkl', 'rb') as f:
    preprocess_pipeline = pickle.load(f)

with open(r'ml_models\cat_model.pkl', 'rb') as f:
    cat_model = pickle.load(f)

with open(r'ml_models\preprocess_pipeline(18-21).pkl', 'rb') as f:
    preprocess_pipeline_18_21 = pickle.load(f)

app = Flask(__name__)
app.secret_key = "my_secret_key"




# Database config (SQLite)
db_path = os.path.join(os.getcwd(), "Mental_Stress.db")
app.config['SQLALCHEMY_DATABASE_URI'] =f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# user model schema

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

    def __repr__(self):
         return f"{self.age},{self.username}"

# database
with app.app_context():
    db.create_all()
print("Database file exists:", os.path.isfile("Mental_Stress.db"))


# basic detail route
@app.route('/basic_details',methods=['GET','POST'])
def basic_details():
    if request.method == 'POST':
        gender = request.form['gender']
        age = int(request.form['age'])
        occupation = request.form['occupation']

        # updating database
        user = User.query.get(session['user_id'])
        user.gender = gender
        user.age = age
        user.occupation = occupation
        db.session.commit()

    # the age condition
    if age >= 18 and age <= 21:
        return redirect(url_for('quiz_18_21'))
    else:
        return redirect(url_for('quiz_22_60'))
    
    return render_template('basic_details.html')

# quize 18-21 route
@app.route('/quiz_18_21',methods=['GET','POST'])
def quiz_18_21():
    if request.method == 'POST':
    #   collecting user inputs
       user_input = {
            'anxiety_level': request.form['anxiety_level'],
            'self_esteem': request.form['self_esteem'],
            'mental_health_history': request.form['mental_health_history'],
            'depression': request.form['depression'],
            'headache': request.form['headache'],
            'blood_pressure': request.form['blood_pressure'],
            'sleep_quality': request.form['sleep_quality'],
            'breathing_problem': request.form['breathing_problem'],
            'noise_level': request.form['noise_level'],
            'living_conditions': request.form['living_conditions'],
            'safety': request.form['safety'],
            'basic_needs': request.form['basic_needs'],
            'academic_performance': request.form['academic_performance'],
            'study_load': request.form['study_load'],
            'teacher_student_relationship': request.form['teacher_student_relationship'],
            'future_career_concerns': request.form['future_career_concerns'],
            'social_support': request.form['social_support'],
            'peer_pressure': request.form['peer_pressure'],
            'bullying': request.form['bullying'] 
       }
       
       df = pd.DataFrame([user_input])
     # preprocessing
       df = preprocess_pipeline_18_21.transform(df)
     # prediction 
       result = model_18_21.predict(df)[0]
     #personalized advice
       advice_list = get_advice_18_21(user_input,result)
      # result in bd
       user = User.query.get(session['user_id'])
       user.stress_level = result
       db.session.commit()

       return redirect(url_for('result',result=result)) 
      
    return render_template('quiz_18_21.html')
 

# rout for 22-60 quiz
@app.route('/quiz_22_60',methods=['GET','POST'])
def quiz_22_60():
    if request.method == 'POST':
        user_input = {
        'Age': request.form['Age'],
        'Gender': request.form['Gender'],
        'Occupation': request.form['Occupation'],
        'Marital_Status': request.form['Marital_Status'],
        'Sleep_Duration': request.form['Sleep_Duration'],
        'Sleep_Quality': request.form['Sleep_Quality'],
        'Wake_Up_Time': request.form['Wake_Up_Time'],
        'Bed_Time': request.form['Bed_Time'],
        'Physical_Activity': request.form['Physical_Activity'],
        'Screen_Time': request.form['Screen_Time'],
        'Caffeine_Intake': request.form['Caffeine_Intake'],
        'Alcohol_Intake': request.form['Alcohol_Intake'],
        'Smoking_Habit': request.form['Smoking_Habit'],
        'Work_Hours': request.form['Work_Hours'],
        'Travel_Time': request.form['Travel_Time'],
        'Social_Interactions': request.form['Social_Interactions'],
        'Meditation_Practice': request.form['Meditation_Practice'],
        'Exercise_Type': request.form['Exercise_Type'],
        'Blood_Pressure': request.form['Blood_Pressure'],
        'Cholesterol_Level': request.form['Cholesterol_Level'],
        'Blood_Sugar_Level': request.form['Blood_Sugar_Level']
            }

        df = pd.DataFrame([user_input]) 
            # preprocessing
        processed = preprocess_pipeline.transform(df)
        
            # prediction
        result = cat_model.predict(processed)[0]
            #personalized advice
            # advice = get_advice_22_60(user_input)    
        # saving in db
        
        user = User.query.get(session['user_id'])
        user.stress_level = result
        db.session.commit    
            
        return redirect(url_for('result', result=result))
    return render_template('quiz_22_60.html')


@app.route('/')
def home():
    return render_template('test_model.html')
@app.route('/result')
def result():
    prediction = request.args.get('result', None)
    return render_template('result.html', prediction=prediction)

# run app 
if __name__=="__main__":
        app.run(debug=True)
