"""Type Trail Blend Poster Generator — v1.1.

Generates Illustrator "Blend Tool" dynamic ribbon posters for any arbitrary word,
featuring:
  - Sub-pixel TrueType Bézier extraction (Arial Bold)
  - Automatic serpentine/zigzag anchor layout calculation
  - Universal multi-hole topological counter detection and morphing
  - Uniform arc-length resampling (500 pts) with cyclic phase minimization
  - Swiss international style four-corner hairline typography and registration marks
  - GSAP cascading time-sequenced reveal baked into SVG/HTML
  - Full HyperFrames CLI compatibility for GPU hardware-accelerated MP4 export

Usage:
  python build_composition.py                   # Default: DESIGN (reference layout)
  python build_composition.py --text "FUTURE"   # Any arbitrary word
  python build_composition.py --text "MOTION" --steps 30 --duration 7.0
"""

from __future__ import annotations

import argparse
import json
import logging
import textwrap
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
FONT_PATH = PROJECT_DIR / "fonts" / "arialbd.ttf"
W, H = 1080, 1440
FPS = 30
STROKE_WIDTH = 1.0
STROKE_ALPHA = 0.65

# Default reference-matched anchor coordinates for "DESIGN"
REFERENCE_DESIGN_ANCHORS: list[tuple[str, np.ndarray]] = [
    ("D", np.array([W * 0.627, H * 0.174])),
    ("E", np.array([W * 0.325, H * 0.330])),
    ("S", np.array([W * 0.797, H * 0.400])),
    ("I", np.array([W * 0.329, H * 0.591])),
    ("G", np.array([W * 0.717, H * 0.700])),
    ("N", np.array([W * 0.434, H * 0.856])),
]


# ── Geometry extraction & resampling ─────────────────────────────────

def extract_loops(font: TTFont, char: str) -> list[np.ndarray]:
    """Extract flattened polygon loops for *char* using CairoPen."""
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 10, 10)
    ctx = cairo.Context(surface)
    pen = CairoPen(font.getGlyphSet(), ctx)
    font.getGlyphSet()[char].draw(pen)
    path = ctx.copy_path_flat()
    loops: list[np.ndarray] = []
    curr: list[tuple[float, float]] = []
    for path_type, pts in list(path):
        if path_type == cairo.PATH_MOVE_TO:
            if len(curr) > 2:
                loops.append(np.array(curr, dtype=float))
            curr = [pts]
        elif path_type == cairo.PATH_LINE_TO:
            curr.append(pts)
        elif path_type == cairo.PATH_CLOSE_PATH:
            if len(curr) > 2:
                loops.append(np.array(curr, dtype=float))
                curr = []
    if len(curr) > 2:
        loops.append(np.array(curr, dtype=float))
    return loops


def normalize_and_flip(loop: np.ndarray, cap_height: float = 1466.0) -> np.ndarray:
    """Flip Y axis (font upward to screen downward) and normalize by cap height."""
    res = loop.copy()
    res[:, 1] = cap_height - res[:, 1]
    res /= cap_height
    return res


def resample_closed(pts: np.ndarray, n: int = 500) -> np.ndarray:
    """Arc-length resample a closed polygon loop to *n* equidistant vertices."""
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
    """Find cyclic shift of loop *b* that minimizes squared Euclidean distance to *a*."""
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


def compute_anchors(text: str) -> list[tuple[str, np.ndarray]]:
    """Compute serpentine/zigzag anchor coordinates for arbitrary text."""
    clean_text = text.upper().strip()
    if clean_text == "DESIGN":
        return REFERENCE_DESIGN_ANCHORS

    k = len(clean_text)
    anchors: list[tuple[str, np.ndarray]] = []
    for i, ch in enumerate(clean_text):
        ratio = i / max(1, k - 1)
        y = H * (0.17 + 0.69 * ratio)
        x = W * 0.68 if i % 2 == 0 else W * 0.32
        anchors.append((ch, np.array([x, y])))
    return anchors


# ── Pipeline build ───────────────────────────────────────────────────

