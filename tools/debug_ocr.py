from PIL import Image, ImageEnhance
import pytesseract

img_path = 'data/job-0001/iguide/3938584280.JPG'
output_path = 'out/bw_debug.jpg'

# Load image
img = Image.open(img_path)

# Convert to grayscale
img = img.convert('L')

# Increase contrast
img = ImageEnhance.Contrast(img).enhance(2.5)

# Convert to black-and-white using a threshold
bw = img.point(lambda x: 0 if x < 180 else 255, '1')

# Save debug output
bw.save(output_path)
print(f"✅ Saved high-contrast image: {output_path}")

# Run OCR and show text
text = pytesseract.image_to_string(bw)
print("🔎 OCR Output:")
print(text)
