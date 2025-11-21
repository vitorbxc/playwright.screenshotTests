import sys
from pathlib import Path
from PIL import Image, ImageChops, ImageEnhance
import numpy as np

"""
Simple image diff:
- Default input: ./screenshot/before.png and ./screenshot/after.png (relative to workspace root)
- Default output: ./screenshot/diff.png
- Usage:
    python3 scripts/compare_images.py [before_path] [after_path] [out_path]
Install deps:
    python3 -m pip install pillow numpy
"""

def load_and_pad(path, size):
    img = Image.open(path).convert("RGBA")
    if img.size == size:
        return img
    base = Image.new("RGBA", size, (0,0,0,0))
    base.paste(img, (0,0))
    return base

def main():
    ws = Path(__file__).resolve().parents[2]  # workspace root
    default_before = ws / "screenshot" / "before.png"
    default_after = ws / "screenshot" / "after.png"
    default_out = ws / "screenshot" / "diff.png"

    args = sys.argv[1:]
    before_path = Path(args[0]) if len(args) >= 1 else default_before
    after_path = Path(args[1]) if len(args) >= 2 else default_after
    out_path = Path(args[2]) if len(args) >= 3 else default_out

    if not before_path.exists() or not after_path.exists():
        print(f"Error: input files not found:\n  before: {before_path}\n  after:  {after_path}")
        sys.exit(1)

    a = Image.open(before_path).convert("RGBA")
    b = Image.open(after_path).convert("RGBA")

    # canvas size = max of both
    width = max(a.width, b.width)
    height = max(a.height, b.height)
    size = (width, height)

    a_pad = load_and_pad(before_path, size)
    b_pad = load_and_pad(after_path, size)

    # raw difference
    diff = ImageChops.difference(a_pad, b_pad)

    # amplify differences for visibility
    enhancer = ImageEnhance.Brightness(diff)
    diff_enh = enhancer.enhance(3.0)

    # create mask where differences exist (convert to grayscale and threshold)
    gray = diff_enh.convert("L")
    arr = np.array(gray)
    mask = arr > 10  # tweak threshold if needed

    # count differing pixels
    diff_pixels = int(mask.sum())
    total_pixels = width * height
    perc = diff_pixels / total_pixels * 100
    print(f"Diff pixels: {diff_pixels} / {total_pixels} ({perc:.4f}%)")

    # create red overlay where mask is True
    red = Image.new("RGBA", size, (255, 0, 0, 180))
    mask_img = Image.fromarray((mask * 255).astype("uint8"), mode="L")

    # overlay red onto the 'after' image to highlight differences
    highlighted = b_pad.copy()
    highlighted.paste(red, (0,0), mask_img)

    # also produce a side-by-side composite: before | diff | after
    spacer = 10
    composite = Image.new("RGBA", (width*3 + spacer*2, height), (255,255,255,255))
    composite.paste(a_pad, (0,0))
    composite.paste(diff_enh.convert("RGBA"), (width+spacer,0))
    composite.paste(highlighted, (width*2+spacer*2,0))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    composite.save(out_path)
    print(f"Saved visual diff to: {out_path}")

if __name__ == "__main__":
    main()