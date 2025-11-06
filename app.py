from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
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

MYSQL_URL = os.getenv(
    "DB_URL",
    "mysql+pymysql://root:tina123@localhost/db_mental_stress"
)
app.config["SQLALCHEMY_DATABASE_URI"] = MYSQL_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = "user" 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=True)
    gender = db.Column(db.String(10))
    age = db.Column(db.Integer)
    occupation = db.Column(db.String(50))
    prediction = db.Column(db.String(50)) 

    def __repr__(self):
        return f"{self.username} ({self.age})"


with app.app_context():
    db.create_all()
    try:
        db.session.execute(text('SELECT 1'))
        print("Connected successfully to DB & ensured tables.")
    except Exception as e:
        print("DB connectivity problem:", e)

print(f"Models loaded: model_18_21={type(model_18_21)}, cat_model={type(cat_model)}")


# -----------------------------
def ensure_user_saved():
    """
    Create (or fetch) a user from session data after basic details step.
    Puts user_id into session for later updates (e.g., prediction).
    """
    user_login = session.get('user_data', {}) 
    user_basic = session.get('user_input_basic', {})  

    if not user_login or not user_basic:
        return None

    email = (user_login.get('email') or "").strip()
    if not email:
        return None

    
    existing = User.query.filter_by(email=email).first()
    if existing:
        
        changed = False
        if existing.username != user_login.get('username'):
            existing.username = user_login.get('username'); changed = True
        if user_basic.get('gender') and existing.gender != user_basic.get('gender'):
            existing.gender = user_basic.get('gender'); changed = True
        if user_basic.get('age') and existing.age != int(user_basic.get('age')):
            existing.age = int(user_basic.get('age')); changed = True
        if user_basic.get('occupation') and existing.occupation != user_basic.get('occupation'):
            existing.occupation = user_basic.get('occupation'); changed = True
        if changed:
            db.session.commit()
        session['user_id'] = existing.id
        return existing.id

    
    try:
        new_user = User(
            username=user_login.get('username') or "Anonymous",
            email=email,
            password=(user_login.get('password') or None),
            gender=user_basic.get('gender'),
            age=int(user_basic.get('age')) if user_basic.get('age') else None,
            occupation=user_basic.get('occupation'),
            prediction="Not yet predicted"
        )
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.id
        return new_user.id
    except IntegrityError:
        db.session.rollback()
        
        user = User.query.filter_by(email=email).first()
        if user:
            session['user_id'] = user.id
            return user.id
        return None
    except Exception as e:
        db.session.rollback()
        print(" User save error:", e)
        return None

def map_catboost_label_to_int(label_value):
    """
    Normalize CatBoost string label to int class 0/1/2.
    Handles cases like ['Low'] or bytes.
    """
    if label_value is None:
        return 1
    s = str(label_value).strip()
    s = s.replace("[", "").replace("]", "").replace("'", "").replace('"', '')
    label_map = {"Low": 0, "Medium": 1, "High": 2, "low": 0, "medium": 1, "high": 2}
    return label_map.get(s, 1)

