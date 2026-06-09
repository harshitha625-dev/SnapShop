"""
backend/routers/upload.py
Image upload — saves temporarily to local disk so CLIP can search it.
"""
import os
import hashlib
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.models.schemas import UploadResponse

router = APIRouter()

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)):
    # Be permissive with image types to avoid 415 errors from different browsers
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(415, f"Only image files are allowed. Got {file.content_type}")

    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, "Max 10MB")

    image_hash = hashlib.sha256(data).hexdigest()[:16]
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
    filename = f"{image_hash}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(data)

    # Return a relative path so the frontend can prepend the correct base URL
    image_url = f"/static/uploads/{filename}"

    return UploadResponse(
        image_url=  image_url,
        image_hash= image_hash,
        message=    "Image uploaded successfully",
    )