def build(
    text: str = "DESIGN",
    steps_per_seg: int = 26,
    duration: float = 6.0,
    letter_h: float | None = None,
) -> None:
    """Execute complete generation pipeline for *text* (v1.1)."""
    clean_text = text.upper().strip()
    if len(clean_text) < 2:
        raise ValueError("Text must contain at least 2 characters.")

    k = len(clean_text)
    calc_letter_h = letter_h if letter_h is not None else min(165.0, 950.0 / k)

    log.info("Type Trail Blend Generator v1.1 — rendering text: %s", clean_text)
    font = TTFont(str(FONT_PATH))

    # 1. Compute anchor positions and transition pairs
    anchors = compute_anchors(clean_text)
    pairs = [(anchors[i][0], anchors[i + 1][0], anchors[i][1], anchors[i + 1][1]) for i in range(k - 1)]

    # 2. Extract raw loops, outer boundaries, and inner holes for all unique characters
    unique_chars = sorted(set(clean_text))
    raw_loops: dict[str, list[np.ndarray]] = {}
    outers_norm: dict[str, np.ndarray] = {}
    inners_norm: dict[str, list[np.ndarray]] = {}

    for ch in unique_chars:
        loops = extract_loops(font, ch)
        raw_loops[ch] = loops
        outers_norm[ch] = normalize_and_flip(loops[0])
        inners_norm[ch] = [normalize_and_flip(loop_pts) for loop_pts in loops[1:]]

    # 3. Center each glyph outline and holes around outer bounding box centroid
    centers: dict[str, np.ndarray] = {}
    centered_outers: dict[str, np.ndarray] = {}
    centered_inners: dict[str, list[np.ndarray]] = {}

    for ch in unique_chars:
        pts = outers_norm[ch]
        min_xy = np.min(pts, axis=0)
        max_xy = np.max(pts, axis=0)
        c = (min_xy + max_xy) / 2
        centers[ch] = c
        centered_outers[ch] = pts - c
        centered_inners[ch] = [loop_pts - c for loop_pts in inners_norm[ch]]

    # 4. Resample outer loops and hole loops
    n_pts = 500
    resampled_outers: dict[str, np.ndarray] = {}
    resampled_inners: dict[str, list[np.ndarray]] = {}

    for ch in unique_chars:
        resampled_outers[ch] = ensure_clockwise(resample_closed(centered_outers[ch], n_pts))
        resampled_inners[ch] = [
            ensure_clockwise(resample_closed(loop_pts, 200)) for loop_pts in centered_inners[ch]
        ]

    # 5. Generate all interpolated contour layers across segments
    contours: list[dict[str, Any]] = []
    layer_id = 0

    for seg_idx, (c1, c2, pos1, pos2) in enumerate(pairs):
        poly1 = resampled_outers[c1]
        poly2_aligned = align_loop(poly1, resampled_outers[c2])

        for s in range(steps_per_seg + 1):
            if seg_idx > 0 and s == 0:
                continue

            t = s / steps_per_seg
            curr_pos = (1 - t) * pos1 + t * pos2
            curr_poly = (1 - t) * poly1 + t * poly2_aligned
            screen_poly = curr_poly * calc_letter_h + curr_pos

            # Universal hole morphing:
            # - Holes from departure letter c1 shrink to 0 as t -> 1
            # - Holes from arrival letter c2 expand from 0 as t -> 1
            hole_paths: list[str] = []

            if centered_inners[c1] and t < 0.90:
                scale_out = max(0.0, 1.0 - t * 1.1)
                for h_loop in resampled_inners[c1]:
                    h_screen = (h_loop * scale_out) * calc_letter_h + curr_pos
                    hole_paths.append(pts_to_svg_d(h_screen))

            if centered_inners[c2] and t > 0.10:
                scale_in = max(0.0, (t - 0.10) / 0.90)
                for h_loop in resampled_inners[c2]:
                    h_screen = (h_loop * scale_in) * calc_letter_h + curr_pos
                    hole_paths.append(pts_to_svg_d(h_screen))

            hole_d_combined = " ".join(hole_paths) if hole_paths else None

            contours.append({
                "layer_id": layer_id,
                "seg_idx": seg_idx,
                "s": s,
                "t": t,
                "outer_d": pts_to_svg_d(screen_poly),
                "hole_d": hole_d_combined,
            })
            layer_id += 1

    total_contours = len(contours)
    log.info("Generated %d total contour layers across %d segments", total_contours, len(pairs))

    # 6. Build solid letters SVG paths for each anchor instance
    solid_letters: list[dict[str, Any]] = []
    for idx, (ch, pos) in enumerate(anchors):
        outer_screen = centered_outers[ch] * calc_letter_h + pos
        holes_screen = [h * calc_letter_h + pos for h in centered_inners[ch]]
        has_holes = len(holes_screen) > 0

        combined_d_parts = [pts_to_svg_d(outer_screen)]
        for h_pts in holes_screen:
            combined_d_parts.append(pts_to_svg_d(h_pts))

        solid_letters.append({
            "idx": idx,
            "char": ch,
            "pos": pos,
            "has_holes": has_holes,
            "d": " ".join(combined_d_parts),
        })

    # 7. Render static poster PNG with corner graphics
    render_static_poster(clean_text, contours, solid_letters)

    # 8. Generate index.html (HyperFrames composition)
    generate_index_html(clean_text, contours, solid_letters, steps_per_seg, duration)

    # 9. Generate preview.html (interactive local preview)
    generate_preview_html(clean_text, duration)

    # 10. Update hyperframes.json
    hf_config = {
        "name": "type-trail-design",
        "width": W,
        "height": H,
        "fps": FPS,
        "duration": int(duration),
    }
    (PROJECT_DIR / "hyperframes.json").write_text(json.dumps(hf_config, indent=2), encoding="utf-8")

    log.info("✓ Build v1.1 complete for text: %s", clean_text)


