import numpy as np
from PIL import Image
import os
import sys

def process(raw_path, output_png):
    print(f"Reading {raw_path}...")
    data = np.fromfile(raw_path, dtype=np.uint8)
    expected_bytes = 4032 * 3024 * 5 // 4
    print(f"File size: {len(data)} bytes (expected: {expected_bytes})")
    if len(data) != expected_bytes:
        print("Warning: File size does not match 4032x3024 RAW10!")
    
    # Reshape to groups of 5 bytes
    num_groups = len(data) // 5
    groups = data[:num_groups * 5].reshape(-1, 5)
    
    b0 = groups[:, 0].astype(np.uint16)
    b1 = groups[:, 1].astype(np.uint16)
    b2 = groups[:, 2].astype(np.uint16)
    b3 = groups[:, 3].astype(np.uint16)
    b4 = groups[:, 4].astype(np.uint16)
    
    p0 = (b0 << 2) | (b4 & 0x03)
    p1 = (b1 << 2) | ((b4 >> 2) & 0x03)
    p2 = (b2 << 2) | ((b4 >> 4) & 0x03)
    p3 = (b3 << 2) | ((b4 >> 6) & 0x03)
    
    raw10 = np.column_stack([p0, p1, p2, p3]).reshape(3024, 4032)
    
    print(f"Raw10 statistics:")
    print(f"  Min: {raw10.min()}")
    print(f"  Max: {raw10.max()}")
    print(f"  Mean: {raw10.mean():.2f}")
    print(f"  Median: {np.median(raw10):.2f}")
    print(f"  Std: {raw10.std():.2f}")
    
    # Check black level subtraction (IMX363 typical black level is 64 in 10-bit)
    black_level = 64
    raw_sub = np.clip(raw10.astype(np.float32) - black_level, 0, 1023 - black_level)
    
    # BGGR pattern:
    # row 0: B, Gb, B, Gb...
    # row 1: Gr, R, Gr, R...
    # Half-resolution RGB:
    b = raw_sub[0::2, 0::2]
    gb = raw_sub[0::2, 1::2]
    gr = raw_sub[1::2, 0::2]
    r = raw_sub[1::2, 1::2]
    g = (gb + gr) / 2.0
    
    # Auto-exposure / normalization for display
    # 99.9 percentile stretch
    p_max = np.percentile(raw_sub, 99.9)
    p_min = np.percentile(raw_sub, 0.1)
    print(f"  P0.1: {p_min:.2f}, P99.9: {p_max:.2f}")
    
    if p_max <= p_min:
        scale = 1.0
    else:
        scale = 255.0 / (p_max - p_min)
        
    r_norm = np.clip((r - p_min) * scale, 0, 255).astype(np.uint8)
    g_norm = np.clip((g - p_min) * scale, 0, 255).astype(np.uint8)
    b_norm = np.clip((b - p_min) * scale, 0, 255).astype(np.uint8)
    
    rgb = np.stack([r_norm, g_norm, b_norm], axis=-1)
    
    img = Image.fromarray(rgb, mode='RGB')
    img.save(output_png)
    print(f"Saved processed preview to {output_png} (size: {img.size})")

    # Also save raw 8-bit grayscale for sanity check
    raw8 = (raw10 >> 2).astype(np.uint8)
    img_raw8 = Image.fromarray(raw8, mode='L')
    raw8_png = output_png.replace('.png', '_raw8.png')
    img_raw8.save(raw8_png)
    print(f"Saved raw grayscale to {raw8_png}")

if __name__ == '__main__':
    raw_file = r"capture_4032x3024.raw"
    out_file = r"./preview_capture.png"
    if len(sys.argv) > 1:
        raw_file = sys.argv[1]
    if len(sys.argv) > 2:
        out_file = sys.argv[2]
    process(raw_file, out_file)
