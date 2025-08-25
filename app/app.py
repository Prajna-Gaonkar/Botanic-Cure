# app/app.py
import os, uuid, json
from flask import Flask, render_template, request, url_for
from app.inference import predict_image

UPLOAD_FOLDER = "app/static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")

# load plant info (create model/plant_info.json)
try:
    with open("model/plant_info.json") as f:
        PLANT_INFO = json.load(f)
except:
    PLANT_INFO = {}

@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
        file = request.files.get("image")
        if not file:
            return render_template("index.html", error="No file uploaded.")
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".jpg",".jpeg",".png"]:
            return render_template("index.html", error="Unsupported file type.")
        fname = f"{uuid.uuid4().hex}{ext}"
        fpath = os.path.join(UPLOAD_FOLDER, fname)
        file.save(fpath)
        res = predict_image(fpath)
        if res["status"] == "recognized":
            info = PLANT_INFO.get(res["label"], {})
            return render_template("result.html", label=res["label"], confidence=res["confidence"], info=info, img_url=url_for("static", filename=f"uploads/"+fname))
        else:
            return render_template("result.html", label="Unknown", confidence=res["confidence"], info=None, img_url=url_for("static", filename="uploads/"+fname))
    return render_template("index.html")
