import io
import os
import uuid
import json
from flask import Blueprint, render_template, request, url_for, redirect, session, flash, send_file, abort

from pdf2image import convert_from_path
from fpdf import FPDF

from . import db
from .inference import predict_image
from .models import User, UploadHistory
from .email_utils import send_feedback_email
from .translations import SUPPORTED_LANGUAGES, TRANSLATIONS, get_translation

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
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.pdf'}

DEFAULT_LANGUAGE = "en"


def get_current_language():
    lang = session.get("language", DEFAULT_LANGUAGE)
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE
    return lang

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


def is_allowed_file(filename):
    return '.' in filename and os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def record_upload_history(user_id, original_filename, stored_filename, preview_filename, status, label, confidence):
    """Persist upload attempt for later display; failures are logged but non-blocking."""
    try:
        entry = UploadHistory(
            user_id=user_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            preview_filename=preview_filename,
            status=status,
            label=label,
            confidence=confidence,
        )
        db.session.add(entry)
        db.session.commit()
        return entry
    except Exception as history_error:
        db.session.rollback()
        print(f"[upload_history] Failed to persist history: {history_error}")
        return None


def build_report_pdf(entry, plant_info):
    """Create a PDF report for a recognized prediction."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Botanic Cure Analysis Report", ln=True)

    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 8, f"Generated for: {entry.original_filename}", ln=True)
    pdf.cell(0, 8, f"Prediction: {entry.label or 'Unknown'}", ln=True)
    if entry.confidence is not None:
        pdf.cell(0, 8, f"Confidence: {entry.confidence * 100:.2f}%", ln=True)
    pdf.cell(0, 8, f"Status: {entry.status}", ln=True)
    pdf.cell(0, 8, f"Created At: {entry.created_at.strftime('%Y-%m-%d %H:%M')}", ln=True)

    image_name = entry.preview_filename or entry.stored_filename
    if image_name:
        image_path = os.path.join(UPLOAD_FOLDER, image_name)
        if os.path.exists(image_path) and image_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            pdf.ln(5)
            width = 120
            pdf.image(image_path, w=width)

    if plant_info:
        pdf.ln(8)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Medicinal Information", ln=True)
        pdf.set_font("Helvetica", size=11)
        for key in ("common_name", "scientific_name", "common_growing_areas", "medicinal_properties", "toxic_properties", "storage_methods"):
            value = plant_info.get(key)
            if value:
                pretty_key = key.replace("_", " ").title()
                pdf.multi_cell(0, 7, f"{pretty_key}: {value}")
                pdf.ln(1)

    pdf_bytes = pdf.output(dest="S")
    buffer = io.BytesIO(pdf_bytes)
    buffer.seek(0)
    return buffer

@main_bp.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('main.home'))
    return render_template('get_started.html')

@main_bp.route('/home', methods=['GET', 'POST'])
def home():
    if not session.get('user_id'):
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.login'))
    
    username = session.get('username', 'User')
    current_lang = get_current_language()
    translations = TRANSLATIONS.get(current_lang, TRANSLATIONS[DEFAULT_LANGUAGE])
    
    if request.method == 'POST':
        if 'leaf_image' not in request.files:
            flash('No file uploaded.', 'error')
            return render_template('home.html',
                username=username,
                translations=translations,
                language_options=SUPPORTED_LANGUAGES,
                current_language=current_lang,
                history_id=None
            )
            
        file = request.files['leaf_image']
        if file.filename == '':
            flash('No file selected.', 'error')
            return render_template('home.html',
                username=username,
                translations=translations,
                language_options=SUPPORTED_LANGUAGES,
                current_language=current_lang,
                history_id=None
            )
            
        if not is_allowed_file(file.filename):
            flash('Invalid file type. Please upload only PDF, JPG, or PNG files.', 'error')
            return render_template('home.html',
                username=username,
                translations=translations,
                language_options=SUPPORTED_LANGUAGES,
                current_language=current_lang,
                history_id=None
            )
            
        # Save the file
        original_filename = file.filename
        filename = f"{uuid.uuid4().hex}{os.path.splitext(file.filename)[1]}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        file_ext = os.path.splitext(filename)[1].lower()
        is_pdf = file_ext == '.pdf'
        preview_filename = None
        display_filename = filename
        prediction_path = filepath
        if is_pdf:
            try:
                poppler_path = os.environ.get('POPPLER_PATH')
                pdf_images = convert_from_path(filepath, first_page=1, last_page=1, poppler_path=poppler_path)
                if not pdf_images:
                    raise ValueError("No renderable pages detected.")
                preview_filename = f"{uuid.uuid4().hex}.png"
                preview_path = os.path.join(UPLOAD_FOLDER, preview_filename)
                pdf_images[0].save(preview_path, 'PNG')
                prediction_path = preview_path
                display_filename = preview_filename
            except Exception as pdf_error:
                if preview_filename:
                    preview_path = os.path.join(UPLOAD_FOLDER, preview_filename)
                    if os.path.exists(preview_path):
                        os.remove(preview_path)
                flash(f'Unable to process PDF file: {pdf_error}', 'error')
                return render_template('home.html',
                    username=username,
                    translations=translations,
                    language_options=SUPPORTED_LANGUAGES,
                    current_language=current_lang,
                    history_id=None
                )
        
        img_url = url_for('static', filename=f'uploads/{display_filename}') if display_filename else None
        
        try:
            # Get prediction
            result = predict_image(prediction_path)
            top_k = result.get('top_k', [])
            top_label = result.get('label', '').lower()
            top_conf = result.get('confidence', 0)
            if not top_label and top_k:
                top_label, top_conf = top_k[0][0].lower(), top_k[0][1]

            if result.get('status') != 'recognized':
                flash(translations['no_match_flash'], 'warning')
                record_upload_history(
                    user_id=session.get('user_id'),
                    original_filename=original_filename,
                    stored_filename=filename,
                    preview_filename=preview_filename,
                    status='unknown',
                    label=top_label,
                    confidence=top_conf,
                )
                return render_template('home.html',
                    username=username,
                    img_url=img_url,
                    no_match_message=translations['no_match_banner'],
                    translations=translations,
                    language_options=SUPPORTED_LANGUAGES,
                    current_language=current_lang,
                    history_id=None
                )

            is_match, plant_info = get_prediction_message(top_label, top_conf)
            if is_match:
                history_entry = record_upload_history(
                    user_id=session.get('user_id'),
                    original_filename=original_filename,
                    stored_filename=filename,
                    preview_filename=preview_filename,
                    status='recognized',
                    label=top_label,
                    confidence=top_conf,
                )
                return render_template('home.html',
                    username=username,
                    img_url=img_url,
                    label=top_label,
                    confidence=top_conf,
                    info=plant_info,
                    top_k=top_k,
                    translations=translations,
                    language_options=SUPPORTED_LANGUAGES,
                    current_language=current_lang,
                    history_id=history_entry.id if history_entry else None
                )
            else:
                flash(translations['no_match_flash'], 'warning')
                record_upload_history(
                    user_id=session.get('user_id'),
                    original_filename=original_filename,
                    stored_filename=filename,
                    preview_filename=preview_filename,
                    status='unknown',
                    label=top_label,
                    confidence=top_conf,
                )
                return render_template('home.html',
                    username=username,
                    img_url=img_url,
                    no_match_message=translations['no_match_banner'],
                    translations=translations,
                    language_options=SUPPORTED_LANGUAGES,
                    current_language=current_lang,
                    history_id=None
                )
                
        except Exception as e:
            flash(f'Error processing image: {str(e)}', 'error')
            return render_template('home.html',
                username=username,
                translations=translations,
                language_options=SUPPORTED_LANGUAGES,
                current_language=current_lang,
                history_id=None
            )
    
    return render_template('home.html',
        username=username,
        translations=translations,
        language_options=SUPPORTED_LANGUAGES,
        current_language=current_lang,
        history_id=None
    )


@main_bp.route('/history')
def history():
    if not session.get('user_id'):
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.login'))

    username = session.get('username', 'User')
    current_lang = get_current_language()
    translations = TRANSLATIONS.get(current_lang, TRANSLATIONS[DEFAULT_LANGUAGE])
    entries = (UploadHistory.query
               .filter_by(user_id=session.get('user_id'))
               .order_by(UploadHistory.created_at.desc())
               .all())

    return render_template('history.html',
        username=username,
        entries=entries,
        translations=translations,
        language_options=SUPPORTED_LANGUAGES,
        current_language=current_lang
    )


@main_bp.route('/history/<int:entry_id>/download')
def download_report(entry_id):
    if not session.get('user_id'):
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.login'))

    entry = UploadHistory.query.filter_by(id=entry_id, user_id=session.get('user_id')).first()
    if not entry:
        abort(404)

    if entry.status != 'recognized':
        flash('Reports are available only for recognized predictions.', 'warning')
        return redirect(request.referrer or url_for('main.history'))

    plant_info = PLANT_INFO.get((entry.label or '').lower(), {})
    pdf_buffer = build_report_pdf(entry, plant_info)
    safe_label = (entry.label or 'report').replace(' ', '_')
    filename = f"botanic_cure_{safe_label}.pdf"
    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name=filename)

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

        current_lang = get_current_language()
        try:
            import os
            smtp_server = os.environ.get('SMTP_SERVER')
            print(f"[DEBUG] SMTP_SERVER env (Flask): {smtp_server}")
            if send_feedback_email(feedback_text, user_info):
                flash(get_translation(current_lang, 'flash_feedback_success'), 'success')
            else:
                flash(get_translation(current_lang, 'flash_feedback_fail'), 'error')
        except Exception as e:
            flash(f'Failed to send feedback: {str(e)} (SMTP_SERVER={smtp_server})', 'error')
    else:
        flash(get_translation(get_current_language(), 'flash_feedback_empty'), 'warning')
        
    return redirect(url_for('main.home'))


@main_bp.route('/set-language', methods=['POST'])
def set_language():
    if not session.get('user_id'):
        flash('Please log in first.', 'warning')
        return redirect(url_for('auth.login'))
    new_lang = request.form.get('language', DEFAULT_LANGUAGE)
    if new_lang not in SUPPORTED_LANGUAGES:
        new_lang = DEFAULT_LANGUAGE
    session['language'] = new_lang
    return redirect(request.referrer or url_for('main.home'))