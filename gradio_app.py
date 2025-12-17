# --- Feedback functionality ---
import os
from dotenv import load_dotenv
import logging
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()
from app.email_utils import send_feedback_email
import json
import gradio as gr
from app.inference import predict_image

# Load plant info
PLANT_INFO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model", "plant_info.json")
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
    Returns a formatted message if the prediction is confident and known,
    otherwise returns the default 'no match' message.
    """
    if top_label in KNOWN_SPECIES and top_conf >= CONFIDENCE_THRESHOLD:
        info = PLANT_INFO.get(top_label, {})
        return f"Label: {top_label}\nConfidence: {top_conf:.2f}\nInfo: {info}"
    else:
        return NO_MATCH_MESSAGE

def identify_leaf(image):
    # Save uploaded image temporarily
    temp_path = "temp_leaf.jpg"
    image.save(temp_path)
    try:
        result = predict_image(temp_path)
        top_label = result.get('label', '').lower()
        top_conf = result.get('confidence', 0)
        top_k = result.get('top_k', [])
        if not top_label and top_k:
            top_label, top_conf = top_k[0][0].lower(), top_k[0][1]
        if result.get('status') != 'recognized':
            return NO_MATCH_MESSAGE, image
        message = get_prediction_message(top_label, top_conf)
        return message, image
    except Exception as e:
        return f"Error: {str(e)}", image

# --- Feedback functionality ---
FEEDBACK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_feedback.txt")

def submit_feedback(feedback_text):
    """
    Appends user feedback to a file and sends it to the admin via email.
    """
    try:
        with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
            f.write(feedback_text.strip() + "\n")
        # Send feedback to admin via email
        try:
            import os
            smtp_server = os.environ.get('SMTP_SERVER')
            print(f"[DEBUG] SMTP_SERVER env: {smtp_server}")
            email_result = send_feedback_email(feedback_text, user_info={"username": "Gradio User"})
        except Exception as email_error:
            logging.error(f"Feedback email error: {email_error}")
            return f"Feedback saved, but failed to notify admin via email: {email_error} (SMTP_SERVER={smtp_server})"
        if email_result:
            return "Thank you for your feedback! (Admin notified)"
        else:
            return "Feedback saved, but failed to notify admin via email."
    except Exception as e:
        logging.error(f"Feedback save error: {e}")
        return f"Error saving feedback: {str(e)}"

with gr.Blocks() as demo:
    gr.Markdown("# Medical Leaf Identification System\nUpload a leaf image to identify the plant.")
    with gr.Row():
        with gr.Column():
            image_input = gr.Image(type="pil", label="Upload Leaf Image")
            feedback_input = gr.Textbox(label="Your Feedback", lines=2, placeholder="Enter feedback here...")
            feedback_btn = gr.Button("Submit Feedback")
        with gr.Column():
            result_text = gr.Textbox(label="Result")
            result_image = gr.Image(type="pil", label="Input Image")
            feedback_output = gr.Textbox(label="Feedback Status", interactive=False)
    image_input.change(
        fn=identify_leaf,
        inputs=image_input,
        outputs=[result_text, result_image]
    )
    feedback_btn.click(
        fn=submit_feedback,
        inputs=feedback_input,
        outputs=feedback_output
    )

if __name__ == "__main__":
    demo.launch()
