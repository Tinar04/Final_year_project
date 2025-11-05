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
    print("\n===  Quiz 18–21 Form Submitted ===")

    if request.method == 'POST':
        data = request.form.to_dict()
        print("Received form data:", data)

       
        try:
            df = pd.DataFrame([data], dtype=float)
            print(" DataFrame created successfully:\n", df)
        except Exception as e:
            print(" Error creating DataFrame:", e)
            return render_template("error.html", message="Error processing form data. Please try again.")

        
        result = None
        try:
            print(" Checking model and pipeline readiness...")

            if preprocess_pipeline_new_18_21 is not None:
                try:
                    print("🔹 Trying pipeline.predict()...")
                    result = preprocess_pipeline_new_18_21.predict(df)[0]
                    print(" Prediction successful via pipeline:", result)

                except Exception as e1:
                    print(" pipeline.predict() failed:", e1)
                    try:
                        print("🔹 Attempting transform() + model.predict() fallback...")
                        transformed = preprocess_pipeline_new_18_21.transform(df)
                        result = model_18_21.predict(transformed)[0]
                        print(" Prediction successful via fallback:", result)
                    except Exception as e2:
                        print(" model.predict() failed:", e2)
                        return render_template(
                            "error.html",
                            message=f"Model prediction failed. Please contact admin.<br><small>{e2}</small>"
                        )

            elif model_18_21 is not None:
                print(" No preprocessing pipeline found. Using model directly...")
                result = model_18_21.predict(df)[0]
                print(" Prediction successful (model only):", result)

            else:
                print(" No model or pipeline object available.")
                return render_template("error.html", message="Model not loaded. Please try again later.")

        except Exception as e:
            print(" General prediction error:", e)
            return render_template("error.html", message=f"Prediction failed. Details: {e}")

       
        if result is None:
            print(" No prediction result generated.")
            return render_template("error.html", message="No prediction result generated. Please retry.")

        print(" Final Predicted result (18–21):", result)
        return redirect(url_for("result", result=result))

    
    return render_template("quiz_18_21.html")



@app.route('/quiz_22_60', methods=['GET', 'POST'])
def quiz_22_60():
    print("\n===  [ROUTE] Quiz 22–60 Form Triggered ===")

    if request.method == 'POST':
        data = request.form.to_dict()
        print(" Received form data:", data)

        session['user_input'] = data
        session['age_group'] = '22-60'

        try:
            df = pd.DataFrame([data])
            print(" DataFrame created successfully:\n", df)
        except Exception as e:
            return render_template("error.html", message=f"Error processing form data.<br><small>{e}</small>")

        categorical_cols = [
            'Gender', 'Marital_Status', 'Smoking_Habit', 'Meditation_Practice',
            'Exercise_Type', 'Occupation', 'Wake_Up_Time', 'Bed_Time'
        ]
        numeric_cols = [c for c in df.columns if c not in categorical_cols]

        try:
            df[categorical_cols] = df[categorical_cols].astype(str).fillna("Unknown")
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
            print("✅ Data cleaning completed successfully.")
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
            result = cat_model.predict(pool)[0]
            print(" Raw model prediction:", result)

            
            result = str(result).strip()

            result = result.replace("[", "").replace("]", "").replace("'", "")

            label_map = {"Low": 0, "Medium": 1, "High": 2}
            result = label_map.get(result, 1)

            result = int(result)

            print("Final normalized result (22–60):", result)

        except Exception as e:
            return render_template("error.html", message=f" Model Prediction Failed.<br><small>{e}</small>")

        if 'user_id' in session:
            try:
                user = User.query.get(session['user_id'])
                if user:
                    user.prediction = str(result)
                    db.session.commit()
            except Exception:
                print(" Database save error")

        return redirect(url_for('result', result=int(result)))

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
