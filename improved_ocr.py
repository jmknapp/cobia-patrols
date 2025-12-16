#!/usr/bin/env python3
"""
Improved OCR for USS Cobia patrol reports using preprocessing and Tesseract 5.
"""

import os
import sys
import cv2
import numpy as np
from PIL import Image
import pytesseract
import img2pdf
from pdf2image import convert_from_path
import fitz  # PyMuPDF

def preprocess_image(image_path, output_path=None):
    """
    Preprocess scanned image for better OCR:
    - Convert to grayscale
    - Denoise
    - Increase contrast
    - Adaptive thresholding (binarization)
    - Deskew
    """
    # Read image
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"  Error: Could not read {image_path}")
        return None
    
    # 1. Denoise (Non-local Means Denoising)
    denoised = cv2.fastNlMeansDenoising(img, None, h=10, templateWindowSize=7, searchWindowSize=21)
    
    # 2. Increase contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast = clahe.apply(denoised)
    
    # 3. Adaptive thresholding for binarization
    # This works better than global thresholding for uneven lighting
    binary = cv2.adaptiveThreshold(
        contrast, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=15,
        C=10
    )
    
    # 4. Deskew
    coords = np.column_stack(np.where(binary < 255))
    if len(coords) > 100:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        if abs(angle) > 0.5:  # Only rotate if skew is significant
            (h, w) = binary.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            binary = cv2.warpAffine(binary, M, (w, h), 
                                     flags=cv2.INTER_CUBIC, 
                                     borderMode=cv2.BORDER_REPLICATE)
    
    if output_path:
        cv2.imwrite(output_path, binary)
    
    return binary


def ocr_image(image, config=None):
    """
    Run Tesseract OCR on a preprocessed image.
    """
    if config is None:
        # Use LSTM engine (more accurate than legacy)
        # PSM 3 = Fully automatic page segmentation (default)
        config = '--oem 1 --psm 3 -l eng'
    
    # Convert numpy array to PIL Image for pytesseract
    if isinstance(image, np.ndarray):
        pil_image = Image.fromarray(image)
    else:
        pil_image = image
    
    text = pytesseract.image_to_string(pil_image, config=config)
    return text


def ocr_image_with_boxes(image, config=None):
    """
    Run Tesseract OCR and get text with bounding boxes.
    """
    if config is None:
        config = '--oem 1 --psm 3 -l eng'
    
    if isinstance(image, np.ndarray):
        pil_image = Image.fromarray(image)
    else:
        pil_image = image
    
    data = pytesseract.image_to_data(pil_image, config=config, output_type=pytesseract.Output.DICT)
    return data


