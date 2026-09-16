"""Type Trail Shang Shan Ruo Shui (上善若水) Graphic Chinese Morphing Generator.

Extracts stylized graphic Chinese characters from artwork and creates a dual-level
blend dynamic poster and animation:
  - Level 1: Inward concentric blend (strictly 10 steps) inside each stroke
  - Level 2: Inter-character serpentine blend connecting 上 -> 善 -> 若 -> 水
  - Swiss international typographic grid with bilingual labels & registration marks
  - GSAP cascading timeline for HyperFrames MP4 video export

Usage:
  python build_composition.py
  python build_composition.py --inner-steps 10 --seg-steps 22 --duration 7.0
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import cairo
import cv2
import numpy as np
from shapely.geometry import MultiPolygon, Polygon

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).resolve().parent
INPUT_IMAGE = PROJECT_DIR / "input_artwork.png"

WIDTH, HEIGHT = 1080, 1440
FPS = 30
GLYPH_SIZE = 260.0

# Serpentine layout for 上善若水 across 1080x1440
ANCHORS = [
    ("上", np.array([360.0, 270.0])),
    ("善", np.array([720.0, 560.0])),
    ("若", np.array([350.0, 870.0])),
    ("水", np.array([720.0, 1170.0])),
]

PALETTE = [
    np.array([0.0, 0.90, 1.0]),    # 上: Celestial Cyan
    np.array([0.10, 0.95, 0.65]),  # 善: Jade Emerald
    np.array([1.0, 0.75, 0.20]),   # 若: Amber Gold
    np.array([0.20, 0.60, 1.0]),   # 水: Azure Blue
]


# ── Vision extraction & contour preprocessing ─────────────────────────

def extract_graphic_characters(image_path: Path) -> dict[str, list[np.ndarray]]:
    """Extract closed stroke polygons for all 4 characters from the input artwork."""
    if not image_path.exists():
        raise FileNotFoundError(f"Input image not found: {image_path}")

    img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    rgb = img[:, :, :3]
    if img.shape[2] == 4:
        alpha = img[:, :, 3] / 255.0
        gray = (rgb[:, :, 0] * 0.114 + rgb[:, :, 1] * 0.587 + rgb[:, :, 2] * 0.299) * alpha + 255.0 * (1.0 - alpha)
        gray = gray.astype(np.uint8)
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    closed[565:, 370:] = 0  # Mask out small search icon in bottom right corner

    crops: dict[str, tuple[int, int, int, int]] = {
        "上": (10, 175, 35, 195),
        "善": (130, 325, 200, 385),
        "若": (295, 445, 35, 205),
        "水": (425, 600, 170, 420),
    }

    chars_raw: dict[str, list[np.ndarray]] = {}
    for name, (y1, y2, x1, x2) in crops.items():
        mask = np.zeros_like(closed)
        mask[y1:y2, x1:x2] = closed[y1:y2, x1:x2]
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS)
        polys = [c[:, 0, :].astype(float) for c in cnts if cv2.contourArea(c) > 40.0]
        polys.sort(key=lambda p: cv2.contourArea(p.astype(np.int32)), reverse=True)
        chars_raw[name] = polys

    return chars_raw


def normalize_glyph_strokes(strokes: list[np.ndarray]) -> list[np.ndarray]:
    """Normalize strokes into centered [-0.5, 0.5] box."""
    all_pts = np.vstack(strokes)
    c = (np.min(all_pts, axis=0) + np.max(all_pts, axis=0)) / 2.0
    scale = float(max(np.max(all_pts, axis=0) - np.min(all_pts, axis=0)))
    return [(p - c) / scale for p in strokes]


def resample_closed(pts: np.ndarray, n: int = 350) -> np.ndarray:
    """Arc-length resample a closed polygon to n equidistant vertices."""
    closed = np.vstack([pts, pts[0:1]]) if not np.allclose(pts[0], pts[-1]) else pts
    diffs = np.diff(closed, axis=0)
    seg_lens = np.hypot(diffs[:, 0], diffs[:, 1])
    cum = np.concatenate([[0.0], np.cumsum(seg_lens)])
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
    """Ensure polygon vertices follow clockwise winding."""
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


def get_inner_rings(poly_pts: np.ndarray, num_rings: int = 10) -> list[np.ndarray]:
    """Generate strictly num_rings inward concentric offset rings using Shapely buffer."""
    p = Polygon(poly_pts)
    if not p.is_valid:
        p = p.buffer(0)
    max_d = np.sqrt(p.area) * 0.32
    distances = np.linspace(0.0, max_d, num_rings)
    rings: list[np.ndarray] = []
    for d in distances:
        b = p.buffer(-d)
        if b.is_empty:
            continue
        if isinstance(b, Polygon):
            rings.append(np.array(b.exterior.coords))
        elif isinstance(b, MultiPolygon):
            for sub in b.geoms:
                rings.append(np.array(sub.exterior.coords))
    return rings


def pts_to_svg_d(pts: np.ndarray, precision: int = 2) -> str:
    """Convert Nx2 point array to closed SVG path string."""
    parts = [f"M{pts[0, 0]:.{precision}f} {pts[0, 1]:.{precision}f}"]
    for p in pts[1:]:
        parts.append(f"L{p[0]:.{precision}f} {p[1]:.{precision}f}")
    parts.append("Z")
    return "".join(parts)


# ── Static Poster Renderer (Cairo) ───────────────────────────────────

def render_static_poster(
    anchors: list[tuple[str, np.ndarray]],
    chars_norm: dict[str, list[np.ndarray]],
    inter_layers: list[dict[str, Any]],
    inner_steps: int,
    out_path: Path,
) -> None:
    """Render 1080x1440 static poster using PyCairo with Swiss typography."""
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)

    # 1. Dark canvas background
    ctx.set_source_rgb(0.02, 0.02, 0.025)
    ctx.paint()

    # Atmospheric radial glow centered behind composition
    pat = cairo.RadialGradient(540.0, 720.0, 50.0, 540.0, 720.0, 780.0)
    pat.add_color_stop_rgba(0.0, 0.04, 0.10, 0.16, 0.35)
    pat.add_color_stop_rgba(0.7, 0.02, 0.03, 0.05, 0.15)
    pat.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)
    ctx.set_source(pat)
    ctx.paint()

    # 2. Draw inter-character blend ribbons (Level 2)
    ctx.set_line_width(0.85)
    for layer in inter_layers:
        col = layer["color"]
        alpha = layer["opacity"]
        ctx.set_source_rgba(col[0], col[1], col[2], alpha)
        pts = layer["pts"]
        ctx.new_path()
        ctx.move_to(pts[0, 0], pts[0, 1])
        for p in pts[1:]:
            ctx.line_to(p[0], p[1])
        ctx.close_path()
        ctx.stroke()

    # 3. Draw 10-step inner blend contours on each character (Level 1)
    ctx.set_line_width(1.1)
    for idx, (name, pos) in enumerate(anchors):
        col = PALETTE[idx]
        for stroke_poly in chars_norm[name]:
            rings = get_inner_rings(stroke_poly, num_rings=inner_steps)
            for r_idx, r in enumerate(rings):
                alpha = 0.95 - (r_idx / float(inner_steps)) * 0.45
                ctx.set_source_rgba(col[0], col[1], col[2], alpha)
                spts = r * GLYPH_SIZE + pos
                ctx.new_path()
                ctx.move_to(spts[0, 0], spts[0, 1])
                for p in spts[1:]:
                    ctx.line_to(p[0], p[1])
                ctx.close_path()
                ctx.stroke()

    # 4. Swiss Typography Grid & Registration Crosshairs
    margin = 54.0

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
    draw_text("TYPE TRAIL // GRAPHIC CHINESE MORPH", margin + 20, margin + 42, 13, bold=True)
    ctx.set_source_rgba(0.85, 0.85, 0.88, 0.82)
    draw_text("VOL. 02 — SHANG SHAN RUO SHUI (上善若水)", margin + 20, margin + 64, 11)
    draw_text("DAO DE JING · CHAPTER 08 // DUAL-LEVEL BLEND", margin + 20, margin + 82, 9)

    # Corner 2: Top-Right
    ctx.set_source_rgba(1.0, 1.0, 1.0, 0.95)
    draw_text("1080 × 1440 PX // 30 FPS", WIDTH - margin - 20, margin + 42, 13, bold=True, right_align=True)
    ctx.set_source_rgba(0.85, 0.85, 0.88, 0.82)
    draw_text("SOURCE: PICTOGRAPHIC MOUNTAIN WATER ARTWORK", WIDTH - margin - 20, margin + 64, 11, right_align=True)
    draw_text("INTERIOR MORPH: 10 CONCENTRIC STEPS", WIDTH - margin - 20, margin + 82, 9, right_align=True)

    # Corner 3: Bottom-Left
    ctx.set_source_rgba(1.0, 1.0, 1.0, 0.95)
    draw_text("GLYPHS: 上 [UPPER] · 善 [KIND] · 若 [AS] · 水 [WATER]", margin + 20, HEIGHT - margin - 52, 13, bold=True)
    ctx.set_source_rgba(0.85, 0.85, 0.88, 0.82)
    draw_text("HIGHEST VIRTUE IS LIKE WATER // BENEFITING ALL", margin + 20, HEIGHT - margin - 32, 11)
    draw_text("HARMONIC S-CURVE: 3-STAGE SERPENTINE TRANSITION", margin + 20, HEIGHT - margin - 16, 9)

    # Corner 4: Bottom-Right
    ctx.set_source_rgba(1.0, 1.0, 1.0, 0.95)
    draw_text("HYPERFRAMES ENGINE // GRAPHIC MORPH PROOF", WIDTH - margin - 20, HEIGHT - margin - 52, 13, bold=True, right_align=True)
    ctx.set_source_rgba(0.85, 0.85, 0.88, 0.82)
    draw_text("SHAPELY SKELETAL BUFFER // ARC-LENGTH RESAMPLING", WIDTH - margin - 20, HEIGHT - margin - 32, 11, right_align=True)
    draw_text("TOPOGRAPHIC RELIEF + SPATIAL TRAIL DYNAMICS", WIDTH - margin - 20, HEIGHT - margin - 16, 9, right_align=True)

    surface.write_to_png(str(out_path))
    log.info("Static poster successfully rendered: %s", out_path)


# ── HTML / HyperFrames Composition Generator ─────────────────────────

def generate_html(
    anchors: list[tuple[str, np.ndarray]],
    chars_norm: dict[str, list[np.ndarray]],
    inter_layers: list[dict[str, Any]],
    inner_steps: int,
    duration: float,
    out_path: Path,
) -> None:
    """Generate HyperFrames compliant index.html with GSAP timeline."""
    margin = 54.0

    # Build SVG for inner blend rings of each character
    inner_svg_elements: list[str] = []
    for char_idx, (name, pos) in enumerate(anchors):
        col_arr = PALETTE[char_idx]
        col_hex = f"#{int(col_arr[0]*255):02x}{int(col_arr[1]*255):02x}{int(col_arr[2]*255):02x}"

        for s_idx, stroke_poly in enumerate(chars_norm[name]):
            rings = get_inner_rings(stroke_poly, num_rings=inner_steps)
            for r_idx, r in enumerate(rings):
                d = pts_to_svg_d(r * GLYPH_SIZE + pos)
                op = 0.95 - (r_idx / float(inner_steps)) * 0.45
                inner_svg_elements.append(
                    f'<path class="inner-ring char-{char_idx}" d="{d}" '
                    f'fill="none" stroke="{col_hex}" stroke-width="1.1" '
                    f'opacity="0" data-target-opacity="{op:.2f}" />'
                )

    # Build SVG for inter-character blend ribbons
    inter_svg_elements: list[str] = []
    for idx, layer in enumerate(inter_layers):
        d = pts_to_svg_d(layer["pts"])
        col_arr = layer["color"]
        col_hex = f"#{int(col_arr[0]*255):02x}{int(col_arr[1]*255):02x}{int(col_arr[2]*255):02x}"
        op = layer["opacity"]
        seg = layer["seg"]
        inter_svg_elements.append(
            f'<path id="inter-{idx}" class="inter-layer seg-{seg}" d="{d}" '
            f'fill="none" stroke="{col_hex}" stroke-width="0.85" '
            f'opacity="0" data-target-opacity="{op:.2f}" />'
        )

    inner_markup = "\n    ".join(inner_svg_elements)
    inter_markup = "\n    ".join(inter_svg_elements)

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1080, height=1440, initial-scale=1.0">
  <title>Type Trail — 上善若水 (Shang Shan Ruo Shui)</title>
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
      background: radial-gradient(circle, rgba(0, 180, 255, 0.08) 0%, rgba(25, 242, 166, 0.06) 35%, rgba(255, 191, 51, 0.04) 65%, rgba(0,0,0,0) 80%);
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
      color: rgba(255, 255, 255, 0.90);
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
      border: 0.75px solid rgba(255, 255, 255, 0.18);
      pointer-events: none;
    }}
  </style>
</head>
<body>
  <div id="artboard"
       data-composition-id="type-trail-shangshanruoshui"
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

      <!-- Inter-character Blend Ribbons -->
      <g id="inter-ribbons">
    {inter_markup}
      </g>

      <!-- 10-step Inner Concentric Rings for all characters -->
      <g id="inner-rings">
    {inner_markup}
      </g>
    </svg>

    <div class="grid-border"></div>

    <div class="typo-layer">
      <div class="label-box top-left">
        <h1>TYPE TRAIL // GRAPHIC CHINESE MORPH</h1>
        <p>VOL. 02 — SHANG SHAN RUO SHUI (上善若水)</p>
        <div class="sub">DAO DE JING · CHAPTER 08 // DUAL-LEVEL BLEND</div>
      </div>
      <div class="label-box top-right">
        <h1>1080 × 1440 PX // 30 FPS</h1>
        <p>SOURCE: PICTOGRAPHIC MOUNTAIN WATER ARTWORK</p>
        <div class="sub">INTERIOR MORPH: 10 CONCENTRIC STEPS</div>
      </div>
      <div class="label-box bottom-left">
        <h1>GLYPHS: 上 [UPPER] · 善 [KIND] · 若 [AS] · 水 [WATER]</h1>
        <p>HIGHEST VIRTUE IS LIKE WATER // BENEFITING ALL</p>
        <div class="sub">HARMONIC S-CURVE: 3-STAGE SERPENTINE TRANSITION</div>
      </div>
      <div class="label-box bottom-right">
        <h1>HYPERFRAMES ENGINE // GRAPHIC MORPH PROOF</h1>
        <p>SHAPELY SKELETAL BUFFER // ARC-LENGTH RESAMPLING</p>
        <div class="sub">TOPOGRAPHIC RELIEF + SPATIAL TRAIL DYNAMICS</div>
      </div>
    </div>
  </div>

  <script>
    const tl = gsap.timeline({{ paused: true }});
    window.__timelines = window.__timelines || {{}};
    window.__timelines["type-trail-shangshanruoshui"] = tl;
    window.tl = tl;

    // 0.0s - 0.4s: Fade in UI borders and metadata
    tl.fromTo('.grid-border, .typo-layer', 
      {{ opacity: 0 }}, 
      {{ opacity: 1, duration: 0.4, ease: 'power1.out' }}, 
      0.0
    );

    // 0.2s - 1.2s: Illuminate 10-step inner rings of character '上'
    document.querySelectorAll('.char-0').forEach((ring, i) => {{
      const op = parseFloat(ring.getAttribute('data-target-opacity')) || 0.8;
      tl.to(ring, {{ opacity: op, duration: 0.35, ease: 'power1.out' }}, 0.2 + i * 0.04);
    }});

    // 1.0s - 2.4s: Reveal Segment 0 (上 -> 善)
    document.querySelectorAll('.seg-0').forEach((layer, i, arr) => {{
      const op = parseFloat(layer.getAttribute('data-target-opacity')) || 0.48;
      tl.to(layer, {{ opacity: op, duration: 0.2, ease: 'power1.inOut' }}, 1.0 + (i / arr.length) * 1.3);
    }});

    // 2.2s - 2.8s: Illuminate character '善'
    document.querySelectorAll('.char-1').forEach((ring, i) => {{
      const op = parseFloat(ring.getAttribute('data-target-opacity')) || 0.8;
      tl.to(ring, {{ opacity: op, duration: 0.35, ease: 'power1.out' }}, 2.2 + i * 0.03);
    }});

    // 2.6s - 3.9s: Reveal Segment 1 (善 -> 若)
    document.querySelectorAll('.seg-1').forEach((layer, i, arr) => {{
      const op = parseFloat(layer.getAttribute('data-target-opacity')) || 0.48;
      tl.to(layer, {{ opacity: op, duration: 0.2, ease: 'power1.inOut' }}, 2.6 + (i / arr.length) * 1.2);
    }});

    // 3.7s - 4.3s: Illuminate character '若'
    document.querySelectorAll('.char-2').forEach((ring, i) => {{
      const op = parseFloat(ring.getAttribute('data-target-opacity')) || 0.8;
      tl.to(ring, {{ opacity: op, duration: 0.35, ease: 'power1.out' }}, 3.7 + i * 0.03);
    }});

    // 4.1s - 5.4s: Reveal Segment 2 (若 -> 水)
    document.querySelectorAll('.seg-2').forEach((layer, i, arr) => {{
      const op = parseFloat(layer.getAttribute('data-target-opacity')) || 0.48;
      tl.to(layer, {{ opacity: op, duration: 0.2, ease: 'power1.inOut' }}, 4.1 + (i / arr.length) * 1.2);
    }});

    // 5.2s - 5.8s: Illuminate character '水'
    document.querySelectorAll('.char-3').forEach((ring, i) => {{
      const op = parseFloat(ring.getAttribute('data-target-opacity')) || 0.8;
      tl.to(ring, {{ opacity: op, duration: 0.35, ease: 'power1.out' }}, 5.2 + i * 0.03);
    }});

    // 5.8s - {duration}s: Entire composition holds in complete harmony
    tl.to({{}}, {{ duration: {duration - 5.8:.2f} }}, 5.8);
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
  <title>Preview — Type Trail: 上善若水 (Shang Shan Ruo Shui)</title>
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
      <h1>TYPE TRAIL // 上善若水 (SHANG SHAN RUO SHUI)</h1>
      <p>Dual-Level Graphic Morphing: 10 Inner Steps + 3-Stage Serpentine Dynamics</p>
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

def build(inner_steps: int = 10, seg_steps: int = 22, duration: float = 7.0) -> None:
    """Execute full Chinese graphic dual-level blend pipeline for 上善若水."""
    log.info("Running Type Trail pipeline for 上善若水 (Shang Shan Ruo Shui)...")
    log.info("Inner steps: %d, Segment steps: %d, Duration: %.1fs", inner_steps, seg_steps, duration)

    chars_raw = extract_graphic_characters(INPUT_IMAGE)

    chars_norm: dict[str, list[np.ndarray]] = {}
    for name, strokes in chars_raw.items():
        chars_norm[name] = normalize_glyph_strokes(strokes)

    # Generate inter-character blend ribbons (Level 2)
    inter_layers: list[dict[str, Any]] = []
    layer_id = 0

    for seg_idx in range(len(ANCHORS) - 1):
        c1, pos1 = ANCHORS[seg_idx]
        c2, pos2 = ANCHORS[seg_idx + 1]

        p1_main = ensure_clockwise(resample_closed(chars_norm[c1][0], 400))
        p2_main = ensure_clockwise(resample_closed(chars_norm[c2][0], 400))
        p2_main_aligned = align_loop(p1_main, p2_main)

        col1 = PALETTE[seg_idx]
        col2 = PALETTE[seg_idx + 1]

        for s in range(seg_steps + 1):
            if seg_idx > 0 and s == 0:
                continue

            t = s / float(seg_steps)
            bend = np.sin(t * np.pi) * 60.0 * (1 if seg_idx % 2 == 0 else -1)
            curr_pos = (1.0 - t) * pos1 + t * pos2 + np.array([bend, 0.0])

            interp = (1.0 - t) * p1_main + t * p2_main_aligned
            col = (1.0 - t) * col1 + t * col2
            spts = interp * GLYPH_SIZE + curr_pos

            inter_layers.append({
                "id": layer_id,
                "seg": seg_idx,
                "t": t,
                "color": col,
                "opacity": 0.48,
                "pts": spts,
            })
            layer_id += 1

    # Render static poster PNG (1080x1440)
    poster_path = PROJECT_DIR / "static_poster.png"
    render_static_poster(
        ANCHORS,
        chars_norm,
        inter_layers,
        inner_steps,
        poster_path,
    )

    # Generate HyperFrames index.html & interactive preview.html
    html_path = PROJECT_DIR / "index.html"
    generate_html(
        ANCHORS,
        chars_norm,
        inter_layers,
        inner_steps,
        duration,
        html_path,
    )

    preview_path = PROJECT_DIR / "preview.html"
    generate_preview(duration, preview_path)

    log.info("All assets generated successfully in: %s", PROJECT_DIR)


def main() -> None:
    """Command-line interface."""
    parser = argparse.ArgumentParser(description="Type Trail — 上善若水 (Shang Shan Ruo Shui)")
    parser.add_argument("--inner-steps", type=int, default=10, help="Inward concentric blend steps (default: 10)")
    parser.add_argument("--seg-steps", type=int, default=22, help="Steps per transition segment (default: 22)")
    parser.add_argument("--duration", type=float, default=7.0, help="Animation duration in seconds (default: 7.0)")
    args = parser.parse_args()
    build(inner_steps=args.inner_steps, seg_steps=args.seg_steps, duration=args.duration)


if __name__ == "__main__":
    main()