# ── Static poster generation ─────────────────────────────────────────

def render_static_poster(
    text: str,
    contours: list[dict[str, Any]],
    solid_letters: list[dict[str, Any]],
) -> None:
    """Render full 1080×1440 static poster to PNG using Cairo."""
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surface)

    ctx.set_source_rgb(0, 0, 0)
    ctx.paint()

    _draw_corner_decorations_cairo(ctx, text, len(contours))

    ctx.set_line_width(STROKE_WIDTH)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

    for c in contours:
        _stroke_svg_path(ctx, c["outer_d"], STROKE_ALPHA)
        if c["hole_d"]:
            _stroke_svg_path(ctx, c["hole_d"], STROKE_ALPHA)

    ctx.set_source_rgb(1, 1, 1)
    for letter in solid_letters:
        if letter["has_holes"]:
            ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        else:
            ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
        _fill_svg_path(ctx, letter["d"])

    out_file = PROJECT_DIR / "static_poster.png"
    surface.write_to_png(str(out_file))
    log.info("Saved %s", out_file)


def _draw_corner_decorations_cairo(ctx: cairo.Context, text: str, total_contours: int) -> None:
    """Draw graphic hairline rules, crosshairs, and typography in four corners."""
    ctx.save()
    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)

    ctx.set_source_rgba(1, 1, 1, 0.45)
    ctx.set_line_width(0.75)
    pad_x, pad_y = 56, 56

    # Top-Left
    ctx.new_path()
    ctx.move_to(pad_x, pad_y)
    ctx.line_to(pad_x + 220, pad_y)
    ctx.move_to(pad_x, pad_y)
    ctx.line_to(pad_x, pad_y + 24)
    ctx.move_to(pad_x + 14, pad_y + 14)
    ctx.line_to(pad_x + 22, pad_y + 14)
    ctx.move_to(pad_x + 18, pad_y + 10)
    ctx.line_to(pad_x + 18, pad_y + 18)
    ctx.stroke()

    ctx.set_font_size(12)
    ctx.set_source_rgba(1, 1, 1, 0.90)
    ctx.move_to(pad_x + 30, pad_y + 18)
    ctx.show_text("TYPE TRAIL // MOTION STUDY")

    ctx.set_source_rgba(1, 1, 1, 0.65)
    ctx.set_font_size(10)
    ctx.move_to(pad_x + 30, pad_y + 34)
    ctx.show_text("v1.1 — DYNAMIC GENERATOR")

    # Top-Right
    right_x = W - pad_x
    ctx.set_source_rgba(1, 1, 1, 0.45)
    ctx.new_path()
    ctx.move_to(right_x - 220, pad_y)
    ctx.line_to(right_x, pad_y)
    ctx.move_to(right_x, pad_y)
    ctx.line_to(right_x, pad_y + 24)
    ctx.stroke()

    ctx.set_source_rgba(1, 1, 1, 0.90)
    ctx.set_font_size(12)
    ctx.move_to(right_x - 170, pad_y + 18)
    ctx.show_text("1080 × 1440 PX // 30 FPS")

    ctx.set_source_rgba(1, 1, 1, 0.65)
    ctx.set_font_size(10)
    ctx.move_to(right_x - 170, pad_y + 34)
    ctx.show_text("ENGINE: HYPERFRAMES")

    # Bottom-Left
    bot_y = H - pad_y
    ctx.set_source_rgba(1, 1, 1, 0.45)
    ctx.new_path()
    ctx.move_to(pad_x, bot_y)
    ctx.line_to(pad_x + 240, bot_y)
    ctx.move_to(pad_x, bot_y - 24)
    ctx.line_to(pad_x, bot_y)
    ctx.move_to(pad_x + 14, bot_y - 14)
    ctx.line_to(pad_x + 22, bot_y - 14)
    ctx.move_to(pad_x + 18, bot_y - 18)
    ctx.line_to(pad_x + 18, bot_y - 10)
    ctx.stroke()

    glyph_str = " — ".join(list(text))
    ctx.set_source_rgba(1, 1, 1, 0.90)
    ctx.set_font_size(12)
    ctx.move_to(pad_x + 30, bot_y - 22)
    ctx.show_text(f"GLYPHS: {glyph_str}")

    ctx.set_source_rgba(1, 1, 1, 0.65)
    ctx.set_font_size(10)
    ctx.move_to(pad_x + 30, bot_y - 8)
    ctx.show_text("FONT: ARIAL BOLD / VECTOR")

    # Bottom-Right
    ctx.set_source_rgba(1, 1, 1, 0.45)
    ctx.new_path()
    ctx.move_to(right_x - 240, bot_y)
    ctx.line_to(right_x, bot_y)
    ctx.move_to(right_x, bot_y - 24)
    ctx.line_to(right_x, bot_y)
    ctx.stroke()

    ctx.set_source_rgba(1, 1, 1, 0.90)
    ctx.set_font_size(12)
    ctx.move_to(right_x - 215, bot_y - 22)
    ctx.show_text(f"INTERPOLATION: {total_contours} CONTOURS")

    ctx.set_source_rgba(1, 1, 1, 0.65)
    ctx.set_font_size(10)
    ctx.move_to(right_x - 215, bot_y - 8)
    ctx.show_text(f"{len(text) - 1} SEGMENTS // UNIVERSAL MORPH")

    ctx.restore()


