from flask import Flask, render_template, request, redirect, url_for, jsonify
import os, json, datetime, traceback
from werkzeug.utils import secure_filename
import re
import numpy as np
import pickle

UPLOAD_FOLDER = 'uploads'
DATA_FILE = 'data.json'
REG_MODEL = 'models/regression_model.pkl'
CLF_MODEL = 'models/classification_model.pkl'
ALLOWED_EXT = {'png','jpg','jpeg','gif','pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Utility: load / save json data
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE,'w') as f:
            json.dump([], f)
    with open(DATA_FILE,'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE,'w') as f:
        json.dump(data, f, indent=2)

# Simple amount extraction from text (very small heuristic)
def extract_amounts_from_text(text):
    # find currency-like numbers
    nums = re.findall(r'(?<!\d)(?:\d{1,3}(?:[,\s]\d{3})+|\d+)(?:\.\d{1,2})?', text.replace('₹','').replace('Rs.','').replace('INR',''))
    amounts = []
    for n in nums:
        try:
            val = float(n.replace(',','').replace(' ','').strip())
            amounts.append(val)
        except:
            pass
    return amounts

# OCR attempt (optional)
def try_ocr(filepath):
    try:
        import pytesseract
        from PIL import Image
        text = pytesseract.image_to_string(Image.open(filepath))
        return text
    except Exception as e:
        # OCR not available or failed; return empty
        return ""

# Load models if present
def load_models():
    reg = clf = None
    if os.path.exists(REG_MODEL):
        try:
            with open(REG_MODEL,'rb') as f:
                reg = pickle.load(f)
        except:
            reg = None
    if os.path.exists(CLF_MODEL):
        try:
            with open(CLF_MODEL,'rb') as f:
                clf = pickle.load(f)
        except:
            clf = None
    return reg, clf

reg_model, clf_model = load_models()

@app.route('/')
def index():
    data = load_data()
    # basic summary
    today = datetime.date.today().isoformat()
    todays = [d for d in data if d.get('date')==today]
    total_today = sum(item.get('amount',0) for item in todays)
    total_month = sum(item.get('amount',0) for item in data if item.get('date', '')[:7]==today[:7])
    health_score = max(0, 100 - min(100, int((total_month/100000)*100)))  # very rough scoring
    return render_template('index.html', total_today=total_today, total_month=total_month, health_score=health_score, todays=todays)

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'receipt' not in request.files:
            return "No file part", 400
        file = request.files['receipt']
        if file.filename == '':
            return "No selected file", 400
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        # try OCR
        text = try_ocr(save_path)
        amounts = extract_amounts_from_text(text)
        extracted = amounts[0] if amounts else None
        # Save an entry with extracted (or None) and OCR text for manual correction
        entry = {
            "date": datetime.date.today().isoformat(),
            "filename": filename,
            "extracted_amount": extracted,
            "ocr_text": text[:200]  # store a snippet
        }
        data = load_data()
        data.append(entry)
        save_data(data)
        # If OCR failed to find amount, prompt user to manual entry via JSON response
        if extracted is None:
            return jsonify({"status":"ok","message":"uploaded","need_manual_amount":True,"entry":entry})
        else:
            # run prediction on extracted amount
            pred = predict_from_amount(float(extracted))
            entry.update(pred)
            save_data(data)
            return jsonify({"status":"ok","message":"uploaded","need_manual_amount":False,"entry":entry})
    except Exception as e:
        traceback.print_exc()
        return str(e), 500

@app.route('/manual-entry', methods=['POST'])
def manual_entry():
    try:
        amount = float(request.form.get('amount',0))
        category = request.form.get('category','Misc')
        date = request.form.get('date', datetime.date.today().isoformat())
        entry = {
            "date": date,
            "amount": amount,
            "category": category,
            "source":"manual"
        }
        data = load_data()
        data.append(entry)
        # predict
        pred = predict_from_amount(amount)
        entry.update(pred)
        save_data(data)
        return redirect(url_for('result'))
    except Exception as e:
        traceback.print_exc()
        return str(e), 500

@app.route('/result')
def result():
    data = load_data()
    # latest entry
    latest = data[-1] if data else {}
    # category breakdown
    breakdown = {}
    for d in data:
        cat = d.get('category','Misc')
        breakdown[cat] = breakdown.get(cat,0) + d.get('amount',0)
    return render_template('result.html', latest=latest, breakdown=breakdown, data=data)

def predict_from_amount(amount):
    # Load models if not loaded
    global reg_model, clf_model
    if reg_model is None or clf_model is None:
        reg_model, clf_model = load_models()
    # Simple fallback prediction rules if models missing
    if reg_model is None:
        # assume daily amount * 365 gives yearly expense
        predicted_annual = amount * 365
    else:
        try:
            predicted_annual = float(reg_model.predict([[amount]])[0])
        except:
            predicted_annual = amount * 365
    if clf_model is None:
        # simple distress probability heuristic: if predicted annual expense > threshold
        distress_prob = min(1.0, predicted_annual / 100000.0)
    else:
        try:
            distress_prob = float(clf_model.predict_proba([[amount, predicted_annual]])[0][1])
        except:
            distress_prob = min(1.0, predicted_annual / 100000.0)
    # Simple savings estimate: assume fixed income (can be extended)
    assumed_income = 100000.0  # placeholder
    predicted_savings = max(0.0, assumed_income - predicted_annual)
    advice = generate_advice(predicted_annual, predicted_savings, distress_prob)
    return {
        "predicted_annual_expense": round(predicted_annual,2),
        "predicted_annual_savings": round(predicted_savings,2),
        "distress_probability": round(distress_prob,3),
        "advice": advice
    }

def generate_advice(predicted_annual, predicted_savings, distress_prob):
    tips = []
    if distress_prob > 0.6:
        tips.append("High risk detected: consider immediately reviewing recurring subscriptions and non-essential spending.")
    if predicted_savings < 0:
        tips.append("Projected savings negative: prioritize reducing expenses or increasing income.")
    if predicted_annual > 50000:
        tips.append("Your projected annual expense seems high; try cutting discretionary spending by 10% to start.")
    if not tips:
        tips.append("Your finances look stable for now. Maintain an emergency fund of 3-6 months of expenses.")
    return " ".join(tips)

@app.route('/predict', methods=['GET'])
def predict_route():
    # Aggregate data and run forecasting using simple rule or model if present
    data = load_data()
    amounts = [d.get('amount') for d in data if d.get('amount') is not None]
    if not amounts:
        return jsonify({"error":"no data"}), 400
    avg_daily = sum(amounts)/len(amounts)
    predicted_annual = avg_daily * 365
    # distress heuristic
    distress_prob = min(1.0, predicted_annual / 100000.0)
    return jsonify({"predicted_annual_expense":predicted_annual, "predicted_annual_savings": max(0,100000-predicted_annual), "distress_probability": distress_prob})

@app.route('/insights', methods=['GET'])
def insights_route():
    # Provide simple rule-based insights (LLM placeholder)
    data = load_data()
    breakdown = {}
    for d in data:
        cat = d.get('category','Misc')
        breakdown[cat] = breakdown.get(cat,0) + d.get('amount',0)
    sorted_cats = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
    top = sorted_cats[0] if sorted_cats else ("None",0)
    message = f"Top spending category: {top[0]} with total {top[1]}. Consider reducing this by 10%."
    return jsonify({"insights": message})

if __name__ == '__main__':
    # Ensure folders exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    # Ensure data file exists
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE,'w') as f:
            json.dump([], f)
    app.run(host='0.0.0.0', port=5000, debug=True)