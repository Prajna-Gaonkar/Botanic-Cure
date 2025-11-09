from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
from . import db, bcrypt
from .models import User
from .email_utils import generate_verification_code, send_verification_email, send_reset_password_email

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

        # Hash the password and generate verification code
        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        verification_code = generate_verification_code()
        verification_expires = datetime.utcnow() + timedelta(minutes=30)

        try:
            new_user = User(
                username=username,
                phone=phone,
                email=email,
                password_hash=hashed_pw,
                verification_code=verification_code,
                verification_code_expires=verification_expires,
                is_verified=False
            )
            db.session.add(new_user)
            db.session.commit()

            # Send verification email
            if send_verification_email(email, verification_code):
                flash("✅ Account created! Please check your email for verification code.", "success")
                return redirect(url_for("auth.verify_email"))
            else:
                flash("⚠️ Account created but failed to send verification email. Please contact support.", "warning")
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
            
        # Check password hash and verification
        if user and bcrypt.check_password_hash(user.password_hash, password):
            if not user.is_verified:
                flash("⚠️ Please verify your email before logging in.", "warning")
                return redirect(url_for("auth.verify_email"))
                
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
@auth_bp.route("/verify-email", methods=["GET", "POST"])
def verify_email():
    if request.method == "POST":
        email = request.form.get("email")
        code = request.form.get("verification_code")
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("⚠️ Email not found.", "danger")
            return redirect(url_for("auth.verify_email"))
            
        if user.is_verified:
            flash("✅ Email already verified. Please log in.", "info")
            return redirect(url_for("auth.login"))
            
        if (user.verification_code == code and 
            user.verification_code_expires and 
            user.verification_code_expires > datetime.utcnow()):
            user.is_verified = True
            user.verification_code = None
            user.verification_code_expires = None
            db.session.commit()
            flash("✅ Email verified successfully! Please log in.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("⚠️ Invalid or expired verification code.", "danger")
            
    return render_template("verify_email.html")

@auth_bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    email = request.form.get("email")
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash("⚠️ Email not found.", "danger")
        return redirect(url_for("auth.verify_email"))
        
    if user.is_verified:
        flash("✅ Email already verified. Please log in.", "info")
        return redirect(url_for("auth.login"))
        
    # Generate new verification code
    verification_code = generate_verification_code()
    user.verification_code = verification_code
    user.verification_code_expires = datetime.utcnow() + timedelta(minutes=30)
    db.session.commit()
    
    if send_verification_email(email, verification_code):
        flash("✅ New verification code sent! Please check your email.", "success")
    else:
        flash("⚠️ Failed to send verification email. Please try again.", "danger")
        
    return redirect(url_for("auth.verify_email"))

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        
        if user:
            reset_code = generate_verification_code()
            user.reset_code = reset_code
            user.reset_code_expires = datetime.utcnow() + timedelta(minutes=30)
            db.session.commit()
            
            if send_reset_password_email(email, reset_code):
                flash("✅ Password reset code sent! Please check your email.", "success")
                return redirect(url_for("auth.reset_password"))
            else:
                flash("⚠️ Failed to send reset email. Please try again.", "danger")
        else:
            flash("⚠️ Email not found.", "danger")
            
    return render_template("forgot_password.html")

@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form.get("email")
        reset_code = request.form.get("reset_code")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        
        if new_password != confirm_password:
            flash("⚠️ Passwords do not match!", "danger")
            return redirect(url_for("auth.reset_password"))
            
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("⚠️ Email not found.", "danger")
            return redirect(url_for("auth.reset_password"))
            
        if (user.reset_code == reset_code and 
            user.reset_code_expires and 
            user.reset_code_expires > datetime.utcnow()):
            hashed_pw = bcrypt.generate_password_hash(new_password).decode("utf-8")
            user.password_hash = hashed_pw
            user.reset_code = None
            user.reset_code_expires = None
            db.session.commit()
            flash("✅ Password reset successfully! Please log in.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("⚠️ Invalid or expired reset code.", "danger")
            
    return render_template("reset_password.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("👋 You have been logged out.", "info")
    return redirect(url_for("auth.login"))
