from ultralytics import YOLO
import os, sys

src = sys.argv[1] if len(sys.argv) > 1 else "data/job-0001/photos"
os.makedirs("out/pred", exist_ok=True)
model = YOLO("yolov8n.pt")  # downloads pre-trained weights on first run
model.predict(source=src, project="out/pred", name="demo", save=True, conf=0.25)
print("Demo results saved to out/pred/demo")
