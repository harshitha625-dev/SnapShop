
import sys
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
sys.path.insert(0, ".")
import open_clip
import torch
from PIL import Image
import requests
from io import BytesIO
import numpy as np

def test_model(model_name, pretrained):
    print(f"\n--- Testing Model: {model_name} | Pretrained: {pretrained} ---")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, _, preprocess = open_clip.create_model_and_transforms(model_name, pretrained=pretrained, device=device)
    model.eval()
    tokenizer = open_clip.get_tokenizer(model_name)

    text = "Nike Air Max 270 Running Shoes White"
    image_url = "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&q=80"
    
    # Embed image
    resp = requests.get(image_url)
    img = Image.open(BytesIO(resp.content)).convert("RGB")
    image_tensor = preprocess(img).unsqueeze(0).to(device)
    with torch.no_grad():
        image_features = model.encode_image(image_tensor)
        image_features /= image_features.norm(dim=-1, keepdim=True)
    
    # Embed text
    text_tokens = tokenizer([text]).to(device)
    with torch.no_grad():
        text_features = model.encode_text(text_tokens)
        text_features /= text_features.norm(dim=-1, keepdim=True)
    
    score = (text_features @ image_features.T).item()
    print(f"Similarity: {score:.4f}")

if __name__ == "__main__":
    test_model("ViT-B-32", "openai")
    test_model("ViT-B-32", "laion2b_s34b_b79k")
    test_model("ViT-L-14", "openai")
