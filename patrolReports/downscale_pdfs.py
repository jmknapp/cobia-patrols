#!/usr/bin/env python3
"""
Downscale PDF files for faster web viewing.
Creates lower-resolution versions in pdfs_web/ subdirectory.
"""

import os
import fitz  # PyMuPDF

# Configuration
SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SOURCE_DIR, 'pdfs_web')
TARGET_WIDTH = 850  # Target width in pixels (good for web viewing)
JPEG_QUALITY = 85   # JPEG quality for images (0-100)

def downscale_pdf(input_path, output_path, target_width=TARGET_WIDTH):
    """Downscale a PDF by rendering pages at lower resolution."""
    
    print(f"Processing: {os.path.basename(input_path)}")
    
    # Open source PDF
    src_doc = fitz.open(input_path)
    
    # Create new PDF
    dst_doc = fitz.open()
    
    for page_num in range(len(src_doc)):
        src_page = src_doc[page_num]
        
        # Calculate scale to achieve target width
        scale = target_width / src_page.rect.width
        
        # Create transformation matrix
        mat = fitz.Matrix(scale, scale)
        
        # Render page to pixmap (image)
        pix = src_page.get_pixmap(matrix=mat, alpha=False)
        
        # Create new page with scaled dimensions
        new_page = dst_doc.new_page(
            width=pix.width,
            height=pix.height
        )
        
        # Insert the rendered image into the new page
        new_page.insert_image(
            new_page.rect,
            pixmap=pix
        )
        
        if (page_num + 1) % 10 == 0:
            print(f"  Processed {page_num + 1}/{len(src_doc)} pages...")
    
    # Save with compression
    dst_doc.save(
        output_path,
        garbage=4,  # Maximum garbage collection
        deflate=True,  # Compress streams
        clean=True,  # Clean up redundancies
    )
    
    src_doc.close()
    dst_doc.close()
    
    # Report size reduction
    src_size = os.path.getsize(input_path) / (1024 * 1024)
    dst_size = os.path.getsize(output_path) / (1024 * 1024)
    reduction = (1 - dst_size / src_size) * 100
    
    print(f"  Done: {src_size:.1f}MB → {dst_size:.1f}MB ({reduction:.0f}% smaller)")
    return dst_size

def main():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Find all PDF files
    pdf_files = sorted([f for f in os.listdir(SOURCE_DIR) if f.endswith('.pdf')])
    
    if not pdf_files:
        print("No PDF files found!")
        return
    
    print(f"Found {len(pdf_files)} PDF files")
    print(f"Target width: {TARGET_WIDTH}px")
    print(f"Output directory: {OUTPUT_DIR}")
    print("-" * 50)
    
    total_src = 0
    total_dst = 0
    
    for pdf_file in pdf_files:
        input_path = os.path.join(SOURCE_DIR, pdf_file)
        output_path = os.path.join(OUTPUT_DIR, pdf_file)
        
        total_src += os.path.getsize(input_path) / (1024 * 1024)
        total_dst += downscale_pdf(input_path, output_path)
    
    print("-" * 50)
    print(f"Total: {total_src:.1f}MB → {total_dst:.1f}MB ({(1-total_dst/total_src)*100:.0f}% smaller)")
    print("Done!")

if __name__ == '__main__':
    main()

