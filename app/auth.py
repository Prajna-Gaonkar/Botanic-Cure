from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from . import db, bcrypt
from .models import User

auth_bp = Blueprint("auth", __name__)

# ✅ User Registration
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if request.is_json:
            data = request.get_json()
            username = data.get("username")
            phone = data.get("phone")
            email = data.get("email")
            password = data.get("password")
            confirm_password = password  # In JSON case, frontend validates password match
        else:
            username = request.form.get("username")
            phone = request.form.get("phone")
            email = request.form.get("email")
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("⚠️ Passwords do not match!", "danger")
            return redirect(url_for("auth.register"))

        # Hash the password
        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

        try:
            new_user = User(username=username, phone=phone, email=email, password_hash=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            flash("✅ Account created successfully! Please log in.", "success")
            return redirect(url_for("auth.login"))
        except:
            db.session.rollback()
            flash("⚠️ Username or Email already exists.", "danger")

    return render_template("register.html")

# ✅ User Login
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.is_json:
            data = request.get_json()
            email = data.get("email")
            password = data.get("password")
            print(f"JSON Login attempt - Email: {email}")  # Debug log
        else:
            email = request.form.get("email")
            password = request.form.get("password")
            print(f"Form Login attempt - Email: {email}")  # Debug log

        if not email or not password:
            error_msg = "Email and password are required"
            if request.is_json:
                return {"error": error_msg, "success": False}, 400
            flash(error_msg, "danger")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(email=email).first()

        # Debug logs
        print(f"User found: {user is not None}")
        if user:
            print(f"Password hash in DB: {user.password_hash}")
            match = bcrypt.check_password_hash(user.password_hash, password)
            print(f"Password match: {match}")
            
        # Check password hash
        if user and bcrypt.check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["username"] = user.username
            flash("🎉 Login successful!", "success")
            if request.is_json:
                return {
                    "success": True,
                    "redirect": url_for("main.home"),
                    "message": "Login successful!"
                }
            return redirect(url_for("main.home"))
        else:
            error_msg = "❌ Invalid email or password!"
            print(f"Login failed: {error_msg}")  # Debug log
            flash(error_msg, "danger")
            if request.is_json:
                return {"error": error_msg, "success": False}, 401

    # 👇 render index.html (your login page)
    return render_template("index.html")

# ✅ User Logout
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("👋 You have been logged out.", "info")
    return redirect(url_for("auth.login"))
