"""Type Trail Chinese Feng Shui (风水) Poster and Animation Generator.

Generates a museum-grade dynamic vector morphing poster and animation between
the Chinese characters '风' (Wind) and '水' (Water), featuring:
  - Sub-pixel TrueType contour extraction via fontTools & CairoPen (SimHei)
  - 2-loop topological correspondence with equidistant arc-length resampling
  - Cyclic Euclidean phase minimization to prevent twisting
  - Fluid aerodynamic curve path connecting top-right to bottom-left
  - Swiss international typographic grid with bilingual labels & registration marks
  - Color gradient options: elemental celestial cyan to warm amber glow, or silver
  - GSAP cascading time-sequenced reveal for HyperFrames MP4 rendering

Usage:
  python build_composition.py
  python build_composition.py --steps 30 --duration 5.0 --style gradient
  python build_composition.py --style wireframe
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import cairo
import numpy as np
from fontTools.pens.cairoPen import CairoPen
from fontTools.ttLib import TTFont

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── Project constants ────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).resolve().parent
LOCAL_FONT = PROJECT_DIR / "fonts" / "simhei.ttf"
SYSTEM_FONT = Path("C:/Windows/Fonts/simhei.ttf")
FONT_PATH = LOCAL_FONT if LOCAL_FONT.exists() else SYSTEM_FONT

WIDTH, HEIGHT = 1080, 1440
FPS = 30
POS_START = np.array([720.0, 380.0])
POS_END = np.array([360.0, 1060.0])
GLYPH_SIZE = 310.0


# ── Geometry extraction & resampling ─────────────────────────────────

def get_glyph_loops(font: TTFont, char: str) -> list[np.ndarray]:
    """Extract flattened polygon loops for a single character using CairoPen."""
    cmap = font.getBestCmap()
    glyph_name = cmap.get(ord(char))
    if not glyph_name:
        raise ValueError(f"Character '{char}' (U+{ord(char):04X}) not found in font.")

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 10, 10)
    ctx = cairo.Context(surface)
    pen = CairoPen(font.getGlyphSet(), ctx)
    font.getGlyphSet()[glyph_name].draw(pen)
    path = ctx.copy_path_flat()

    loops: list[np.ndarray] = []
    curr: list[tuple[float, float]] = []
    for ptype, pts in list(path):
        if ptype == cairo.PATH_MOVE_TO:
            if len(curr) > 2:
                loops.append(np.array(curr, dtype=float))
            curr = [pts]
        elif ptype == cairo.PATH_LINE_TO:
            curr.append(pts)
        elif ptype == cairo.PATH_CLOSE_PATH:
            if len(curr) > 2:
                loops.append(np.array(curr, dtype=float))
                curr = []
    if len(curr) > 2:
        loops.append(np.array(curr, dtype=float))
    return loops


def resample_closed(pts: np.ndarray, n: int) -> np.ndarray:
    """Arc-length resample a closed polygon loop to n equidistant vertices."""
    closed = np.vstack([pts, pts[0:1]]) if not np.allclose(pts[0], pts[-1]) else pts
    diffs = np.diff(closed, axis=0)
    seg_lens = np.hypot(diffs[:, 0], diffs[:, 1])
    cum = np.concatenate([[0], np.cumsum(seg_lens)])
    total = cum[-1]
    if total < 1e-8:
        return np.tile(pts[0], (n, 1))
    targets = np.linspace(0, total, n, endpoint=False)
    out = np.zeros((n, 2))
    for i, d in enumerate(targets):
        idx = min(int(np.searchsorted(cum, d, side="right")) - 1, len(seg_lens) - 1)
        t = (d - cum[idx]) / seg_lens[idx] if seg_lens[idx] > 1e-8 else 0.0
        out[i] = closed[idx] + t * diffs[idx]
    return out


def ensure_clockwise(pts: np.ndarray) -> np.ndarray:
    """Ensure polygon vertices follow clockwise winding in screen coordinates."""
    x, y = pts[:, 0], pts[:, 1]
    area = 0.5 * np.sum(x * np.roll(y, -1) - y * np.roll(x, -1))
    if area < 0:
        return pts[::-1]
    return pts


def align_loop(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Find cyclic shift of loop b that minimizes squared Euclidean distance to a."""
    n = len(a)
    best_cost = float("inf")
    best_shift = 0
    step = max(1, n // 100)
    for shift in range(0, n, step):
        cost = float(np.sum((a - np.roll(b, shift, axis=0)) ** 2))
        if cost < best_cost:
            best_cost = cost
            best_shift = shift
    for shift in range(best_shift - step, best_shift + step + 1):
        actual_shift = shift % n
        cost = float(np.sum((a - np.roll(b, actual_shift, axis=0)) ** 2))
        if cost < best_cost:
            best_cost = cost
            best_shift = actual_shift
    return np.roll(b, best_shift, axis=0)


def pts_to_svg_d(pts: np.ndarray, precision: int = 2) -> str:
    """Convert Nx2 point array to closed SVG path string."""
    parts = [f"M{pts[0, 0]:.{precision}f} {pts[0, 1]:.{precision}f}"]
    for p in pts[1:]:
        parts.append(f"L{p[0]:.{precision}f} {p[1]:.{precision}f}")
    parts.append("Z")
    return "".join(parts)


# ── Color Palette Calculation ────────────────────────────────────────

def get_layer_color(t: float, style: str) -> tuple[str, float]:
    """Return hex color string and opacity for intermediate layer at parameter t."""
    if style == "wireframe":
        return "#ffffff", 0.65

    c_start = np.array([0.0, 0.90, 1.0])
    c_mid = np.array([0.98, 0.98, 1.0])
    c_end = np.array([1.0, 0.62, 0.23])

    if t < 0.5:
        col = (1.0 - t * 2.0) * c_start + (t * 2.0) * c_mid
    else:
        u = (t - 0.5) * 2.0
        col = (1.0 - u) * c_mid + u * c_end

    r = int(np.clip(col[0] * 255.0, 0, 255))
    g = int(np.clip(col[1] * 255.0, 0, 255))
    b = int(np.clip(col[2] * 255.0, 0, 255))
    return f"#{r:02x}{g:02x}{b:02x}", 0.68


# ── Static Poster Renderer (Cairo) ───────────────────────────────────

def render_static_poster(
    layers: list[dict[str, Any]],
    poly_f: list[np.ndarray],
    poly_s: list[np.ndarray],
    out_path: Path,
) -> None:
    """Render 1080x1440 static poster using PyCairo with Swiss typography."""
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)

    # 1. Dark canvas background
    ctx.set_source_rgb(0.025, 0.025, 0.028)
    ctx.paint()

    # Subtle radial atmospheric gradient glow
    pat = cairo.RadialGradient(540.0, 720.0, 50.0, 540.0, 720.0, 750.0)
    pat.add_color_stop_rgba(0.0, 0.05, 0.12, 0.18, 0.35)
    pat.add_color_stop_rgba(0.7, 0.02, 0.03, 0.05, 0.15)
    pat.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
    ctx.set_source(pat)
    ctx.paint()

    # 2. Draw all intermediate blend contours
    ctx.set_line_width(0.9)
    for layer in layers:
        col_hex = layer["color"]
        r = int(col_hex[1:3], 16) / 255.0
        g = int(col_hex[3:5], 16) / 255.0
        b = int(col_hex[5:7], 16) / 255.0
        alpha = layer["opacity"]
        ctx.set_source_rgba(r, g, b, alpha)

        for poly in [layer["poly0"], layer["poly1"]]:
            ctx.new_path()
            ctx.move_to(poly[0, 0], poly[0, 1])
            for p in poly[1:]:
                ctx.line_to(p[0], p[1])
            ctx.close_path()
            ctx.stroke()

    # 3. Draw solid endpoint glyphs on top with evenodd fill
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)

    # Start: 风 (Top-right)
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.new_path()
    for p in poly_f:
        spts = p * GLYPH_SIZE + POS_START
        ctx.move_to(spts[0, 0], spts[0, 1])
        for pt in spts[1:]:
            ctx.line_to(pt[0], pt[1])
        ctx.close_path()
    ctx.fill()

    # End: 水 (Bottom-left)
    ctx.new_path()
    for p in poly_s:
        spts = p * GLYPH_SIZE + POS_END
        ctx.move_to(spts[0, 0], spts[0, 1])
        for pt in spts[1:]:
            ctx.line_to(pt[0], pt[1])
        ctx.close_path()
    ctx.fill()

    # 4. Swiss Typography Grid & Registration Crosshairs
    margin = 54.0
    ctx.set_source_rgba(0.9, 0.9, 0.9, 0.85)

    def draw_text(text: str, x: float, y: float, size: float, bold: bool = False, right_align: bool = False) -> None:
        ctx.select_font_face("Microsoft YaHei", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(size)
        ext = ctx.text_extents(text)
        px = x - ext.width if right_align else x
        ctx.move_to(px, y)
        ctx.show_text(text)

    # Hairline registration borders
    ctx.set_line_width(0.75)
    ctx.set_source_rgba(1.0, 1.0, 1.0, 0.18)
    ctx.rectangle(margin, margin, WIDTH - 2 * margin, HEIGHT - 2 * margin)
    ctx.stroke()

    # Registration corner marks (+)
    cross_len = 12.0
    for cx, cy in [
        (margin, margin),
        (WIDTH - margin, margin),
        (margin, HEIGHT - margin),
        (WIDTH - margin, HEIGHT - margin),
    ]:
        ctx.new_path()
        ctx.move_to(cx - cross_len, cy)
        ctx.line_to(cx + cross_len, cy)
        ctx.move_to(cx, cy - cross_len)
        ctx.line_to(cx, cy + cross_len)
        ctx.stroke()

    # Corner 1: Top-Left
    ctx.set_source_rgba(1.0, 1.0, 1.0, 0.95)
    draw_text("TYPE TRAIL // CHINESE VECTOR MORPH", margin + 20, margin + 42, 13, bold=True)
    ctx.set_source_rgba(0.75, 0.75, 0.75, 0.7)
    draw_text("VOL. 01 — FENG SHUI (风水) · 气乘风散 界水则止", margin + 20, margin + 64, 11)
    draw_text("SERIES: ORIENTAL MODERNISM / DUAL-LOOP DYNAMICS", margin + 20, margin + 82, 9)

    # Corner 2: Top-Right
    ctx.set_source_rgba(1.0, 1.0, 1.0, 0.95)
    draw_text("1080 × 1440 PX // 30 FPS", WIDTH - margin - 20, margin + 42, 13, bold=True, right_align=True)
    ctx.set_source_rgba(0.75, 0.75, 0.75, 0.7)
    draw_text("FONT: SIMHEI VECTOR ENGINE", WIDTH - margin - 20, margin + 64, 11, right_align=True)
    draw_text("TOPOLOGY: 2 LOOPS 1-TO-1 MAPPING", WIDTH - margin - 20, margin + 82, 9, right_align=True)

    # Corner 3: Bottom-Left
    ctx.set_source_rgba(1.0, 1.0, 1.0, 0.95)
    draw_text("GLYPHS: 风 [WIND] → 水 [WATER]", margin + 20, HEIGHT - margin - 52, 13, bold=True)
    ctx.set_source_rgba(0.75, 0.75, 0.75, 0.7)
    draw_text("NATURAL FLUID INTERPOLATION // 32 CONTOURS", margin + 20, HEIGHT - margin - 32, 11)
    draw_text("HARMONIC CURVE: QUADRATIC FLUID DISPLACEMENT", margin + 20, HEIGHT - margin - 16, 9)

    # Corner 4: Bottom-Right
    ctx.set_source_rgba(1.0, 1.0, 1.0, 0.95)
    draw_text("HYPERFRAMES ENGINE // VERIFIED PROOF", WIDTH - margin - 20, HEIGHT - margin - 52, 13, bold=True, right_align=True)
    ctx.set_source_rgba(0.75, 0.75, 0.75, 0.7)
    draw_text("ARC-LENGTH UNIFORM RESAMPLING (400 / 250 PTS)", WIDTH - margin - 20, HEIGHT - margin - 32, 11, right_align=True)
    draw_text("CYCLIC PHASE MINIMIZATION // ZERO-TWIST MORPH", WIDTH - margin - 20, HEIGHT - margin - 16, 9, right_align=True)

    surface.write_to_png(str(out_path))
    log.info("Static poster successfully rendered: %s", out_path)


# ── HTML / HyperFrames Composition Generator ─────────────────────────

def generate_html(
    layers: list[dict[str, Any]],
    poly_f: list[np.ndarray],
    poly_s: list[np.ndarray],
    duration: float,
    out_path: Path,
) -> None:
    """Generate HyperFrames compliant index.html with GSAP timeline."""
    margin = 54.0

    path_f0 = pts_to_svg_d(poly_f[0] * GLYPH_SIZE + POS_START)
    path_f1 = pts_to_svg_d(poly_f[1] * GLYPH_SIZE + POS_START)
    path_s0 = pts_to_svg_d(poly_s[0] * GLYPH_SIZE + POS_END)
    path_s1 = pts_to_svg_d(poly_s[1] * GLYPH_SIZE + POS_END)

    solid_f_d = f"{path_f0} {path_f1}"
    solid_s_d = f"{path_s0} {path_s1}"

    contour_svg_elements: list[str] = []
    for idx, layer in enumerate(layers):
        d0 = pts_to_svg_d(layer["poly0"])
        d1 = pts_to_svg_d(layer["poly1"])
        col = layer["color"]
        op = layer["opacity"]
        contour_svg_elements.append(
            f'<path id="layer-{idx}" class="contour-layer" d="{d0} {d1}" '
            f'fill="none" stroke="{col}" stroke-width="0.9" opacity="0" '
            f'data-target-opacity="{op:.2f}" />'
        )

    layers_markup = "\n    ".join(contour_svg_elements)

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1080, height=1440, initial-scale=1.0">
  <title>Type Trail — 风水 (Feng Shui)</title>
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      width: 1080px;
      height: 1440px;
      overflow: hidden;
      background: #060608;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      user-select: none;
      -webkit-font-smoothing: antialiased;
    }}
    #artboard {{
      position: relative;
      width: 1080px;
      height: 1440px;
      background: #060608;
    }}
    .glow {{
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 1100px;
      height: 1100px;
      background: radial-gradient(circle, rgba(0, 180, 255, 0.08) 0%, rgba(255, 150, 50, 0.05) 50%, rgba(0,0,0,0) 75%);
      pointer-events: none;
    }}
    svg {{
      position: absolute;
      top: 0;
      left: 0;
      width: 1080px;
      height: 1440px;
    }}
    .typo-layer {{
      position: absolute;
      top: 0;
      left: 0;
      width: 1080px;
      height: 1440px;
      pointer-events: none;
    }}
    .label-box {{
      position: absolute;
      color: rgba(255, 255, 255, 0.85);
      font-size: 11px;
      line-height: 1.5;
      letter-spacing: 0.08em;
    }}
    .label-box h1 {{
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.12em;
      color: #ffffff;
      margin-bottom: 3px;
    }}
    .label-box p {{
      color: rgba(255, 255, 255, 0.82);
    }}
    .label-box .sub {{
      font-size: 9px;
      color: rgba(255, 255, 255, 0.68);
    }}
    .top-left {{
      top: {margin + 20:.1f}px;
      left: {margin + 20:.1f}px;
    }}
    .top-right {{
      top: {margin + 20:.1f}px;
      right: {margin + 20:.1f}px;
      text-align: right;
    }}
    .bottom-left {{
      bottom: {margin + 20:.1f}px;
      left: {margin + 20:.1f}px;
    }}
    .bottom-right {{
      bottom: {margin + 20:.1f}px;
      right: {margin + 20:.1f}px;
      text-align: right;
    }}
    .grid-border {{
      position: absolute;
      top: {margin:.1f}px;
      left: {margin:.1f}px;
      width: {WIDTH - 2 * margin:.1f}px;
      height: {HEIGHT - 2 * margin:.1f}px;
      border: 0.75px solid rgba(255, 255, 255, 0.16);
      pointer-events: none;
    }}
  </style>
