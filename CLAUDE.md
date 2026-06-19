# CLAUDE.md

## Project

`circles` is a single-file generative art script. It produces PNGs of
concentric, gradient-colored rings with a soft glow.

## Layout

- `main.py` — the whole program.
  - `random_color()` — vivid random RGB via HSV.
  - `interpolate(start, end, factor)` — linear color blend.
  - `generator(save_path, target_size, rings)` — renders one image. Draws
    nested ellipses at `scale_factor`x resolution, additively blends them,
    adds a Gaussian-blurred glow layer, then downscales with LANCZOS.
  - `main()` — argparse CLI; writes `circle_{i}.png` files into the output dir.
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
