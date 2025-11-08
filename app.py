from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_cors import CORS
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
CORS(app)  # Enable CORS for all routes
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize EasyOCR reader (lazy loading)
ocr_reader = None

def get_ocr_reader():
    """Lazy initialization of EasyOCR reader"""
    global ocr_reader
    if ocr_reader is None:
        try:
            import easyocr
            print("Initializing EasyOCR reader...")
            ocr_reader = easyocr.Reader(['en'], gpu=False)  # Set gpu=True if you have CUDA
            print("EasyOCR reader initialized successfully!")
        except Exception as e:
            print(f"Error initializing EasyOCR: {e}")
            ocr_reader = False
    return ocr_reader if ocr_reader is not False else None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

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

# Enhanced amount extraction from text
def extract_amounts_from_text(text):
    """Extract monetary amounts from text with improved patterns"""
    if not text:
        return []
    
    # CRITICAL FIX: Clean up misread rupee symbols that appear as digits
    # OCR often misreads ₹ symbol as "2" when followed by numbers
    # Only apply this fix in UPI/payment contexts where we expect small amounts
    # Look for patterns like "Paid to ... 21,750" or "Debited ... 21,750"
    text_cleaned = text
    
    # Check if this looks like a UPI/payment receipt (strong indicators)
    is_upi_context = bool(re.search(
        r'(?:PAID\s+TO|DEBITED|CREDITED|TRANSACTION|UPI|TRANSFER|UTR)',
        text.upper()
    ))
    
    if is_upi_context:
        # In UPI context, amounts like "21,750" are suspicious (likely ₹1,750)
        # But "21,750.50" or amounts > 22,000 are likely legitimate
        # Pattern: fix "2X,XXX" where X is 1-9 (e.g., 21,750 but not 22,000 or higher)
        text_cleaned = re.sub(r'\b2([1-9],\d{3})(?![,\d])\b', r'\1', text_cleaned)  # 21,750 -> 1,750 (not followed by more digits)
        text_cleaned = re.sub(r'\b2([1-9]\d{2,3})(?![,\d])\b', r'\1', text_cleaned)   # 21750 -> 1750 (3-4 digits after 2)
        
        if text != text_cleaned:
            print(f"⚠️ UPI context detected - fixed likely rupee symbol misread (₹ → '2')")
    
    # Convert to uppercase for easier matching
    text_upper = text_cleaned.upper()
    amounts = []
    amount_contexts = []  # Store (amount, context_score) tuples
    
    # High priority patterns - look for keywords like TOTAL, AMOUNT, etc.
    priority_patterns = [
        (r'(?:TOTAL|GRAND\s*TOTAL|NET\s*TOTAL|AMOUNT\s*PAYABLE|BILL\s*AMOUNT|INVOICE\s*TOTAL)[\s:]*(?:RS\.?|₹|INR)?\s*(\d+(?:[,\s]\d{3})*(?:\.\d{1,2})?)', 100),
        (r'(?:TO\s*PAY|PAYABLE|BALANCE|DUE|BALANCE\s*DUE)[\s:]*(?:RS\.?|₹|INR)?\s*(\d+(?:[,\s]\d{3})*(?:\.\d{1,2})?)', 90),
        (r'(?:PAID|PAYMENT|RECEIVED|AMOUNT\s*PAID)[\s:]*(?:RS\.?|₹|INR)?\s*(\d+(?:[,\s]\d{3})*(?:\.\d{1,2})?)', 80),
        # UPI/Payment specific patterns - PAID TO and DEBITED are critical for UPI
        (r'(?:PAID\s+TO|DEBITED|CREDITED|TRANSFERRED)[\s\w]*?(?:RS\.?|₹|INR)?\s*(\d+(?:[,\s]\d{3})*(?:\.\d{1,2})?)', 95),
    ]
    
    # Check high priority patterns first
    for pattern, score in priority_patterns:
        matches = re.findall(pattern, text_upper, re.IGNORECASE)
        for match in matches:
            try:
                cleaned = match.replace(',', '').replace(' ', '').strip()
                value = float(cleaned)
                if 1 <= value <= 10000000:  # Increased max to 10M
                    amount_contexts.append((value, score))
                    print(f"Found priority amount: {value} (score: {score}, pattern: {pattern[:50]})")
            except:
                pass
    
    # If we found high-priority amounts, return the highest scored one
    if amount_contexts:
        amount_contexts.sort(key=lambda x: (x[1], x[0]), reverse=True)
        return [amt[0] for amt in amount_contexts[:5]]  # Top 5 candidates
    
    # Medium priority - currency prefixed amounts (more variations)
    medium_patterns = [
        # Direct rupee symbol patterns - these should catch ₹1,750 correctly
        (r'₹\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{1,2})?)', 70),  # ₹ symbol with formatted number
        (r'₹\s*(\d+(?:\.\d{1,2})?)', 65),  # ₹ symbol with simple number
        (r'RS\.?\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{1,2})?)', 55),  # RS.
        (r'INR\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{1,2})?)', 55),  # INR
        (r'RS\.?\s*(\d+(?:\.\d{1,2})?)', 45),  # Simple RS
        # Handle amounts with comma as decimal separator (some regions)
        (r'₹\s*(\d{1,3}(?:\.\d{3})*,\d{2})', 50),  # European style: ₹1.234,56
        # Handle cases where ₹ might be directly attached to number (no space)
        (r'₹(\d{1,3}(?:,\d{3})*)', 68),  # ₹1,750 (no space)
        (r'₹(\d+)', 63),  # ₹1750 (no space, no comma)
    ]
    
    for pattern, score in medium_patterns:
        matches = re.findall(pattern, text_upper, re.IGNORECASE)
        for match in matches:
            try:
                # Handle European decimal format
                if ',' in match and match.count(',') == 1 and match.count('.') > 0:
                    cleaned = match.replace('.', '').replace(',', '.').strip()
                else:
                    cleaned = match.replace(',', '').replace(' ', '').strip()
                value = float(cleaned)
                if 10 <= value <= 10000000:  # Minimum 10 for currency-prefixed
                    amount_contexts.append((value, score))
                    print(f"Found currency-prefixed amount: {value} (score: {score})")
            except Exception as e:
                print(f"Error parsing medium pattern '{match}': {e}")
                pass
    
    # If we found medium-priority amounts
    if amount_contexts:
        amount_contexts.sort(key=lambda x: (x[1], x[0]), reverse=True)
        return [amt[0] for amt in amount_contexts[:5]]
    
    # Low priority - plain numbers with specific patterns
    low_patterns = [
        r'(\d{1,3}(?:,\d{3})+\.\d{2})',  # 1,234.56
        r'(\d{1,3}(?:,\d{3})+)',  # 1,234 (large numbers with commas)
        r'(\d{3,}\.\d{2})',  # 123.56 (at least 3 digits before decimal)
    ]
    
    for pattern in low_patterns:
        matches = re.findall(pattern, text_upper)
        for match in matches:
            try:
                cleaned = match.replace(',', '').replace(' ', '').strip()
                value = float(cleaned)
                if 50 <= value <= 10000000:  # Minimum 50 for plain numbers
                    amounts.append(value)
                    print(f"Found plain number: {value}")
            except:
                pass
    
    # Return unique amounts, sorted descending (largest first)
    unique_amounts = list(set(amounts))
    unique_amounts.sort(reverse=True)
    return unique_amounts[:5]  # Top 5 candidates

