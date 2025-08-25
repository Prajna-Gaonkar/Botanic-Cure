import os, random, shutil
from math import floor

SRC = "dataset_clean"
DST = "splits"
RATIOS = {"train": 0.7, "val": 0.15, "test": 0.15}
SEED = 42

random.seed(SEED)
os.makedirs(DST, exist_ok=True)

for cls in os.listdir(SRC):
    in_dir = os.path.join(SRC, cls)
    if not os.path.isdir(in_dir):
        continue
    files = [f for f in os.listdir(in_dir) if f.lower().endswith((".jpg",".jpeg",".png"))]
    random.shuffle(files)
    n = len(files)
    n_train = int(floor(RATIOS["train"] * n))
    n_val = int(floor(RATIOS["val"] * n))
    parts = {"train": files[:n_train], "val": files[n_train:n_train+n_val], "test": files[n_train+n_val:]}
    for subset, flist in parts.items():
        out_dir = os.path.join(DST, subset, cls)
        os.makedirs(out_dir, exist_ok=True)
        for f in flist:
            shutil.copy2(os.path.join(in_dir, f), os.path.join(out_dir, f))

print("Stratified split complete.")
