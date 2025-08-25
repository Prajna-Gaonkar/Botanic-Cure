# scripts/evaluate.py
import os, json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator

MODEL_FILE = "model/xception_botanicure.h5"
LABELMAP_FILE = "model/label_map.json"
IMG_SIZE = (299,299)
BATCH = 16

with open(LABELMAP_FILE) as f:
    inv_map = json.load(f)  # index -> class_name

# Create ordered class list from inv_map keys (keys are strings if saved that way)
ordered_indices = sorted([int(k) for k in inv_map.keys()])
classes = [inv_map[str(i)] if str(i) in inv_map else inv_map[i] for i in ordered_indices]

test_gen = ImageDataGenerator(rescale=1.0/255.0).flow_from_directory(
    "splits/test", target_size=IMG_SIZE, batch_size=BATCH, class_mode="categorical", shuffle=False
)

model = load_model(MODEL_FILE)
probs = model.predict(test_gen, verbose=1)
y_pred = np.argmax(probs, axis=1)
y_true = test_gen.classes

print("\nClassification Report:\n")
print(classification_report(y_true, y_pred, target_names=classes, digits=4))

cm = confusion_matrix(y_true, y_pred)
plt.figure(figsize=(8,6))
plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
plt.title("Confusion Matrix")
plt.colorbar()
plt.xticks(range(len(classes)), classes, rotation=45, ha="right")
plt.yticks(range(len(classes)), classes)
plt.ylabel("True label")
plt.xlabel("Predicted label")
plt.tight_layout()
os.makedirs("model", exist_ok=True)
plt.savefig("model/confusion_matrix.png", dpi=150)
print("Saved confusion matrix to model/confusion_matrix.png")
