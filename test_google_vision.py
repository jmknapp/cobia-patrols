#!/usr/bin/env python3
"""
Test Google Cloud Vision OCR on USS Cobia patrol report pages.
Compare results with Tesseract.
"""

import os
import sys
import subprocess
from google.cloud import vision

def ocr_with_google_vision(image_path):
    """Run Google Cloud Vision OCR on an image."""
    client = vision.ImageAnnotatorClient()
    
    with open(image_path, 'rb') as f:
        content = f.read()
    
    image = vision.Image(content=content)
    response = client.document_text_detection(image=image)
    
    if response.error.message:
        raise Exception(response.error.message)
    
    return response.full_text_annotation.text

def ocr_with_tesseract(image_path):
    """Run Tesseract OCR on an image."""
    result = subprocess.run(
        ['tesseract', image_path, 'stdout', '-l', 'eng', '--psm', '6'],
        capture_output=True, text=True
    )
    return result.stdout

def compare_ocr(image_path, correct_text=None):
    """Compare Google Vision vs Tesseract on an image."""
    print(f"\nProcessing: {image_path}")
    print("=" * 60)
    
    # Run both OCR engines
    print("\nRunning Google Cloud Vision...")
    google_text = ocr_with_google_vision(image_path)
    
    print("Running Tesseract...")
    tesseract_text = ocr_with_tesseract(image_path)
    
    # Display results
    print("\n--- Google Cloud Vision (first 800 chars) ---")
    print(google_text[:800])
    
    print("\n--- Tesseract (first 800 chars) ---")
    print(tesseract_text[:800])
    
    # Compare word counts
    google_words = set(google_text.lower().split())
    tesseract_words = set(tesseract_text.lower().split())
    
    print("\n--- Comparison ---")
    print(f"Google Vision words: {len(google_words)}")
    print(f"Tesseract words: {len(tesseract_words)}")
    
    if correct_text:
        correct_words = set(correct_text.lower().split())
        google_match = len(google_words & correct_words)
        tesseract_match = len(tesseract_words & correct_words)
        
        print(f"\nAgainst corrected text ({len(correct_words)} words):")
        print(f"  Google Vision recall: {google_match}/{len(correct_words)} = {google_match/len(correct_words)*100:.1f}%")
        print(f"  Tesseract recall:     {tesseract_match}/{len(correct_words)} = {tesseract_match/len(correct_words)*100:.1f}%")
    
    return google_text, tesseract_text

def main():
    # Default test image
    test_image = "/home/jmknapp/cobia/cobia_1st_patrol_report/page_01.jpg"
    
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
    
    if not os.path.exists(test_image):
        print(f"Image not found: {test_image}")
        print("\nUsage: python test_google_vision.py [image_path]")
        print("Example: python test_google_vision.py cobia_1st_patrol_report/page_05.jpg")
        sys.exit(1)
    
    # Check for credentials
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        print("Error: GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        print("Run: export GOOGLE_APPLICATION_CREDENTIALS='/path/to/your-key.json'")
        sys.exit(1)
    
    compare_ocr(test_image)
    
    print("\n" + "=" * 60)
    print("Test complete!")

if __name__ == '__main__':
    main()



