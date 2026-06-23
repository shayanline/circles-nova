# CLAUDE.md

## Project

`circles` is a single-file generative art script. It produces PNGs of
concentric, gradient-colored rings with a soft glow.

## Layout

- `main.py` — the whole program.
  - `random_color()` — vivid random RGB via HSV.
  - `interpolate(start, end, factor)` — linear color blend.
  - `generator(save_path, target_size, rings, shape)` — renders one static
    image via `_draw_ring` at `scale_factor`x resolution, additively blends,
    adds a Gaussian-blurred glow, then downscales with LANCZOS.
  - `generate_gif(save_path, ..., style, shape)` — render a seamless 1s looping
    GIF. Styles via `STYLES`, each a `render_*_frame(...)` function periodic in
    `phase` so the loop is seamless: `ripple`, `flow`, `rippleflow`, `tunnel`
    (infinite zoom), `twist` (off-center vortex), `breathing` (asymmetric pulse
    via `_breathe`), `kaleidoscope` (orbiting cluster folded by
    `_fold_symmetry`), `interference` (two ring families moire).
    `_draw_ring`/`_draw_offset_ring` draw a ring (centered / off-center) and
    `_finish_frame` composites them.
  - Shapes: `--shape` draws rings as polygons instead of circles.
  - `main()` — argparse CLI; writes `circle_{i}.png` (or `.gif` with `--gif`)
    files into the output dir.
- `imgs/` — generated output (also used by the README gallery).
- `requirements.txt` — runtime deps (Pillow).

## Running

```bash
pip install -r requirements.txt
python main.py            # 16 images into imgs/
python main.py --seed 7   # reproducible output
```

## Conventions

- Standard library + Pillow only; keep it dependency-light.
- Image work goes through Pillow (`Image`, `ImageDraw`, `ImageChops`,
  `ImageFilter`); render high-res then downscale for anti-aliasing.
