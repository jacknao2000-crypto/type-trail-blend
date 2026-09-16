# Type Trail DESIGN — Illustrator "Blend Tool" Dynamic Poster

[English](./README_EN.md) | [中文](./README.md) · [Live Interactive Demo](https://jacknao2000-crypto.github.io/type-trail-blend/preview.html)

This project recreates the iconic **Adobe Illustrator "Blend Tool" ribbon effect** across the complete word **"DESIGN"** (**D → E → S → I → G → N**) as a code-driven, high-fidelity dynamic poster. Powered by **HyperFrames**, Python mathematical geometry extraction, arc-length resampling, and cyclic phase alignment, finished with Swiss international style hairline typography.

![Type Trail DESIGN Static Poster](./static_poster.png)

---

## Deliverables & Project Structure

| File | Description |
| :--- | :--- |
| `type_trail_design.mp4` | 6.0s, 30fps, 1080×1440 high-bitrate MP4 video |
| `static_poster.png` | 1080×1440 high-resolution poster (PNG) |
| `preview.html` | Standalone browser player with interactive scrubber slider |
| `index.html` | HyperFrames composition source (DOM + 131 SVG paths + GSAP timeline) |
| `build_composition.py` | Python pipeline: TrueType extraction, morphing, and baking |
| `hyperframes.json` | HyperFrames project configuration (1080x1440, 30fps, 6s) |
| `fonts/arialbd.ttf` | Embedded bold sans-serif typeface (Arial Bold) |
| `snapshots/` | Milestone review snapshots and contact sheets |

---

## Visual Design & Geometry Specifications

1. **Canvas**: 1080 × 1440 portrait, solid pitch-black (`#000000`) background.
2. **Serpentine Diagonal Trajectory** (Anchor centers derived from reference composition):
   - **D**: `(677, 251)`, cap height 165px (top-right)
   - **E**: `(351, 475)`, cap height 165px (top-left)
   - **S**: `(861, 576)`, cap height 165px (mid-right)
   - **I**: `(355, 851)`, cap height 165px (mid-left)
   - **G**: `(774, 1008)`, cap height 165px (lower-right)
   - **N**: `(469, 1233)`, cap height 165px (bottom-left)
3. **Wireframe Ribbon Contours**:
   - 5 transition segments: `D → E`, `E → S`, `S → I`, `I → G`, `G → N`.
   - 26 intermediate steps per segment = **131 total SVG contour layers**.
   - Stroke: `1.0px`, soft white (`rgba(255, 255, 255, 0.65)`), fill none.
4. **Top-Layer Solid Masks**:
   - 6 solid pure white (`#ffffff`) letters overlaid on top.
   - D employs the `evenodd` fill rule to preserve its counter hole (letting the background ribbon show through), while the solid glyph stems cleanly occlude the wireframe lines underneath.
5. **Swiss International Corner Typography**:
   - Hairline `0.75px` rules, registration crosshairs (`+`), and technical metadata in all four corners for a contemporary editorial aesthetic.

---

## Animation Timeline (6.0 Seconds)

- **0.0s – 0.4s**: Corner hairline graphics and typography fade in; solid D appears.
- **0.4s – 1.3s**: Ribbon sweeps from D to E; solid E lights up at `1.3s`.
- **1.3s – 2.2s**: Ribbon sweeps across from E to S; solid S lights up at `2.2s`.
- **2.2s – 3.1s**: Ribbon curves from S down into I; solid I lights up at `3.1s`.
- **3.1s – 4.0s**: Ribbon unfolds into G's circular bowl; solid G lights up at `4.0s`.
- **4.0s – 4.9s**: Ribbon charges diagonally into N; final solid N lights up at `4.9s`.
- **4.9s – 6.0s**: Complete poster of 131 contour layers and 6 solid letters fully locked in static hold.

---

## Core Algorithmic Implementation

### 1. Sub-pixel TrueType Bézier Extraction
Using `fontTools` and `pycairo`, native quadratic B-splines from `arialbd.ttf` are flattened into continuous closed polygon loops with curvature-adaptive precision, preserving sharp architectural corners.

### 2. Centroid Normalization & Uniform Arc-length Resampling
Each glyph outline is normalized to its bounding box centroid `(0, 0)` and resampled into $N = 500$ equidistant vertices by cumulative polyline arc length.

### 3. Cyclic Phase Shift Minimization
To eliminate vertex twisting and polygon self-intersection between radically different topologies (e.g. 3-arm E to sinuous S):
$$\min_{s \in [0, N-1]} \sum_{i=0}^{N-1} \|A_i - B_{(i + s) \bmod N}\|^2$$
The optimal cyclic shift $s$ is computed via circular distance minimization, guaranteeing smooth, untangled transitional vectors.

### 4. Topological Counter Collapse
Letter D is Genus 1 (has an inner hole), whereas E, S, I, G, N are Genus 0 (single boundary). The hole is isolated as an independent sub-path in segment $D \to E$ and linearly scaled down to zero towards its centroid over $t \in [0, 0.90]$, emulating Illustrator's counter interpolation behavior.

### 5. Deterministic Baked DOM + GPU Acceleration
All 131 contour paths are pre-computed into static SVG paths inside `index.html`. GSAP drives discrete visibility states, ensuring 100% deterministic frame rendering during scrubbing, seeking, and GPU video export.

---

### Quick Start & Regeneration (v1.1)

```bash
# 1. Clone the repository
git clone https://github.com/jacknao2000-crypto/type-trail-blend.git
cd type-trail-blend

# 2. Generate the default "DESIGN" flagship poster
python build_composition.py

# 3. (NEW in v1.1) Generate blend posters for ANY custom word:
python build_composition.py --text "FUTURE"
python build_composition.py --text "MOTION" --steps 30 --duration 7.0
python build_composition.py --text "CREATIVE"

# 4. Render high-res MP4 video via HyperFrames CLI:
npx hyperframes render --quality high --output my_custom_poster.mp4

# 5. Preview locally:
# Open preview.html directly in any browser!
```

---

## What's New in v1.1

- **Arbitrary Text Support (`--text`)**: Feed any English word (e.g. `FUTURE`, `MOTION`, `ART`) directly via CLI.
- **Adaptive Serpentine Layout**: Dynamically computes optimal zigzag coordinates based on character count.
- **Universal Multi-hole Morphing**: Automatically detects glyph counters (A, B, D, O, P, Q, R, 0, 8, etc.) and smoothly interpolates topological inner boundaries without self-intersection.
- **Dynamic Corner Metadata**: Four-corner Swiss editorial metadata automatically reflects the active text and contour count.

---

## License

MIT License. Open for educational, creative coding, and experimental typography exploration.
