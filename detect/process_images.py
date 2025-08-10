from ultralytics import YOLO
import cv2
import os
import pandas as pd

model = YOLO("yolov8n.pt")  # Using a small pre-trained YOLOv8 model

job_id = "job-0001"
image_folder = f"data/{job_id}"
output_folder = f"out/{job_id}_detections"
os.makedirs(output_folder, exist_ok=True)

results_data = []

for img_file in os.listdir(image_folder):
    if not img_file.lower().endswith((".jpg", ".jpeg", ".png")):
        continue

    img_path = os.path.join(image_folder, img_file)
    results = model(img_path)

    for box in results[0].boxes:
        cls = int(box.cls[0])
        label = results[0].names[cls]
        conf = float(box.conf[0])
        x1, y1, x2, y2 = box.xyxy[0]

        results_data.append({
            "image": img_file,
            "label": label,
            "confidence": conf,
            "x1": int(x1),
            "y1": int(y1),
            "x2": int(x2),
            "y2": int(y2)
        })

    # Save image with bounding boxes
    results[0].save(filename=os.path.join(output_folder, img_file))

# Save results as CSV
df = pd.DataFrame(results_data)
df.to_csv(f"out/{job_id}_detections.csv", index=False)

print(f"✅ Detection complete: {len(results_data)} issues found")
