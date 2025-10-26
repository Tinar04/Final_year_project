from flask import Flask, render_template,jsonify, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import pickle
import os
from advice_data import advise_18_21 ,advise_22_60
import random
import numpy
import pandas as pd



with open(r'ml_models\model.pkl', 'rb') as f:
    model_18_21 = pickle.load(f)

with open(r'ml_models\xgb_model .pkl', 'rb') as f:
      model_22_60  = pickle.load(f)


with open(r'ml_models\encoders.pkl', 'rb') as f:
      encoder = pickle.load(f)
      
with open(r'ml_models\scaler.pkl', 'rb') as f:
      scaler = pickle.load(f)
    

with open(r'ml_models\target_encoder.pkl', 'rb') as f:
      target  = pickle.load(f)



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


# advice fucntion 18-21
def get_advice_18_21(answers):
    advice_list = []
    category_map = {0: "High", 1: "Medium", 2: "Low"}  # numeric to string mapping

    for idx, column in advise_18_21.items():
        ans = answers[idx]
        # category mapping
        cat = 2 if ans <= 2 else 1 if ans == 3 else 0

        # pick advice from the correct column and category
        advice_list.append(random.choice(column[category_map[cat]]))

    return " ".join(advice_list)


# advice fucntion for  22-60
def get_advice_22_60(answers):
    advice_list = []
    category_map = {0: "High", 1: "Medium", 2: "Low"}  # map numeric category to string

    for idx, column in advise_22_60.items():
        ans = answers[idx]

        # mapping for specific columns
        if idx == 4:  # Sleep_Duration
            cat = 2 if ans < 6 else 1 if ans <= 7 else 0
        elif idx == 13:  # Work_Hours
            cat = 2 if ans > 10 else 1 if ans >= 8 else 0
        elif idx == 9:  # Screen_Time
            cat = 2 if ans > 6 else 1 if ans >= 4 else 0
        elif idx == 10:  # Caffeine_Intake
            cat = 2 if ans >= 2 else 1 if ans == 1 else 0
        else:
            cat = 2 if ans <= 2 else 1 if ans == 3 else 0

        # append a random advice from correct column and category
        advice_list.append(random.choice(column[category_map[cat]]))

    return " ".join(advice_list)

# predic route
@app.route("/predict", methods = ["POST"])
def predict():
    data = request.json
    if not data:
       return jsonify({"eroor : no data received"}),400
     
    
    age = int(data.get("age"))
    answers = data.get("answers")

    if not isinstance(answers,list):
        return jsonify ({"error : answers  must be list"}),400
    
    
    #age condition
    if 18<= age <=21:
        if len(answers) != 20:
            return jsonify({"error fill all answers"}),400
        model = model_18_21
        advice = get_advice_18_21(answers)

    elif 22<= age<=60:
        if len(answers) != 18:
            return jsonify({"error please insert all inputs"}),400
        model = model_22_60
        advice = get_advice_22_60(answers)

    else:
        return jsonify({"error age is not supported"}),400
    
    # model prediction
    columns = ['Age', 'Gender', 'Occupation', 'Marital_Status', 'Sleep_Duration',
       'Sleep_Quality', 'Wake_Up_Time', 'Bed_Time', 'Physical_Activity',
       'Screen_Time', 'Caffeine_Intake', 'Alcohol_Intake', 'Smoking_Habit',
       'Work_Hours', 'Travel_Time', 'Social_Interactions',
       'Meditation_Practice', 'Exercise_Type', 'Blood_Pressure',
       'Cholesterol_Level', 'Blood_Sugar_Level']
    answer = pd.DataFrame(answer)

    numeric_cols =  ['Age', 'Sleep_Duration', 'Sleep_Quality', 'Physical_Activity', 
                'Screen_Time', 'Caffeine_Intake', 'Alcohol_Intake', 'Work_Hours', 
                'Travel_Time', 'Social_Interactions']
    answer[numeric_cols] = scaler.transform(answer[numeric_cols])

    binary_cols = ['Gender', 'Marital_Status','Smoking_Habit','Meditation_Practice']
    for i in range(len(binary_cols)):
        answer[binary_cols[i]] = encoder[i].transform(answer[binary_cols[i]])
        
    model_pred = model.predict([answers])[0]
    stress_map = {0:"Low",1:"Medium",2:"High"}
    stress_level = stress_map.get(model_pred,"unknown")
    

    # user answers in database
    user = User(
        username=data.get("username","Anonmyous"),
        age = age,
        q1=answers[0],
        q2=answers[1],
        q3=answers[2],

        prediction = stress_level
        )
    db.session.add(user)
    db.session.commit()

    return jsonify({"Prediction":stress_level,"Advise":advice})
# run app 
if __name__=="__main__":
        app.run(debug=True)
