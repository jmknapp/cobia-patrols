"""
USS Cobia Patrol Reports Search Web App
Search through historical submarine patrol reports with highlighted results.
"""

import os
import re
import json
import glob
from flask import Flask, render_template, request, jsonify, send_from_directory
import fitz  # PyMuPDF

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, env vars should be set another way

app = Flask(__name__)

# Corrections directory
CORRECTIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'corrections')

# Path to PDF files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_ORIGINAL_DIR = BASE_DIR  # Original high-res PDFs

# V3 OCR PDFs have better text extraction AND embedded text layers for selection
# Use these for both searching and viewing
PDF_OCR_DIR = BASE_DIR  # V3 PDFs are named *_v3.pdf

# Serve V3 PDFs for viewing (they have text layers for selection/Ctrl+F)
PDF_DIR = BASE_DIR

# Cache for extracted PDF text
pdf_cache = {}


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file, returning a list of (page_num, text) tuples."""
    if pdf_path in pdf_cache:
        return pdf_cache[pdf_path]
    
    pages = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            pages.append((page_num + 1, text))  # 1-indexed page numbers
        doc.close()
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return []
    
    pdf_cache[pdf_path] = pages
    return pages


def get_pdf_files():
    """Get list of main PDF files (not OCR variants)."""
    return sorted([f for f in os.listdir(PDF_ORIGINAL_DIR) 
                   if f.endswith('.pdf') 
                   and not f.endswith('_v3.pdf') 
                   and not f.endswith('_improved.pdf') 
                   and not f.endswith('_gv.pdf')
                   and not f.endswith('_corrected.pdf')
                   and 'test_' not in f])


def search_pdfs(query, context_chars=150):
    """
    Search through all PDFs for the query pattern.
    Returns matches with context.
    """
    if not query or len(query.strip()) < 2:
        return []
    
    # Strip surrounding quotes if present
    query = query.strip()
    if (query.startswith('"') and query.endswith('"')) or \
       (query.startswith("'") and query.endswith("'")):
        query = query[1:-1]
    
    if not query or len(query.strip()) < 2:
        return []
    
    results = []
    pdf_files = get_pdf_files()
    
    # Create regex pattern (case-insensitive)
    try:
        pattern = re.compile(re.escape(query), re.IGNORECASE)
    except re.error:
        return []
    
    for pdf_file in pdf_files:
        # Load corrections for this PDF
        corrections = load_corrections(pdf_file)
        
        # Try Google Vision OCR first (best quality), then V3, then original
        base_name = pdf_file.replace('.pdf', '')
        gv_json = os.path.join(BASE_DIR, f"{base_name}_gv_ocr.json")
        
        if os.path.exists(gv_json):
            # Use Google Vision OCR text
            with open(gv_json, 'r', encoding='utf-8') as f:
                gv_data = json.load(f)
            pages = [(int(pn), txt) for pn, txt in gv_data.items()]
            pages.sort(key=lambda x: x[0])
        else:
            # Fall back to V3 or original PDF
            v3_path = os.path.join(PDF_OCR_DIR, f"{base_name}_v3.pdf")
            if os.path.exists(v3_path):
                pdf_path = v3_path
            else:
                pdf_path = os.path.join(PDF_ORIGINAL_DIR, pdf_file)
            pages = extract_text_from_pdf(pdf_path)
        
        for page_num, ocr_text in pages:
            # Use correction if available, otherwise OCR
            text = corrections.get(str(page_num), ocr_text)
            # Find all matches in this page
            for match in pattern.finditer(text):
                start = match.start()
                end = match.end()
                
                # Get context around the match
                context_start = max(0, start - context_chars)
                context_end = min(len(text), end + context_chars)
                
                # Adjust to word boundaries
                if context_start > 0:
                    # Find the start of the word or sentence
                    while context_start > 0 and text[context_start - 1] not in ' \n\t':
                        context_start -= 1
                
                if context_end < len(text):
                    # Find the end of the word or sentence
                    while context_end < len(text) and text[context_end] not in ' \n\t':
                        context_end += 1
                
                context = text[context_start:context_end]
                
                # Clean up the context (remove excessive whitespace)
                context = ' '.join(context.split())
                
                # Calculate relative position of match in context
                match_in_context_start = start - context_start
                match_in_context_end = end - context_start
                
                results.append({
                    'pdf_file': pdf_file,
                    'page_num': page_num,
                    'context': context,
                    'match_start': match_in_context_start,
                    'match_end': match_in_context_end,
                    'matched_text': match.group()
                })
    
    return results


@app.route('/')
def index():
    """Serve the main search page."""
    return render_template('index.html')


@app.route('/robots.txt')
def robots():
    """Serve robots.txt for SEO."""
    return send_from_directory(app.static_folder, 'robots.txt', mimetype='text/plain')


@app.route('/favicon.ico')
def favicon():
    """Serve favicon for browsers that request it directly."""
    return send_from_directory(app.static_folder, 'cobiaicon.png', mimetype='image/png')


@app.route('/favicon.png')
def favicon_png():
    """Serve PNG favicon for browsers that request it."""
    return send_from_directory(app.static_folder, 'cobiaicon.png', mimetype='image/png')


@app.route('/google6587657f8b526a48.html')
def google_verify():
    """Serve Google Search Console verification file."""
    return send_from_directory(app.static_folder, 'google6587657f8b526a48.html')


@app.route('/sitemap.xml')
def sitemap():
    """Serve sitemap.xml for SEO."""
    return send_from_directory(app.static_folder, 'sitemap.xml', mimetype='application/xml')


@app.route('/about')
def about():
    """Serve the about/help page."""
    return render_template('about.html')


@app.route('/analytics')
def analytics():
    """Serve the analytics page (hidden - not linked from main site)."""
    from analytics import get_analytics
    from datetime import datetime
    
    days = request.args.get('days', 30, type=int)
    if days not in [7, 30, 90]:
        days = 30
    
    stats = get_analytics(days=days)
    return render_template('analytics.html', 
                         stats=stats, 
                         days=days,
                         now=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@app.route('/torpedo_attacks')
def torpedo_attacks():
    """Serve the torpedo attacks visualization page (hidden)."""
    import mysql.connector
    
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('''
        SELECT id, patrol, attack_number, attack_date, attack_time,
               target_name, target_type, target_tonnage, result
        FROM torpedo_attacks
        ORDER BY patrol, attack_number
    ''')
    attacks = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('torpedo_attacks.html', attacks=attacks)


@app.route('/attack_viz/<int:attack_id>')
def attack_viz(attack_id):
    """Serve the visualization for a specific attack."""
    import mysql.connector
    
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    cursor = conn.cursor(dictionary=True)
    
    # Get attack data
    cursor.execute('SELECT * FROM torpedo_attacks WHERE id = %s', (attack_id,))
    attack = cursor.fetchone()
    
    if not attack:
        cursor.close()
        conn.close()
        return "Attack not found", 404
    
    # Get torpedo data
    cursor.execute('SELECT * FROM torpedoes_fired WHERE attack_id = %s ORDER BY fire_sequence', (attack_id,))
    torpedoes = cursor.fetchall()
    
    # Get convoy ships (if any)
    convoy_ships = []
    try:
        cursor.execute('SELECT * FROM convoy_ships WHERE attack_id = %s ORDER BY ship_letter', (attack_id,))
        convoy_ships = cursor.fetchall()
    except:
        pass  # Table may not exist yet
    
    cursor.close()
    conn.close()
    
    return render_template('attack_viz.html', attack=attack, torpedoes=torpedoes, convoy_ships=convoy_ships)


@app.route('/view')
def viewer():
    """Serve the PDF viewer page."""
    return render_template('viewer.html')


@app.route('/search')
def search():
    """API endpoint for searching PDFs."""
    query = request.args.get('q', '').strip()
    results = search_pdfs(query)
    return jsonify({
        'query': query,
        'count': len(results),
        'results': results
    })


@app.route('/pdfs/<filename>')
def serve_pdf(filename):
    """Serve PDF files. Use downscaled web versions for fast loading."""
    base_name = filename.replace('.pdf', '')
    
    # Use downscaled web version (fast loading with text layer)
    web_dir = os.path.join(BASE_DIR, "pdfs_web")
    web_filename = f"{base_name}.pdf"
    web_path = os.path.join(web_dir, web_filename)
    if os.path.exists(web_path):
        return send_from_directory(web_dir, web_filename)
    
    # Fall back to Google Vision version
    gv_filename = f"{base_name}_gv.pdf"
    gv_path = os.path.join(BASE_DIR, gv_filename)
    if os.path.exists(gv_path):
        return send_from_directory(BASE_DIR, gv_filename)
    
    # Fall back to V3 version
    v3_filename = f"{base_name}_v3.pdf"
    v3_path = os.path.join(PDF_OCR_DIR, v3_filename)
    if os.path.exists(v3_path):
        return send_from_directory(PDF_OCR_DIR, v3_filename)
    
    # Fall back to original
    return send_from_directory(PDF_DIR, filename)


@app.route('/pdf-list')
def pdf_list():
    """Return list of available PDFs."""
    return jsonify(get_pdf_files())


# --- Corrections System ---

def get_correction_path(pdf_name):
    """Get the path to the corrections file for a PDF."""
    base_name = pdf_name.replace('.pdf', '')
    return os.path.join(CORRECTIONS_DIR, f"{base_name}.json")


def load_corrections(pdf_name):
    """Load corrections for a PDF. Returns dict of {page_num: corrected_text}."""
    path = get_correction_path(pdf_name)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_correction(pdf_name, page_num, text):
    """Save a correction for a specific page."""
    corrections = load_corrections(pdf_name)
    corrections[str(page_num)] = text
    path = get_correction_path(pdf_name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(corrections, f, indent=2, ensure_ascii=False)


def get_page_text(pdf_name, page_num):
    """Get text for a page, preferring corrections over OCR."""
    corrections = load_corrections(pdf_name)
    if str(page_num) in corrections:
        return corrections[str(page_num)]
    
    # Fall back to OCR text
    base_name = pdf_name.replace('.pdf', '')
    v3_path = os.path.join(PDF_OCR_DIR, f"{base_name}_v3.pdf")
    if os.path.exists(v3_path):
        pdf_path = v3_path
    else:
        pdf_path = os.path.join(PDF_ORIGINAL_DIR, pdf_name)
    
    pages = extract_text_from_pdf(pdf_path)
    for pn, text in pages:
        if pn == page_num:
            return text
    return ""


def get_image_folder(pdf_name):
    """Get the folder containing original scan images for a PDF."""
    # Map PDF names to image folders (in parent cobia directory)
    base_name = pdf_name.replace('.pdf', '').replace('USS_Cobia_', 'cobia_').lower()
    # Image folders are in /home/jmknapp/cobia/, not in patrolReports
    cobia_dir = os.path.dirname(BASE_DIR)  # Go up from patrolReports to cobia
    folder = os.path.join(cobia_dir, base_name)
    if os.path.exists(folder):
        return folder
    return None


@app.route('/correct')
def correct_page():
    """Serve the OCR correction interface."""
    return render_template('correct.html')


@app.route('/api/corrections/<pdf_name>/<int:page_num>', methods=['GET'])
def get_correction(pdf_name, page_num):
    """Get text for a page (correction or OCR)."""
    text = get_page_text(pdf_name, page_num)
    corrections = load_corrections(pdf_name)
    is_corrected = str(page_num) in corrections
    
    # Get total pages
    base_name = pdf_name.replace('.pdf', '')
    v3_path = os.path.join(PDF_OCR_DIR, f"{base_name}_v3.pdf")
    if os.path.exists(v3_path):
        pdf_path = v3_path
    else:
        pdf_path = os.path.join(PDF_ORIGINAL_DIR, pdf_name)
    
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        doc.close()
    except:
        total_pages = 0
    
    return jsonify({
        'pdf_name': pdf_name,
        'page_num': page_num,
        'total_pages': total_pages,
        'text': text,
        'is_corrected': is_corrected
    })


@app.route('/api/corrections/<pdf_name>/<int:page_num>', methods=['POST'])
def save_correction_api(pdf_name, page_num):
    """Save a correction for a page."""
    data = request.get_json()
    text = data.get('text', '')
    save_correction(pdf_name, page_num, text)
    
    # Clear cache for this PDF so search uses new corrections
    base_name = pdf_name.replace('.pdf', '')
    v3_path = os.path.join(PDF_OCR_DIR, f"{base_name}_v3.pdf")
    if v3_path in pdf_cache:
        del pdf_cache[v3_path]
    orig_path = os.path.join(PDF_ORIGINAL_DIR, pdf_name)
    if orig_path in pdf_cache:
        del pdf_cache[orig_path]
    
    return jsonify({'success': True, 'message': f'Saved correction for page {page_num}'})


@app.route('/api/scan-image/<pdf_name>/<int:page_num>')
def get_scan_image(pdf_name, page_num):
    """Serve the original scan image for a page."""
    folder = get_image_folder(pdf_name)
    if not folder:
        return jsonify({'error': 'Image folder not found'}), 404
    
    # Find the image file (could be page_001.jpg, page_001.png, etc.)
    patterns = [f"page_{page_num:03d}.*", f"page_{page_num:02d}.*", f"page_{page_num}.*"]
    for pattern in patterns:
        matches = glob.glob(os.path.join(folder, pattern))
        if matches:
            return send_from_directory(folder, os.path.basename(matches[0]))
    
    return jsonify({'error': f'Image for page {page_num} not found'}), 404


@app.route('/api/correction-stats')
def correction_stats():
    """Get statistics about corrections for all PDFs."""
    stats = []
    for pdf_file in get_pdf_files():
        corrections = load_corrections(pdf_file)
        
        # Get total pages
        base_name = pdf_file.replace('.pdf', '')
        v3_path = os.path.join(PDF_OCR_DIR, f"{base_name}_v3.pdf")
        if os.path.exists(v3_path):
            pdf_path = v3_path
        else:
            pdf_path = os.path.join(PDF_ORIGINAL_DIR, pdf_file)
        
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            doc.close()
        except:
            total_pages = 0
        
        stats.append({
            'pdf_name': pdf_file,
            'total_pages': total_pages,
            'corrected_pages': len(corrections),
            'percent_complete': round(len(corrections) / total_pages * 100, 1) if total_pages > 0 else 0
        })
    
    return jsonify(stats)


@app.route('/api/rebuild-pdf/<pdf_name>', methods=['POST'])
def rebuild_pdf(pdf_name):
    """Rebuild a PDF with corrected text embedded."""
    import time
    
    # Get the image folder
    folder = get_image_folder(pdf_name)
    if not folder:
        return jsonify({'error': 'Image folder not found'}), 404
    
    # Find all images
    images = sorted(glob.glob(os.path.join(folder, '*.jpg')) + 
                   glob.glob(os.path.join(folder, '*.png')))
    if not images:
        return jsonify({'error': 'No images found'}), 404
    
    # Load corrections
    corrections = load_corrections(pdf_name)
    
    # Get OCR text as fallback
    base_name = pdf_name.replace('.pdf', '')
    v3_path = os.path.join(PDF_OCR_DIR, f"{base_name}_v3.pdf")
    if os.path.exists(v3_path):
        ocr_pages = extract_text_from_pdf(v3_path)
    else:
        ocr_pages = extract_text_from_pdf(os.path.join(PDF_ORIGINAL_DIR, pdf_name))
    
    # Create new PDF
    output_path = os.path.join(BASE_DIR, f"{base_name}_corrected.pdf")
    doc = fitz.open()
    
    for i, img_path in enumerate(images):
        page_num = i + 1
        
        # Get text for this page (correction or OCR)
        if str(page_num) in corrections:
            text = corrections[str(page_num)]
        else:
            text = ""
            for pn, t in ocr_pages:
                if pn == page_num:
                    text = t
                    break
        
        # Load image and get dimensions
        img = fitz.open(img_path)
        img_rect = img[0].rect
        
        # Create a new page with image dimensions
        page = doc.new_page(width=img_rect.width, height=img_rect.height)
        
        # Insert the image
        page.insert_image(page.rect, filename=img_path)
        
        # Insert text as invisible layer
        # Split text into lines and position them
        if text.strip():
            fontsize = 12
            lines = text.split('\n')
            y_pos = 50  # Start position
            for line in lines:
                if line.strip():
                    # Insert invisible text
                    page.insert_text(
                        (50, y_pos),
                        line,
                        fontsize=fontsize,
                        render_mode=3  # Invisible
                    )
                y_pos += fontsize * 1.5
        
        img.close()
    
    # Save the new PDF
    doc.save(output_path)
    doc.close()
    
    # Clear cache so the new PDF is used
    if output_path in pdf_cache:
        del pdf_cache[output_path]
    
    return jsonify({
        'success': True,
        'message': f'Rebuilt PDF with {len(corrections)} corrected pages',
        'output_file': os.path.basename(output_path),
        'total_pages': len(images),
        'corrected_pages': len(corrections)
    })


@app.route('/pdf-text/<filename>/<int:page_num>')
def get_pdf_text(filename, page_num):
    """Get text content and positions from original PDF for highlighting."""
    import fitz
    
    pdf_path = os.path.join(PDF_ORIGINAL_DIR, filename)
    if not os.path.exists(pdf_path):
        return jsonify({'error': 'PDF not found'}), 404
    
    try:
        doc = fitz.open(pdf_path)
        if page_num < 1 or page_num > len(doc):
            return jsonify({'error': 'Invalid page number'}), 400
        
        page = doc[page_num - 1]  # 0-indexed
        
        # Get page dimensions for scaling
        original_width = page.rect.width
        original_height = page.rect.height
        
        # Extract text with positions
        blocks = []
        text_dict = page.get_text("dict")
        
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if text:
                            bbox = span.get("bbox", [0, 0, 0, 0])
                            blocks.append({
                                "text": text,
                                "x": bbox[0],
                                "y": bbox[1],
                                "width": bbox[2] - bbox[0],
                                "height": bbox[3] - bbox[1]
                            })
        
        doc.close()
        
        return jsonify({
            "page": page_num,
            "original_width": original_width,
            "original_height": original_height,
            "blocks": blocks
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Pre-cache all PDFs on startup
    print("Pre-caching PDF text extraction...")
    print(f"  Serving PDFs from: {PDF_DIR}")
    print(f"  Looking for V3 OCR PDFs in: {PDF_OCR_DIR}")
    for pdf_file in get_pdf_files():
        # Try V3 first
        base_name = pdf_file.replace('.pdf', '')
        v3_path = os.path.join(PDF_OCR_DIR, f"{base_name}_v3.pdf")
        if os.path.exists(v3_path):
            extract_text_from_pdf(v3_path)
            print(f"  Cached (V3 OCR): {pdf_file}")
        else:
            pdf_path = os.path.join(PDF_ORIGINAL_DIR, pdf_file)
            extract_text_from_pdf(pdf_path)
            print(f"  Cached (original): {pdf_file}")
    print("Ready!")
    
    app.run(debug=True, port=5012, host='0.0.0.0')

