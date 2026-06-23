# circles · nova

> A small generative-art script that fills a square with concentric rings.
> Originally hand-built before AI; later evolved — with AI — into glossy
> 3D-looking rings colored like slices of an abstract painting.

![a nova circle](imgs/circle_5.png)
![a nova circle](imgs/circle_1.png)
![a nova circle](imgs/circle_3.png)

## The story

**circles** started as a personal project, written before AI tools were in the
picture. The idea was simple and entirely hand-made: draw a stack of nested
circles in a square and let them form hypnotic, gradient-colored targets. The
core color-blending trick came from a YouTube tutorial; turning it into a
generative **concentric-circle** art piece was the original author's own touch.

**circles · nova** is that same idea, taken further with AI as a collaborator.
The shape stayed true to the original — centered rings in a square — but the
rendering and color were reimagined.

## What was original

- Nested ellipses drawn in a square to form concentric "target" rings.
- A two-color gradient, blended ring to ring via linear color interpolation.
- Additive blending of each ring onto a near-black canvas.
- Run in a loop to produce a gallery of unique images.

## What AI added (the "nova" touches)

- **3D glossy-tube rings.** Each ring is still a flat 2D outline, but its
  stroke is shaded from dark edges up to a bright highlight across its width,
  so every line reads like a rounded, glossy wire/pipe.
- **Abstract-painting color.** Instead of two random colors, rings are colored
  from a lush master palette that flows orange → coral → rose → magenta →
  violet → indigo → azure → teal. Each image "catches" a smooth, continuous
  slice of it, so colors melt from one ring into the next — like a cutout of
  an abstract painting — with a touch of jitter so it feels hand-painted.
- **High-res render + downscale.** Drawn at 4× resolution and shrunk with
  LANCZOS resampling for clean, anti-aliased edges.
- **A limited soft glow.** A faint blurred halo under the rings for depth,
  kept subtle on purpose.
- **A proper CLI.** Control the number of images, size, ring count, output
  directory, and a random seed for reproducible output.

## Animated GIFs

Pass `--gif` to render a seamless looping GIF instead of static PNGs. Pick the
motion with `--style`:

| `ripple` | `flow` | `rippleflow` |
|:--------:|:------:|:------------:|
| ![ripple](examples/ripple.gif) | ![flow](examples/flow.gif) | ![rippleflow](examples/rippleflow.gif) |
| rings drift inward | rings still, color flows inward | both at once |

The outermost ring is pinned in place and new rings are born behind it, so
nothing ever pops or fades in the rim. The loop is always exactly one second:
the single `--fps` knob sets both speed and smoothness, and is limited to 20,
25, or 50, the only rates that map to GIF's 1/100s frame delays exactly, so the
timing is always even and the loop is always perfect.

```bash
python main.py --gif                     # ripple GIFs into imgs/
python main.py --gif --style flow         # still rings, flowing color
python main.py --gif --style rippleflow   # both
python main.py --gif --fps 50             # smoothest
```

## Shapes

By default the rings are circles. Pass `--shape` to draw them as any regular
polygon instead, `superellipse` for a soft rounded square, or `star`:

| `triangle` | `square` | `hexagon` | `star` | `superellipse` |
|:----------:|:--------:|:---------:|:------:|:--------------:|
| ![triangle](examples/shape_triangle.png) | ![square](examples/shape_square.png) | ![hexagon](examples/shape_hexagon.png) | ![star](examples/shape_star.png) | ![superellipse](examples/shape_superellipse.png) |

`--shape` works for both static PNGs and `--gif`. For GIFs there is also a
special `morph` shape that smoothly cycles the rings through every shape and
loops seamlessly:

![morph](examples/morph.gif)

```bash
python main.py --shape star               # five-pointed star rings
python main.py --shape hexagon -s 512     # bigger hexagons
python main.py --gif --shape morph        # rings morph shape over the loop
```

## Usage

```bash
pip install -r requirements.txt
python main.py                 # 16 images into imgs/
python main.py --seed 7        # reproducible output
python main.py -n 8 -s 512 -r 20
python main.py --gif -s 512    # 512px looping GIFs
```

### Options

```
-n, --count    number of images to generate (default: 16)
-s, --size     output image size in pixels (default: 256)
-r, --rings    number of rings per image (default: 16)
-o, --out-dir  output directory (default: imgs)
    --gif      render a seamless looping GIF instead of static PNGs
    --style    GIF motion: ripple, flow, or rippleflow (default: ripple)
    --fps      GIF speed and smoothness: 20, 25, or 50; loop is always 1s (default: 25)
    --shape    ring shape: circle, triangle, square, pentagon, hexagon, star,
               superellipse, or morph (GIF only) (default: circle)
    --seed     random seed for reproducible output
```

## Credits

- Original concept, concentric-circle generator, and code: the repository owner.
- Color-interpolation technique: adapted from a YouTube tutorial.
- "nova" rendering & color reimagining: built collaboratively with AI.
