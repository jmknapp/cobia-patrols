#!/usr/bin/env python3
"""
Create a searchable PDF from the USS Cobia muster roll images.
Uses tesseract to OCR each page and create a PDF with embedded text layer.
"""

import os
import subprocess
from pathlib import Path

# Directories
INPUT_DIR = "/home/jmknapp/cobia/cobia_muster_rolls/full_set"
OUTPUT_DIR = "/home/jmknapp/cobia/cobia_muster_rolls"
OUTPUT_PDF = os.path.join(OUTPUT_DIR, "USS_Cobia_SS245_Muster_Rolls_1944-1946.pdf")

def create_searchable_pdf():
    """Create a searchable PDF from all muster roll images."""
    
    # Get all jpg files sorted by name
    input_path = Path(INPUT_DIR)
    jpg_files = sorted(input_path.glob("page_*.jpg"))
    
    if not jpg_files:
        print("No image files found!")
        return False
    
    print(f"Found {len(jpg_files)} images")
    print("Creating searchable PDF with OCR...")
    print("=" * 60)
    
    # Create temporary directory for individual PDFs
    temp_dir = os.path.join(OUTPUT_DIR, "temp_pdfs")
    os.makedirs(temp_dir, exist_ok=True)
    
    pdf_files = []
    
    for i, jpg_file in enumerate(jpg_files):
        print(f"  Processing {jpg_file.name} ({i+1}/{len(jpg_files)})...", end=" ", flush=True)
        
        # Output PDF for this page (tesseract adds .pdf extension)
        page_pdf_base = os.path.join(temp_dir, f"page_{i:03d}")
        page_pdf = page_pdf_base + ".pdf"
        
        try:
            # Use tesseract to create a searchable PDF
            # -l eng = English language
            # pdf = output format
            result = subprocess.run(
                ["tesseract", str(jpg_file), page_pdf_base, "-l", "eng", "pdf"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and os.path.exists(page_pdf):
                pdf_files.append(page_pdf)
                print("done")
            else:
                print(f"FAILED: {result.stderr}")
        except Exception as e:
            print(f"ERROR: {e}")
    
    print("=" * 60)
    print(f"Created {len(pdf_files)} individual PDFs")
    
    if not pdf_files:
        print("No PDFs created!")
        return False
    
    # Merge all PDFs using pdfunite (from poppler-utils) or pdftk
    print("Merging PDFs...")
    
    # Try pdfunite first
    try:
        cmd = ["pdfunite"] + pdf_files + [OUTPUT_PDF]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"SUCCESS: Created {OUTPUT_PDF}")
            # Clean up temp files
            for f in pdf_files:
                os.remove(f)
            os.rmdir(temp_dir)
            return True
    except FileNotFoundError:
        pass
    
    # Try pdftk as fallback
    try:
        cmd = ["pdftk"] + pdf_files + ["cat", "output", OUTPUT_PDF]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"SUCCESS: Created {OUTPUT_PDF}")
            # Clean up temp files
            for f in pdf_files:
                os.remove(f)
            os.rmdir(temp_dir)
            return True
    except FileNotFoundError:
        pass
    
    # Try using Python's PyPDF2 as last resort
    try:
        from PyPDF2 import PdfMerger
        merger = PdfMerger()
        for pdf in pdf_files:
            merger.append(pdf)
        merger.write(OUTPUT_PDF)
        merger.close()
        print(f"SUCCESS: Created {OUTPUT_PDF}")
        # Clean up temp files
        for f in pdf_files:
            os.remove(f)
        os.rmdir(temp_dir)
        return True
    except ImportError:
        print("ERROR: No PDF merge tool available (tried pdfunite, pdftk, PyPDF2)")
        print(f"Individual PDFs are in: {temp_dir}")
        return False

def main():
    print("USS Cobia Muster Roll PDF Creator")
    print("Source: National Archives Catalog ID 125745304")
    print("=" * 60)
    
    success = create_searchable_pdf()
    
    if success:
        # Show file size
        size_mb = os.path.getsize(OUTPUT_PDF) / (1024 * 1024)
        print(f"Final PDF size: {size_mb:.1f} MB")

if __name__ == "__main__":
    main()