# OCR using EasyOCR with image preprocessing
def try_ocr(filepath):
    """Extract text from image using EasyOCR with preprocessing and multiple strategies"""
    try:
        reader = get_ocr_reader()
        if reader is None:
            print("⚠️ OCR reader not available - returning empty text")
            return ""
        
        print(f"\n{'='*60}")
        print(f"Processing image: {filepath}")
        print(f"{'='*60}")
        
        all_results = []
        
        # Try to preprocess image for better OCR
        try:
            import cv2
            import numpy as np
            
            # Read image
            img = cv2.imread(filepath)
            if img is None:
                print(f"❌ Failed to read image file: {filepath}")
                return ""
            
            print(f"✓ Image loaded: {img.shape}")
            
            # Strategy 1: Enhanced preprocessing (original method)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(blurred)
            thresh = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            print("Strategy 1: Enhanced preprocessing...")
            results1 = reader.readtext(thresh, detail=0, paragraph=False)
            all_results.extend(results1)
            print(f"  → Found {len(results1)} segments")
            
            # Strategy 2: Simple grayscale
            print("Strategy 2: Simple grayscale...")
            results2 = reader.readtext(gray, detail=0, paragraph=False)
            all_results.extend(results2)
            print(f"  → Found {len(results2)} segments")
            
            # Strategy 3: Original color image
            print("Strategy 3: Original image...")
            results3 = reader.readtext(img, detail=0, paragraph=False)
            all_results.extend(results3)
            print(f"  → Found {len(results3)} segments")
            
            # Strategy 4: Inverted image (white text on dark background)
            print("Strategy 4: Inverted image...")
            inverted = cv2.bitwise_not(gray)
            results4 = reader.readtext(inverted, detail=0, paragraph=False)
            all_results.extend(results4)
            print(f"  → Found {len(results4)} segments")
            
            # Strategy 5: High contrast binary
            print("Strategy 5: Binary threshold...")
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            results5 = reader.readtext(binary, detail=0, paragraph=False)
            all_results.extend(results5)
            print(f"  → Found {len(results5)} segments")
            
        except Exception as preprocess_error:
            print(f"⚠️ Preprocessing failed: {preprocess_error}")
            traceback.print_exc()
            # Fallback to original image
            try:
                print("Fallback: Using original image path...")
                results_fallback = reader.readtext(filepath, detail=0, paragraph=False)
                all_results.extend(results_fallback)
                print(f"  → Found {len(results_fallback)} segments")
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
        
        # Remove duplicates while preserving order
        unique_results = []
        seen = set()
        for text in all_results:
            text_clean = text.strip()
            if text_clean and text_clean not in seen:
                unique_results.append(text_clean)
                seen.add(text_clean)
        
        # Join all detected text with spaces
        final_text = ' '.join(unique_results)
        print(f"\n{'='*60}")
        print(f"✓ Total unique segments: {len(unique_results)}")
        print(f"✓ Total text length: {len(final_text)} chars")
        print(f"{'='*60}")
        print(f"Extracted text preview:\n{final_text[:500]}")
        print(f"{'='*60}\n")
        
        # Print line by line for debugging
        if unique_results:
            print("Detected text lines (unique):")
            for i, line in enumerate(unique_results[:30], 1):  # Show first 30 lines
                print(f"  {i:2d}. {line}")
            if len(unique_results) > 30:
                print(f"  ... and {len(unique_results) - 30} more lines")
        else:
            print("⚠️ No text detected from any strategy!")
        
        return final_text
    except Exception as e:
        print(f"❌ OCR Error: {e}")
        traceback.print_exc()
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
    return render_template('index.html', total_today=total_today, total_month=total_month, health_score=health_score, todays=todays, today=today)

