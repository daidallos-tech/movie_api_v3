import uuid
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

MEDIA_DIR = Path("media")

IMAGE_CONFIGS = {
    "user": {"dir": MEDIA_DIR / "profile_pics", "size": (300, 300)},
    "movie": {"dir": MEDIA_DIR / "movie_posters", "size": (600, 900)},
    "director": {"dir": MEDIA_DIR / "dir_pics", "size": (400, 500)},    
}

def process_and_save_image(content: bytes, image_type: str) -> str:
    config = IMAGE_CONFIGS.get(image_type)
    if not config:
        raise ValueError(f"Unknown image type: {image_type}")
        
    target_dir = config["dir"]
    target_size = config["size"]

    with Image.open(BytesIO(content)) as original:
        img = ImageOps.exif_transpose(original)

        img = ImageOps.fit(img, target_size, method=Image.Resampling.LANCZOS)

        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        filename = f"{uuid.uuid4().hex}.jpg"
        filepath = target_dir / filename

        target_dir.mkdir(parents=True, exist_ok=True)

        img.save(filepath, "JPEG", quality=85, optimize=True)

    return filename


def delete_image(filename: str | None, image_type: str) -> None:
    if filename is None:
        return

    config = IMAGE_CONFIGS.get(image_type)
    if not config:
        return

    filepath = config['dir'] / filename
    if filepath.exists():
        filepath.unlink()