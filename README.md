# Medical Leaf Identification System – Installation & Usage Guide

## Prerequisites

- **Windows 10/11** (recommended)
- **Python 3.8+** (preferably 3.10 or 3.11)
- **Git** (optional, for cloning from a repository)
- **Internet connection** (for first-time setup and package installation)

---

## 1. Copy Project Files

- Copy the entire project folder (including all subfolders and files) from the CD to your computer, e.g., `D:\MedicalLeafID`.

---

## 2. Install Python

- Download Python from [python.org](https://www.python.org/downloads/).
- During installation, **check the box** that says “Add Python to PATH”.

---

## 3. Open Command Prompt

- Press `Win + R`, type `cmd`, and press Enter.
- Navigate to your project directory:
  ```
  cd D:\MedicalLeafID
  ```

---

## 4. Create a Virtual Environment (Recommended)

```
python -m venv venv
```
- Activate it:
  - On **Windows**:
    ```
    venv\Scripts\activate
    ```
  - On **Mac/Linux**:
    ```
    source venv/bin/activate
    ```

---

## 5. Install Required Packages

```
pip install -r requirements.txt
```

---

## 6. Set Up Environment Variables

- Edit the `.env` file in the project root.
- Make sure it contains your email settings (for feedback email to work). Example:
  ```
  SMTP_SERVER=smtp.gmail.com
  SMTP_PORT=587
  SMTP_EMAIL=your_email@gmail.com
  SMTP_PASSWORD=your_app_password
  OWNER_EMAIL=your_email@gmail.com
  FLASK_SECRET_KEY=your_secret_key
  ```
- **Tip:** For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833) if you have 2FA enabled.

---

## 7. Initialize the Database

- The database will be created automatically on first run. No manual steps needed.

---

## 8. Run the Application

```
python runserver.py
```
- The app will start and show a message like:
  ```
  * Running on http://127.0.0.1:5000
  ```
- Open this address in your web browser.

---

## 9. Using the Application

- **Upload a leaf image** (from your computer or, on mobile, directly from your camera).
- **Analyze** to get plant identification and medicinal info.
- **Send feedback** using the feedback form.
- **Toggle theme** using the moon button.
- **View history** and download reports.

---

## 10. Troubleshooting

- If you see errors about missing packages, run `pip install -r requirements.txt` again.
- If feedback email fails, double-check your `.env` email settings.
- For any other issues, check the terminal for error messages.

---

## 11. Optional: Gradio Interface

- To use the Gradio demo (if included), run:
  ```
  python gradio_app.py
  ```
- This will open a different interface in your browser.

---

**That’s it! Your Medical Leaf Identification System is ready to use.**
