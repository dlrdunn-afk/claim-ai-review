import os
import shutil
import zipfile


def detect_file_type(filepath):
    with open(filepath, "rb") as f:
        content = f.read(5120).decode("utf-8", errors="ignore").lower()

    if filepath.endswith(".jpg") or "jfif" in content:
        return "image"
    if "room" in content and "area" in content:
        return "floorplan"
    if "xactimate" in content or "lineitem" in content:
        return "estimate"
    return "unknown"


def import_esx(esx_path, output_base):
    if not os.path.exists(esx_path):
        print(f"❌ File not found: {esx_path}")
        return

    # Rename to .zip and unzip contents
    zip_path = esx_path.replace(".esx", ".zip")
    shutil.copy(esx_path, zip_path)

    unpack_dir = os.path.join(output_base, "esx_unpacked")
    os.makedirs(unpack_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(unpack_dir)

    # Create folders
    folders = {
        "images": os.path.join(output_base, "images"),
        "floorplan": os.path.join(output_base, "floorplan"),
        "estimate": os.path.join(output_base, "estimate"),
        "ignored": os.path.join(output_base, "ignored"),
    }
    for f in folders.values():
        os.makedirs(f, exist_ok=True)

    # Sort the files
    for filename in os.listdir(unpack_dir):
        path = os.path.join(unpack_dir, filename)

        if filename.lower().endswith(".jpg"):
            shutil.move(path, os.path.join(folders["images"], filename))
            print(f"🖼️  Image: {filename}")

        elif "xactdoc" in filename.lower():
            shutil.move(path, os.path.join(folders["estimate"], filename))
            print(f"📄 Estimate ZIPXML: {filename}")

        elif filename.lower().endswith(".xml"):
            ftype = detect_file_type(path)
            if ftype == "floorplan":
                shutil.move(path, os.path.join(folders["floorplan"], filename))
                print(f"📐 Floorplan XML: {filename}")
            else:
                shutil.move(path, os.path.join(folders["ignored"], filename))
                print(f"🔍 Unknown XML moved to ignored: {filename}")

        else:
            shutil.move(path, os.path.join(folders["ignored"], filename))
            print(f"❓ Unknown file moved to ignored: {filename}")

    print("✅ ESX import complete.")


# === Run it ===
if __name__ == "__main__":
    esx_file = "data/job-0001/sarena_irwin.esx"
    output_folder = "data/job-0001"
    import_esx(esx_file, output_folder)