</head>
<body>
  <div id="artboard"
       data-composition-id="type-trail-fengshui"
       data-width="{WIDTH}"
       data-height="{HEIGHT}"
       data-duration="{duration}">
    <div class="glow"></div>

    <svg viewBox="0 0 1080 1440" fill="none" xmlns="http://www.w3.org/2000/svg">
      <!-- Hairline registration crosshairs -->
      <g stroke="rgba(255, 255, 255, 0.25)" stroke-width="0.75">
        <line x1="{margin - 12:.1f}" y1="{margin:.1f}" x2="{margin + 12:.1f}" y2="{margin:.1f}" />
        <line x1="{margin:.1f}" y1="{margin - 12:.1f}" x2="{margin:.1f}" y2="{margin + 12:.1f}" />
        <line x1="{WIDTH - margin - 12:.1f}" y1="{margin:.1f}" x2="{WIDTH - margin + 12:.1f}" y2="{margin:.1f}" />
        <line x1="{WIDTH - margin:.1f}" y1="{margin - 12:.1f}" x2="{WIDTH - margin:.1f}" y2="{margin + 12:.1f}" />
        <line x1="{margin - 12:.1f}" y1="{HEIGHT - margin:.1f}" x2="{margin + 12:.1f}" y2="{HEIGHT - margin:.1f}" />
        <line x1="{margin:.1f}" y1="{HEIGHT - margin - 12:.1f}" x2="{margin:.1f}" y2="{HEIGHT - margin + 12:.1f}" />
        <line x1="{WIDTH - margin - 12:.1f}" y1="{HEIGHT - margin:.1f}" x2="{WIDTH - margin + 12:.1f}" y2="{HEIGHT - margin:.1f}" />
        <line x1="{WIDTH - margin:.1f}" y1="{HEIGHT - margin - 12:.1f}" x2="{WIDTH - margin:.1f}" y2="{HEIGHT - margin + 12:.1f}" />
      </g>

      <!-- Morph Contour Layers -->
      <g id="contours-group">
    {layers_markup}
      </g>

      <!-- Solid Departure Glyph (风) -->
      <path id="glyph-feng" d="{solid_f_d}" fill="#ffffff" fill-rule="evenodd" opacity="0" />

      <!-- Solid Arrival Glyph (水) -->
      <path id="glyph-shui" d="{solid_s_d}" fill="#ffffff" fill-rule="evenodd" opacity="0" />
    </svg>

    <div class="grid-border"></div>

    <div class="typo-layer">
      <div class="label-box top-left">
        <h1>TYPE TRAIL // CHINESE VECTOR MORPH</h1>
        <p>VOL. 01 — FENG SHUI (风水) · 气乘风散 界水则止</p>
        <div class="sub">SERIES: ORIENTAL MODERNISM / DUAL-LOOP DYNAMICS</div>
      </div>
      <div class="label-box top-right">
        <h1>1080 × 1440 PX // 30 FPS</h1>
        <p>FONT: SIMHEI VECTOR ENGINE</p>
        <div class="sub">TOPOLOGY: 2 LOOPS 1-TO-1 MAPPING</div>
      </div>
      <div class="label-box bottom-left">
        <h1>GLYPHS: 风 [WIND] → 水 [WATER]</h1>
        <p>NATURAL FLUID INTERPOLATION // 32 CONTOURS</p>
        <div class="sub">HARMONIC CURVE: QUADRATIC FLUID DISPLACEMENT</div>
      </div>
      <div class="label-box bottom-right">
        <h1>HYPERFRAMES ENGINE // VERIFIED PROOF</h1>
        <p>ARC-LENGTH UNIFORM RESAMPLING (400 / 250 PTS)</p>
        <div class="sub">CYCLIC PHASE MINIMIZATION // ZERO-TWIST MORPH</div>
      </div>
    </div>
  </div>

  <script>
    const tl = gsap.timeline({{ paused: true }});
    window.__timelines = window.__timelines || {{}};
    window.__timelines["type-trail-fengshui"] = tl;
    window.tl = tl;

    tl.fromTo('.grid-border, .typo-layer', 
      {{ opacity: 0 }}, 
      {{ opacity: 1, duration: 0.4, ease: 'power1.out' }}, 
      0.0
    );

    tl.fromTo('#glyph-feng',
      {{ opacity: 0, scale: 0.94, transformOrigin: 'center center' }},
      {{ opacity: 1, scale: 1.0, duration: 0.45, ease: 'back.out(1.4)' }},
      0.2
    );

    const layers = document.querySelectorAll('.contour-layer');
    layers.forEach((layer, i) => {{
      const targetOpacity = parseFloat(layer.getAttribute('data-target-opacity')) || 0.68;
      const startTime = 0.5 + (i / layers.length) * 2.4;
      tl.to(layer, {{
        opacity: targetOpacity,
        duration: 0.22,
        ease: 'power1.inOut'
      }}, startTime);
    }});

    tl.fromTo('#glyph-shui',
      {{ opacity: 0, scale: 0.94, transformOrigin: 'center center' }},
      {{ opacity: 1, scale: 1.0, duration: 0.5, ease: 'power2.out' }},
      3.0
    );

    tl.to({{}}, {{ duration: {duration - 3.5:.2f} }}, 3.5);
  </script>
