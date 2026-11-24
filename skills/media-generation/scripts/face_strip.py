"""Face strip: her face cropped from the raw clip every 1/4 s, time-stamped, to write the mouth lines from.

Usage: face_strip.py <clip.mp4> <guide>/keypoints.npz <out.jpg> [--every 0.25]
The crop box follows her face landmarks in the guide's keypoints.npz (cv_tools.motion_guide writes it).
"""
import argparse

import cv2
import numpy as np

FACE = ("eye", "nose", "lip", "mouth", "chin", "jaw")
TILE, COLUMNS = 180, 11


def face_box(points, frame_shape):
    if len(points) < 4:
        h, w = frame_shape[:2]
        return w / 2, h / 3, min(w, h) / 4
    cx, cy = np.median(points, axis=0)
    # [Agent] Half a box = 1.3 × the landmarks' height, so the whole mouth and chin stay in even when she tips her head.
    return cx, cy, max(60, 1.3 * np.ptp(points[:, 1]))


def crop(frame, cx, cy, half, label):
    h, w = frame.shape[:2]
    x0, y0, x1, y1 = (int(max(0, cx - half)), int(max(0, cy - half)), int(min(w, cx + half)), int(min(h, cy + half)))
    tile = cv2.resize(frame[y0:y1, x0:x1], (TILE, TILE))
    # [Agent] Night clips are too dark to read lips; a fixed gain is enough and keeps every tile comparable.
    tile = np.clip(tile.astype(np.float32) * 1.8, 0, 255).astype(np.uint8)
    cv2.putText(tile, label, (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    return tile


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("clip")
    p.add_argument("keypoints")
    p.add_argument("out")
    p.add_argument("--every", type=float, default=0.25, help="Seconds between crops (default 0.25)")
    args = p.parse_args()

    k = np.load(args.keypoints)
    face = [i for i, n in enumerate(k["names"]) if any(w in str(n) for w in FACE)]
    cap = cv2.VideoCapture(args.clip)
    fps = cap.get(cv2.CAP_PROP_FPS)
    step = max(1, round(fps * args.every))
    tiles, index = [], 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if index % step == 0 and index < len(k["points"]):
            pts = k["points"][index, face][k["scores"][index, face] > 0.3]
            tiles.append(crop(frame, *face_box(pts, frame.shape), f"{index / fps:.2f}"))
        index += 1
    blank = np.zeros_like(tiles[0])
    rows = [np.hstack(tiles[r:r + COLUMNS] + [blank] * (COLUMNS - len(tiles[r:r + COLUMNS]))) for r in range(0, len(tiles), COLUMNS)]
    cv2.imwrite(args.out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(f"face strip: {len(tiles)} crops every {args.every} s -> {args.out}")


if __name__ == "__main__":
    main()
