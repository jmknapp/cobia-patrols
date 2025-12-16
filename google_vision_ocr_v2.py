#!/usr/bin/env python3
"""
Process all USS Cobia patrol reports with Google Cloud Vision OCR.
Creates searchable PDFs with text positioned at correct locations.
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

REPORTS = [
    ("cobia_1st_patrol_report", "USS_Cobia_1st_Patrol_Report"),
    ("cobia_2nd_patrol_report", "USS_Cobia_2nd_Patrol_Report"),
    ("cobia_3rd_patrol_report", "USS_Cobia_3rd_Patrol_Report"),
    ("cobia_4th_patrol_report", "USS_Cobia_4th_Patrol_Report"),
    ("cobia_5th_patrol_report", "USS_Cobia_5th_Patrol_Report"),
    ("cobia_6th_patrol_report", "USS_Cobia_6th_Patrol_Report"),
]

def ocr_with_google_vision(image_path):
    """Run Google Cloud Vision OCR, returning words with positions."""
    client = vision.ImageAnnotatorClient()
    
    with open(image_path, 'rb') as f:
        content = f.read()
    
    image = vision.Image(content=content)
    response = client.document_text_detection(image=image)
    
    if response.error.message:
        raise Exception(response.error.message)
    
    full_text = response.full_text_annotation.text if response.full_text_annotation else ""
    
    words = []
    if response.full_text_annotation:
        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        word_text = ''.join([s.text for s in word.symbols])
                        vertices = word.bounding_box.vertices
                        if len(vertices) >= 4:
                            x = min(v.x for v in vertices)
                            y = min(v.y for v in vertices)
                            x2 = max(v.x for v in vertices)
                            y2 = max(v.y for v in vertices)
                            words.append({
                                'text': word_text,
                                'x': x, 'y': y, 'x2': x2, 'y2': y2,
                                'height': y2 - y
                            })
    
    return full_text, words

def process_report(folder_name, output_name):
    folder_path = os.path.join(COBIA_DIR, folder_name)
    
    if not os.path.exists(folder_path):
        print(f"  Folder not found: {folder_path}")
        return False
    
    images = sorted(glob.glob(os.path.join(folder_path, "*.jpg")) +
                   glob.glob(os.path.join(folder_path, "*.png")))
    
    if not images:
        return False
    
    print(f"  Found {len(images)} pages")
    
    output_pdf = os.path.join(OUTPUT_DIR, f"{output_name}_gv.pdf")
    doc = fitz.open()
    ocr_texts = {}
    
    for i, img_path in enumerate(images):
        page_num = i + 1
        print(f"  Page {page_num}/{len(images)}...", end=" ", flush=True)
        
        try:
            full_text, words = ocr_with_google_vision(img_path)
            ocr_texts[str(page_num)] = full_text
            print(f"({len(words)} words)", flush=True)
            
            img = Image.open(img_path)
            img_width, img_height = img.size
            
            page = doc.new_page(width=img_width, height=img_height)
            page.insert_image(page.rect, filename=img_path)
            
            for word_info in words:
                try:
                    word_text = word_info['text']
                    x = word_info['x']
                    y = word_info['y2']
                    height = word_info['height']
                    fontsize = max(6, min(24, int(height * 0.8)))
                    
                    page.insert_text(
                        (x, y),
                        word_text,
                        fontsize=fontsize,
                        render_mode=3
                    )
                except:
                    pass
            
        except Exception as e:
            print(f"Error: {e}")
            ocr_texts[str(page_num)] = ""
    
    doc.save(output_pdf)
    doc.close()
    print(f"  Saved: {output_pdf}")
    
    json_path = os.path.join(OUTPUT_DIR, f"{output_name}_gv_ocr.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(ocr_texts, f, indent=2, ensure_ascii=False)
    
    return True

def main():
    print("Google Cloud Vision OCR v2 (with word positions)")
    print("=" * 60)
    
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        print("Error: GOOGLE_APPLICATION_CREDENTIALS not set")
        sys.exit(1)
    
    for folder_name, output_name in REPORTS:
        print(f"\nProcessing: {output_name}")
        process_report(folder_name, output_name)
    
    print("\nComplete!")

if __name__ == '__main__':
    main()
