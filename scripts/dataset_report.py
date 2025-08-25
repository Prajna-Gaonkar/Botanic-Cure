import os
splits = ["train","val","test"]
classes = sorted(next(os.walk("splits/train"))[1]) if os.path.isdir("splits/train") else []
print("Dataset report:")
total = 0
for s in splits:
    subtotal = 0
    print(f"\n{s.upper()}:")
    for cls in classes:
        p = os.path.join("splits", s, cls)
        cnt = len([f for f in os.listdir(p) if f.lower().endswith((".jpg",".jpeg",".png"))]) if os.path.isdir(p) else 0
        print(f"  {cls}: {cnt}")
        subtotal += cnt
    print(f"  subtotal: {subtotal}")
    total += subtotal
print(f"\nTotal images: {total}")