def _parse_svg_d(d_str: str) -> list[list[tuple[float, float]]]:
    """Minimal SVG path parser (M/L/Z only)."""
    import re
    subpaths: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    for token in re.findall(r"[MLZ][-\d.]+(?:\s[-\d.]+)?|Z", d_str):
        cmd = token[0]
        if cmd in ("M", "L"):
            nums = re.findall(r"-?[\d.]+", token[1:])
            if len(nums) >= 2:
                current.append((float(nums[0]), float(nums[1])))
        elif cmd == "Z":
            if current:
                subpaths.append(current)
                current = []
    if current:
        subpaths.append(current)
    return subpaths


def _stroke_svg_path(ctx: cairo.Context, d_str: str, alpha: float) -> None:
    """Stroke an SVG path string onto *ctx*."""
    ctx.set_source_rgba(1, 1, 1, alpha)
    for subpath in _parse_svg_d(d_str):
        if not subpath:
            continue
        ctx.new_path()
        ctx.move_to(*subpath[0])
        for pt in subpath[1:]:
            ctx.line_to(*pt)
        ctx.close_path()
        ctx.stroke()


def _fill_svg_path(ctx: cairo.Context, d_str: str) -> None:
    """Fill an SVG path string onto *ctx*."""
    ctx.new_path()
    for subpath in _parse_svg_d(d_str):
        if not subpath:
            continue
        ctx.move_to(*subpath[0])
        for pt in subpath[1:]:
            ctx.line_to(*pt)
        ctx.close_path()
    ctx.fill()