def create_searchable_pdf_from_images(input_dir, output_pdf, preprocess=True):
    """
    Create a searchable PDF from a directory of images.
    """
    # Get all page images
    pages = sorted([f for f in os.listdir(input_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.tif', '.tiff'))])
    
    if not pages:
        print(f"No images found in {input_dir}")
        return False
    
    print(f"Found {len(pages)} pages in {input_dir}")
    
    # Create output PDF
    pdf_doc = fitz.open()
    
    for i, page_file in enumerate(pages):
        page_path = os.path.join(input_dir, page_file)
        print(f"  Processing page {i+1}/{len(pages)}: {page_file}...", end=" ", flush=True)
        
        # Read original image for the PDF
        original_img = cv2.imread(page_path)
        if original_img is None:
            print("SKIP (unreadable)")
            continue
        
        height, width = original_img.shape[:2]
        
        # Preprocess for OCR
        if preprocess:
            processed_img = preprocess_image(page_path)
        else:
            processed_img = cv2.imread(page_path, cv2.IMREAD_GRAYSCALE)
        
        if processed_img is None:
            print("SKIP (preprocess failed)")
            continue
        
        # Get OCR data with bounding boxes
        ocr_data = ocr_image_with_boxes(processed_img)
        
        # Count words found
        words = [w for w, c in zip(ocr_data['text'], ocr_data['conf']) if w.strip() and int(c) > 0]
        print(f"{len(words)} words")
        
        # Create PDF page from original image
        img_bytes = cv2.imencode('.jpg', original_img, [cv2.IMWRITE_JPEG_QUALITY, 95])[1].tobytes()
        
        # Insert image as page
        img_doc = fitz.open(stream=img_bytes, filetype="jpeg")
        rect = img_doc[0].rect
        pdf_page = pdf_doc.new_page(width=rect.width, height=rect.height)
        pdf_page.insert_image(rect, stream=img_bytes)
        
        # Add invisible text layer
        # Scale factor if preprocessing changed dimensions
        scale_x = width / processed_img.shape[1] if processed_img.shape[1] != width else 1
        scale_y = height / processed_img.shape[0] if processed_img.shape[0] != height else 1
        
        for j in range(len(ocr_data['text'])):
            text = ocr_data['text'][j]
            conf = int(ocr_data['conf'][j])
            
            if text.strip() and conf > 30:  # Only include text with reasonable confidence
                x = ocr_data['left'][j] * scale_x
                y = ocr_data['top'][j] * scale_y
                w = ocr_data['width'][j] * scale_x
                h = ocr_data['height'][j] * scale_y
                
                # Insert invisible text at the correct position
                text_rect = fitz.Rect(x, y, x + w, y + h)
                
                # Calculate font size to fit the box
                fontsize = h * 0.8
                if fontsize > 0:
                    # Insert text with transparent color (invisible but searchable)
                    try:
                        pdf_page.insert_text(
                            (x, y + h * 0.8),  # baseline position
                            text,
                            fontsize=fontsize,
                            color=(1, 1, 1),  # white (invisible on white background)
                            render_mode=3  # invisible
                        )
                    except:
                        pass  # Skip problematic text
        
        img_doc.close()
    
    # Save the PDF
    print(f"\nSaving PDF...")
    pdf_doc.save(output_pdf, garbage=4, deflate=True)
    pdf_doc.close()
    
    size_mb = os.path.getsize(output_pdf) / (1024 * 1024)
    print(f"Created: {output_pdf} ({size_mb:.1f} MB)")
    return True


def compare_ocr_quality(image_path):
    """
    Compare OCR quality with and without preprocessing.
    """
    print(f"\nComparing OCR on: {image_path}")
    
    # Without preprocessing
    img_raw = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    text_raw = ocr_image(img_raw)
    words_raw = len(text_raw.split())
    
    # With preprocessing  
    img_processed = preprocess_image(image_path)
    text_processed = ocr_image(img_processed)
    words_processed = len(text_processed.split())
    
    print(f"  Raw OCR:        {words_raw} words")
    print(f"  Preprocessed:   {words_processed} words")
    print(f"  Improvement:    {(words_processed - words_raw) / max(words_raw, 1) * 100:.1f}%")
    
    return text_raw, text_processed


if __name__ == '__main__':
    # Example usage
    if len(sys.argv) > 1:
        if sys.argv[1] == 'compare':
            # Compare OCR quality on a single image
            image_path = sys.argv[2] if len(sys.argv) > 2 else 'cobia_1st_patrol_report/page_004.jpg'
            compare_ocr_quality(image_path)
        elif sys.argv[1] == 'process':
            # Process a full patrol report
            input_dir = sys.argv[2] if len(sys.argv) > 2 else 'cobia_1st_patrol_report'
            output_pdf = sys.argv[3] if len(sys.argv) > 3 else 'USS_Cobia_1st_Patrol_Report_improved.pdf'
            create_searchable_pdf_from_images(input_dir, output_pdf)
    else:
        print("Usage:")
        print("  python improved_ocr.py compare [image_path]  - Compare OCR quality")
        print("  python improved_ocr.py process [input_dir] [output.pdf]  - Create searchable PDF")



