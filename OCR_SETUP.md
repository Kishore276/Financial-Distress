# EasyOCR Integration Guide

## What Changed?

The application now uses **EasyOCR** instead of Tesseract for better text detection from receipt images.

## Features

### ✨ Improved OCR Capabilities

1. **Better Text Detection**: EasyOCR uses deep learning models for superior text recognition
2. **Multiple Language Support**: Currently configured for English, easily extensible
3. **No External Dependencies**: No need to install Tesseract separately
4. **GPU Support**: Can leverage GPU if available (currently set to CPU mode)

### 🎯 Amount Extraction Patterns

The system now detects amounts in multiple formats:

- ✅ `₹1,234.56` - Currency symbol with commas
- ✅ `Rs. 1234` - Rs prefix
- ✅ `INR 1234.50` - INR prefix
- ✅ `1,234.56` - Plain numbers with commas
- ✅ `Total: 1234` - After keywords like "total", "amount", "paid"
- ✅ `123.45` - Decimal amounts

### 🔍 Smart Amount Selection

- Extracts all possible amounts from the receipt
- Prioritizes larger amounts (typically the total)
- Filters out unreasonable values (< ₹1 or > ₹1,000,000)
- Returns unique amounts sorted by value

## Installation

### Required Packages

```bash
pip install easyocr opencv-python-headless torch torchvision
```

All packages are listed in `requirements.txt`.

## How It Works

### 1. **Image Upload**
- User uploads a receipt image (JPG, PNG, GIF, PDF)
- Image is saved to `uploads/` folder

### 2. **OCR Processing**
- EasyOCR reader is initialized (lazy loading on first use)
- Text is extracted from the image
- Progress is logged in the console

### 3. **Amount Detection**
- Multiple regex patterns scan the extracted text
- All potential amounts are identified
- Best amount is selected (usually the largest)

### 4. **User Feedback**
- If amount is detected: Shows success with predicted analysis
- If no amount: Prompts for manual entry with debug info
- Shows extracted text snippet for debugging

## Configuration

### GPU vs CPU

In `app.py`, the EasyOCR reader is configured:

```python
ocr_reader = easyocr.Reader(['en'], gpu=False)
```

- Set `gpu=False` for CPU mode (default, works everywhere)
- Set `gpu=True` if you have NVIDIA GPU with CUDA installed

### Language Support

To add more languages:

```python
ocr_reader = easyocr.Reader(['en', 'hi'], gpu=False)  # English + Hindi
```

Available languages: en, hi, zh, ja, ko, th, vi, etc.

## Debugging

### Check Console Output

When you upload a receipt, the console shows:

```
==================================================
Processing receipt: bill.jpg
==================================================
Initializing EasyOCR reader...
EasyOCR reader initialized successfully!
Full extracted text: Total Amount Rs. 1234.50 Thank you
Detected amounts: [1234.5]
Selected amount: 1234.5
```

### If OCR Fails

1. **Check image quality**: Ensure the image is clear and well-lit
2. **Check file format**: JPG, PNG work best
3. **View debug text**: The UI shows what text was detected
4. **Manual entry**: Always available as fallback

## Performance

### First Load
- Initial EasyOCR setup downloads models (~100MB)
- First image processing may take 5-10 seconds
- Models are cached for subsequent uses

### Subsequent Uses
- Processing time: 2-5 seconds per image
- Faster with GPU
- Reader is initialized once and reused

## Tips for Best Results

### 📸 Image Quality
1. **Good lighting**: Natural light works best
2. **Focus**: Ensure text is sharp and clear
3. **Angle**: Take photo straight-on, not at an angle
4. **Resolution**: Higher resolution = better results
5. **Contrast**: Dark text on light background works best

### 📄 Receipt Types
- **Printed receipts**: ✅ Excellent results
- **Thermal receipts**: ✅ Very good results
- **Handwritten**: ⚠️ May require manual entry
- **Faded receipts**: ⚠️ May not detect all text

## Troubleshooting

### Issue: "OCR reader not available"
**Solution**: Ensure EasyOCR is installed:
```bash
pip install easyocr
```

### Issue: Slow processing
**Solutions**:
- Use smaller image files
- Enable GPU if available
- Wait for first-time model download to complete

### Issue: Wrong amount detected
**Solutions**:
- Check the debug text shown in UI
- Use manual entry to override
- Improve image quality
- Ensure receipt shows clear "Total" or "Amount"

### Issue: No amount detected
**Solutions**:
- The UI will show what text was extracted
- Check if the receipt has clear numeric values
- Use manual entry feature
- Try re-uploading with better lighting

## Advanced Usage

### Custom Amount Patterns

Edit `extract_amounts_from_text()` in `app.py` to add custom patterns:

```python
# Add your custom pattern
r'your_pattern_here',
```

### Adjust Amount Filtering

Modify the amount range validation:

```python
if 1 <= value <= 1000000:  # Adjust min/max as needed
    amounts.append(value)
```

## Comparison: Tesseract vs EasyOCR

| Feature | Tesseract | EasyOCR |
|---------|-----------|---------|
| Setup | External installation required | Python package only |
| Accuracy | Good | Excellent |
| Handwriting | Poor | Better |
| Speed | Fast | Moderate |
| GPU Support | No | Yes |
| Languages | 100+ | 80+ |
| Deep Learning | No | Yes |

## API Response Format

### Success Response (Amount Detected)
```json
{
  "status": "ok",
  "message": "uploaded",
  "need_manual_amount": false,
  "extracted_amount": 1234.56,
  "entry": { ... }
}
```

### Partial Success (No Amount)
```json
{
  "status": "ok",
  "message": "uploaded",
  "need_manual_amount": true,
  "debug_text": "Thank you for shopping...",
  "entry": { ... }
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description"
}
```

---

**🎉 EasyOCR is now integrated and ready to use!**

Simply restart your Flask app and upload a receipt to see it in action.
