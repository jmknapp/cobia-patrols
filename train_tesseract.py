#!/usr/bin/env python3
"""
Simple Tesseract fine-tuning test for USS Cobia typewriter font.
Uses corrected pages as training data.
"""

import os
import sys
import json
import subprocess
import tempfile
from PIL import Image

# Paths
COBIA_DIR = "/home/jmknapp/cobia"
CORRECTIONS_DIR = os.path.join(COBIA_DIR, "patrolReports/corrections")
TRAINING_DIR = os.path.join(COBIA_DIR, "tesseract_training")

def get_image_folder(pdf_name):
    """Get the folder containing original scan images for a PDF."""
    base_name = pdf_name.replace('.pdf', '').replace('USS_Cobia_', 'cobia_').lower()
    return os.path.join(COBIA_DIR, base_name)

def create_training_data():
    """Create training data from corrections."""
    os.makedirs(TRAINING_DIR, exist_ok=True)
    
    training_pairs = []
    
    # Find all correction files
    for filename in os.listdir(CORRECTIONS_DIR):
        if not filename.endswith('.json'):
            continue
        
        pdf_name = filename.replace('.json', '.pdf')
        image_folder = get_image_folder(pdf_name)
        
        if not os.path.exists(image_folder):
            print(f"Image folder not found: {image_folder}")
            continue
        
        # Load corrections
        with open(os.path.join(CORRECTIONS_DIR, filename), 'r') as f:
            corrections = json.load(f)
        
        print(f"\nProcessing {pdf_name}: {len(corrections)} corrected pages")
        
        for page_num, text in corrections.items():
            # Find the image (try different naming conventions)
            img_path = None
            for num_fmt in [f"{int(page_num):02d}", f"{int(page_num):03d}", str(page_num)]:
                for ext in ['.jpg', '.png', '.tif']:
                    candidate = os.path.join(image_folder, f"page_{num_fmt}{ext}")
                    if os.path.exists(candidate):
                        img_path = candidate
                        break
                if img_path:
                    break
            
            if not img_path:
                print(f"  Image not found for page {page_num}")
                continue
            
            # Create training pair
            base_name = f"{pdf_name.replace('.pdf', '')}_page{page_num}"
            
            # Copy image to training dir
            img = Image.open(img_path)
            tif_path = os.path.join(TRAINING_DIR, f"{base_name}.tif")
            img.save(tif_path)
            
            # Save ground truth text
            gt_path = os.path.join(TRAINING_DIR, f"{base_name}.gt.txt")
            with open(gt_path, 'w', encoding='utf-8') as f:
                # Clean up the text - one line per file for training
                clean_text = ' '.join(text.split())
                f.write(clean_text)
            
            training_pairs.append((tif_path, gt_path))
            print(f"  Created training pair for page {page_num}")
    
    return training_pairs

def generate_lstmf_files(training_pairs):
    """Generate .lstmf files for training."""
    print("\nGenerating LSTM training files...")
    
    for tif_path, gt_path in training_pairs:
        base = tif_path.replace('.tif', '')
        
        # Generate box file using Tesseract
        cmd = [
            'tesseract', tif_path, base,
            '--psm', '6',  # Assume uniform block of text
            '-l', 'eng',
            'lstm.train'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                print(f"  Generated LSTMF for {os.path.basename(tif_path)}")
            else:
                print(f"  Error: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            print(f"  Timeout processing {os.path.basename(tif_path)}")
        except Exception as e:
            print(f"  Error: {e}")

def test_ocr_comparison():
    """Compare OCR before/after on a sample."""
    print("\n" + "="*60)
    print("OCR Comparison Test")
    print("="*60)
    
    # Find a corrected page
    for filename in os.listdir(CORRECTIONS_DIR):
        if not filename.endswith('.json'):
            continue
        
        pdf_name = filename.replace('.json', '.pdf')
        image_folder = get_image_folder(pdf_name)
        
        with open(os.path.join(CORRECTIONS_DIR, filename), 'r') as f:
            corrections = json.load(f)
        
        for page_num, correct_text in corrections.items():
            # Try different naming conventions
            img_path = None
            for fmt in [f"page_{int(page_num):02d}.jpg", f"page_{int(page_num):03d}.jpg", f"page_{int(page_num)}.jpg"]:
                candidate = os.path.join(image_folder, fmt)
                if os.path.exists(candidate):
                    img_path = candidate
                    break
            
            if not img_path:
                continue
            
            print(f"\nTesting: {pdf_name} page {page_num}")
            
            # Run OCR
            result = subprocess.run(
                ['tesseract', img_path, 'stdout', '-l', 'eng', '--psm', '6'],
                capture_output=True, text=True
            )
            ocr_text = result.stdout
            
            # Compare first 500 chars
            print("\n--- Correct text (first 500 chars) ---")
            print(correct_text[:500])
            print("\n--- OCR output (first 500 chars) ---")
            print(ocr_text[:500])
            
            # Simple accuracy metric
            correct_words = set(correct_text.lower().split())
            ocr_words = set(ocr_text.lower().split())
            
            if correct_words:
                overlap = len(correct_words & ocr_words)
                precision = overlap / len(ocr_words) if ocr_words else 0
                recall = overlap / len(correct_words)
                print(f"\n--- Accuracy ---")
                print(f"Correct words: {len(correct_words)}")
                print(f"OCR words: {len(ocr_words)}")
                print(f"Matching words: {overlap}")
                print(f"Word recall: {recall:.1%}")
            
            return  # Just test one page

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'compare':
        test_ocr_comparison()
        return
    
    print("Tesseract Fine-Tuning for USS Cobia Patrol Reports")
    print("="*60)
    
    # Step 1: Create training data
    training_pairs = create_training_data()
    
    if not training_pairs:
        print("\nNo training data found! Please correct some pages first.")
        print("Use the correction tool at: http://localhost:5012/correct")
        return
    
    print(f"\nCreated {len(training_pairs)} training pairs")
    
    # Step 2: Generate LSTMF files
    generate_lstmf_files(training_pairs)
    
    print("\n" + "="*60)
    print("Training data prepared!")
    print(f"Files are in: {TRAINING_DIR}")
    print("\nNext steps for full training:")
    print("1. Download eng.traineddata LSTM model")
    print("2. Extract starter model: combine_tessdata -e eng.traineddata eng.lstm")
    print("3. Run: lstmtraining --model_output cobia --continue_from eng.lstm ...")
    print("\nOr run 'python train_tesseract.py compare' to see current OCR accuracy")

if __name__ == '__main__':
    main()

