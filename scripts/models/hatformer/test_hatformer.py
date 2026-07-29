#!/usr/bin/env python3
"""Test pipeline for the recognizer model (HATFormer).

Loads a trained HATFormer checkpoint, takes a line image as input,
runs it through the OCR model, and prints the predicted transcription.

Usage:
    python scripts/models/hatformer/test_recognizer.py --image path/to/image.png --checkpoint checkpoints/hatformer/ours/best
"""
import argparse
import os
import sys

import torch
from PIL import Image
from transformers import PreTrainedTokenizerFast, VisionEncoderDecoderModel


from dataset import hatformer_canvas, to_pixel_values


def pick_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def load_model_and_tokenizer(checkpoint, tokenizer_path):
    # Prefer the tokenizer saved alongside a trained checkpoint; else the vendored one
    try:
        tok = PreTrainedTokenizerFast.from_pretrained(checkpoint)
        if tok.pad_token_id is None:
            raise ValueError("no special tokens")
    except Exception:
        tok = PreTrainedTokenizerFast(tokenizer_file=tokenizer_path)
        tok.add_special_tokens({"pad_token": "<pad>", "eos_token": "</s>",
                                "cls_token": "<s>", "bos_token": "<s>"})
    
    print(f"Loading HATFormer from {checkpoint}...")
    model = VisionEncoderDecoderModel.from_pretrained(checkpoint).eval()
    return model, tok


def main():
    ap = argparse.ArgumentParser(description="Test recognizer (HATFormer) on a single image.")
    ap.add_argument("--image", required=True, help="Name of the image file (assumes it is in test_recognizer/images/)")
    ap.add_argument("--checkpoint", required=True, help="Path to the trained model directory.")
    ap.add_argument("--tokenizer", default="scripts/models/hatformer/tokenizer/tokenizer.json",
                    help="Fallback tokenizer if the checkpoint has none")
    ap.add_argument("--num-beams", type=int, default=3, help="Number of beams for search")
    ap.add_argument("--max-text-length", type=int, default=64, help="Max length of generated text")
    args = ap.parse_args()

    device = pick_device()
    print(f"Using device: {device}")

    # 1. Load Model and Tokenizer
    model, tok = load_model_and_tokenizer(args.checkpoint, args.tokenizer)
    model.to(device)

    # Resolve paths
    base_name = os.path.basename(args.image)
    image_name_no_ext = os.path.splitext(base_name)[0]
    
    img_dir = "test_recognizer/images"
    out_dir = "test_recognizer/prediction"
    os.makedirs(out_dir, exist_ok=True)
    
    img_path = os.path.join(img_dir, base_name)
    out_path = os.path.join(out_dir, f"{image_name_no_ext}.txt")

    if not os.path.exists(img_path):
        print(f"Error: Image not found at {img_path}")
        sys.exit(1)

    # 2. Load and Preprocess Image
    print(f"Loading image {img_path}...")
    pil_img = Image.open(img_path).convert("RGB")
    
    # Preprocess mirroring training (height=64, canvas=384, rtl_flip=True)
    canvas_img = hatformer_canvas(pil_img, height=64, canvas=384, rtl_flip=True)
    pixel_values = to_pixel_values(canvas_img)
    
    # Add batch dimension -> (1, C, H, W)
    pixel_values = pixel_values.unsqueeze(0).to(device)

    # 3. Inference
    print("Running inference...")
    with torch.no_grad():
        out = model.generate(
            pixel_values, 
            num_beams=args.num_beams,
            length_penalty=0, 
            max_new_tokens=args.max_text_length
        )

    # 4. Decode and Print/Save
    pred_text = tok.batch_decode(out.tolist(), skip_special_tokens=True)[0]
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(pred_text)
        
    print("\n" + "="*50)
    print("PREDICTED TRANSCRIPTION:")
    print("="*50)
    print(pred_text)
    print("="*50 + "\n")
    print(f"Saved prediction to: {out_path}")

if __name__ == "__main__":
    main()
