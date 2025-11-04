
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import pickle
import os
import pandas as pd
from advice_func import get_advice_18_21, get_advice_22_60

try:
    import sklearn.compose._column_transformer as ct
    class _RemainderColsList(list):
        pass
    ct._RemainderColsList = _RemainderColsList
except Exception:
    pass

BASE_MODELS = os.path.join("ml_models")

with open(os.path.join(BASE_MODELS, 'model.pkl'), 'rb') as f:
    model_18_21 = pickle.load(f)

try:
    with open(os.path.join(BASE_MODELS, 'preprocess__new_pipeline(18-21).pkl'), 'rb') as f:
        preprocess_pipeline_new_18_21 = pickle.load(f)
except FileNotFoundError:
    preprocess_pipeline_new_18_21 = None

with open(os.path.join(BASE_MODELS, 'cat_model.pkl'), 'rb') as f:
    cat_model = pickle.load(f)

try:
    with open(os.path.join(BASE_MODELS, 'preprocess_cat_new_pipeline.pkl'), 'rb') as f:
        preprocess_pipeline_new_catboost = pickle.load(f)
except FileNotFoundError:
    preprocess_pipeline_new_catboost = None

app = Flask(__name__)
app.secret_key = "my_secret_key"

db_path = os.path.join(os.getcwd(), "Mental_Stress.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
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
    prediction = db.Column(db.String(50))

    def __repr__(self):
        return f"{self.username} ({self.age})"


with app.app_context():
    db.create_all()

print("Database file exists:", os.path.isfile("Mental_Stress.db"))
print(f"Models loaded: model_18_21={type(model_18_21)}, cat_model={type(cat_model)}")


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        session['user_data'] = {
            'username': username,
            'email': email
        }

        return redirect(url_for('basic_details'))

    return render_template('login.html')


@app.route('/basic_details', methods=['GET', 'POST'])
def basic_details():
    if request.method == 'POST':
        age = request.form.get('age')
        gender = request.form.get('gender')
        occupation = request.form.get('occupation')

        session['user_input_basic'] = {
            'age': age,
            'gender': gender,
            'occupation': occupation
        }

        try:
            age_val = int(age)
            if 18 <= age_val <= 21:
                return redirect(url_for('quiz_18_21'))
            else:
                return redirect(url_for('quiz_22_60'))
        except:
            return redirect(url_for('basic_details'))

    return render_template('basic_details.html')


def _to_float_safe(d):
    out = {}
    for k, v in d.items():
        try:
            out[k] = float(v)
        except Exception:
            out[k] = v
    return out


@app.route('/quiz_18_21', methods=['GET', 'POST'])
def quiz_18_21():
    if request.method == 'POST':
        print("Quiz 18-21 form submitted.")

        user_input = {k: request.form.get(k, 0) for k in [
            'anxiety_level', 'self_esteem', 'mental_health_history', 'depression',
            'headache', 'blood_pressure', 'sleep_quality', 'breathing_problem',
            'noise_level', 'living_conditions', 'safety', 'basic_needs',
            'academic_performance', 'study_load', 'teacher_student_relationship',
            'future_career_concerns', 'social_support', 'peer_pressure',
            'extracurricular_activities', 'bullying'
        ]}

        session['user_input'] = user_input
        session['age_group'] = '18-21'

        try:
            df = pd.DataFrame([_to_float_safe(user_input)])
        except Exception as e:
            print("DataFrame creation failed:", e)
            return render_template('error.html', message="Form data processing failed.")

        result = None
        try:
            if preprocess_pipeline_new_18_21 is not None:
                try:
                    result = preprocess_pipeline_new_18_21.predict(df)[0]
                except Exception:
                    transformed = preprocess_pipeline_new_18_21.transform(df)
                    result = model_18_21.predict(transformed)[0]
            else:
                result = model_18_21.predict(df)[0]
        except Exception as e:
            print("Prediction error (18–21):", e)
            result = 1

        print("Predicted result (18–21):", result)

        if 'user_id' in session:
            try:
                user = User.query.get(session['user_id'])
                if user:
                    user.prediction = str(result)
                    db.session.commit()
            except Exception as e:
                print("Database save error:", e)

        return redirect(url_for('result', result=result))

    return render_template('quiz_18_21.html')


@app.route('/quiz_22_60', methods=['GET', 'POST'])
def quiz_22_60():
    if request.method == 'POST':
        print("Quiz 22–60 form submitted.")

        user_input = {k: request.form.get(k, '') for k in [
            'Age', 'Gender', 'Occupation', 'Marital_Status', 'Sleep_Duration',
            'Sleep_Quality', 'Wake_Up_Time', 'Bed_Time', 'Physical_Activity',
            'Screen_Time', 'Caffeine_Intake', 'Alcohol_Intake', 'Smoking_Habit',
            'Work_Hours', 'Travel_Time', 'Social_Interactions', 'Meditation_Practice',
            'Exercise_Type', 'Blood_Pressure', 'Cholesterol_Level', 'Blood_Sugar_Level'
        ]}

        session['user_input'] = user_input
        session['age_group'] = '22-60'

        df = pd.DataFrame([user_input])
        categorical_cols = [
            'Gender', 'Marital_Status', 'Smoking_Habit', 'Meditation_Practice',
            'Exercise_Type', 'Occupation', 'Wake_Up_Time', 'Bed_Time'
        ]
        numeric_cols = [c for c in df.columns if c not in categorical_cols]

        df[categorical_cols] = df[categorical_cols].astype(str).fillna("Unknown")
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

        import numpy as np
        result = None

        try:
            from catboost import Pool
            try:
                cat_features = cat_model.get_cat_feature_names()
            except Exception:
                cat_features = categorical_cols

            pool = Pool(df, cat_features=cat_features)
            result = cat_model.predict(pool)[0]

            if isinstance(result, (list, tuple, np.ndarray)):
                result = result[0]

            try:
                result = int(round(float(result)))
            except Exception:
                result = 1

            if result not in [0, 1, 2]:
                result = 1

        except Exception as e:
            print("Prediction error (22–60):", e)
            result = 1

        print("Predicted result (22–60):", result)

        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                user.prediction = str(result)
                db.session.commit()

        return redirect(url_for('result', result=result))

    return render_template('quiz_22_60.html')

@app.route('/result')
def result():
    print("\n============================")
    print("[INFO] /result route triggered")

    try:
        result_value = int(request.args.get('result', -1))
        print(f"[INFO] Retrieved result value from request: {result_value}")
    except (TypeError, ValueError):
        result_value = -1
        print("[WARN] Invalid result value — defaulting to -1")

    user_input = session.get('user_input', {}) or {}
    age_group = session.get('age_group', '18-21')
    print(f"[INFO] Retrieved session data — age_group: {age_group}, user_input keys: {list(user_input.keys())}")

    stress_levels = {
        0: {
            "title": "Low Stress",
            "subtitle": "Assessment Complete",
            "description": "You're maintaining a balanced lifestyle with healthy habits. Keep doing what works for you.",
            "summary": "Balanced lifestyle with healthy habits",
            "distribution": {"low": 80, "medium": 85, "high": 85},
            "default_advice": [
                "Continue your current healthy routines.",
                "Maintain a good work-life balance.",
                "Keep regular sleep and exercise patterns.",
                "Stay proactive in preventing unnecessary stress."
            ],
            "color": "#A7F3D0"
        },
        1: {
            "title": "Medium Stress Level",
            "subtitle": "Assessment Complete",
            "description": "You're experiencing moderate stress levels. This is manageable with some lifestyle adjustments.",
            "summary": "Moderate stress requiring attention",
            "distribution": {"low": 20, "medium": 60, "high": 20},
            "default_advice": [
                "Reduce screen time, especially before bed.",
                "Take short breaks between tasks to recharge.",
                "Incorporate relaxation or mindfulness exercises.",
                "Focus on improving sleep and maintaining physical activity."
            ],
            "color": "#FDE68A"
        },
        2: {
            "title": "High Stress Level",
            "subtitle": "Assessment Complete",
            "description": "Your stress levels are high and could affect your well-being. It's important to take active steps to reduce it.",
            "summary": "Elevated stress needing support",
            "distribution": {"low": 10, "medium": 25, "high": 65},
            "default_advice": [
                "Prioritize rest and disconnect from digital distractions.",
                "Talk to someone you trust about what's stressing you.",
                "Engage in physical activity to release tension.",
                "Seek professional support if you feel overwhelmed."
            ],
            "color": "#FCA5A5"
        },
        3: {
            "title": "Severe Stress Level",
            "subtitle": "Assessment Complete",
            "description": "Your stress level is severe. Please consider reaching out to a mental health professional for support.",
            "summary": "Critical stress needing immediate care",
            "distribution": {"low": 5, "medium": 10, "high": 85},
            "default_advice": [
                "Talk to a counselor or trusted person immediately.",
                "Take time off from work or studies to rest.",
                "Avoid isolation — connect with supportive people.",
                "Engage in stress-reducing habits and professional therapy."
            ],
            "color": "#EF4444"
        }
    }

    print("[INFO] Stress level data loaded successfully.")

    stress_data = stress_levels.get(result_value, stress_levels[1])
    print(f"[INFO] Selected Stress Level: {stress_data['title']}")
    print(f"[INFO] Distribution: {stress_data['distribution']}")

    try:
        print(f"[INFO] Generating advice for age group: {age_group}")
        if age_group == '18-21':
            advice_list = get_advice_18_21(user_input, result_value)
        else:
            advice_list = get_advice_22_60(user_input, result_value)
        print(f"[INFO] Advice function returned {len(advice_list)} items.")
    except Exception as e:
        print("[ERROR] Advice generation error:", e)
        advice_list = []

    if not advice_list:
        advice_list = stress_data["default_advice"]
        print("[INFO] No personalized advice found — using default advice.")
    else:
        print("[INFO] Personalized advice successfully loaded.")

    print("[INFO] Final render summary:")
    print(f"   Result Value: {result_value}")
    print(f"   Level Title: {stress_data['title']}")
    print(f"   Advice Count: {len(advice_list)}")
    print(f"   Theme Color: {stress_data['color']}")
    print("============================\n")

    return render_template(
        'result.html',
        result=result_value,
        title=stress_data["title"],
        subtitle=stress_data["subtitle"],
        description=stress_data["description"],
        summary=stress_data["summary"],
        distribution=stress_data["distribution"],
        advice_list=advice_list,
        color=stress_data["color"]
    )


if __name__ == "__main__":
    app.run(debug=True)







# from flask import Flask, render_template,jsonify, request, redirect, url_for, session
# from flask_sqlalchemy import SQLAlchemy
# import pickle
# import os
# from advice_func import get_advice_18_21
# import random
# import numpy
# import pandas as pd
# # from catboost import CatBoostClassifier

# # from advice_func import get_advice_18_21, get_advice_22_60



# with open(r'ml_models\model.pkl', 'rb') as f:
#     model_18_21 = pickle.load(f)

# with open(r'ml_models\preprocess__new_pipeline(18-21).pkl', 'rb') as f:
#     preprocess_pipeline_new_18_21 = pickle.load(f)

# with open(r'ml_models\cat_model.pkl', 'rb') as f:
#     cat_model = pickle.load(f)

# with open(r'ml_models\preprocess_cat_new_pipeline.pkl', 'rb') as f:
#     preprocess_pipeline_new_catboost = pickle.load(f)

# app = Flask(__name__)
# app.secret_key = "my_secret_key"




# # Database config (SQLite)
# db_path = os.path.join(os.getcwd(), "Mental_Stress.db")
# app.config['SQLALCHEMY_DATABASE_URI'] =f"sqlite:///{db_path}"
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db = SQLAlchemy(app)

# # user model schema

# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(30), nullable=False)
#     email = db.Column(db.String(50), unique=True, nullable=False)
#     phone = db.Column(db.String(15), nullable=False)
#     password = db.Column(db.String(30), nullable=False)
#     gender = db.Column(db.String(3))
#     age = db.Column(db.Integer)
#     occupation = db.Column(db.String(50))

#     # Quiz answers + prediction
#     q1 = db.Column(db.Integer)
#     q2 = db.Column(db.Integer)
#     q3 = db.Column(db.Integer)
    
#     prediction = db.Column(db.String(50))

#     def __repr__(self):
#          return f"{self.age},{self.username}"

# # database
# with app.app_context():
#     db.create_all()
# print("Database file exists:", os.path.isfile("Mental_Stress.db"))


# # basic detail route
# @app.route('/basic_details',methods=['GET','POST'])
# def basic_details():
#     if request.method == 'POST':
#         gender = request.form['gender']
#         age = int(request.form['age'])
#         occupation = request.form['occupation']

#         # updating database
#         user = User.query.get(session['user_id'])
#         user.gender = gender
#         user.age = age
#         user.occupation = occupation
#         db.session.commit()

#     # the age condition
#     if age >= 18 and age <= 21:
#         return redirect(url_for('quiz_18_21'))
#     else:
#         return redirect(url_for('quiz_22_60'))
    
#     return render_template('basic_details.html')

# # quize 18-21 route
# @app.route('/quiz_18_21',methods=['GET','POST'])
# def quiz_18_21():
#     if request.method == 'POST':
#     #   collecting user inputs
#        user_input = {
#             'anxiety_level': request.form['anxiety_level'],
#             'self_esteem': request.form['self_esteem'],
#             'mental_health_history': request.form['mental_health_history'],
#             'depression': request.form['depression'],
#             'headache': request.form['headache'],
#             'blood_pressure': request.form['blood_pressure'],
#             'sleep_quality': request.form['sleep_quality'],
#             'breathing_problem': request.form['breathing_problem'],
#             'noise_level': request.form['noise_level'],
#             'living_conditions': request.form['living_conditions'],
#             'safety': request.form['safety'],
#             'basic_needs': request.form['basic_needs'],
#             'academic_performance': request.form['academic_performance'],
#             'study_load': request.form['study_load'],
#             'teacher_student_relationship': request.form['teacher_student_relationship'],
#             'future_career_concerns': request.form['future_career_concerns'],
#             'social_support': request.form['social_support'],
#             'peer_pressure': request.form['peer_pressure'],
#             'bullying': request.form['bullying'] 
#        }
       
#        df = pd.DataFrame([user_input])
#      # preprocessing
#        df = preprocess_pipeline_new_18_21.transform(df)
#      # prediction 
#        result = model_18_21.predict(df)[0]
#      #personalized advice
#        advice_list = get_advice_18_21(user_input,result)
#       # result in bd
#        user = User.query.get(session['user_id'])
#        user.stress_level = result
#        db.session.commit()

#        return redirect(url_for('result',result=result)) 
      
#     return render_template('quiz_18_21.html')
 

# # rout for 22-60 quiz
# @app.route('/quiz_22_60',methods=['GET','POST'])
# def quiz_22_60():
#     if request.method == 'POST':
#         user_input = {
#         'Age': request.form['Age'],
#         'Gender': request.form['Gender'],
#         'Occupation': request.form['Occupation'],
#         'Marital_Status': request.form['Marital_Status'],
#         'Sleep_Duration': request.form['Sleep_Duration'],
#         'Sleep_Quality': request.form['Sleep_Quality'],
#         'Wake_Up_Time': request.form['Wake_Up_Time'],
#         'Bed_Time': request.form['Bed_Time'],
#         'Physical_Activity': request.form['Physical_Activity'],
#         'Screen_Time': request.form['Screen_Time'],
#         'Caffeine_Intake': request.form['Caffeine_Intake'],
#         'Alcohol_Intake': request.form['Alcohol_Intake'],
#         'Smoking_Habit': request.form['Smoking_Habit'],
#         'Work_Hours': request.form['Work_Hours'],
#         'Travel_Time': request.form['Travel_Time'],
#         'Social_Interactions': request.form['Social_Interactions'],
#         'Meditation_Practice': request.form['Meditation_Practice'],
#         'Exercise_Type': request.form['Exercise_Type'],
#         'Blood_Pressure': request.form['Blood_Pressure'],
#         'Cholesterol_Level': request.form['Cholesterol_Level'],
#         'Blood_Sugar_Level': request.form['Blood_Sugar_Level']
#             }

#         df = pd.DataFrame([user_input]) 
#             # preprocessing
#         processed = preprocess_pipeline_new_catboost.transform(df)
        
#             # prediction
#         result = cat_model.predict(processed)[0]
#             #personalized advice
#             # advice = get_advice_22_60(user_input)    
#         # saving in db
        
#         user = User.query.get(session['user_id'])
#         user.stress_level = result
#         db.session.commit    
            
#         return redirect(url_for('result', result=result))
#     return render_template('quiz_22_60.html')


# @app.route('/')
# def home():
#     return render_template('test_model.html')
# @app.route('/result')
# def result():
#     prediction = request.args.get('result', None)
#     return render_template('result.html', prediction=prediction)

# # run app 
# if __name__=="__main__":
#         app.run(debug=True)










