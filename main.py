# a generative art script
#
# Draws concentric rings whose colors are interpolated between two random
# endpoints, then additively blends them onto a dark canvas. Everything is
# rendered at a high resolution and downscaled with LANCZOS for smooth,
# anti-aliased edges, plus a soft glow layer underneath each ring.

import argparse
import os
import random

from PIL import Image, ImageDraw, ImageChops, ImageFilter


# A lush abstract-painting gradient: warm sunset melting into deep ocean.
# Neighboring stops are harmonious, so any continuous slice flows beautifully.
PALETTE = [
    (255, 138, 40),   # orange
    (255, 94, 86),    # coral
    (232, 64, 120),   # rose
    (188, 55, 168),   # magenta
    (120, 60, 200),   # violet
    (66, 72, 206),    # indigo / blue
    (40, 128, 196),   # azure
    (44, 176, 164),   # teal
]


def palette_color(pos: float):
    """Sample the painting palette at pos in [0, 1] (0 = orange, 1 = teal)."""
    pos = max(0.0, min(1.0, pos))
    scaled = pos * (len(PALETTE) - 1)
    i = int(scaled)
    if i >= len(PALETTE) - 1:
        return PALETTE[-1]
    return interpolate(PALETTE[i], PALETTE[i + 1], scaled - i)


def draw_tube_ring(draw, center, radius, width, color):
    """Draw one ring as a rounded 3D-looking tube.

    It's still flat 2D, but shading the stroke from dark edges up to a bright
    highlight across its width makes each line read like a glossy wire/pipe.
    """
    dark = interpolate(color, (0, 0, 0), 0.65)
    light = interpolate(color, (255, 255, 255), 0.6)

    steps = max(3, int(width))
    for s in range(steps + 1):
        t = s / steps  # 0 = inner edge of the stroke, 1 = outer edge
        rr = radius - width / 2 + t * width
        # Bead profile: dark at both edges, bright highlight just inside center.
        val = max(0.0, 1 - ((t - 0.42) / 0.5) ** 2)
        shade = interpolate(dark, light, val)
        draw.ellipse((center - rr, center - rr, center + rr, center + rr),
                     outline=shade, width=2)


def interpolate(start_color, end_color, factor: float):
    """Linearly blend between two colors. factor=0 -> start, factor=1 -> end."""
    reciprocal = 1 - factor
    return (
        int(start_color[0] * reciprocal + end_color[0] * factor),
        int(start_color[1] * reciprocal + end_color[1] * factor),
        int(start_color[2] * reciprocal + end_color[2] * factor),
    )


def generator(save_path: str, target_size: int = 256, rings: int = 16):
    # Render at a higher resolution, then shrink down at the end. This is what
    # gives the rings clean, anti-aliased edges instead of jagged pixels.
    scale_factor = 4
    canvas_px = target_size * scale_factor
    padding = 4 * scale_factor

    # Each image "catches" a smooth, continuous slice of the painting palette,
    # so the rings melt from one beautiful color into the next.
    lo = random.uniform(0.0, 0.55)
    hi = lo + random.uniform(0.35, 1.0 - lo)
    if random.random() < 0.5:
        lo, hi = hi, lo  # flow inward or outward

    # Plain dark canvas, plus separate black layers for the crisp rings and
    # their glow (kept black so the blur stays clean before compositing).
    image = Image.new("RGB", (canvas_px, canvas_px), (8, 10, 20))
    rings_layer = Image.new("RGB", (canvas_px, canvas_px), (0, 0, 0))
    rings_draw = ImageDraw.Draw(rings_layer)
    glow = Image.new("RGB", (canvas_px, canvas_px), (0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    center = canvas_px / 2
    step = (canvas_px - 2 * padding) / (2 * rings)

    for i in range(rings):
        # Centered nested rings; stroke a little fatter than half the gap so
        # the tube shading has room, with a thin space left between rings.
        radius = center - (padding + i * step)
        width = step * 0.55

        # Walk the palette slice from outer to inner, with a little jitter so
        # it feels hand-painted rather than perfectly mechanical.
        f = i / max(1, rings - 1)
        pos = lo + (hi - lo) * f + random.uniform(-0.03, 0.03)
        circle_color = palette_color(pos)

        draw_tube_ring(rings_draw, center, radius, width, circle_color)
        glow_draw.ellipse((center - radius, center - radius,
                           center + radius, center + radius),
                          outline=circle_color, width=int(width))

    # Composite: dark canvas -> soft halo (limited) -> crisp tube rings on top.
    glow = glow.filter(ImageFilter.GaussianBlur(radius=scale_factor * 2))
    image = ImageChops.add(image, glow, scale=2.5)  # scale>1 dims the glow
    image = ImageChops.add(image, rings_layer)

    # Downscale to the target size (this is the step the original code dropped).
    image = image.resize((target_size, target_size), resample=Image.Resampling.LANCZOS)
    image.save(save_path)


def main():
    parser = argparse.ArgumentParser(description="Generate concentric-circle art.")
    parser.add_argument("-n", "--count", type=int, default=16,
                        help="number of images to generate (default: 16)")
    parser.add_argument("-s", "--size", type=int, default=256,
                        help="output image size in pixels (default: 256)")
    parser.add_argument("-r", "--rings", type=int, default=16,
                        help="number of rings per image (default: 16)")
    parser.add_argument("-o", "--out-dir", default="imgs",
                        help="output directory (default: imgs)")
    parser.add_argument("--seed", type=int, default=None,
                        help="random seed for reproducible output")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    os.makedirs(args.out_dir, exist_ok=True)
    for i in range(args.count):
        path = os.path.join(args.out_dir, f"circle_{i}.png")
        generator(path, target_size=args.size, rings=args.rings)
        print(f"saved {path}")


if __name__ == "__main__":
    main()
