
import sys
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
sys.path.insert(0, ".")
from ml.clip_engine import get_engine
import torch
import numpy as np

def check_direct_match():
    engine = get_engine()
    
    text = "Nike Air Max 270 Running Shoes White"
    # This is one of the images in catalog.json
    image_url = "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&q=80"
    
    text_vec = engine.embed_text(text)
    image_vec = engine.embed_image_url(image_url)
    
    # Dot product of normalized vectors = Cosine Similarity
    score = np.dot(text_vec[0], image_vec[0])
    print(f"Similarity between '{text}' and its image: {score:.4f}")

    # Try with prompt
    text_prompt = f"a photo of {text}"
    text_vec_prompt = engine.embed_text(text_prompt)
    score_prompt = np.dot(text_vec_prompt[0], image_vec[0])
    print(f"Similarity with prompt '{text_prompt}': {score_prompt:.4f}")

if __name__ == "__main__":
    check_direct_match()