@app.route('/upload', methods=['POST'])
def upload():
    try:
        print("\n" + "="*50)
        print("Upload request received")
        print("="*50)
        
        if 'receipt' not in request.files:
            print("ERROR: No file part in request")
            return jsonify({"status":"error","message":"No file part"}), 400
        
        file = request.files['receipt']
        print(f"File received: {file.filename}")
        
        if file.filename == '':
            print("ERROR: No file selected")
            return jsonify({"status":"error","message":"No selected file"}), 400
        
        if not allowed_file(file.filename):
            print(f"ERROR: Invalid file type: {file.filename}")
            return jsonify({"status":"error","message":"Invalid file type. Allowed: JPG, PNG, GIF, PDF"}), 400
        
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        print(f"Saving to: {save_path}")
        file.save(save_path)
        print(f"File saved successfully")
        
        print(f"\n{'='*50}")
        print(f"Processing receipt: {filename}")
        print(f"{'='*50}")
        
        # Try OCR
        text = try_ocr(save_path)
        print(f"\n{'='*50}")
        print(f"OCR Complete - Text length: {len(text)} chars")
        print(f"{'='*50}")
        
        # Extract amounts
        amounts = extract_amounts_from_text(text)
        print(f"\n{'='*50}")
        print(f"Amount Extraction Results:")
        print(f"  Detected {len(amounts)} potential amounts: {amounts}")
        print(f"{'='*50}")
        
        # Use the first (highest priority) amount if found
        extracted = amounts[0] if amounts else None
        print(f"Selected amount: ₹{extracted}" if extracted else "⚠️ No amount detected")
        print(f"{'='*50}\n")
        
        # Save an entry with extracted (or None) and OCR text for manual correction
        entry = {
            "date": datetime.date.today().isoformat(),
            "filename": filename,
            "extracted_amount": extracted,
            "all_detected_amounts": amounts[:5],  # Store top 5 for reference
            "ocr_text": text[:500]  # store more text for debugging
        }
        
        data = load_data()
        
        # If OCR failed to find amount, prompt user to manual entry via JSON response
        if extracted is None:
            data.append(entry)
            save_data(data)
            print("No amount detected - returning manual entry request")
            return jsonify({
                "status":"ok",
                "message":"uploaded",
                "need_manual_amount":True,
                "entry":entry,
                "debug_text": text[:300]  # Send more text for debugging
            }), 200
        else:
            # run prediction on extracted amount
            entry['amount'] = extracted  # Set amount field
            pred = predict_from_amount(float(extracted))
            entry.update(pred)
            data.append(entry)
            save_data(data)
            print(f"Amount detected: ₹{extracted} - returning success")
            
            # Prepare response with alternatives if available
            alternatives = amounts[1:4] if len(amounts) > 1 else []
            
            return jsonify({
                "status":"ok",
                "message":"uploaded",
                "need_manual_amount":False,
                "entry":entry,
                "extracted_amount": extracted,
                "alternative_amounts": alternatives,  # Show other detected amounts
                "ocr_text_sample": text[:200]
            }), 200
    except Exception as e:
        print(f"\n{'='*50}")
        print(f"ERROR in upload route:")
        print(f"{'='*50}")
        traceback.print_exc()
        return jsonify({"status":"error","message":str(e)}), 500

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
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)