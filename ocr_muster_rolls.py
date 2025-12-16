#!/usr/bin/env python3
"""OCR the Muster Rolls PDF with Google Cloud Vision."""

import os
import io
import json
import fitz
from google.cloud import vision
from PIL import Image

SOURCE_PDF = "/home/jmknapp/cobia/patrolReports/USS_Cobia_SS245_Muster_Rolls_1944-1946.pdf"
OUTPUT_DIR = "/home/jmknapp/cobia/patrolReports"
BASE_NAME = "USS_Cobia_SS245_Muster_Rolls_1944-1946"

def ocr_image_bytes(image_bytes):
    """Run Google Cloud Vision OCR on image bytes."""
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_bytes)
    response = client.document_text_detection(image=image)
    
    if response.error.message:
        raise Exception(response.error.message)
    
    full_text = response.full_text_annotation.text if response.full_text_annotation else ""
    
    # Extract words with positions
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
                            y2 = max(v.y for v in vertices)
                            words.append({
                                'text': word_text,
                                'x': x, 'y': y, 'y2': y2,
                                'height': y2 - y
                            })
    
    return full_text, words

def main():
    print(f"Processing: {SOURCE_PDF}")
    print("=" * 60)
    
    # Open source PDF
    doc = fitz.open(SOURCE_PDF)
    num_pages = len(doc)
    print(f"Pages: {num_pages}")
    
    # Create output PDF
    new_doc = fitz.open()
    ocr_texts = {}
    
    for page_num in range(num_pages):
        print(f"  Page {page_num + 1}/{num_pages}...", end=" ", flush=True)
        
        page = doc[page_num]
        
        # Render page to image at higher resolution for OCR
        mat = fitz.Matrix(2.0, 2.0)  # 2x scale for better OCR
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to bytes for OCR
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes = img_bytes.getvalue()
        
        try:
            # OCR with Google Vision
            full_text, words = ocr_image_bytes(img_bytes)
            ocr_texts[str(page_num + 1)] = full_text
            print(f"({len(words)} words)")
            
            # Create new page with original dimensions
            new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
            
            # Copy original page content
            new_page.show_pdf_page(new_page.rect, doc, page_num)
            
            # Add OCR text layer (scaled back from 2x)
            scale = 0.5  # Because we rendered at 2x
            for word_info in words:
                try:
                    x = word_info['x'] * scale
                    y = word_info['y2'] * scale
                    height = word_info['height'] * scale
                    fontsize = max(4, int(height * 0.8))
                    
                    new_page.insert_text(
                        (x, y),
                        word_info['text'],
                        fontsize=fontsize,
                        render_mode=3  # Invisible
                    )
                except:
                    pass
                    
        except Exception as e:
            print(f"Error: {e}")
            ocr_texts[str(page_num + 1)] = ""
    
    doc.close()
    
    # Save OCR PDF
    output_pdf = os.path.join(OUTPUT_DIR, f"{BASE_NAME}_gv.pdf")
    new_doc.save(output_pdf)
    new_doc.close()
    print(f"\nSaved: {output_pdf}")
    
    # Save OCR text JSON
    json_path = os.path.join(OUTPUT_DIR, f"{BASE_NAME}_gv_ocr.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(ocr_texts, f, indent=2, ensure_ascii=False)
    print(f"Saved: {json_path}")
    
    # Create downscaled web version
    print("\nCreating downscaled web version...")
    create_web_version(output_pdf)

def create_web_version(input_pdf):
    """Create a downscaled version for web serving."""
    TARGET_WIDTH = 850
    JPEG_QUALITY = 75
    
    doc = fitz.open(input_pdf)
    new_doc = fitz.open()
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Calculate scale
        scale = TARGET_WIDTH / page.rect.width
        new_width = TARGET_WIDTH
        new_height = int(page.rect.height * scale)
        
        # Render to pixmap
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to JPEG
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG", quality=JPEG_QUALITY)
        img_bytes.seek(0)
        
        # Create new page
        new_page = new_doc.new_page(width=new_width, height=new_height)
        new_page.insert_image(new_page.rect, stream=img_bytes.read())
        
        # Scale text layer
        text_dict = page.get_text("dict")
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "")
                        if text.strip():
                            x = span["origin"][0] * scale
                            y = span["origin"][1] * scale
                            fontsize = max(4, span["size"] * scale)
                            try:
                                new_page.insert_text((x, y), text, fontsize=fontsize, render_mode=3)
                            except:
                                pass
    
    # Save to pdfs_web
    web_dir = os.path.join(OUTPUT_DIR, "pdfs_web")
    os.makedirs(web_dir, exist_ok=True)
    output_path = os.path.join(web_dir, f"{BASE_NAME}.pdf")
    new_doc.save(output_path, garbage=4, deflate=True)
    new_doc.close()
    doc.close()
    
    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"Saved web version: {output_path} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    main()
