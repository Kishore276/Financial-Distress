# Quick Start Guide - Smart Finance Guardian

## 🚀 Running the Application

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Train Models (Optional)
```bash
python train_models.py
```

### Step 3: Run the Application
```bash
python app.py
```

### Step 4: Open in Browser
Navigate to: **http://127.0.0.1:5000**

---

## 🎨 New UI Features

### Dashboard Page (`/`)
- **Stats Overview**: See today's spending, monthly total, and financial health score at a glance
- **Upload Receipt**: Drag and drop or select receipt images
- **Manual Entry**: Add expenses manually with amount, category, and date
- **Today's Transactions**: View all transactions from today

### Results Page (`/result`)
- **Latest Entry Analysis**: Detailed breakdown of your most recent transaction
- **Predictions**: AI-powered predictions for annual expenses and savings
- **Distress Probability**: Risk assessment with color-coded indicators
- **Financial Advice**: Personalized recommendations
- **Spending Breakdown**: Category-wise expense analysis
- **Recent Transactions**: Scrollable list of recent entries

---

## 📱 Features

### ✨ Upload Receipt
1. Click "Choose File" or drag and drop an image
2. See preview of uploaded image
3. System automatically extracts amount using OCR
4. If OCR fails, manual entry form appears
5. View detailed analysis on results page

### ✏️ Manual Entry
1. Enter amount in rupees
2. Add category (Food, Transport, Shopping, etc.)
3. Select date (defaults to today)
4. Click "Add Entry"
5. Redirected to results page with analysis

### 📊 Dashboard Stats
- **Green cards**: Good financial health
- **Yellow cards**: Warning - moderate spending
- **Red cards**: Danger - high spending or distress risk

### 🎯 Health Score
- **80-100**: Excellent financial health
- **60-79**: Good, but room for improvement
- **40-59**: Fair, needs attention
- **0-39**: Poor, immediate action needed

---

## 🎨 Color Guide

| Color | Meaning | When You'll See It |
|-------|---------|-------------------|
| 🟢 Green | Success/Good | Low spending, positive savings, good health |
| 🟡 Yellow | Warning/Moderate | Moderate spending, attention recommended |
| 🔴 Red | Danger/High | High spending, financial distress risk |
| 🟣 Purple | Primary/Action | Buttons, links, brand elements |

---

## 💡 Tips for Best Experience

1. **Upload Clear Images**: For best OCR results, ensure receipt images are clear and well-lit
2. **Categorize Consistently**: Use consistent category names for better analytics
3. **Regular Updates**: Add expenses daily for accurate predictions
4. **Review Advice**: Read the AI-generated financial advice carefully
5. **Track Trends**: Monitor your health score weekly

---

## 🛠️ Troubleshooting

### Receipt Upload Not Working?
- Check file format (JPG, PNG, GIF, PDF supported)
- Ensure file size is reasonable (<10MB)
- Try manual entry as fallback

### OCR Not Detecting Amount?
- The system will prompt for manual entry
- This is normal for handwritten receipts or complex layouts
- Simply enter the amount manually when asked

### Health Score Seems Off?
- The score is calculated based on monthly spending
- Formula: `100 - (monthly_spending / 1000)`
- Add more data for more accurate scoring

---

## 📂 Project Structure

```
Financial-Distress-main/
├── app.py                  # Flask application
├── train_models.py         # Model training script
├── data.json              # Transaction data storage
├── requirements.txt       # Python dependencies
├── templates/
│   ├── index.html         # Dashboard page
│   └── result.html        # Results page
├── static/
│   ├── style.css          # Modern UI styles
│   └── script.js          # Frontend interactions
├── uploads/               # Uploaded receipts
└── models/                # ML models (created after training)
```

---

## 🔒 Privacy & Data

- All data stored locally in `data.json`
- No external API calls (except optional OCR)
- Receipts saved to `uploads/` folder
- Can delete data anytime by removing `data.json`

---

## 🚀 Next Steps

1. **Add Your First Expense**: Try uploading a receipt or manual entry
2. **Explore Results**: Check predictions and financial advice
3. **Track Weekly**: Add expenses for a week to see trends
4. **Review Monthly**: Check spending breakdown at month end

---

**Enjoy your new Smart Finance Guardian experience! 💰📊**
