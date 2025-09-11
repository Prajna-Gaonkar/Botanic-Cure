# app/app.py
import os, uuid, json
import mysql.connector
from flask import Flask, render_template, request, url_for, redirect, session
from flask_bcrypt import Bcrypt
from inference import predict_image

# ----------------------------
# Flask setup
# ----------------------------
UPLOAD_FOLDER = "app/static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "supersecretkey"   # required for sessions
bcrypt = Bcrypt(app)

# ----------------------------
# MySQL setup
# ----------------------------
conn = mysql.connector.connect(
    host="localhost",
    user="root",             # change if needed
    password="08*Prajna",    # change to your MySQL password
    database="botanic_cure"  # change to your DB name
)
cursor = conn.cursor(dictionary=True)

# ----------------------------
# Load plant info
# ----------------------------
try:
    with open("model/plant_info.json") as f:
        PLANT_INFO = json.load(f)
except:
    PLANT_INFO = {}

# ----------------------------
# Routes
# ----------------------------

# Login Page
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("home"))
        else:
            return render_template("index.html", error="Invalid credentials")

    return render_template("index.html")


# Register Page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # hash the password
        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                       (username, email, hashed_pw))
        conn.commit()
        return redirect(url_for("login"))

    return render_template("register.html")


# Home Page (Leaf Prediction)
@app.route("/home", methods=["GET", "POST"])
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files.get("leaf_image")
        if not file:
            return render_template("home.html", error="No file uploaded.", username=session["username"])
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png"]:
            return render_template("home.html", error="Unsupported file type.", username=session["username"])

        fname = f"{uuid.uuid4().hex}{ext}"
        fpath = os.path.join(UPLOAD_FOLDER, fname)
        file.save(fpath)

        res = predict_image(fpath)

        if res["status"] == "recognized":
            info = PLANT_INFO.get(res["label"], {})
            return render_template("home.html",
                                   label=res["label"],
                                   confidence=res["confidence"],
                                   info=info,
                                   img_url=url_for("static", filename=f"uploads/{fname}"),
                                   username=session["username"])
        else:
            return render_template("home.html",
                                   label="Unknown",
                                   confidence=res["confidence"],
                                   info=None,
                                   img_url=url_for("static", filename=f"uploads/{fname}"),
                                   username=session["username"])

    return render_template("home.html", username=session["username"])


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# Feedback
@app.route("/feedback", methods=["POST"])
def feedback():
    if "user_id" not in session:
        return redirect(url_for("login"))

    feedback_text = request.form["feedback"]
    cursor.execute("INSERT INTO feedback (user_id, feedback_text) VALUES (%s, %s)", 
                   (session["user_id"], feedback_text))
    conn.commit()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
