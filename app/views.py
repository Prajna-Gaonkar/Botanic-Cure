import os
import uuid
import json
import traceback
from flask import Blueprint, render_template, request, url_for, redirect, session, flash

from .inference import predict_image

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
            
            if result['status'] == 'recognized':
                label = result['label']
                confidence = result['confidence']
                plant_info = PLANT_INFO.get(label, {})
                
                return render_template('home.html',
                    username=username,
                    img_url=url_for('static', filename=f'uploads/{filename}'),
                    label=label,
                    confidence=confidence,
                    info=plant_info
                )
            else:
                flash('Could not identify the plant in this image.', 'warning')
                return render_template('home.html',
                    username=username,
                    img_url=url_for('static', filename=f'uploads/{filename}')
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
        flash('Thank you for your feedback!', 'success')
    else:
        flash('Feedback cannot be empty.', 'warning')
        
    return redirect(url_for('main.home'))