# ── HTML composition generation ──────────────────────────────────────

def generate_index_html(
    text: str,
    contours: list[dict[str, Any]],
    solid_letters: list[dict[str, Any]],
    steps_per_seg: int,
    duration: float,
) -> None:
    """Write index.html — the HyperFrames composition."""
    blend_elements: list[str] = []
    for c in contours:
        layer_id = c["layer_id"]
        outer = c["outer_d"]
        hole = c["hole_d"]
        combined = f"{outer} {hole}" if hole else outer
        blend_elements.append(
            f'    <path id="blend-{layer_id}" d="{combined}" '
            f'fill="none" stroke="rgba(255,255,255,{STROKE_ALPHA})" '
            f'stroke-width="{STROKE_WIDTH}" stroke-linejoin="round" '
            f'style="opacity:0"/>'
        )
    blend_svg = "\n".join(blend_elements)

    solid_elements: list[str] = []
    for item in solid_letters:
        idx = item["idx"]
        fill_rule = 'fill-rule="evenodd" ' if item["has_holes"] else ""
        solid_elements.append(
            f'    <path id="solid-{idx}" d="{item["d"]}" '
            f'fill="#ffffff" {fill_rule}style="opacity:0"/>'
        )
    solid_svg = "\n".join(solid_elements)

    glyph_str = " — ".join(list(text))

    template = textwrap.dedent("""\
    <!doctype html>
    <html lang="en">
    <head>
    <meta charset="utf-8">
    <title>Type Trail — __TEXT__ Blend</title>
    <style>
    *{box-sizing:border-box;margin:0;padding:0}
    html,body{background:#000;overflow:hidden;font-family:Arial,Helvetica,sans-serif}
    #type-trail-design{
      position:relative;width:__W__px;height:__H__px;background:#000;overflow:hidden;
    }
    #blend-svg,#solid-svg,#decor-svg{
      position:absolute;left:0;top:0;width:__W__px;height:__H__px;pointer-events:none;
    }
    #decor-svg{z-index:3}
    #solid-svg{z-index:2}
    #blend-svg{z-index:1}
    .meta-text{fill:#ffffff;letter-spacing:1.5px;font-family:Arial,sans-serif;font-weight:700}
    .meta-sub{fill:rgba(255,255,255,0.68);letter-spacing:1px;font-family:Arial,sans-serif}
    .rule-line{stroke:rgba(255,255,255,0.45);stroke-width:0.75}
    </style>
    </head>
    <body>
    <div id="type-trail-design"
         data-composition-id="type-trail-design"
         data-width="__W__" data-height="__H__"
         data-duration="__DURATION__">

    <!-- Four-corner graphic decorations and Swiss typography -->
    <svg id="decor-svg" viewBox="0 0 __W__ __H__" xmlns="http://www.w3.org/2000/svg">
      <!-- Top-Left -->
      <line x1="56" y1="56" x2="280" y2="56" class="rule-line"/>
      <line x1="56" y1="56" x2="56" y2="80" class="rule-line"/>
      <path d="M70 70H78 M74 66V74" class="rule-line"/>
      <text x="88" y="74" class="meta-text" font-size="12">TYPE TRAIL // MOTION STUDY</text>
      <text x="88" y="90" class="meta-sub" font-size="10">v1.1 — DYNAMIC GENERATOR</text>

      <!-- Top-Right -->
      <line x1="800" y1="56" x2="1024" y2="56" class="rule-line"/>
      <line x1="1024" y1="56" x2="1024" y2="80" class="rule-line"/>
      <text x="840" y="74" class="meta-text" font-size="12">1080 × 1440 PX // 30 FPS</text>
      <text x="840" y="90" class="meta-sub" font-size="10">ENGINE: HYPERFRAMES</text>

      <!-- Bottom-Left -->
      <line x1="56" y1="1384" x2="320" y2="1384" class="rule-line"/>
      <line x1="56" y1="1360" x2="56" y2="1384" class="rule-line"/>
      <path d="M70 1370H78 M74 1366V1374" class="rule-line"/>
      <text x="88" y="1362" class="meta-text" font-size="12">GLYPHS: __GLYPH_STR__</text>
      <text x="88" y="1376" class="meta-sub" font-size="10">FONT: ARIAL BOLD / VECTOR</text>

      <!-- Bottom-Right -->
      <line x1="760" y1="1384" x2="1024" y2="1384" class="rule-line"/>
      <line x1="1024" y1="1360" x2="1024" y2="1384" class="rule-line"/>
      <text x="795" y="1362" class="meta-text" font-size="12">INTERPOLATION: __TOTAL_CONTOURS__ CONTOURS</text>
      <text x="795" y="1376" class="meta-sub" font-size="10">__NUM_SEGS__ SEGMENTS // UNIVERSAL MORPH</text>
    </svg>

    <!-- Blend contour layer -->
    <svg id="blend-svg" viewBox="0 0 __W__ __H__" xmlns="http://www.w3.org/2000/svg">
    __BLEND_SVG__
    </svg>

    <!-- Solid endpoint letters (top layer) -->
    <svg id="solid-svg" viewBox="0 0 __W__ __H__" xmlns="http://www.w3.org/2000/svg">
    __SOLID_SVG__
    </svg>

    </div>

    <script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
    <script>
    (function() {
      const TOTAL_CONTOURS = __TOTAL_CONTOURS__;
      const NUM_LETTERS = __NUM_LETTERS__;
      const tl = gsap.timeline({ paused: true });

      tl.fromTo("#decor-svg", { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.5, ease: "power2.out" }, 0.0);
      tl.fromTo("#solid-0", { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.35, ease: "power2.out" }, 0.05);

      const revealStart = 0.4;
      const revealEnd = __DURATION__ * 0.82;
      const totalRevealTime = revealEnd - revealStart;
      const numSegs = NUM_LETTERS - 1;
      const segDur = totalRevealTime / numSegs;
      const stepsPerSeg = __STEPS_PER_SEG__;

      for (let i = 0; i < TOTAL_CONTOURS; i++) {
        const segIdx = Math.min(Math.floor(i / stepsPerSeg), numSegs - 1);
        const stepInSeg = i - segIdx * stepsPerSeg;
        const t = revealStart + (segIdx * segDur) + (segDur * stepInSeg) / stepsPerSeg;
        tl.set("#blend-" + i, { autoAlpha: 1 }, t);
      }

      for (let l = 1; l < NUM_LETTERS; l++) {
        const appearTime = revealStart + l * segDur;
        tl.fromTo("#solid-" + l, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.25, ease: "power2.out" }, appearTime);
      }

      window.__timelines = window.__timelines || {};
      window.__timelines["type-trail-design"] = tl;
    })();
    </script>
    </body>
    </html>
    """)

    html = (
        template.replace("__TEXT__", text)
        .replace("__GLYPH_STR__", glyph_str)
        .replace("__W__", str(W))
        .replace("__H__", str(H))
        .replace("__DURATION__", str(int(duration)))
        .replace("__TOTAL_CONTOURS__", str(len(contours)))
        .replace("__NUM_LETTERS__", str(len(solid_letters)))
        .replace("__NUM_SEGS__", str(len(solid_letters) - 1))
        .replace("__STEPS_PER_SEG__", str(steps_per_seg))
        .replace("__BLEND_SVG__", blend_svg)
        .replace("__SOLID_SVG__", solid_svg)
    )

    out = PROJECT_DIR / "index.html"
    out.write_text(html, encoding="utf-8")
    log.info("Saved %s", out)


