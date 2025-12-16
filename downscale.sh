cd /home/jmknapp/cobia && source patrolReports/venv/bin/activate && python3 << 'EOF'
import os, io, fitz
from PIL import Image

SOURCE = "patrolReports/USS_Cobia_SS245_Muster_Rolls_1944-1946_gv.pdf"
OUTPUT = "patrolReports/pdfs_web/USS_Cobia_SS245_Muster_Rolls_1944-1946.pdf"

print(f"Downscaling {SOURCE}...")
doc = fitz.open(SOURCE)
new_doc = fitz.open()

for i in range(len(doc)):
    if i % 10 == 0:
        print(f"  Page {i+1}/{len(doc)}")
    
    page = doc[i]
    scale = 850 / page.rect.width
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat)
    
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75)
    buf.seek(0)
    
    new_page = new_doc.new_page(width=850, height=int(page.rect.height * scale))
    new_page.insert_image(new_page.rect, stream=buf.read())
    
    # Copy text layer
    for b in page.get_text("dict").get("blocks", []):
        if b.get("type") == 0:
            for ln in b.get("lines", []):
                for sp in ln.get("spans", []):
                    if sp.get("text", "").strip():
                        try:
                            new_page.insert_text(
                                (sp["origin"][0]*scale, sp["origin"][1]*scale),
                                sp["text"],
                                fontsize=max(4, sp["size"]*scale),
                                render_mode=3
                            )
                        except:
                            pass

print("Saving...")
new_doc.save(OUTPUT, garbage=4, deflate=True)
new_doc.close()
doc.close()
print(f"Done! Size: {os.path.getsize(OUTPUT)/1024/1024:.1f} MB")
EOF
