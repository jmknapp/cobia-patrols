#!/usr/bin/env python3
"""OCR v3 - Aggressive preprocessing with binarization"""
import os, sys, glob, tempfile, subprocess
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import img2pdf
import cv2
import numpy as np

def preprocess(inp, out):
    # Read with OpenCV for better processing
    img = cv2.imread(inp, cv2.IMREAD_GRAYSCALE)
    
    # Denoise
    img = cv2.fastNlMeansDenoising(img, None, 10, 7, 21)
    
    # Adaptive threshold (binarization)
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10)
    
    cv2.imwrite(out, img)

def process(folder, outpdf):
    imgs = sorted(glob.glob(os.path.join(folder, '*.jpg')))
    print(f"Found {len(imgs)} images")
    
    with tempfile.TemporaryDirectory() as tmp:
        preproc = []
        for i, p in enumerate(imgs):
            o = os.path.join(tmp, f"p{i:03d}.png")
            preprocess(p, o)
            preproc.append(o)
            if (i+1) % 10 == 0: print(f"  Preprocessed {i+1}/{len(imgs)}")
        
        print("Creating PDF...")
        tpdf = os.path.join(tmp, "t.pdf")
        with open(tpdf, "wb") as f:
            f.write(img2pdf.convert(preproc))
        
        print("Running OCR...")
        subprocess.run(['ocrmypdf', '--force-ocr', '-l', 'eng', tpdf, outpdf], check=True)
    
    print(f"Done: {outpdf}")

if __name__ == '__main__':
    process(sys.argv[1], sys.argv[2])
