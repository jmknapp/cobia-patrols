#!/usr/bin/env python3
"""Improved OCR using ocrmypdf"""
import os, sys, glob, tempfile, subprocess
from PIL import Image, ImageFilter, ImageEnhance
import img2pdf

def preprocess(inp, out):
    img = Image.open(inp).convert('L')
    img = ImageEnhance.Contrast(img).enhance(1.5)
    img = img.filter(ImageFilter.SHARPEN)
    img.save(out, 'PNG')

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
        subprocess.run(['ocrmypdf', '--force-ocr', '-l', 'eng', '--deskew', '--clean', tpdf, outpdf], check=True)
    
    print(f"Done: {outpdf}")

if __name__ == '__main__':
    process(sys.argv[1], sys.argv[2])
