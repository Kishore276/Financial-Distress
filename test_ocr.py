"""
Test OCR functionality on uploaded images
"""
import os
import sys

# Test EasyOCR installation
print("Testing OCR Dependencies...")
print("=" * 60)

try:
    import easyocr
    print("✓ EasyOCR imported successfully")
    print(f"  Version: {easyocr.__version__ if hasattr(easyocr, '__version__') else 'Unknown'}")
except ImportError as e:
    print(f"❌ EasyOCR import failed: {e}")
    print("\nTo install: pip install easyocr")
    sys.exit(1)

try:
    import cv2
    print("✓ OpenCV imported successfully")
    print(f"  Version: {cv2.__version__}")
except ImportError as e:
    print(f"❌ OpenCV import failed: {e}")
    print("\nTo install: pip install opencv-python-headless")
    sys.exit(1)

try:
    import torch
    print("✓ PyTorch imported successfully")
    print(f"  Version: {torch.__version__}")
    print(f"  CUDA available: {torch.cuda.is_available()}")
except ImportError as e:
    print(f"❌ PyTorch import failed: {e}")
    print("\nTo install: pip install torch torchvision")
    sys.exit(1)

print("\n" + "=" * 60)
print("Initializing OCR Reader...")
print("=" * 60)

try:
    reader = easyocr.Reader(['en'], gpu=False)
    print("✓ OCR Reader initialized successfully!")
except Exception as e:
    print(f"❌ Failed to initialize OCR reader: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test on uploaded images
print("\n" + "=" * 60)
print("Testing on Uploaded Images")
print("=" * 60)

upload_dir = 'uploads'
if not os.path.exists(upload_dir):
    print(f"❌ Upload directory '{upload_dir}' not found")
    sys.exit(1)

files = [f for f in os.listdir(upload_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif'))]

if not files:
    print(f"⚠️ No image files found in '{upload_dir}'")
else:
    print(f"Found {len(files)} image(s) to test\n")
    
    for filename in files:
        filepath = os.path.join(upload_dir, filename)
        print(f"\n{'=' * 60}")
        print(f"Testing: {filename}")
        print(f"{'=' * 60}")
        
        # Check file size
        filesize = os.path.getsize(filepath)
        print(f"File size: {filesize:,} bytes ({filesize/1024:.2f} KB)")
        
        # Test image loading
        try:
            img = cv2.imread(filepath)
            if img is None:
                print(f"❌ Failed to load image")
                continue
            print(f"✓ Image loaded: {img.shape} (H x W x C)")
        except Exception as e:
            print(f"❌ Error loading image: {e}")
            continue
        
        # Run OCR
        try:
            print("\nRunning OCR...")
            results = reader.readtext(filepath, detail=0, paragraph=False)
            print(f"✓ OCR completed: {len(results)} text segments detected")
            
            if results:
                text = ' '.join(results)
                print(f"\nExtracted text ({len(text)} chars):")
                print("-" * 60)
                print(text)
                print("-" * 60)
                
                print("\nText segments:")
                for i, segment in enumerate(results[:20], 1):
                    print(f"  {i:2d}. {segment}")
                if len(results) > 20:
                    print(f"  ... and {len(results) - 20} more segments")
            else:
                print("⚠️ No text detected!")
                
        except Exception as e:
            print(f"❌ OCR failed: {e}")
            import traceback
            traceback.print_exc()

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
