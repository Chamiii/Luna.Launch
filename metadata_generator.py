
import json
import tempfile
import os

def create_metadata_json(name, symbol, description, logo_file, website=None):
    metadata = {
        "name": name,
        "symbol": symbol,
        "description": description,
    }
    if website:
        metadata["external_url"] = website

    if logo_file:
        image_path = save_temp_logo(logo_file)
        metadata["image"] = image_path

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        return f.name

def save_temp_logo(file):
    path = os.path.join(tempfile.gettempdir(), file.name)
    with open(path, "wb") as out_file:
        out_file.write(file.getbuffer())
    return path
