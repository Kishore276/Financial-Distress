"""
Fix the incorrect amount in data.json
The UPI receipt shows ₹1,750 not ₹21,750
"""
import json

# Load existing data
with open('data.json', 'r') as f:
    data = json.load(f)

print("Fixing incorrect amounts in data.json")
print("=" * 80)

fixed_count = 0
for entry in data:
    if 'filename' in entry and entry.get('filename') == 'Reciept.jpg':
        old_amount = entry.get('amount') or entry.get('extracted_amount')
        if old_amount == 21750.0:
            print(f"\nFound incorrect entry:")
            print(f"  File: {entry['filename']}")
            print(f"  Old amount: ₹{old_amount:,.2f}")
            print(f"  New amount: ₹1,750.00")
            
            # Fix the amount
            if 'amount' in entry:
                entry['amount'] = 1750.0
            if 'extracted_amount' in entry:
                entry['extracted_amount'] = 1750.0
            
            # Recalculate predictions with correct amount
            if 'predicted_annual_expense' in entry:
                # Correct calculation: 1750 * 365 = 638,750
                entry['predicted_annual_expense'] = 1750.0 * 365
                entry['predicted_annual_savings'] = max(0.0, 100000.0 - entry['predicted_annual_expense'])
                entry['distress_probability'] = min(1.0, entry['predicted_annual_expense'] / 100000.0)
                
                print(f"  Updated predictions:")
                print(f"    Annual expense: ₹{entry['predicted_annual_expense']:,.2f}")
                print(f"    Annual savings: ₹{entry['predicted_annual_savings']:,.2f}")
                print(f"    Distress probability: {entry['distress_probability']:.1%}")
            
            fixed_count += 1

# Save the corrected data
if fixed_count > 0:
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\n✓ Fixed {fixed_count} entry(ies) and saved to data.json")
else:
    print("\nℹ️ No entries needed fixing")

print("=" * 80)
