# a generative art script
#
# Draws concentric rings whose colors are interpolated between two random
# endpoints, then additively blends them onto a dark canvas. Everything is
# rendered at a high resolution and downscaled with LANCZOS for smooth,
# anti-aliased edges, plus a soft glow layer underneath each ring.

import argparse
import functools
import math
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


def draw_tube_ring(draw, center, radius, width, color, alpha: float = 1.0):
    """Draw one ring as a rounded 3D-looking tube.

    It's still flat 2D, but shading the stroke from dark edges up to a bright
    highlight across its width makes each line read like a glossy wire/pipe.

    `alpha` < 1 dims the whole tube toward black *after* shading, so a fading
    ring keeps its hue (dimming the input color first would turn the white
    highlight gray).
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
        if alpha < 1.0:
            shade = interpolate((0, 0, 0), shade, alpha)
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


def generator(save_path: str, target_size: int = 256, rings: int = 16,
              shape: str = "circle"):
    # Render at a higher resolution, then shrink down at the end. This is what
    # gives the rings clean, anti-aliased edges instead of jagged pixels.
    scale_factor = 4
    canvas_px = target_size * scale_factor
    padding = 4 * scale_factor
    factors = shape_factors_for(shape)  # None for a circle (fast ellipse path)

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

        _draw_ring(rings_draw, glow_draw, center, radius, width, circle_color,
                   factors=factors)

    # Composite: dark canvas -> soft halo (limited) -> crisp tube rings on top.
    glow = glow.filter(ImageFilter.GaussianBlur(radius=scale_factor * 2))
    image = ImageChops.add(image, glow, scale=2.5)  # scale>1 dims the glow
    image = ImageChops.add(image, rings_layer)

    # Downscale to the target size (this is the step the original code dropped).
    image = image.resize((target_size, target_size), resample=Image.Resampling.LANCZOS)
    image.save(save_path)


SHAPE_NAMES = ("circle", "triangle", "square", "pentagon", "hexagon", "star",
               "superellipse", "morph")
# Shapes cycled through by the morph option (back to the first to loop).
_MORPH_SEQUENCE = ("triangle", "square", "pentagon", "hexagon", "star", "superellipse")
_SHAPE_SAMPLES = 120  # points used to trace a non-circular ring


def _shape_factors(shape, n=_SHAPE_SAMPLES):
    """Radius factor at n evenly spaced angles for a unit `shape` (circle == 1)."""
    out = []
    for j in range(n):
        th = 2 * math.pi * j / n - math.pi / 2  # start at the top
        if shape == "circle":
            r = 1.0
        elif shape == "superellipse":
            p = 4.0
            r = (abs(math.cos(th)) ** p + abs(math.sin(th)) ** p) ** (-1.0 / p)
        elif shape == "star":
            pts, k = 5, (th + math.pi / 2) / (math.pi / 5)
            a = 1.0 if int(k) % 2 == 0 else 0.45
            b = 1.0 if (int(k) + 1) % 2 == 0 else 0.45
            r = a + (b - a) * (k - int(k))
        else:
            sides = {"triangle": 3, "square": 4, "pentagon": 5, "hexagon": 6}[shape]
            ang = 2 * math.pi / sides
            r = math.cos(math.pi / sides) / math.cos(((th + math.pi / 2) % ang) - math.pi / sides)
        out.append(r)
    peak = max(out)
    return [v / peak for v in out]


@functools.lru_cache(maxsize=None)
def _shape_table(shape):
    return tuple(_shape_factors(shape))


def shape_factors_for(shape, phase=0.0):
    """Factors for a ring at the given loop phase. `circle` -> None (use the
    fast ellipse path). `morph` cycles through the shapes and loops seamlessly."""
    if shape == "circle":
        return None
    if shape != "morph":
        return _shape_table(shape)
    seq = _MORPH_SEQUENCE
    pos = (phase % 1.0) * len(seq)
    i = int(pos)
    frac = pos - i
    frac = frac * frac * (3 - 2 * frac)  # smoothstep between shapes
    a, b = _shape_table(seq[i % len(seq)]), _shape_table(seq[(i + 1) % len(seq)])
    return tuple(av + (bv - av) * frac for av, bv in zip(a, b))


def _shape_xy(center, radius, factors):
    n = len(factors)
    return [(center + radius * factors[j] * math.cos(2 * math.pi * j / n - math.pi / 2),
             center + radius * factors[j] * math.sin(2 * math.pi * j / n - math.pi / 2))
            for j in range(n)]


def _draw_ring(rings_draw, glow_draw, center, radius, width, color, alpha=1.0,
               factors=None):
    """Draw one ring onto the crisp and glow layers, dimmed by alpha. With
    `factors` (a shape's per-angle radii) the ring is a polygon instead of a
    circle; without it the fast ellipse path is used (unchanged)."""
    glow_color = interpolate((0, 0, 0), color, alpha) if alpha < 1.0 else color
    if factors is None:
        draw_tube_ring(rings_draw, center, radius, width, color, alpha)
        glow_draw.ellipse((center - radius, center - radius,
                           center + radius, center + radius),
                          outline=glow_color, width=int(width))
        return

    # Shaped ring: trace the bead-shaded tube as nested polygons.
    dark = interpolate(color, (0, 0, 0), 0.65)
    light = interpolate(color, (255, 255, 255), 0.6)
    steps = max(3, int(width))
    for s in range(steps + 1):
        t = s / steps
        rr = radius - width / 2 + t * width
        val = max(0.0, 1 - ((t - 0.42) / 0.5) ** 2)
        shade = interpolate(dark, light, val)
        if alpha < 1.0:
            shade = interpolate((0, 0, 0), shade, alpha)
        pts = _shape_xy(center, rr, factors)
        rings_draw.line(pts + [pts[0]], fill=shade, width=2, joint="curve")
    gpts = _shape_xy(center, radius, factors)
    glow_draw.line(gpts + [gpts[0]], fill=glow_color, width=int(width), joint="curve")


def _finish_frame(canvas_px, rings_layer, glow, scale_factor, target_size):
    """Composite the dark canvas, soft glow and crisp rings, then downscale."""
    glow = glow.filter(ImageFilter.GaussianBlur(radius=scale_factor * 2))
    image = Image.new("RGB", (canvas_px, canvas_px), (8, 10, 20))
    image = ImageChops.add(image, glow, scale=2.5)  # scale>1 dims the glow
    image = ImageChops.add(image, rings_layer)
    return image.resize((target_size, target_size), resample=Image.Resampling.LANCZOS)


def _flow_color(coord, rings, lo, hi, phase):
    """Color for the flowing styles: a there-and-back (cyclic) palette slice
    sampled at `coord`, shifted by `phase` so it flows and loops seamlessly."""
    u = coord / max(1, rings - 1) - phase
    tri = 1 - abs(2 * (u % 1.0) - 1)  # triangle wave, period 1: 0 -> 1 -> 0
    return palette_color(lo + (hi - lo) * tri)


def render_ripple_frame(canvas_px, center, step, padding, rings, lo, hi,
                        phase, scale_factor, target_size, flow=False,
                        shape="circle"):
    """Moving rings that drift inward (the classic ripple).

    The outermost ring is pinned in place and each new ring is born *beneath*
    it and slides out from behind it at full brightness, so nothing ever pops,
    fades or pulses in the rim. With `flow=True` (the "rippleflow" style) the
    color also streams inward on top of the drift.
    """
    rings_layer = Image.new("RGB", (canvas_px, canvas_px), (0, 0, 0))
    rings_draw = ImageDraw.Draw(rings_layer)
    glow = Image.new("RGB", (canvas_px, canvas_px), (0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    factors = shape_factors_for(shape, phase)
    width = step * 0.55

    # Moving rings drift inward. Each is born hidden behind the permanent outer
    # ring and materialises gradually over one full loop as it travels its one
    # ring-step out from under it, reaching full strength exactly when it sits
    # at normal spacing. That paces emergence to the drift, so the rim emits at
    # the loop's rhythm. The innermost fades out as it collapses to a point at
    # the center (the bullseye), which is imperceptible.
    for k in range(1, rings + 1):
        eff = k - 1 + phase  # phase .. rings-1+phase
        radius = center - (padding + eff * step)
        emerge = min(1.0, eff)  # 0 at birth -> 1 one step in, paced to the loop
        collapse = max(0.0, min(1.0, (radius - width) / step))
        fade = min(emerge, collapse)
        if fade <= 0:
            continue
        alpha = fade * fade * (3 - 2 * fade)  # smoothstep
        if flow:
            color = _flow_color(eff, rings, lo, hi, phase)
        else:
            color = palette_color(lo + (hi - lo) * (eff / max(1, rings - 1)))
        _draw_ring(rings_draw, glow_draw, center, radius, width, color, alpha,
                   factors)

    # Permanent outermost ring, drawn LAST so it is never overwritten and stays
    # exactly the same every frame, masking where the next ring is born.
    _draw_ring(rings_draw, glow_draw, center, center - padding, width,
               palette_color(lo), factors=factors)

    return _finish_frame(canvas_px, rings_layer, glow, scale_factor, target_size)


def render_flow_frame(canvas_px, center, step, padding, rings, lo, hi,
                      phase, scale_factor, target_size, shape="circle"):
    """Still rings, flowing color.

    Rings stay exactly where the static image puts them; only the color flows
    inward. A there-and-back (cyclic) palette makes the flow wrap seamlessly,
    with no fades and no rings appearing or vanishing.
    """
    rings_layer = Image.new("RGB", (canvas_px, canvas_px), (0, 0, 0))
    rings_draw = ImageDraw.Draw(rings_layer)
    glow = Image.new("RGB", (canvas_px, canvas_px), (0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    factors = shape_factors_for(shape, phase)
    width = step * 0.55
    for i in range(rings):
        radius = center - (padding + i * step)
        _draw_ring(rings_draw, glow_draw, center, radius, width,
                   _flow_color(i, rings, lo, hi, phase), factors=factors)

    return _finish_frame(canvas_px, rings_layer, glow, scale_factor, target_size)


def render_tunnel_frame(canvas_px, center, step, padding, rings, lo, hi,
                        phase, scale_factor, target_size):
    """Infinite-zoom tunnel: fall endlessly into the circle.

    Ring radii are spaced geometrically and the whole field scales by exactly
    one ratio per loop, so each ring lands where the next one was: a perfectly
    seamless zoom. Rings grow outward and exit past the frame while new ones
    emerge at the center; thickness scales with depth and the color flows with
    it, so it reads as perspective.
    """
    rings_layer = Image.new("RGB", (canvas_px, canvas_px), (0, 0, 0))
    rings_draw = ImageDraw.Draw(rings_layer)
    glow = Image.new("RGB", (canvas_px, canvas_px), (0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    ratio = 1.0 + 2.4 / rings  # each ring this much bigger than the one before
    corner = center * 1.41421356  # beyond this a ring is fully off-frame
    r_min = step * 0.6  # smallest ring near the vanishing point

    k = -2  # start a touch inside so new rings emerge from the center, not pop
    while True:
        radius = r_min * ratio ** (k + phase)
        k += 1
        if radius > corner:
            break
        width = radius * (ratio - 1.0) * 0.55  # thickness scales with depth
        # Fade the tiniest rings in at the vanishing point (a pure function of
        # radius, hence of k+phase, so the loop stays seamless).
        fade = max(0.0, min(1.0, (radius / r_min - 1.0 / ratio) / (1.0 - 1.0 / ratio)))
        alpha = fade * fade * (3 - 2 * fade)
        if alpha <= 0:
            continue
        color = _flow_color(k + phase, rings, lo, hi, 0.0)
        _draw_ring(rings_draw, glow_draw, center, radius, width, color, alpha)

    return _finish_frame(canvas_px, rings_layer, glow, scale_factor, target_size)


def _draw_offset_ring(rings_draw, glow_draw, cx, cy, radius, width, color,
                      alpha=1.0):
    """Like the standard ring, but at an arbitrary (cx, cy) so rings can sit
    off the canvas center. Used by the trippy styles that swirl or duplicate
    rings away from the middle."""
    if radius <= 0:
        return
    dark = interpolate(color, (0, 0, 0), 0.65)
    light = interpolate(color, (255, 255, 255), 0.6)
    steps = max(3, int(width))
    for s in range(steps + 1):
        t = s / steps
        rr = radius - width / 2 + t * width
        if rr <= 0:
            continue
        val = max(0.0, 1 - ((t - 0.42) / 0.5) ** 2)
        shade = interpolate(dark, light, val)
        if alpha < 1.0:
            shade = interpolate((0, 0, 0), shade, alpha)
        rings_draw.ellipse((cx - rr, cy - rr, cx + rr, cy + rr),
                           outline=shade, width=2)
    glow_color = interpolate((0, 0, 0), color, alpha) if alpha < 1.0 else color
    glow_draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                      outline=glow_color, width=int(width))


def render_twist_frame(canvas_px, center, step, padding, rings, lo, hi,
                       phase, scale_factor, target_size):
    """A hypnotic vortex: nested rings whose centers spiral away from the
    middle, further the deeper they go, and the whole spiral winds round once
    per loop so it turns forever without a seam."""
    rings_layer = Image.new("RGB", (canvas_px, canvas_px), (0, 0, 0))
    rings_draw = ImageDraw.Draw(rings_layer)
    glow = Image.new("RGB", (canvas_px, canvas_px), (0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    width = step * 0.55
    swirl = 2.6   # how far the deepest rings drift off-center (in ring-steps)
    winds = 1.0   # extra turns the spiral makes from rim to core
    for i in range(rings):
        radius = center - (padding + i * step)
        if radius <= width:
            continue
        depth = i / max(1, rings - 1)          # 0 at the rim, 1 at the core
        off = swirl * step * depth
        ang = 2 * math.pi * (winds * depth + phase)
        cx = center + off * math.cos(ang)
        cy = center + off * math.sin(ang)
        color = palette_color(lo + (hi - lo) * depth)
        _draw_offset_ring(rings_draw, glow_draw, cx, cy, radius, width, color)

    return _finish_frame(canvas_px, rings_layer, glow, scale_factor, target_size)


def _breathe(x):
    """Asymmetric breath wave, period 1: a quick inhale and a long exhale. It
    is a sine warped by its own phase, which stays perfectly periodic (so the
    loop is seamless) but is no longer a symmetric in-and-out pulse."""
    a = 2 * math.pi * (x % 1.0)
    return math.sin(a + 0.6 * math.sin(a))


def render_breathing_frame(canvas_px, center, step, padding, rings, lo, hi,
                           phase, scale_factor, target_size):
    """Centered rings that swell and shrink like a breathing chest. The breath
    travels inward (each ring lags the one outside it) and is deliberately
    lop-sided: a fast inhale and a slow exhale."""
    rings_layer = Image.new("RGB", (canvas_px, canvas_px), (0, 0, 0))
    rings_draw = ImageDraw.Draw(rings_layer)
    glow = Image.new("RGB", (canvas_px, canvas_px), (0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    width = step * 0.55
    amp = 0.45 * step
    for i in range(rings):
        base = center - (padding + i * step)
        depth = i / max(1, rings - 1)
        radius = base + amp * _breathe(phase - 0.5 * depth)
        if radius <= width:
            continue
        color = palette_color(lo + (hi - lo) * depth)
        _draw_ring(rings_draw, glow_draw, center, radius, width, color)

    return _finish_frame(canvas_px, rings_layer, glow, scale_factor, target_size)


def _fold_symmetry(image, segments):
    """Fold a frame into a kaleidoscope: max-blend rotated copies (the near
    black background is untouched, only the bright rings combine) for n-fold
    rotational symmetry, then mirror once for reflection symmetry."""
    folded = image
    for k in range(1, segments):
        folded = ImageChops.lighter(
            folded, image.rotate(360.0 * k / segments,
                                 resample=Image.Resampling.BICUBIC))
    return ImageChops.lighter(folded,
                              folded.transpose(Image.Transpose.FLIP_LEFT_RIGHT))


def render_kaleidoscope_frame(canvas_px, center, step, padding, rings, lo, hi,
                              phase, scale_factor, target_size):
    """A turning mandala. One lop-sided cluster of rings orbits the center over
    the loop, then the frame is folded into six mirrored segments, so the
    single cluster becomes a symmetric, slowly rotating kaleidoscope."""
    rings_layer = Image.new("RGB", (canvas_px, canvas_px), (0, 0, 0))
    rings_draw = ImageDraw.Draw(rings_layer)
    glow = Image.new("RGB", (canvas_px, canvas_px), (0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    reach = canvas_px / 2 - padding
    width = step * 0.6
    ang = 2 * math.pi * phase
    cx = center + reach * 0.45 * math.cos(ang)
    cy = center + reach * 0.45 * math.sin(ang)
    cluster = max(4, rings // 2)
    for i in range(cluster):
        radius = reach * 0.32 - i * step * 0.9
        if radius <= width:
            continue
        color = palette_color(lo + (hi - lo) * (i / max(1, cluster - 1)))
        _draw_offset_ring(rings_draw, glow_draw, cx, cy, radius, width, color)

    frame = _finish_frame(canvas_px, rings_layer, glow, scale_factor, target_size)
    return _fold_symmetry(frame, 6)


def render_interference_frame(canvas_px, center, step, padding, rings, lo, hi,
                              phase, scale_factor, target_size):
    """Two families of fine concentric rings drawn from two centers that drift
    apart and back together, so their overlap ripples with shifting moire
    bands. The separation follows a cosine, so it returns to the start."""
    rings_layer = Image.new("RGB", (canvas_px, canvas_px), (0, 0, 0))
    rings_draw = ImageDraw.Draw(rings_layer)
    glow = Image.new("RGB", (canvas_px, canvas_px), (0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    width = step * 0.42
    sep = (canvas_px / 2 - padding) * 0.22 * (0.5 - 0.5 * math.cos(2 * math.pi * phase))
    count = int((canvas_px / 2) / step) + rings  # plenty of rings for clear moire
    for sign, pos in ((-1, lo), (1, hi)):
        cx = center + sign * sep
        color = palette_color(pos)
        for i in range(count):
            radius = (i + 0.5) * step
            _draw_offset_ring(rings_draw, glow_draw, cx, center, radius, width, color)

    return _finish_frame(canvas_px, rings_layer, glow, scale_factor, target_size)


FPS_CHOICES = (20, 25, 50)  # only fps that map to exact GIF frame delays (1/100s)
STYLES = {
    "ripple": render_ripple_frame,
    "rippleflow": functools.partial(render_ripple_frame, flow=True),
    "flow": render_flow_frame,
    "tunnel": render_tunnel_frame,
    "twist": render_twist_frame,
    "breathing": render_breathing_frame,
    "kaleidoscope": render_kaleidoscope_frame,
    "interference": render_interference_frame,
}


def generate_gif(save_path: str, target_size: int = 256, rings: int = 16,
                 fps: int = 25, style: str = "ripple", shape: str = "circle"):
    # The loop is always one second: one frame per fps. fps is restricted to
    # values that divide cleanly into GIF's 1/100s frame delays, so timing is
    # always even (50/40/20 ms) and the loop is perfect.
    frames = fps
    scale_factor = 4
    canvas_px = target_size * scale_factor
    padding = 4 * scale_factor

    # Same color-slice setup as the static generator.
    lo = random.uniform(0.0, 0.55)
    hi = lo + random.uniform(0.35, 1.0 - lo)
    if random.random() < 0.5:
        lo, hi = hi, lo  # flow inward or outward

    center = canvas_px / 2
    step = (canvas_px - 2 * padding) / (2 * rings)

    render = STYLES[style]
    images = [render(canvas_px, center, step, padding, rings, lo, hi,
                     frame / frames, scale_factor, target_size, shape=shape)
              for frame in range(frames)]

    images[0].save(save_path, save_all=True, append_images=images[1:], loop=0,
                   duration=round(1000 / fps), disposal=2)


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
    parser.add_argument("--gif", action="store_true",
                        help="render a seamless looping GIF instead of static PNGs")
    parser.add_argument("--style", choices=sorted(STYLES), default="ripple",
                        help="GIF motion: 'ripple' (rings drift inward), 'flow' "
                             "(still rings, color flows inward), 'rippleflow' "
                             "(both), 'tunnel' (infinite zoom), 'twist' "
                             "(spiralling vortex), 'breathing' (asymmetric "
                             "in/out pulse), 'kaleidoscope' (rotating mandala) "
                             "or 'interference' (drifting moire) (default: "
                             "ripple)")
    parser.add_argument("--fps", type=int, default=25, choices=FPS_CHOICES,
                        help="GIF speed and smoothness; the loop is always 1s "
                             "(default: 25)")
    parser.add_argument("--shape", choices=SHAPE_NAMES, default="circle",
                        help="ring shape: circle (default), triangle, square, "
                             "pentagon, hexagon, star, superellipse, or 'morph' "
                             "(cycles through the shapes; GIF only)")
    parser.add_argument("--seed", type=int, default=None,
                        help="random seed for reproducible output")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    ext = "gif" if args.gif else "png"
    os.makedirs(args.out_dir, exist_ok=True)
    for i in range(args.count):
        path = os.path.join(args.out_dir, f"circle_{i}.{ext}")
        if args.gif:
            generate_gif(path, target_size=args.size, rings=args.rings,
                         fps=args.fps, style=args.style, shape=args.shape)
        else:
            generator(path, target_size=args.size, rings=args.rings,
                      shape=args.shape)
        print(f"saved {path}")


if __name__ == "__main__":
    main()
