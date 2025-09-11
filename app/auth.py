from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
import mysql.connector

auth_bp = Blueprint("auth", __name__)
bcrypt = Bcrypt()

# DB connection helper
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",         # change to your MySQL username
        password="08*Prajna", # change to your MySQL password
        database="botanic_cure"
    )

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # ✅ hash the password
        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

        conn = get_db()
        cur = conn.cursor()
        try:
            # ✅ insert into 'password' column
            cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s,%s,%s)",
            (username, email, hashed_pw))
            conn.commit()
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))
        except:
            flash("Username or Email already exists.", "danger")
        finally:
            cur.close()
            conn.close()

    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        # ✅ check against user["password"], not password_hash
        if user and bcrypt.check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Login successful!", "success")
            return redirect(url_for("home"))   # use 'home', not 'index'
        else:
            flash("Invalid credentials!", "danger")

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))
