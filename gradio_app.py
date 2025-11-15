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

def identify_leaf(image):
    # Save uploaded image temporarily
    temp_path = "temp_leaf.jpg"
    image.save(temp_path)
    try:
        result = predict_image(temp_path)
        top_k = result.get('top_k', [])
        if result.get('status') == 'recognized':
            label = result['label']
            confidence = result['confidence']
            info = PLANT_INFO.get(label, {})
            return f"Label: {label}\nConfidence: {confidence:.2f}\nInfo: {info}", image
        else:
            candidates = "\n".join([f"{c['label']} ({c['confidence']:.2f})" for c in top_k])
            return f"Could not confidently identify. Top candidates:\n{candidates}", image
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
