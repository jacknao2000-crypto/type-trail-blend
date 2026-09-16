# Type Trail Blend 2.0 — Dynamic Vector Morphing & Poster Engine

[中文说明](README.md) · [Live Interactive Showcase](https://jacknao2000-crypto.github.io/type-trail-blend/preview.html)

**Type Trail** is a math-driven, code-crafted dynamic vector ribbon poster engine that recreates and evolves the iconic **Adobe Illustrator "Blend Tool"** effect inside the modern web browser and headless rendering pipelines.

In **v2.0 (Major Milestone Release)**, the engine advances from Latin alphabet blending to **Chinese Calligraphic Vector Morphing, Vision-based Graphic Character Extraction, and a pioneering "Dual-Level Blend" architecture (10-Step Inward Topographic Relief + Inter-Character Serpentine Blend)**.

---

## 🌟 What's New in v2.0

1. **Vision-based Graphic Character Extraction**:
   - Eliminates the dependency on installed font files (TTF/OTF).
   - Extracts vector contours directly from raster artwork, poster cutouts, and calligraphy images (PNG/JPG) using adaptive thresholding, morphological closing, and Ramer-Douglas-Peucker (RDP) polygon approximation.
2. **Dual-Level Blend Engine**:
   - **Micro Level 1 (10-Step Inner Topographic Blend)**: Uses Shapely polygon skeletal buffering to compute **strictly 10 concentric inward contour rings** inside each character stroke, generating tactile 3D relief like mountain topographic maps and water currents.
   - **Macro Level 2 (Inter-Character Fluid Ribbon)**: Traverses the canvas along a dynamic serpentine S-curve trajectory to interpolate continuously across multiple characters.
3. **Chinese TrueType Morphing & Topological Pairing**:
   - Employs arc-length uniform resampling and cyclic Euclidean phase minimization to achieve clean, twist-free morphing between complex Chinese glyphs (e.g. 「风水」).
4. **HyperFrames CI/CD Compliance**:
   - 100% WCAG AA contrast pass rate, 0 lint errors, GPU hardware-accelerated 60fps/30fps MP4 export.

---

## 🎨 Showcase Gallery

### 1. Flagship 03: 上善若水 (Shang Shan Ruo Shui) — Dual-Level Graphic Blend
- **Highlights**: Extracted from mountain-water graphic artwork; features **strictly 10 inner concentric contours per stroke (Level 1)**, connected by a **68-layer spatial serpentine ribbon (Level 2)**.
- **Palette**: Celestial Cyan (上) $\to$ Jade Emerald (善) $\to$ Amber Gold (若) $\to$ Azure Blue (水).

| 7.0s Dynamic Video Preview | 1080×1440 Static Poster |
| :---: | :---: |
| ![Shang Shan Ruo Shui Preview](assets/shangshanruoshui_anim.gif) | ![Shang Shan Ruo Shui Poster](assets/shangshanruoshui_static_poster.png) |

---

### 2. Showcase 02: 风水 (Feng Shui) — Chinese TTF Morphing
- **Highlights**: Dual-loop 1-to-1 correspondence between SimHei glyphs 「风」 and 「水」 (Wind into Water), with 32 aerodynamic gradient contour layers.

| 5.0s Dynamic Video Preview | 1080×1440 Static Poster |
| :---: | :---: |
| ![Feng Shui Preview](assets/fengshui_anim.gif) | ![Feng Shui Poster](assets/fengshui_static_poster.png) |

---

### 3. Showcase 01: DESIGN (v1.1) — Latin Serpentine Blend
- **Highlights**: Diagonal 6-letter cascade (D → E → S → I → G → N), 131 vector contour layers, D counter hole fade matrix, and Swiss typographic grid.

| 6.0s Dynamic Video Preview | 1080×1440 Static Poster |
| :---: | :---: |
| ![DESIGN Preview](assets/design_anim.gif) | ![DESIGN Poster](assets/design_static_poster.png) |

---

## 📂 Repository Structure

```
type-trail-blend/
├── assets/                          # Posters, animated GIFs & contact sheets
│   ├── design_static_poster.png
│   ├── design_anim.gif
│   ├── fengshui_static_poster.png
│   ├── fengshui_anim.gif
│   ├── shangshanruoshui_static_poster.png
│   ├── shangshanruoshui_anim.gif
│   └── input_artwork.png
├── examples/
│   ├── fengshui/                    # Standalone "Feng Shui" project & video
│   └── shangshanruoshui/            # Standalone "Shang Shan Ruo Shui" project & video
├── fonts/                           # Embedded typefaces
├── build_composition.py             # Latin CLI blend generator
├── preview.html                     # 3-in-1 interactive showcase player
├── hyperframes.json                 # 1080x1440 composition config
└── README.md                        # Documentation
```

---

## 🚀 Quick Start

### 1. Requirements
```bash
pip install -r requirements.txt  # cairo, numpy, fonttools, shapely, opencv-python, ruff
npm install -g hyperframes
```

### 2. Generate and Render Examples

#### Render Shang Shan Ruo Shui (Dual-Level Blend):
```bash
cd examples/shangshanruoshui
python build_composition.py --inner-steps 10 --seg-steps 22 --duration 7.0
npx hyperframes check
npx hyperframes render --output type_trail_shangshanruoshui.mp4
```

#### Render Feng Shui (Chinese Vector Morph):
```bash
cd examples/fengshui
python build_composition.py --steps 30 --duration 5.0 --style gradient
npx hyperframes check
npx hyperframes render --output type_trail_fengshui.mp4
```

#### Render Any Latin Word (e.g. MOTION):
```bash
python build_composition.py --text "MOTION" --steps 26 --duration 6.0
npx hyperframes check
npx hyperframes render --output type_trail_motion.mp4
```

---

## 🧮 Algorithmic Principles

1. **Vision-based Polygon Extraction**:
   - Grayscale $\to$ Adaptive Threshold $\to$ Morphological Closing $\to$ `cv2.findContours`.
   - Ramer-Douglas-Peucker (RDP) polygon approximation to yield sub-pixel vector loops.
2. **Inward Topographic Skeletal Buffering**:
   - `shapely.Polygon.buffer(-d)` over equidistant steps $d \in [0, d_{\max}]$ producing parallel contour rings with automatic multi-component splitting.
3. **Uniform Arc-length Resampling & Cyclic Phase Alignment**:
   - Polyline arc-length re-parameterization to eliminate speed distortion.
   - Closed-form phase shift search:
     $$\min_{s \in [0, N-1]} \sum_{i=0}^{N-1} \|A_i - B_{(i + s) \bmod N}\|^2$$
     guaranteeing twist-free, knot-free geometric morphing.

---

## 📄 License

MIT License © 2026 Type Trail Blend Contributors.
