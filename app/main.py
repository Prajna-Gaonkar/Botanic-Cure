# app/main.py
import os
import uuid
import json
import traceback
from flask import Blueprint, render_template, request, url_for, redirect, session, flash
from app.inference import predict_image

main_bp = Blueprint('main', __name__)

# File uploads & plant info
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

PLANT_INFO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model", "plant_info.json")
try:
    with open(PLANT_INFO_PATH, "r", encoding="utf-8") as f:
        PLANT_INFO = json.load(f)
except Exception:
    PLANT_INFO = {}

@main_bp.route("/")
def root():
    """Keep the root URL simple: if logged in, go to home; otherwise go to login."""
    if session.get("user_id"):
        return redirect(url_for("main.home"))
    return redirect(url_for("auth.login"))

@main_bp.route("/home", methods=["GET", "POST"])
def home():
    """Leaf prediction page (requires login)."""
    if "user_id" not in session:
        flash("Please log in to continue.", "warning")
        return redirect(url_for("auth.login"))

    username = session.get("username", "User")

    if request.method == "POST":
        file = request.files.get("leaf_image")
        if not file or file.filename.strip() == "":
            return render_template("home.html", error="No file uploaded.", username=username)

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in {".jpg", ".jpeg", ".png"}:
            return render_template("home.html", error="Unsupported file type.", username=username)

        # Save upload
        fname = f"{uuid.uuid4().hex}{ext}"
        fpath = os.path.join(UPLOAD_FOLDER, fname)
        print(f"Saving uploaded file to: {fpath}")  # Debug log
        file.save(fpath)

        # Predict
        try:
            print(f"Running prediction on: {fpath}")  # Debug log
            res = predict_image(fpath)
            print(f"Prediction result: {res}")  # Debug log
        except Exception as e:
            print(f"Prediction error: {str(e)}")  # Debug log
            traceback.print_exc()
            return render_template(
                "home.html",
                error=f"Prediction failed: {e}",
                username=username
            )

        # Render with results
        img_url = url_for("static", filename=f"uploads/{fname}")

        if isinstance(res, dict) and res.get("status") == "recognized":
            label = res.get("label", "Unknown")
            confidence = res.get("confidence")
            info = PLANT_INFO.get(label, {})
            return render_template(
                "home.html",
                label=label,
                confidence=confidence,
                info=info,
                img_url=img_url,
                username=username
            )
        else:
            # Unknown / low confidence
            confidence = res.get("confidence") if isinstance(res, dict) else None
            return render_template(
                "home.html",
                label="Unknown",
                confidence=confidence,
                info=None,
                img_url=img_url,
                username=username
            )

    # GET
    return render_template("home.html", username=username)

@main_bp.route("/feedback", methods=["POST"])
def feedback():
    """Handle user feedback submission and email it to owner."""
    try:
        if "user_id" not in session:
            print("Debug: User not in session")  # Debug log
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login"))

        feedback_text = request.form.get("feedback", "").strip()
        print(f"Debug: Received feedback: {feedback_text}")  # Debug log
        
        if not feedback_text:
            print("Debug: Empty feedback")  # Debug log
            flash("Feedback cannot be empty.", "warning")
            return redirect(url_for("main.home"))

        # Get user info for the feedback email
        from .models import User
        user = User.query.get(session["user_id"])
        print(f"Debug: User info - ID: {session['user_id']}, Found: {user is not None}")  # Debug log
        
        if not user:
            print("Debug: User not found in database")  # Debug log
            flash("Error: User not found.", "error")
            return redirect(url_for("main.home"))

        user_info = {
            "username": user.username,
            "email": user.email
        }
        print(f"Debug: User info prepared: {user_info}")  # Debug log

        # Import and send feedback email
        from .email_utils import send_feedback_email
        print("Debug: Attempting to send feedback email")  # Debug log
        if send_feedback_email(feedback_text, user_info):
            print("Debug: Email sent successfully")  # Debug log
            flash("Thanks for your feedback! We'll review it soon.", "success")
        else:
            print("Debug: Failed to send email")  # Debug log
            flash("Thanks for your feedback! However, there was an issue sending it to our team.", "warning")
        
        return redirect(url_for("main.home"))
    except Exception as e:
        print(f"Debug: Error in feedback route: {str(e)}")  # Debug log
        import traceback
        traceback.print_exc()  # Print full error traceback
        flash("An error occurred while sending feedback.", "error")
        return redirect(url_for("main.home"))