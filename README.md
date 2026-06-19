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

## Usage

```bash
pip install -r requirements.txt
python main.py                 # 16 images into imgs/
python main.py --seed 7        # reproducible output
python main.py -n 8 -s 512 -r 20
```

### Options

```
-n, --count    number of images to generate (default: 16)
-s, --size     output image size in pixels (default: 256)
-r, --rings    number of rings per image (default: 16)
-o, --out-dir  output directory (default: imgs)
    --seed     random seed for reproducible output
```

## Credits

- Original concept, concentric-circle generator, and code: the repository owner.
- Color-interpolation technique: adapted from a YouTube tutorial.
- "nova" rendering & color reimagining: built collaboratively with AI.
