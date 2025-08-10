import sys
import os
import csv
import pytesseract
import cv2
import numpy as np

job_id = sys.argv[1] if len(sys.argv) > 1 else 'job-0001'
image_path = f'out/bw_debug.jpg'  # Use the enhanced image
output_csv = f'out/{job_id}_ocr_rooms.csv'

# Load image
img = cv2.imread(image_path)
if img is None:
    print(f"❌ Could not load image: {image_path}")
    sys.exit(1)
print(f"✅ Loaded image size: {img.shape}")

# OCR
print("🔍 Running OCR on floorplan image...")
detection = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

# Collect room-related texts
rows = []
for i in range(len(detection['text'])):
    text = detection['text'][i].strip()
    if text:
        x, y, w, h = detection['left'][i], detection['top'][i], detection['width'][i], detection['height'][i]
        rows.append([text, x, y, w, h])

# Save raw OCR results
with open(output_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Room Name', 'X', 'Y', 'Width', 'Height'])
    for row in rows:
        writer.writerow(row)

print(f"✅ OCR results saved to: {output_csv}")
