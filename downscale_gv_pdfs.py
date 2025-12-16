#!/usr/bin/env python3
"""Downscale Google Vision PDFs for faster web loading."""

import os
import io
import fitz  # PyMuPDF
from PIL import Image

SOURCE_DIR = "/home/jmknapp/cobia/patrolReports"
TARGET_WIDTH = 850  # pixels
JPEG_QUALITY = 75

def downscale_pdf(input_path, output_path):
    """Downscale a PDF with JPEG compression."""
    doc = fitz.open(input_path)
    new_doc = fitz.open()
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Calculate scale factor
        orig_width = page.rect.width
        scale = TARGET_WIDTH / orig_width
        
        # New dimensions
        new_width = TARGET_WIDTH
        new_height = int(page.rect.height * scale)
        
        # Render original page to pixmap
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image for JPEG compression
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Save as JPEG to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG", quality=JPEG_QUALITY)
        img_bytes.seek(0)
        
        # Create new page
        new_page = new_doc.new_page(width=new_width, height=new_height)
        
        # Insert JPEG image
        new_page.insert_image(new_page.rect, stream=img_bytes.read())
        
        # Copy and scale text layer
        text_dict = page.get_text("dict")
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "")
                        if text.strip():
                            x = span["origin"][0] * scale
                            y = span["origin"][1] * scale
                            fontsize = max(4, span["size"] * scale)
                            try:
                                new_page.insert_text(
                                    (x, y), text,
                                    fontsize=fontsize,
                                    render_mode=3
                                )
                            except:
                                pass
    
    new_doc.save(output_path, garbage=4, deflate=True)
    new_doc.close()
    doc.close()
    
    return os.path.getsize(output_path) / 1024 / 1024

def main():
    print(f"Downscaling Google Vision PDFs to {TARGET_WIDTH}px width (JPEG {JPEG_QUALITY}%)")
    print("=" * 60)
    
    gv_pdfs = sorted([f for f in os.listdir(SOURCE_DIR) if f.endswith("_gv.pdf")])
    
    web_dir = os.path.join(SOURCE_DIR, "pdfs_web")
    os.makedirs(web_dir, exist_ok=True)
    
    total_orig = 0
    total_new = 0
    
    for pdf_name in gv_pdfs:
        input_path = os.path.join(SOURCE_DIR, pdf_name)
        base_name = pdf_name.replace("_gv.pdf", ".pdf")
        output_path = os.path.join(web_dir, base_name)
        
        orig_size = os.path.getsize(input_path) / 1024 / 1024
        total_orig += orig_size
        print(f"\n{pdf_name}: {orig_size:.1f} MB", end=" -> ")
        
        new_size = downscale_pdf(input_path, output_path)
        total_new += new_size
        print(f"{new_size:.1f} MB")
    
    print("\n" + "=" * 60)
    print(f"Total: {total_orig:.0f} MB -> {total_new:.0f} MB ({(1-total_new/total_orig)*100:.0f}% reduction)")

if __name__ == "__main__":
    main()
