# Smart Finance Guardian (Flask)

A lightweight Flask app that accepts receipt images, extracts amounts (OCR if available), stores entries in a local `data.json`, predicts yearly expenses and a simple financial distress probability, and offers basic advice. Uploads are saved to the `uploads/` folder.

## How to run locally

1. (Optional) Create a virtualenv:
   ```bash
   python -m venv venv
   source venv/bin/activate   # on Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. (Optional) Install Tesseract for OCR:
   - On Ubuntu: `sudo apt-get install tesseract-ocr`
   - On Windows: install from https://github.com/tesseract-ocr/tesseract and ensure it's in PATH

3. Train models (creates `models/*.pkl`) if not present:
   ```bash
   python train_models.py
   ```

4. Run the app:
   ```bash
   python app.py
   ```

5. Open http://127.0.0.1:5000 in your browser.

Notes:
- The app gracefully handles missing OCR by asking for manual amount input after upload.
- The LLM/Chat components are replaced by simple rule-based advice to avoid external API dependencies in the starter project.