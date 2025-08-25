# scripts/train_xception.py
import os, json
import tensorflow as tf
from tensorflow.keras.applications import Xception
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau, TensorBoard
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.utils.class_weight import compute_class_weight
import numpy as np

# -----------------------------
# Config
# -----------------------------
IMG_SIZE = (299, 299)
BATCH_SIZE = 16
STAGE1_EPOCHS = 15
STAGE2_EPOCHS = 10
MODEL_DIR = "model"
MODEL_FILE = os.path.join(MODEL_DIR, "xception_botanicure.h5")
LABELMAP_FILE = os.path.join(MODEL_DIR, "label_map.json")
LOGDIR = "logs/xception"
SEED = 42
os.makedirs(MODEL_DIR, exist_ok=True)
tf.random.set_seed(SEED)

# -----------------------------
# Data generators
# -----------------------------
train_datagen = ImageDataGenerator(
    rescale=1.0/255.0,
    rotation_range=20,
    width_shift_range=0.1,
    height_shift_range=0.1,
    zoom_range=0.1,
    horizontal_flip=True,
    brightness_range=(0.8, 1.2),
    fill_mode="nearest"
)

val_datagen = ImageDataGenerator(rescale=1.0/255.0)

train_dir = "splits/train"
val_dir   = "splits/val"

train_gen = train_datagen.flow_from_directory(
    train_dir,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="categorical",
    shuffle=True,
    seed=SEED
)

val_gen = val_datagen.flow_from_directory(
    val_dir,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="categorical",
    shuffle=False
)

# Save label map (index -> class name)
inv_map = {v: k for k, v in train_gen.class_indices.items()}
with open(LABELMAP_FILE, "w") as f:
    json.dump(inv_map, f, indent=2)
print("Saved label map to", LABELMAP_FILE)

# -----------------------------
# Compute optional class weights
# -----------------------------
y = train_gen.classes
classes = np.unique(y)
cw = compute_class_weight(class_weight="balanced", classes=classes, y=y)
class_weight = {int(i): float(w) for i, w in enumerate(cw)}
print("Class weights:", class_weight)

# -----------------------------
# Build model
# -----------------------------
base = Xception(weights="imagenet", include_top=False, input_shape=(*IMG_SIZE, 3))
x = GlobalAveragePooling2D()(base.output)
x = Dense(256, activation="relu")(x)
x = Dropout(0.3)(x)
outputs = Dense(train_gen.num_classes, activation="softmax")(x)
model = Model(inputs=base.input, outputs=outputs)

# -----------------------------
# Callbacks
# -----------------------------
cb_list = [
    EarlyStopping(monitor="val_loss", patience=6, restore_best_weights=True, verbose=1),
    ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3, min_lr=1e-6, verbose=1),
    ModelCheckpoint(MODEL_FILE, monitor="val_accuracy", save_best_only=True, verbose=1),
    TensorBoard(log_dir=LOGDIR)
]

# -----------------------------
# Stage 1: Train head (freeze base)
# -----------------------------
for layer in base.layers:
    layer.trainable = False

model.compile(optimizer=tf.keras.optimizers.Adam(1e-3),
              loss="categorical_crossentropy", metrics=["accuracy"])

print("Stage 1: training head (base frozen)")
history1 = model.fit(
    train_gen,
    validation_data=val_gen,
    epochs=STAGE1_EPOCHS,
    callbacks=cb_list,
    class_weight=class_weight,
    verbose=1
)

# -----------------------------
# Stage 2: Fine-tune top of base
# -----------------------------
# Unfreeze whole base, then freeze the earlier layers, keep the top blocks trainable
for layer in base.layers:
    layer.trainable = True

# Option: freeze the first N layers (tune N if needed)
freeze_until = len(base.layers) - 40  # unfreeze last ~40 layers
for i, layer in enumerate(base.layers):
    if i < freeze_until:
        layer.trainable = False

model.compile(optimizer=tf.keras.optimizers.Adam(3e-5),
              loss="categorical_crossentropy", metrics=["accuracy"])

print("Stage 2: fine-tuning top base layers")
history2 = model.fit(
    train_gen,
    validation_data=val_gen,
    epochs=STAGE2_EPOCHS,
    callbacks=cb_list,
    class_weight=class_weight,
    verbose=1
)

print("Training finished. Best model saved to:", MODEL_FILE)