</body>
</html>
"""
    out_path.write_text(html_content, encoding="utf-8")
    log.info("HyperFrames index.html successfully generated: %s", out_path)


# ── Interactive Preview Generator ────────────────────────────────────

def generate_preview(duration: float, out_path: Path) -> None:
    """Generate preview.html with responsive viewport, controls and scrubber."""
    preview_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Preview — Type Trail: 风水 (Feng Shui)</title>
  <style>
    body {{
      margin: 0;
      padding: 0;
      background: #0d0e12;
      color: #eee;
      font-family: system-ui, -apple-system, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
      overflow-x: hidden;
    }}
    header {{
      width: 100%;
      padding: 16px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(20, 22, 28, 0.95);
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      position: sticky;
      top: 0;
      z-index: 100;
    }}
    .title-group h1 {{
      font-size: 16px;
      font-weight: 700;
      letter-spacing: 0.05em;
      margin: 0;
    }}
    .title-group p {{
      font-size: 12px;
      color: #888;
      margin: 2px 0 0 0;
    }}
    .controls {{
      display: flex;
      gap: 12px;
      align-items: center;
    }}
    button {{
      background: #252836;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.12);
      padding: 6px 14px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 12px;
      font-weight: 600;
      transition: all 0.15s ease;
    }}
    button:hover {{
      background: #32364a;
      border-color: rgba(255, 255, 255, 0.25);
    }}
    button.primary {{
      background: #00d2ff;
      color: #000;
      border: none;
    }}
    button.primary:hover {{
      background: #33dcff;
    }}
    .scrubber-container {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      font-variant-numeric: tabular-nums;
      color: #aaa;
    }}
    input[type=range] {{
      width: 200px;
      accent-color: #00d2ff;
      cursor: pointer;
    }}
    .stage-wrapper {{
      margin: 24px 0;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(255, 255, 255, 0.08);
      border-radius: 8px;
      overflow: hidden;
      display: flex;
      justify-content: center;
      align-items: center;
      background: #000;
      transform-origin: top center;
    }}
    iframe {{
      width: 1080px;
      height: 1440px;
      border: none;
      display: block;
      transform: scale(0.52);
      transform-origin: top center;
    }}
    .viewport-box {{
      width: 561.6px;
      height: 748.8px;
      overflow: hidden;
      position: relative;
    }}
  </style>
</head>
<body>
  <header>
    <div class="title-group">
      <h1>TYPE TRAIL // CHINESE FENG SHUI (风水)</h1>
      <p>Dual-Loop Vector Morphing & Cascading Dynamic Poster</p>
    </div>
    <div class="controls">
      <button id="btn-play" class="primary">Play / Pause</button>
      <button id="btn-restart">Restart</button>
      <div class="scrubber-container">
        <span id="time-display">0.00s</span>
        <input type="range" id="scrubber" min="0" max="{duration}" step="0.01" value="0">
        <span>{duration:.1f}s</span>
      </div>
    </div>
  </header>

  <div class="stage-wrapper">
    <div class="viewport-box">
      <iframe id="anim-frame" src="index.html"></iframe>
    </div>
  </div>

  <script>
    const iframe = document.getElementById('anim-frame');
    const btnPlay = document.getElementById('btn-play');
    const btnRestart = document.getElementById('btn-restart');
    const scrubber = document.getElementById('scrubber');
    const timeDisplay = document.getElementById('time-display');

    let tl = null;

    iframe.addEventListener('load', () => {{
      const iWindow = iframe.contentWindow;
      tl = iWindow.tl;
      if (tl) {{
        tl.play();
        requestAnimationFrame(updateLoop);
      }}
    }});

    function updateLoop() {{
      if (tl) {{
        const time = tl.time();
        scrubber.value = time;
        timeDisplay.textContent = time.toFixed(2) + 's';
      }}
      requestAnimationFrame(updateLoop);
    }}

    btnPlay.addEventListener('click', () => {{
      if (!tl) return;
      if (tl.paused()) {{
        tl.play();
        btnPlay.textContent = 'Pause';
      }} else {{
        tl.pause();
        btnPlay.textContent = 'Play';
      }}
    }});

    btnRestart.addEventListener('click', () => {{
      if (!tl) return;
      tl.restart();
      btnPlay.textContent = 'Pause';
    }});

    scrubber.addEventListener('input', (e) => {{
      if (!tl) return;
      tl.pause();
      tl.time(parseFloat(e.target.value));
      btnPlay.textContent = 'Play';
    }});
  </script>
</body>
</html>
"""
    out_path.write_text(preview_content, encoding="utf-8")
    log.info("Preview preview.html successfully generated: %s", out_path)


