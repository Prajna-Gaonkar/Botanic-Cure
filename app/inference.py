import os
import json
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array

# Constants
IMG_SIZE = (299, 299)
THRESHOLD = 0.75  # Confidence threshold for predictions

# Load model and label map
MODEL_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model", "xception_botanicure.h5")
LABELMAP_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model", "label_map.json")

model = load_model(MODEL_FILE)
with open(LABELMAP_FILE) as f:
    inv_map = json.load(f)

def predict_image(img_path):
    """
    Predict the plant type from an image file
    
    Args:
        img_path (str): Path to the image file
        
    Returns:
        dict: Prediction result with status, label (if recognized), and confidence
    """
    img = load_img(img_path, target_size=IMG_SIZE)
    arr = img_to_array(img) / 255.0
    arr = np.expand_dims(arr, 0)
    probs = model.predict(arr)[0]
    idx = int(np.argmax(probs))
    confidence = float(np.max(probs))
    label = inv_map.get(str(idx), inv_map.get(idx, None))
    
    if confidence < THRESHOLD:
        return {"status": "unknown", "confidence": confidence}
    return {"status": "recognized", "label": label, "confidence": confidence}
