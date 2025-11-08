import json

with open('data.json', 'r') as f:
    data = json.load(f)

print("OCR Extraction Results:")
print("=" * 80)
for entry in data:
    if 'filename' in entry:
        filename = entry.get('filename', 'N/A')
        extracted = entry.get('extracted_amount', 'None')
        ocr_text = entry.get('ocr_text', '')
        print(f"File: {filename:40}")
        print(f"  Extracted Amount: {extracted}")
        print(f"  OCR Text Length: {len(ocr_text)} chars")
        print(f"  OCR Text Preview: {ocr_text[:200] if ocr_text else 'EMPTY'}")
        print("-" * 80)