def generate_preview_html(text: str, duration: float) -> None:
    """Write standalone interactive browser preview page."""
    template = textwrap.dedent("""\
    <!doctype html>
    <html lang="en">
    <head>
    <meta charset="utf-8">
    <title>Type Trail __TEXT__ — Preview v1.1</title>
    <style>
    *{margin:0;padding:0;box-sizing:border-box}
    html,body{background:#111;display:flex;flex-direction:column;align-items:center;
      justify-content:center;min-height:100vh;font-family:system-ui,sans-serif;color:#aaa}
    h1{font-size:14px;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;color:#888}
    .wrap{position:relative;width:__PREV_W__px;height:__PREV_H__px;border:1px solid #333;background:#000}
    iframe{border:none;width:__W__px;height:__H__px;transform-origin:0 0;transform:scale(0.5)}
    .controls{margin-top:16px;display:flex;gap:12px;align-items:center}
    button{background:#222;color:#ccc;border:1px solid #444;padding:6px 16px;cursor:pointer;
      border-radius:4px;font-size:13px}
    button:hover{background:#333}
    input[type=range]{width:280px;accent-color:#666}
    .time{font-size:12px;font-variant-numeric:tabular-nums;min-width:80px;text-align:center}
    </style>
    </head>
    <body>
    <h1>Type Trail __TEXT__ — Blend Poster (v1.1)</h1>
    <div class="wrap">
      <iframe id="comp" src="index.html"></iframe>
    </div>
    <div class="controls">
      <button id="play">▶ Play</button>
      <input id="scrub" type="range" min="0" max="1" step="0.001" value="0">
      <span class="time" id="clock">0.00 / __DURATION_FLOAT__s</span>
    </div>
    <script>
    const iframe = document.getElementById("comp");
    const playBtn = document.getElementById("play");
    const scrub = document.getElementById("scrub");
    const clock = document.getElementById("clock");
    let tl = null, playing = false, raf = null;

    iframe.addEventListener("load", () => {
      const w = iframe.contentWindow;
      const check = setInterval(() => {
        if (w.__timelines && w.__timelines["type-trail-design"]) {
          tl = w.__timelines["type-trail-design"];
          clearInterval(check);
        }
      }, 50);
    });

    playBtn.addEventListener("click", () => {
      if (!tl) return;
      if (playing) {
        playing = false;
        playBtn.textContent = "▶ Play";
        cancelAnimationFrame(raf);
      } else {
        if (tl.progress() >= 1) tl.progress(0);
        playing = true;
        playBtn.textContent = "⏸ Pause";
        const startTime = performance.now() - tl.time() * 1000;
        (function tick(now) {
          if (!playing) return;
          const elapsed = (now - startTime) / 1000;
          if (elapsed >= __DURATION__) {
            tl.progress(1);
            playing = false;
            playBtn.textContent = "▶ Play";
            update();
            return;
          }
          tl.time(elapsed);
          update();
          raf = requestAnimationFrame(tick);
        })(performance.now());
      }
    });

    scrub.addEventListener("input", () => {
      if (!tl) return;
      playing = false;
      playBtn.textContent = "▶ Play";
      cancelAnimationFrame(raf);
      tl.progress(parseFloat(scrub.value));
      update();
    });

    function update() {
      if (!tl) return;
      scrub.value = tl.progress();
      clock.textContent = tl.time().toFixed(2) + " / __DURATION_FLOAT__s";
    }
    </script>
    </body>
    </html>
    """)

    html = (
        template.replace("__TEXT__", text)
        .replace("__PREV_W__", str(W // 2))
        .replace("__PREV_H__", str(H // 2))
        .replace("__W__", str(W))
        .replace("__H__", str(H))
        .replace("__DURATION__", str(int(duration)))
        .replace("__DURATION_FLOAT__", f"{duration:.1f}")
    )

    out = PROJECT_DIR / "preview.html"
    out.write_text(html, encoding="utf-8")
    log.info("Saved %s", out)


# ── Entry point (CLI) ────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Type Trail Blend Poster Generator — v1.1")
    parser.add_argument(
        "--text",
        type=str,
        default="DESIGN",
        help="Text/word to generate blend poster for (default: DESIGN)",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=26,
        help="Intermediate blend steps per segment (default: 26)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=6.0,
        help="Animation duration in seconds (default: 6.0)",
    )
    parser.add_argument(
        "--height",
        type=float,
        default=None,
        help="Cap height in pixels (default: adaptive based on word length)",
    )

    args = parser.parse_args()
    build(
        text=args.text,
        steps_per_seg=args.steps,
        duration=args.duration,
        letter_h=args.height,
    )


if __name__ == "__main__":
    main()
