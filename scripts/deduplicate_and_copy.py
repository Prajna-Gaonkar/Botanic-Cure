import os
from PIL import Image
import imagehash
import shutil

SRC = "dataset_raw"
DST = "dataset_clean"
HASH_THRESHOLD = 5  # lower = stricter

os.makedirs(DST, exist_ok=True)

for cls in os.listdir(SRC):
    src_cls = os.path.join(SRC, cls)
    dst_cls = os.path.join(DST, cls)
    if not os.path.isdir(src_cls):
        continue
    os.makedirs(dst_cls, exist_ok=True)
    hashes = []
    kept = 0
    files = [f for f in os.listdir(src_cls) if f.lower().endswith((".jpg",".jpeg",".png"))]
    for fname in files:
        src_path = os.path.join(src_cls, fname)
        try:
            img = Image.open(src_path).convert("RGB")
            h = imagehash.phash(img)
        except Exception as e:
            print("Skipping unreadable:", src_path, e)
            continue
        if any((h - old) <= HASH_THRESHOLD for old in hashes):
            continue
        hashes.append(h)
        kept += 1
        dst_name = f"{cls}_{kept:04d}.jpg"
        shutil.copy2(src_path, os.path.join(dst_cls, dst_name))

print("Deduplication & copy complete.")
