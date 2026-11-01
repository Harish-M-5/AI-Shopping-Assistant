"""Generate synthetic test media (needs only numpy + opencv).

    python generate_samples.py

Creates in this folder:
  sample_good_label.jpg      clean pack, readable MFD / EXP  (OCR: valid dates)
  sample_expired_label.jpg   pack with dates in the past      (OCR: "expired")
  sample_damaged_box.jpg     crumpled / torn pack             (damage detection)
  sample_video.mp4           moving pack with dates           (video / OCR test)

NOTE: these are cartoon packs for testing OCR + damage logic. COCO-trained YOLO
will not recognise them as products - use real photos (bottle, banana, cup...)
or your webcam to see YOLO boxes. On the Camera page you can also type a
product name manually to run the full pipeline on these images.
"""
from pathlib import Path

import cv2
import numpy as np

OUT = Path(__file__).parent
FONT = cv2.FONT_HERSHEY_DUPLEX
rng = np.random.default_rng(7)


def canvas(w=900, h=700):
    img = np.full((h, w, 3), 205, np.uint8)  # light grey table
    return img


def draw_pack(img, x, y, w, h, name, mfd, exp, color=(60, 140, 220)):
    """Draw a simple retail pack with a printed date block."""
    cv2.rectangle(img, (x, y), (x + w, y + h), color, -1)
    cv2.rectangle(img, (x, y), (x + w, y + h), (30, 30, 30), 3)
    cv2.rectangle(img, (x + 20, y + 20), (x + w - 20, y + 130), (255, 255, 255), -1)
    cv2.putText(img, name, (x + 40, y + 95), FONT, 1.6, (40, 40, 40), 3, cv2.LINE_AA)
    cv2.rectangle(img, (x + 20, y + h - 190), (x + w - 20, y + h - 30), (255, 255, 255), -1)
    cv2.putText(img, f"MFD: {mfd}", (x + 40, y + h - 125), FONT, 1.3, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(img, f"EXP: {exp}", (x + 40, y + h - 60), FONT, 1.3, (0, 0, 0), 2, cv2.LINE_AA)


def crumple(img, x, y, w, h):
    """Overlay jagged edges, creases and tears to mimic a crushed pack."""
    # Torn / bitten jagged corner & edge cutouts in the table colour
    for cx, cy in [(x, y), (x + w, y + h), (x + w, y + 40)]:
        pts = [(cx, cy)]
        for k in range(8):
            ang = rng.uniform(0, 2 * np.pi)
            r = rng.uniform(25, 75)
            pts.append((int(cx + r * np.cos(ang)), int(cy + r * np.sin(ang))))
        cv2.fillPoly(img, [cv2.convexHull(np.array(pts, np.int32))], (205, 205, 205))
    # Random crease lines
    for _ in range(45):
        p1 = (int(rng.integers(x, x + w)), int(rng.integers(y, y + h)))
        p2 = (p1[0] + int(rng.integers(-90, 90)), p1[1] + int(rng.integers(-90, 90)))
        cv2.line(img, p1, p2, (20, 20, 20) if rng.random() > .5 else (230, 230, 230), 2)
    return img


def save(name, img):
    cv2.imwrite(str(OUT / name), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print("wrote", name)


def main():
    img = canvas(); draw_pack(img, 250, 60, 400, 580, "SNACKY", "12/03/2026", "11/03/2027")
    save("sample_good_label.jpg", img)

    img = canvas(); draw_pack(img, 250, 60, 400, 580, "CRUNCH", "05 JAN 2024", "05 JUL 2024", (90, 170, 90))
    save("sample_expired_label.jpg", img)

    img = canvas(); draw_pack(img, 250, 60, 400, 580, "SNACKY", "12/03/2026", "11/03/2027", (60, 80, 200))
    save("sample_damaged_box.jpg", crumple(img, 250, 60, 400, 580))

    # 5-second video: pack slides left-right
    vw, vh, fps = 960, 540, 20
    vid = cv2.VideoWriter(str(OUT / "sample_video.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), fps, (vw, vh))
    for f in range(fps * 5):
        frame = np.full((vh, vw, 3), 205, np.uint8)
        x = int(280 + 120 * np.sin(f / fps * 2))
        draw_pack(frame, x, 20, 360, 500, "SNACKY", "12/03/2026", "11/03/2027")
        vid.write(frame)
    vid.release()
    print("wrote sample_video.mp4")


if __name__ == "__main__":
    main()
