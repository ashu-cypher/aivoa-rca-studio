"""Generate demo_data/fictional_drying_incident.pdf from the fictional .txt (text-based, not scanned)."""
import pathlib

import fitz

root = pathlib.Path(__file__).resolve().parents[1]
text = (root / "demo_data" / "fictional_drying_incident.txt").read_text()
doc = fitz.open()
page = doc.new_page()
# Simple wrapped text insertion
rect = fitz.Rect(54, 54, 540, 760)
page.insert_textbox(rect, text, fontsize=11, fontname="helv")
doc.save(root / "demo_data" / "fictional_drying_incident.pdf")
print("wrote", root / "demo_data" / "fictional_drying_incident.pdf")
