#!/usr/bin/env python3
"""Create a searchable PDF from the patrol report images using OCR."""

import os
import subprocess
import img2pdf
from PIL import Image

input_dir = "patrol_report_5th"
output_pdf = "USS_Cobia_5th_Patrol_Report.pdf"
temp_pdf = "temp_patrol_report.pdf"

# Get all page images in order
pages = sorted([f for f in os.listdir(input_dir) if f.endswith('.jpg')])
print(f"Found {len(pages)} pages")

# First, create a simple PDF from the images
print("Creating PDF from images...")
image_paths = [os.path.join(input_dir, p) for p in pages]

# Use img2pdf to create the initial PDF (preserves quality)
with open(temp_pdf, "wb") as f:
    f.write(img2pdf.convert(image_paths))
print(f"  Created temporary PDF: {temp_pdf}")

# Now run OCR on the PDF to make it searchable
print("Running OCR (this may take several minutes for 45 pages)...")
print("  Processing...")

result = subprocess.run([
    "ocrmypdf",
    "--language", "eng",
    "--rotate-pages",  # Auto-rotate if needed
    "--deskew",  # Straighten pages
    "--clean",  # Clean up scanned images
    "--optimize", "1",  # Light optimization
    "--output-type", "pdf",
    "--jobs", "4",  # Use 4 parallel processes
    temp_pdf,
    output_pdf
], capture_output=True, text=True)

if result.returncode == 0:
    print(f"  OCR complete!")
else:
    print(f"  OCR warning/info: {result.stderr[:500] if result.stderr else 'none'}")

# Clean up temp file
if os.path.exists(temp_pdf):
    os.remove(temp_pdf)

# Report result
if os.path.exists(output_pdf):
    size_mb = os.path.getsize(output_pdf) / (1024 * 1024)
    print(f"\nSuccess! Created: {output_pdf} ({size_mb:.1f} MB)")
    print("The PDF is now searchable - you can use Ctrl+F to find text.")
else:
    print("Error: PDF was not created")
