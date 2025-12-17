from dotenv import load_dotenv
load_dotenv(override=True)
from app import create_app, db

from dotenv import load_dotenv
load_dotenv(override=True)

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)