import os
import uuid
import json
import traceback
from flask import Blueprint, render_template, request, url_for, redirect, session, flash

from .inference import predict_image
from .models import User
from .email_utils import send_feedback_email

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

# Define known species
KNOWN_SPECIES = {"curry", "hibiscus", "neem", "aloevera"}
CONFIDENCE_THRESHOLD = 0.6  # You can adjust this value as needed
NO_MATCH_MESSAGE = "No match found"

def get_prediction_message(top_label, top_conf):
    """
    Returns True and info if the prediction is confident and known,
    otherwise returns False and the default 'no match' message.
    """
    if top_label in KNOWN_SPECIES and top_conf >= CONFIDENCE_THRESHOLD:
        plant_info = PLANT_INFO.get(top_label, {})
        return True, plant_info
    else:
        return False, None

@main_bp.route('/')
def index():
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))
    return redirect(url_for('main.home'))

@main_bp.route('/home', methods=['GET', 'POST'])
def home():
    if not session.get('user_id'):
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.login'))
    
    username = session.get('username', 'User')
    
    if request.method == 'POST':
        if 'leaf_image' not in request.files:
            flash('No file uploaded.', 'error')
            return render_template('home.html', username=username)
            
        file = request.files['leaf_image']
        if file.filename == '':
            flash('No file selected.', 'error')
            return render_template('home.html', username=username)
            
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            flash('Invalid file type. Please upload a PNG or JPEG image.', 'error')
            return render_template('home.html', username=username)
            
        # Save the file
        filename = f"{uuid.uuid4().hex}{os.path.splitext(file.filename)[1]}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        try:
            # Get prediction
            result = predict_image(filepath)
            top_k = result.get('top_k', [])
            top_label = result.get('label', '').lower()
            top_conf = result.get('confidence', 0)
            if not top_label and top_k:
                top_label, top_conf = top_k[0][0].lower(), top_k[0][1]

            if result.get('status') != 'recognized':
                flash(NO_MATCH_MESSAGE, 'warning')
                return render_template('home.html',
                    username=username,
                    img_url=url_for('static', filename=f'uploads/{filename}'),
                    no_match_message=NO_MATCH_MESSAGE
                )

            is_match, plant_info = get_prediction_message(top_label, top_conf)
            if is_match:
                return render_template('home.html',
                    username=username,
                    img_url=url_for('static', filename=f'uploads/{filename}'),
                    label=top_label,
                    confidence=top_conf,
                    info=plant_info,
                    top_k=top_k
                )
            else:
                flash(NO_MATCH_MESSAGE, 'warning')
                return render_template('home.html',
                    username=username,
                    img_url=url_for('static', filename=f'uploads/{filename}'),
                    no_match_message=NO_MATCH_MESSAGE
                )
                
        except Exception as e:
            flash(f'Error processing image: {str(e)}', 'error')
            return render_template('home.html', username=username)
    
    return render_template('home.html', username=username)

@main_bp.route('/feedback', methods=['POST'])
def feedback():
    if not session.get('user_id'):
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.login'))
        
    feedback_text = request.form.get('feedback', '').strip()
    if feedback_text:
        user_info = {
            "username": session.get('username', 'User')
        }
        try:
            user = User.query.filter_by(id=session.get('user_id')).first()
            if user:
                user_info['email'] = user.email
        except Exception:
            pass  # Non-blocking; feedback can still be sent without email

        try:
            if send_feedback_email(feedback_text, user_info):
                flash('Thank you! Your feedback was sent to the app owner.', 'success')
            else:
                flash('Unable to send feedback right now. Please try again later.', 'error')
        except Exception as e:
            flash(f'Failed to send feedback: {str(e)}', 'error')
    else:
        flash('Feedback cannot be empty.', 'warning')
        
    return redirect(url_for('main.home'))