# ── Pipeline Entry ───────────────────────────────────────────────────

def build(steps: int = 30, duration: float = 5.0, style: str = "gradient") -> None:
    """Execute full Chinese Type Trail pipeline for 风水."""
    log.info("Running Chinese Type Trail generation pipeline for 风水 (Feng Shui)...")
    log.info("Steps: %d, Duration: %.1fs, Style: %s", steps, duration, style)

    font = TTFont(str(FONT_PATH))

    loops_f = get_glyph_loops(font, "风")
    loops_s = get_glyph_loops(font, "水")

    if len(loops_f) != 2 or len(loops_s) != 2:
        raise ValueError(
            f"Unexpected loop count for SimHei: 风 has {len(loops_f)}, 水 has {len(loops_s)}."
        )

    all_f = np.vstack(loops_f)
    c_f = (np.min(all_f, axis=0) + np.max(all_f, axis=0)) / 2.0
    s_f = float(np.max(np.max(all_f, axis=0) - np.min(all_f, axis=0)))

    all_s = np.vstack(loops_s)
    c_s = (np.min(all_s, axis=0) + np.max(all_s, axis=0)) / 2.0
    s_s = float(np.max(np.max(all_s, axis=0) - np.min(all_s, axis=0)))

    norm_f: list[np.ndarray] = []
    for loop_pts in loops_f:
        nl = (loop_pts - c_f) / s_f
        nl[:, 1] = -nl[:, 1]
        norm_f.append(nl)

    norm_s: list[np.ndarray] = []
    for loop_pts in loops_s:
        nl = (loop_pts - c_s) / s_s
        nl[:, 1] = -nl[:, 1]
        norm_s.append(nl)

    poly_f0 = ensure_clockwise(resample_closed(norm_f[0], 400))
    poly_f1 = ensure_clockwise(resample_closed(norm_f[1], 250))

    poly_s0 = ensure_clockwise(resample_closed(norm_s[0], 400))
    poly_s1 = ensure_clockwise(resample_closed(norm_s[1], 250))

    poly_s0_aligned = align_loop(poly_f0, poly_s0)
    poly_s1_aligned = align_loop(poly_f1, poly_s1)

    total_layers = steps + 2
    layers: list[dict[str, Any]] = []

    for i in range(total_layers):
        t = i / float(total_layers - 1)

        bend = np.sin(t * np.pi) * 85.0
        curr_pos = (1.0 - t) * POS_START + t * POS_END + np.array([-bend, bend * 0.45])

        interp_0 = (1.0 - t) * poly_f0 + t * poly_s0_aligned
        interp_1 = (1.0 - t) * poly_f1 + t * poly_s1_aligned

        poly0_screen = interp_0 * GLYPH_SIZE + curr_pos
        poly1_screen = interp_1 * GLYPH_SIZE + curr_pos

        color_hex, opacity = get_layer_color(t, style)

        layers.append({
            "index": i,
            "t": t,
            "color": color_hex,
            "opacity": opacity,
            "poly0": poly0_screen,
            "poly1": poly1_screen,
        })

    poster_path = PROJECT_DIR / "static_poster.png"
    render_static_poster(
        layers,
        [poly_f0, poly_f1],
        [poly_s0_aligned, poly_s1_aligned],
        poster_path,
    )

    html_path = PROJECT_DIR / "index.html"
    generate_html(
        layers,
        [poly_f0, poly_f1],
        [poly_s0_aligned, poly_s1_aligned],
        duration,
        html_path,
    )

    preview_path = PROJECT_DIR / "preview.html"
    generate_preview(duration, preview_path)

    log.info("All pipeline assets generated successfully in: %s", PROJECT_DIR)


def main() -> None:
    """Command-line interface."""
    parser = argparse.ArgumentParser(description="Chinese Type Trail — 风水 (Feng Shui)")
    parser.add_argument("--steps", type=int, default=30, help="Intermediate contour steps (default: 30)")
    parser.add_argument("--duration", type=float, default=5.0, help="Animation duration in seconds (default: 5.0)")
    parser.add_argument(
        "--style",
        type=str,
        choices=["gradient", "wireframe"],
        default="gradient",
        help="Visual aesthetic style (default: gradient)",
    )
    args = parser.parse_args()
    build(steps=args.steps, duration=args.duration, style=args.style)


if __name__ == "__main__":
    main()
