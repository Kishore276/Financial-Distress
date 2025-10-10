# Testing EasyOCR Integration

## Quick Test Steps

### 1. Restart the Flask App

Stop the current Flask app (Ctrl+C in terminal) and restart:

```bash
cd c:\Codes\Financial-Distress-main
python app.py
```

### 2. Upload a Test Receipt

1. Go to http://127.0.0.1:5000
2. Click on "Choose file" under "Upload Receipt"
3. Select a receipt image
4. Click "Upload & Analyze"

### 3. Check Console Output

You should see detailed output like:

```
==================================================
Processing receipt: bill.jpg
==================================================
Initializing EasyOCR reader...
EasyOCR reader initialized successfully!
Full extracted text: TOTAL AMOUNT RS 1234.50 THANK YOU
Detected amounts: [1234.5]
Selected amount: 1234.5
```

### 4. Expected Results

#### ✅ Success (Amount Detected)
- Green success message appears
- Shows: "Amount detected: ₹1234.56"
- Click "View Detailed Results" to see predictions

#### ⚠️ Partial Success (No Amount)
- Yellow warning message appears
- Shows extracted text for debugging
- Manual entry form appears
- Enter amount manually and click "Save Entry"

#### ❌ Error
- Red error message appears
- Shows error details
- Check console for full error traceback

## Test Receipt Examples

### Good Receipt Format
```
=====================================
    ABC STORE
    123 Main Street
    Phone: 555-1234
=====================================

ITEMS:
Apple      ₹50.00
Bread      ₹30.00
Milk       ₹80.00

-------------------------------------
TOTAL:     ₹160.00
-------------------------------------
Thank you for shopping!
```

### What EasyOCR Will Extract
```
ABC STORE 123 Main Street Phone 555-1234
ITEMS Apple 50.00 Bread 30.00 Milk 80.00
TOTAL 160.00 Thank you for shopping
```

### Detected Amounts
```
[160.0, 80.0, 50.0, 30.0]
Selected: 160.0 (largest amount, likely the total)
```

## Sample Test Images

Create test receipts with:

1. **Clear printed text**: Best results
2. **Good contrast**: Dark text on white background
3. **Proper alignment**: Not rotated or skewed
4. **High resolution**: At least 800x600 pixels
5. **Clear total line**: "TOTAL: ₹XXX" format

## Debugging Checklist

- [ ] Flask app is running (check http://127.0.0.1:5000)
- [ ] EasyOCR is installed (`pip list | grep easyocr`)
- [ ] Console shows OCR initialization message
- [ ] Upload shows file preview
- [ ] Console shows extracted text
- [ ] UI shows success or manual entry form

## Common Issues & Solutions

### Issue: First upload is slow
**Cause**: EasyOCR downloading models on first use  
**Solution**: Wait 1-2 minutes, subsequent uploads will be faster

### Issue: No amount detected from clear receipt
**Cause**: Text format doesn't match patterns  
**Solution**: Check console for "Detected amounts" - may need to add custom pattern

### Issue: Module not found error
**Cause**: EasyOCR not installed  
**Solution**: Run `pip install easyocr opencv-python-headless`

## Performance Benchmarks

| Operation | Time (CPU) | Time (GPU) |
|-----------|-----------|-----------|
| First initialization | 30-60s | 10-20s |
| Model download (first time) | 1-2min | 1-2min |
| Process receipt (800x600) | 3-5s | 1-2s |
| Process receipt (1920x1080) | 5-8s | 2-3s |

## Next Steps After Testing

1. ✅ Verify amount detection works
2. ✅ Test manual entry fallback
3. ✅ Check predictions are generated
4. ✅ View results page
5. ✅ Test with various receipt formats
6. Consider adding more language support
7. Fine-tune amount extraction patterns
8. Add receipt category auto-detection

---

**Ready to test!** Upload a receipt and watch the magic happen! 🎉
