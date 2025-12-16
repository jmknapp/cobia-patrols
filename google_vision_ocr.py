#!/usr/bin/env python3
"""
Process all USS Cobia patrol reports with Google Cloud Vision OCR.
Creates searchable PDFs with embedded text.
"""

import os
import sys
import glob
import json
from google.cloud import vision
from PIL import Image
import fitz  # PyMuPDF

COBIA_DIR = "/home/jmknapp/cobia"
OUTPUT_DIR = os.path.join(COBIA_DIR, "patrolReports")

# Report folders mapping
REPORTS = [
    ("cobia_1st_patrol_report", "USS_Cobia_1st_Patrol_Report"),
    ("cobia_2nd_patrol_report", "USS_Cobia_2nd_Patrol_Report"),
    ("cobia_3rd_patrol_report", "USS_Cobia_3rd_Patrol_Report"),
    ("cobia_4th_patrol_report", "USS_Cobia_4th_Patrol_Report"),
    ("cobia_5th_patrol_report", "USS_Cobia_5th_Patrol_Report"),
    ("cobia_6th_patrol_report", "USS_Cobia_6th_Patrol_Report"),
]

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

def process_report(folder_name, output_name):
    """Process a single patrol report."""
    folder_path = os.path.join(COBIA_DIR, folder_name)
    
    if not os.path.exists(folder_path):
        print(f"  Folder not found: {folder_path}")
        return False
    
    # Find all images
    images = sorted(glob.glob(os.path.join(folder_path, "*.jpg")) +
                   glob.glob(os.path.join(folder_path, "*.png")))
    
    if not images:
        print(f"  No images found in {folder_path}")
        return False
    
    print(f"  Found {len(images)} pages")
    
    # Create new PDF
    output_pdf = os.path.join(OUTPUT_DIR, f"{output_name}_gv.pdf")
    doc = fitz.open()
    
    # Also save OCR text to JSON for search
    ocr_texts = {}
    
    for i, img_path in enumerate(images):
        page_num = i + 1
        print(f"  Processing page {page_num}/{len(images)}...", end=" ", flush=True)
        
        try:
            # Get OCR text from Google Vision
            text = ocr_with_google_vision(img_path)
            ocr_texts[str(page_num)] = text
            print(f"({len(text)} chars)", flush=True)
            
            # Load image and get dimensions
            img = Image.open(img_path)
            img_width, img_height = img.size
            
            # Create page with image dimensions
            page = doc.new_page(width=img_width, height=img_height)
            
            # Insert the image
            page.insert_image(page.rect, filename=img_path)
            
            # Insert OCR text as invisible layer
            if text.strip():
                fontsize = 11
                lines = text.split('\n')
                y_pos = 40
                for line in lines:
                    if line.strip():
                        try:
                            page.insert_text(
                                (40, y_pos),
                                line,
                                fontsize=fontsize,
                                render_mode=3  # Invisible
                            )
                        except:
                            pass  # Skip problematic characters
                    y_pos += fontsize * 1.2
                    if y_pos > img_height - 40:
                        break
            
        except Exception as e:
            print(f"Error: {e}")
            ocr_texts[str(page_num)] = ""
    
    # Save PDF
    doc.save(output_pdf)
    doc.close()
    print(f"  Saved: {output_pdf}")
    
    # Save OCR text to JSON
    json_path = os.path.join(OUTPUT_DIR, f"{output_name}_gv_ocr.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(ocr_texts, f, indent=2, ensure_ascii=False)
    print(f"  Saved OCR text: {json_path}")
    
    return True

def main():
    print("Google Cloud Vision OCR for USS Cobia Patrol Reports")
    print("=" * 60)
    
    # Check credentials
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        print("Error: GOOGLE_APPLICATION_CREDENTIALS not set")
        sys.exit(1)
    
    total_success = 0
    
    for folder_name, output_name in REPORTS:
        print(f"\nProcessing: {output_name}")
        if process_report(folder_name, output_name):
            total_success += 1
    
    print("\n" + "=" * 60)
    print(f"Complete! Processed {total_success}/{len(REPORTS)} reports")
    print(f"Output files are in: {OUTPUT_DIR}")
    print("\nNew files created:")
    print("  *_gv.pdf - PDFs with Google Vision OCR")
    print("  *_gv_ocr.json - OCR text for searching")

if __name__ == '__main__':
    main()



