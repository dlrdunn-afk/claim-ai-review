from ultralytics import YOLO
import sys, os

src = sys.argv[1] if len(sys.argv) > 1 else "data/job-0001/photos"
weights = "detect/weights/damage-v1.pt"

if not os.path.exists(weights):
    raise SystemExit(f"Missing {weights}. Train first, then copy best.pt to that path.")

model = YOLO(weights)
model.predict(source=src, project="out/pred", name="damage-v1", save=True, conf=0.25)
print("Predictions saved to out/pred/damage-v1")
