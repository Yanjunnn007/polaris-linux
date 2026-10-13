import subprocess
import os
import sys
import numpy as np
from PIL import Image

PHONE_IP = "172.16.42.1"
WORK_DIR = r"."
ARTIFACT_DIR = r"./output"

def shoot(focus_val=None):
    if focus_val is not None:
        print(f"[0/3] Setting focus to {focus_val}...")
        cmd_f = f'sshpass -p pmos ssh -o StrictHostKeyChecking=no user@{PHONE_IP} "polaris-focus {focus_val}"'
        subprocess.run(cmd_f, shell=True)

    print("[1/3] Triggering camera shot on phone...")
    cmd1 = f'sshpass -p pmos ssh -o StrictHostKeyChecking=no user@{PHONE_IP} "/tmp/shoot.sh"'
    res1 = subprocess.run(cmd1, shell=True, capture_output=True, text=True)
    if res1.returncode != 0:
        print(f"Shoot failed: {res1.stderr}")
        return False
    print("Capture trigger succeeded.")

    print("[2/3] Transferring shot.raw to host...")
    cmd2 = f'bash -c "sshpass -p pmos scp -o StrictHostKeyChecking=no user@{PHONE_IP}:/tmp/shot.raw /home/www/shot.raw && cp /home/www/shot.raw \'./shot.raw\'"'
    res2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
    if res2.returncode != 0:
        print(f"SCP failed: {res2.stderr}")
        return False

    raw_path = os.path.join(WORK_DIR, "shot.raw")
    if not os.path.exists(raw_path):
        print(f"File not found: {raw_path}")
        return False
        
    print(f"Downloaded shot.raw ({os.path.getsize(raw_path)} bytes).")

    print("[3/3] Decoding RAW10 frame...")
    data = np.fromfile(raw_path, dtype=np.uint8)
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
    print(f"Pixel Stats: Min={raw10.min()}, Max={raw10.max()}, Mean={raw10.mean():.2f}, Median={np.median(raw10):.2f}, Std={raw10.std():.2f}")

    black_level = 64
    raw_sub = np.clip(raw10.astype(np.float32) - black_level, 0, 1023 - black_level)

    # BGGR pattern half-res RGB
    b = raw_sub[0::2, 0::2]
    gb = raw_sub[0::2, 1::2]
    gr = raw_sub[1::2, 0::2]
    r = raw_sub[1::2, 1::2]
    g = (gb + gr) / 2.0

    p_min = np.percentile(raw_sub, 0.5)
    p_max = np.percentile(raw_sub, 99.5)
    print(f"Dynamic range: P0.5={p_min:.2f}, P99.5={p_max:.2f}")

    if p_max <= p_min:
        scale = 1.0
    else:
        scale = 255.0 / (p_max - p_min)

    r_norm = np.clip((r - p_min) * scale, 0, 255).astype(np.uint8)
    g_norm = np.clip((g - p_min) * scale, 0, 255).astype(np.uint8)
    b_norm = np.clip((b - p_min) * scale, 0, 255).astype(np.uint8)
    rgb = np.stack([r_norm, g_norm, b_norm], axis=-1)

    out_png = os.path.join(WORK_DIR, "shot.png")
    img = Image.fromarray(rgb, mode='RGB')
    img.save(out_png)

    art_png = os.path.join(ARTIFACT_DIR, "shot.png")
    img.save(art_png)
    print(f"Saved: {out_png} and {art_png}")
    return True

if __name__ == '__main__':
    focus = sys.argv[1] if len(sys.argv) > 1 else None
    shoot(focus)
