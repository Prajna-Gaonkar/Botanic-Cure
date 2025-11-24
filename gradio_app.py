import os
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

def get_prediction_message(top_label, top_conf):
    """
    Returns a formatted message if the prediction is confident and known,
    otherwise returns the default 'no match' message.
    """
    if top_label in KNOWN_SPECIES and top_conf >= CONFIDENCE_THRESHOLD:
        info = PLANT_INFO.get(top_label, {})
        return f"Label: {top_label}\nConfidence: {top_conf:.2f}\nInfo: {info}"
    else:
        return "The uploaded image does not match any species the system is trained to identify."

def identify_leaf(image):
    # Save uploaded image temporarily
    temp_path = "temp_leaf.jpg"
    image.save(temp_path)
    try:
        result = predict_image(temp_path)
        # Defensive: get label/confidence from top_k if available
        top_k = result.get('top_k', [])
        if top_k:
            top_label, top_conf = top_k[0][0].lower(), top_k[0][1]
        else:
            top_label = result.get('label', '').lower()
            top_conf = result.get('confidence', 0)
        message = get_prediction_message(top_label, top_conf)
        return message, image
    except Exception as e:
        return f"Error: {str(e)}", image

iface = gr.Interface(
    fn=identify_leaf,
    inputs=gr.Image(type="pil"),
    outputs=[gr.Textbox(), gr.Image(type="pil")],
    title="Medical Leaf Identification System",
    description="Upload a leaf image to identify the plant."
)

if __name__ == "__main__":
    iface.launch()
