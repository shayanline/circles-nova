# CLAUDE.md

## Project

`circles` is a single-file generative art script. It produces PNGs of
concentric, gradient-colored rings with a soft glow.

## Layout

- `main.py` — the whole program.
  - `random_color()` — vivid random RGB via HSV.
  - `interpolate(start, end, factor)` — linear color blend.
  - `generator(save_path, target_size, rings, shape)` — renders one image.
    Draws nested rings via `_draw_ring` at `scale_factor`x resolution,
    additively blends them, adds a Gaussian-blurred glow layer, then downscales
    with LANCZOS.
  - `generate_gif(save_path, ..., style, shape)` — render a seamless 1s looping
    GIF. Styles via `STYLES`: `ripple` (rings drift inward), `flow` (still
    rings, color flows), `rippleflow` (both); `render_ripple_frame`/
    `render_flow_frame` draw the frames and `_finish_frame` composites them.
  - Shapes: `--shape` draws rings as polygons instead of circles. `SHAPE_NAMES`
    lists the options; `shape_factors_for(shape, phase)` returns per-angle
    radius factors (None for `circle`, the fast ellipse path), `_draw_ring`
    traces the shaded tube as polygons when given factors, and `morph` blends
    between shapes across the GIF loop.
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
