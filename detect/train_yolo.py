from ultralytics import YOLO
import torch, os

def pick_device():
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"          # Apple GPU
    if torch.cuda.is_available():
        return 0              # NVIDIA GPU
    return "cpu"              # CPU

if __name__ == "__main__":
    os.makedirs("out/yolo", exist_ok=True)
    device = pick_device()
    print("Using device:", device)

    model = YOLO("yolov8n.pt")  # start from nano weights for speed
    model.train(
        data="detect/data_damage_v1.yaml",
        epochs=30,
        imgsz=960,
        batch=16,
        project="out/yolo",
        name="damage-v1",
        device=device,
        patience=8,
        cos_lr=True
    )
    print("Training complete. Check out/yolo/damage-v1")
