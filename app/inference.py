# app/inference.py
import json, numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array

MODEL_FILE = "model/xception_botanicure.h5"
LABELMAP_FILE = "model/label_map.json"
IMG_SIZE = (299,299)
THRESHOLD = 0.75  # tune this later

model = load_model(MODEL_FILE)
with open(LABELMAP_FILE) as f:
    inv_map = json.load(f)

def predict_image(img_path):
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
