"""
Test the rupee symbol misread fix
"""
import re

def extract_amounts_from_text(text):
    """Extract monetary amounts from text with improved patterns"""
    if not text:
        return []
    
    # CRITICAL FIX: Clean up misread rupee symbols in UPI/payment contexts
    text_cleaned = text
    
    # Check if this looks like a UPI/payment receipt
    is_upi_context = bool(re.search(
        r'(?:PAID\s+TO|DEBITED|CREDITED|TRANSACTION|UPI|TRANSFER|UTR)',
        text.upper()
    ))
    
    if is_upi_context:
        # In UPI context, fix "2X,XXX" patterns (likely misread ₹)
        original_text = text_cleaned
        text_cleaned = re.sub(r'\b2([1-9],\d{3})(?![,\d])\b', r'\1', text_cleaned)
        text_cleaned = re.sub(r'\b2([1-9]\d{2,3})(?![,\d])\b', r'\1', text_cleaned)
        
        if original_text != text_cleaned:
            print(f"✓ UPI context detected - fixed rupee symbol misread")
            print(f"  Before: ...{original_text[max(0, original_text.find('2')-10):original_text.find('2')+20]}...")
            print(f"  After:  ...{text_cleaned[max(0, text_cleaned.find('1')-10):text_cleaned.find('1')+20]}...")
    else:
        print(f"ℹ️ No UPI context - keeping amounts as-is")
    
    text_upper = text_cleaned.upper()
    amounts = []
    amount_contexts = []
    
    # High priority patterns
    priority_patterns = [
        (r'(?:TOTAL|GRAND\s*TOTAL|NET\s*TOTAL|AMOUNT\s*PAYABLE|BILL\s*AMOUNT|INVOICE\s*TOTAL)[\s:]*(?:RS\.?|₹|INR)?\s*(\d+(?:[,\s]\d{3})*(?:\.\d{1,2})?)', 100),
        (r'(?:TO\s*PAY|PAYABLE|BALANCE|DUE|BALANCE\s*DUE)[\s:]*(?:RS\.?|₹|INR)?\s*(\d+(?:[,\s]\d{3})*(?:\.\d{1,2})?)', 90),
        (r'(?:PAID|PAYMENT|RECEIVED|AMOUNT\s*PAID)[\s:]*(?:RS\.?|₹|INR)?\s*(\d+(?:[,\s]\d{3})*(?:\.\d{1,2})?)', 80),
        (r'(?:PAID\s+TO|DEBITED|CREDITED|TRANSFERRED)[\s\w]*?(?:RS\.?|₹|INR)?\s*(\d+(?:[,\s]\d{3})*(?:\.\d{1,2})?)', 95),
    ]
    
    for pattern, score in priority_patterns:
        matches = re.findall(pattern, text_upper, re.IGNORECASE)
        for match in matches:
            try:
                cleaned = match.replace(',', '').replace(' ', '').strip()
                value = float(cleaned)
                if 1 <= value <= 10000000:
                    amount_contexts.append((value, score))
                    print(f"  ✓ Priority: ₹{value:,.2f} (score: {score})")
            except:
                pass
    
    if amount_contexts:
        amount_contexts.sort(key=lambda x: (x[1], x[0]), reverse=True)
        return [amt[0] for amt in amount_contexts[:5]]
    
    # Medium priority - currency symbols
    medium_patterns = [
        (r'₹\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{1,2})?)', 70),
        (r'₹\s*(\d+(?:\.\d{1,2})?)', 65),
        (r'₹(\d{1,3}(?:,\d{3})*)', 68),
        (r'₹(\d+)', 63),
    ]
    
    for pattern, score in medium_patterns:
        matches = re.findall(pattern, text_upper, re.IGNORECASE)
        for match in matches:
            try:
                cleaned = match.replace(',', '').replace(' ', '').strip()
                value = float(cleaned)
                if 10 <= value <= 10000000:
                    amount_contexts.append((value, score))
                    print(f"  ✓ Currency: ₹{value:,.2f} (score: {score})")
            except:
                pass
    
    if amount_contexts:
        amount_contexts.sort(key=lambda x: (x[1], x[0]), reverse=True)
        return [amt[0] for amt in amount_contexts[:5]]
    
    return []


print("Testing Rupee Symbol Misread Fix")
print("=" * 80)

# Test cases based on the actual OCR output
test_cases = [
    # The actual OCR output from your image (with misread rupee as "2")
    ("Paid to DIGITAL DREAMS 21,750", "OCR misread: ₹ as '2' (should be ₹1,750)"),
    ("Debited Kishore 21,750", "OCR misread in debited line"),
    
    # With actual rupee symbol (should work correctly)
    ("Paid to DIGITAL DREAMS ₹1,750", "Correct with rupee symbol"),
    ("₹1,750", "Just the amount with rupee symbol"),
    
    # Edge cases
    ("21,750 Paid", "Misread rupee at start, no keyword before"),
    ("Amount: 21,750", "With amount keyword"),
    ("Total 21,750", "With total keyword"),
    
    # Should NOT be changed (legitimate 21,750)
    ("Invoice Total: 21,750", "Legitimate invoice (NO UPI context)"),
    ("Balance: 21,750.50", "Legitimate balance (NO UPI context)"),
    ("Grand Total 21,750", "Restaurant bill (NO UPI context)"),
]

for i, (text, description) in enumerate(test_cases, 1):
    print(f"\nTest {i}: {description}")
    print("-" * 80)
    amounts = extract_amounts_from_text(text)
    if amounts:
        print(f"✓ Extracted: {amounts}")
        print(f"  Best match: ₹{amounts[0]:,.2f}")
    else:
        print(f"❌ No amounts found!")
    print()

print("=" * 80)
print("Test Complete!")