# -----------------------------


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Very simple "session login" to capture username/email/password and move on.
    """
    if request.method == 'POST':
        username = (request.form.get('username') or "").strip()
        password = (request.form.get('password') or "").strip()
        email = (request.form.get('email') or "").strip()

        session['user_data'] = {
            'username': username,
            'email': email,
            'password': password
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

        user_login = session.get('user_data', {})

        if user_login:

            existing_user = User.query.filter_by(email=user_login.get('email')).first()

            if existing_user:

                existing_user.username = user_login.get('username')
                existing_user.password = user_login.get('password')
                existing_user.gender = gender
                existing_user.age = int(age)
                existing_user.occupation = occupation
                db.session.commit()
                session['user_id'] = existing_user.id

            else:
                new_user = User(
                    username=user_login.get('username'),
                    email=user_login.get('email'),
                    password=user_login.get('password'),
                    gender=gender,
                    age=int(age),
                    occupation=occupation,
                    prediction="Not yet predicted"
                )
                db.session.add(new_user)
                db.session.commit()
                session['user_id'] = new_user.id

        age_val = int(age)
        if 18 <= age_val <= 21:
            session['age_group'] = '18-21'
            return redirect(url_for('quiz_18_21'))
        else:
            session['age_group'] = '22-60'
            return redirect(url_for('quiz_22_60'))

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
    print("\n===  Quiz 18–21 Form Submitted ===")

    if request.method == 'POST':
        data = request.form.to_dict()
        print("Received form data (18-21):", data)

        
        session['user_input'] = data
        session['age_group'] = '18-21'

        
        try:
            df = pd.DataFrame([data], dtype=float)
            print(" DataFrame created successfully (18-21):\n", df)
        except Exception as e:
            print(" Error creating DataFrame (18-21):", e)
            return render_template("error.html", message="Error processing form data. Please try again.")

        result = None
        try:
            print(" Checking model and pipeline readiness (18-21)...")
            if preprocess_pipeline_new_18_21 is not None:
                try:
                    result = preprocess_pipeline_new_18_21.predict(df)[0]
                    print(" Prediction via pipeline:", result)
                except Exception as e1:
                    print(" pipeline.predict() failed:", e1)
                    try:
                        transformed = preprocess_pipeline_new_18_21.transform(df)
                        result = model_18_21.predict(transformed)[0]
                        print(" Prediction via fallback:", result)
                    except Exception as e2:
                        print(" model.predict() failed:", e2)
                        return render_template(
                            "error.html",
                            message=f"Model prediction failed. Please contact admin.<br><small>{e2}</small>"
                        )
            elif model_18_21 is not None:
                result = model_18_21.predict(df)[0]
                print(" Prediction (model only):", result)
            else:
                return render_template("error.html", message="Model not loaded. Please try again later.")
        except Exception as e:
            print(" General prediction error (18-21):", e)
            return render_template("error.html", message=f"Prediction failed. Details: {e}")

        if result is None:
            return render_template("error.html", message="No prediction result generated. Please retry.")

        print(" Final Predicted result (18–21):", result)
        try:
            result_int = int(result)
        except Exception:
            result_int = map_catboost_label_to_int(result)

        return redirect(url_for("result", result=result_int))

    return render_template("quiz_18_21.html")



@app.route('/quiz_22_60', methods=['GET', 'POST'])
def quiz_22_60():
    print("\n===  [ROUTE] Quiz 22–60 Form Triggered ===")

    if request.method == 'POST':
        data = request.form.to_dict()
        print(" Received form data (22-60):", data)

        
        session['user_input'] = data
        session['age_group'] = '22-60'

        try:
            df = pd.DataFrame([data])
            print(" DataFrame created successfully (22-60):\n", df)
        except Exception as e:
            return render_template("error.html", message=f"Error processing form data.<br><small>{e}</small>")

        categorical_cols = [
            'Gender', 'Marital_Status', 'Smoking_Habit', 'Meditation_Practice',
            'Exercise_Type', 'Occupation', 'Wake_Up_Time', 'Bed_Time'
        ]
        numeric_cols = [c for c in df.columns if c not in categorical_cols]

        try:
            for col in categorical_cols:
                if col not in df.columns:
                    df[col] = "Unknown"
            df[categorical_cols] = df[categorical_cols].astype(str).fillna("Unknown")
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
            print("✅ Data cleaning completed successfully (22-60).")
        except Exception as e:
            return render_template("error.html", message=f"Error preparing data.<br><small>{e}</small>")

        try:
            print(" Running CatBoost model prediction...")
            from catboost import Pool

            try:
                cat_features = cat_model.get_cat_feature_names()
                print(" Loaded cat features from model metadata.")
            except Exception:
                cat_features = categorical_cols
                print(" Using fallback categorical features list.")

            pool = Pool(df, cat_features=cat_features)
            raw_pred = cat_model.predict(pool)[0]
            print(" Raw model prediction:", raw_pred)

            result_int = map_catboost_label_to_int(raw_pred)
            print(" Final normalized result (22–60 int):", result_int)

        except Exception as e:
            return render_template("error.html", message=f" Model Prediction Failed.<br><small>{e}</small>")

        return redirect(url_for('result', result=int(result_int)))

    return render_template('quiz_22_60.html')


@app.route('/result')
def result():
    print("\n============================")
    print("[INFO] /result route triggered")

    try:
        result_value = int(request.args.get('result', -1))
    except:
        result_value = -1
        print("[WARN] Invalid result value — defaulting to -1")

    user_input = session.get('user_input', {}) or {}
    age_group = session.get('age_group', '18-21')
    user_id = session.get('user_id')

    print(f"[INFO] age_group={age_group}, user_id={user_id}")

    if user_id is not None and result_value in (0, 1, 2, 3):
        try:
            user = User.query.get(user_id)
            if user:
                user.prediction = str(result_value)
                db.session.commit()
                print("✅ Prediction saved successfully to database.")
        except Exception as e:
            db.session.rollback()
            print("⚠️ Failed to save prediction to DB:", e)


    stress_levels = {
        0: {
            "title": "Low Stress",
            "subtitle": "Assessment Complete",
            "description": "You're maintaining a balanced lifestyle with healthy habits.",
            "summary": "Balanced lifestyle",
            "distribution": {"low": 80, "medium": 15, "high": 5},
            "default_advice": [
                "Continue your current healthy routines.",
                "Maintain a good work-life balance.",
                "Keep regular sleep and exercise patterns.",
                "Stay proactive to avoid unnecessary stress."
            ],
            "color": "#A7F3D0"
        },
        1: {
            "title": "Medium Stress Level",
            "subtitle": "Assessment Complete",
            "description": "You're experiencing moderate stress that can be improved.",
            "summary": "Moderate stress requiring attention",
            "distribution": {"low": 20, "medium": 60, "high": 20},
            "default_advice": [
                "Reduce screen time, especially before bed.",
                "Take short breaks between tasks.",
                "Try mindfulness or relaxation exercises.",
                "Improve sleep consistency & daily routine."
            ],
            "color": "#FDE68A"
        },
        2: {
            "title": "High Stress Level",
            "subtitle": "Assessment Complete",
            "description": "Your stress level is high and should be addressed soon.",
            "summary": "Elevated stress needing support",
            "distribution": {"low": 10, "medium": 25, "high": 65},
            "default_advice": [
                "Disconnect from digital distractions.",
                "Talk to someone trusted.",
                "Engage in physical activity.",
                "Seek professional support if needed."
            ],
            "color": "#FCA5A5"
        },
        3: {
            "title": "Severe Stress Level",
            "subtitle": "Assessment Complete",
            "description": "Your stress level is severe. Immediate care is recommended.",
            "summary": "Critical stress needing immediate care",
            "distribution": {"low": 5, "medium": 10, "high": 85},
            "default_advice": [
                "Talk to a counselor or trusted person immediately.",
                "Take rest from work/study pressures.",
                "Avoid isolation — stay connected.",
                "Consider therapy or guided intervention."
            ],
            "color": "#EF4444"
        }
    }

    stress_data = stress_levels.get(result_value, stress_levels[1])


    try:
        advice_list = (
            get_advice_18_21(user_input, result_value)
            if age_group == '18-21'
            else get_advice_22_60(user_input, result_value)
        )
    except Exception as e:
        print("[ERROR] Advice generation failed:", e)
        advice_list = []

    if not advice_list:
        advice_list = stress_data["default_advice"]

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
