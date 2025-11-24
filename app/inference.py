import os
import json
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array

# Constants
IMG_SIZE = (299, 299)
# Allow easy tuning via environment variable; default lowered to accept reasonable predictions
THRESHOLD = float(os.environ.get('PRED_THRESHOLD', '0.55'))  # Confidence threshold for predictions
TOP_K = 3

# Allowed species (normalized names) and helper map for aliases
KNOWN_SPECIES = {"curry", "neem", "aloevera", "hibiscus"}
SPECIES_NORMALIZATION = {
    "aloe_vera": "aloevera",
    "aloevera": "aloevera",
    "aloeveraa": "aloevera",
    "curry": "curry",
    "curry_leaves": "curry",
    "hibiscus": "hibiscus",
    "hibiscuss": "hibiscus",
    "neem": "neem",
}


def normalize_label(label):
    """Normalize raw model labels to one of the supported species."""
    if not label:
        return ""
    return SPECIES_NORMALIZATION.get(label.lower(), label.lower())


# Load model and label map
MODEL_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model", "xception_botanicure.h5")
LABELMAP_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model", "label_map.json")

model = load_model(MODEL_FILE)
with open(LABELMAP_FILE) as f:
    inv_map = json.load(f)

def predict_image(img_path):
    """Predict the plant type from an image file and return top-k candidates.

    Returns a dict with:
      - status: 'recognized' or 'unknown'
      - label, confidence for the top result (if available)
      - top_k: list of (label, confidence) tuples in descending order
    """
    img = load_img(img_path, target_size=IMG_SIZE)
    arr = img_to_array(img) / 255.0
    arr = np.expand_dims(arr, 0)
    probs = model.predict(arr)[0]

    # Get top-k indices and confidences
    top_idxs = np.argsort(probs)[::-1][:TOP_K]
    top_probs = probs[top_idxs]
    raw_labels = [inv_map.get(str(int(i)), inv_map.get(int(i), str(i))) for i in top_idxs]
    top_labels = [normalize_label(label) for label in raw_labels]
    top_k = [(label, float(conf)) for label, conf in zip(top_labels, top_probs)]

    best_idx = int(top_idxs[0])
    best_conf = float(top_probs[0])
    best_label = top_labels[0]

    # Debug: print top candidates (visible in server logs)
    try:
        print(f"[predict_image] img={img_path} best={best_label}:{best_conf:.4f} top_k={top_k}")
    except Exception:
        pass

    if best_conf < THRESHOLD or best_label not in KNOWN_SPECIES:
        return {
            "status": "unknown",
            "label": best_label,
            "confidence": best_conf,
            "top_k": top_k,
            "message": "No match found",
        }

    return {
        "status": "recognized",
        "label": best_label,
        "confidence": best_conf,
        "top_k": top_k,
    }
