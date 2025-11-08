"""
Test amount extraction patterns on various bill formats
"""
import re

def extract_amounts_from_text(text):
    """Extract monetary amounts from text with improved patterns"""
    if not text:
        return []
    
    # Convert to uppercase for easier matching
    text_upper = text.upper()
    amounts = []
    amount_contexts = []  # Store (amount, context_score) tuples
    
    # High priority patterns - look for keywords like TOTAL, AMOUNT, etc.
    priority_patterns = [
        (r'(?:TOTAL|GRAND\s*TOTAL|NET\s*TOTAL|AMOUNT\s*PAYABLE|BILL\s*AMOUNT|INVOICE\s*TOTAL)[\s:]*(?:RS\.?|₹|INR)?\s*(\d+(?:[,\s]\d{3})*(?:\.\d{1,2})?)', 100),
        (r'(?:TO\s*PAY|PAYABLE|BALANCE|DUE|BALANCE\s*DUE)[\s:]*(?:RS\.?|₹|INR)?\s*(\d+(?:[,\s]\d{3})*(?:\.\d{1,2})?)', 90),
        (r'(?:PAID|PAYMENT|RECEIVED|AMOUNT\s*PAID)[\s:]*(?:RS\.?|₹|INR)?\s*(\d+(?:[,\s]\d{3})*(?:\.\d{1,2})?)', 80),
        (r'(?:DEBITED|CREDITED|TRANSFERRED)[\s:]*(?:RS\.?|₹|INR)?\s*(\d+(?:[,\s]\d{3})*(?:\.\d{1,2})?)', 85),
    ]
    
    # Check high priority patterns first
    for pattern, score in priority_patterns:
        matches = re.findall(pattern, text_upper, re.IGNORECASE)
        for match in matches:
            try:
                cleaned = match.replace(',', '').replace(' ', '').strip()
                value = float(cleaned)
                if 1 <= value <= 10000000:
                    amount_contexts.append((value, score))
                    print(f"  ✓ Priority: ₹{value} (score: {score})")
            except:
                pass
    
    if amount_contexts:
        amount_contexts.sort(key=lambda x: (x[1], x[0]), reverse=True)
        return [amt[0] for amt in amount_contexts[:5]]
    
    # Medium priority - currency prefixed amounts
    medium_patterns = [
        (r'₹\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{1,2})?)', 60),
        (r'RS\.?\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{1,2})?)', 55),
        (r'INR\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{1,2})?)', 55),
        (r'₹\s*(\d+(?:\.\d{1,2})?)', 50),
        (r'RS\.?\s*(\d+(?:\.\d{1,2})?)', 45),
    ]
    
    for pattern, score in medium_patterns:
        matches = re.findall(pattern, text_upper, re.IGNORECASE)
        for match in matches:
            try:
                cleaned = match.replace(',', '').replace(' ', '').strip()
                value = float(cleaned)
                if 10 <= value <= 10000000:
                    amount_contexts.append((value, score))
                    print(f"  ✓ Currency: ₹{value} (score: {score})")
            except:
                pass
    
    if amount_contexts:
        amount_contexts.sort(key=lambda x: (x[1], x[0]), reverse=True)
        return [amt[0] for amt in amount_contexts[:5]]
    
    # Low priority - plain numbers
    low_patterns = [
        r'(\d{1,3}(?:,\d{3})+\.\d{2})',
        r'(\d{1,3}(?:,\d{3})+)',
        r'(\d{3,}\.\d{2})',
    ]
    
    for pattern in low_patterns:
        matches = re.findall(pattern, text_upper)
        for match in matches:
            try:
                cleaned = match.replace(',', '').replace(' ', '').strip()
                value = float(cleaned)
                if 50 <= value <= 10000000:
                    amounts.append(value)
                    print(f"  ✓ Plain: ₹{value}")
            except:
                pass
    
    unique_amounts = list(set(amounts))
    unique_amounts.sort(reverse=True)
    return unique_amounts[:5]


# Test cases
test_cases = [
    # UPI/Payment receipts
    ("Transaction Successful Paid to DIGITAL DREAMS 21,750 Debited Kishore 21,750", "UPI Receipt"),
    ("Amount Paid: Rs. 1,234.50", "Restaurant bill"),
    ("TOTAL: ₹ 5,678", "Simple total"),
    ("Grand Total Rs 12345", "Grand total"),
    ("Balance Due: 999.99", "Balance due"),
    ("Invoice Total: INR 50,000", "Invoice"),
    ("Bill Amount ₹2500", "Bill amount"),
    ("Payable: 1234", "Simple payable"),
    ("TO PAY Rs. 10,500.50", "To pay"),
    ("AMOUNT PAYABLE ₹15000", "Amount payable"),
    ("Debited Rs 5432.10", "Debited"),
    ("Payment Received: 7890", "Payment received"),
    # Complex cases
    ("Item 1: ₹100\nItem 2: ₹200\nTotal: ₹300", "Multiple items with total"),
    ("Subtotal: 500\nTax: 50\nGrand Total: 550", "With tax"),
    # Edge cases
    ("Phone: 9876543210, Amount: ₹1500", "Phone number present"),
    ("Date: 17/09/2025 Total Rs 2500", "With date"),
]

print("Testing Amount Extraction Patterns")
print("=" * 80)

for i, (text, description) in enumerate(test_cases, 1):
    print(f"\nTest {i}: {description}")
    print(f"Input: {text}")
    print(f"Extracted amounts:")
    amounts = extract_amounts_from_text(text)
    if amounts:
        print(f"  → Result: {amounts}")
        print(f"  → Best match: ₹{amounts[0]}")
    else:
        print(f"  ❌ No amounts found!")
    print("-" * 80)

print("\n" + "=" * 80)
print("Test Complete!")
