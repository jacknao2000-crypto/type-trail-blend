<div align="center">

# 🌊 Type Trail Blend 2.0
### Dynamic Vector Morphing Poster Engine · Code Reconstruction of Adobe Illustrator "Blend Tool"

[🇬🇧 English](README_EN.md) · [🇨🇳 中文文档](README.md) · [🌐 Live Interactive Showcase](https://jacknao2000-crypto.github.io/type-trail-blend/preview.html)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://python.org)
[![Rendered with HyperFrames](https://img.shields.io/badge/Rendered%20with-HyperFrames-orange.svg)](https://hyperframes.org)
[![Accessibility: WCAG AA](https://img.shields.io/badge/Accessibility-WCAG%20AA%20Passed-success.svg)](#)

<br/>

| 01. DESIGN (Latin Serpentine) | 02. Feng Shui (Chinese TTF) | 03. Shang Shan Ruo Shui (Dual Blend) |
| :---: | :---: | :---: |
| <img src="assets/design_anim.gif" width="240" /> | <img src="assets/fengshui_anim.gif" width="240" /> | <img src="assets/shangshanruoshui_anim.gif" width="240" /> |
| **6-Letter Latin Word Cascade** | **SimHei 2-Loop Topological Morph** | **Vision Extraction + 10-Step Inner Relief** |

</div>

---

## 📖 Introduction

**Type Trail** is a math-driven, code-crafted dynamic vector ribbon poster engine that recreates and elevates the iconic **Adobe Illustrator "Blend Tool"** effect directly inside web browsers (SVG + GSAP) and headless video rendering pipelines (HyperFrames).

In the **v2.0 Milestone Release**, the engine transcends traditional typography limits: evolving from single-contour Latin letterforms into **Chinese Calligraphic Vector Morphing, Vision-based Graphical Character Extraction (Computer Vision Pipeline), and a groundbreaking "Dual-Level Blend" architecture (10-Step Inward Topographic Relief + Inter-Character Serpentine Ribbon)**.

---

## 🌟 What's New in v2.0

| Feature | v1.1 (Latin Base) | **v2.0 (Major Milestone)** |
| :--- | :--- | :--- |
| **Language Support** | ASCII Latin characters only | **Full coverage: Latin + Chinese TTF fonts + Hand-drawn / Graphic Artwork** |
| **Glyph Sourcing** | Requires local TTF/OTF fonts | **Computer Vision Extraction**: Extracts sub-pixel vector loops directly from raster artwork (PNG/JPG) |
| **Blend Depth** | Single macro spatial ribbon | **Dual-Level Blend Engine**:<br>• Micro: **Strictly 10-step inward topographic relief**<br>• Macro: Inter-character S-curve fluid ribbons |
| **Topological Mapping** | Centroid alignment + simple hole collapse | **Multi-loop dual correspondence + Arc-length resampling + Cyclic Euclidean phase minimization** |
| **Color System** | Monochrome silver wireframe | **Five-Element Oriental Gradient Palette** (Celestial Cyan, Jade, Amber, Azure) + Swiss typography |
| **Production CI/CD** | Basic checks | **HyperFrames Certified** (60/60 text checks pass WCAG AA, 0 lint errors, GPU export) |

---

## 🎨 Showcase Gallery

### 1. Flagship 03: 【Shang Shan Ruo Shui (上善若水)】— Vision Extraction & Dual-Level Blend (New in v2.0)
- **Concept**: Rooted in Laozi's Dao De Jing (Chapter 08): *"Highest virtue is like water, benefiting all things without contention."*
- **Technical Highlights**:
  - **Raster to Vector Extraction**: Automatically extracts closed stroke contours from user-provided graphic artwork;
  - **Micro Level 1**: Computes **strictly 10 inward concentric buffer contours** per stroke, yielding tactile 3D topographic relief;
  - **Macro Level 2**: Connects the 4 characters along a **68-layer spatial serpentine ribbon**;
  - **Palette Flow**: Celestial Cyan (上) $\to$ Jade Emerald (善) $\to$ Amber Gold (若) $\to$ Azure Blue (水).

| 7.0s Dynamic Fluid Video | 1080×1440 Final Static Poster |
| :---: | :---: |
| ![Shang Shan Ruo Shui Preview](assets/shangshanruoshui_anim.gif) | ![Shang Shan Ruo Shui Poster](assets/shangshanruoshui_static_poster.png) |

---

### 2. Showcase 02: 【Feng Shui (风水)】— Chinese TrueType Topological Morph (New in v2.0)
- **Highlights**: Discovered that SimHei glyphs 「风」 and 「水」 possess **exactly 2 closed loops**, allowing 1-to-1 pure fluid morphing across 32 aerodynamic gradient contour layers.

| 5.0s Dynamic Fluid Video | 1080×1440 Final Static Poster |
| :---: | :---: |
| ![Feng Shui Preview](assets/fengshui_anim.gif) | ![Feng Shui Poster](assets/fengshui_static_poster.png) |

---

### 3. Showcase 01: 【DESIGN】— Latin Serpentine Word Blend (v1.1 Benchmark)
- **Highlights**: Diagonal 6-letter cascade (D → E → S → I → G → N), 131 vector contour layers, D counter hole progressive collapse matrix, Swiss typographic grid.

| 6.0s Dynamic Fluid Video | 1080×1440 Final Static Poster |
| :---: | :---: |
| ![DESIGN Preview](assets/design_anim.gif) | ![DESIGN Poster](assets/design_static_poster.png) |

---

## 📂 Repository Structure

```
type-trail-blend/
├── assets/                          # Animations, posters & graphical assets
│   ├── design_static_poster.png
│   ├── design_anim.gif
│   ├── fengshui_static_poster.png
│   ├── fengshui_anim.gif
│   ├── shangshanruoshui_static_poster.png
│   ├── shangshanruoshui_anim.gif
│   └── input_artwork.png            # Original artwork input
├── examples/
│   ├── fengshui/                    # Standalone "Feng Shui" project & video
│   │   ├── build_composition.py
│   │   ├── index.html
│   │   ├── preview.html
│   │   ├── static_poster.png
│   │   └── type_trail_fengshui.mp4
│   └── shangshanruoshui/            # Standalone "Shang Shan Ruo Shui" project & video
│       ├── build_composition.py
│       ├── index.html
│       ├── preview.html
│       ├── static_poster.png
│       └── type_trail_shangshanruoshui.mp4
├── fonts/                           # Embedded typefaces
├── build_composition.py             # Arbitrary Latin text blend generator (v1.1)
├── index.html                       # Primary composition entry point
├── preview.html                     # 3-in-1 interactive showcase player
├── hyperframes.json                 # 1080x1440 composition configuration
├── requirements.txt                 # Python dependencies
├── LICENSE                          # MIT License
├── README.md                        # Chinese Documentation
└── README_EN.md                     # English Documentation
```

---

## 🚀 Quick Start

### 1. Prerequisites
```bash
git clone https://github.com/jacknao2000-crypto/type-trail-blend.git
cd type-trail-blend

# Install Python dependencies
pip install -r requirements.txt

# Install HyperFrames renderer (optional, for MP4 export)
npm install -g hyperframes
```

### 2. Generate and Render Showcase Examples

#### Render Shang Shan Ruo Shui (Graphical Dual-Level Blend):
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

#### Render Any Latin Word (e.g. FUTURE or MOTION):
```bash
python build_composition.py --text "FUTURE" --steps 26 --duration 6.0
npx hyperframes check
npx hyperframes render --output type_trail_future.mp4
```

### 3. Interactive Web Showcase
Open `preview.html` directly in any modern browser to experience the interactive 3-in-1 player with instant tab-switching, timeline scrubbing, and sub-frame precision playback!

---

## 🧮 Mathematical & Computational Geometry

1. **Vision-based Contour Extraction**:
   - Image $\to$ Grayscale $\to$ Adaptive Otsu Thresholding $\to$ Morphological Closing $\to$ `cv2.findContours`.
   - Ramer-Douglas-Peucker (RDP) algorithm simplifies stair-stepped pixels into sub-pixel closed polygonal loops.
2. **Inward Topographic Skeletal Buffering**:
   - `shapely.Polygon.buffer(-d)` over steps $d \in [0, d_{\max}]$ produces equidistant inward contours, preserving multi-component separation (MultiPolygon) to generate authentic landscape relief.
3. **Uniform Arc-Length Resampling**:
   - Polyline arc-length parameterization resamples $N$ equidistant vertices, removing velocity distortion caused by local curvature variations.
4. **Cyclic Euclidean Phase Minimization**:
   - Computes optimal cyclic shift between contours $A$ and $B$:
     $$\min_{s \in [0, N-1]} \sum_{i=0}^{N-1} \|A_i - B_{(i + s) \bmod N}\|^2$$
     preventing twisting, pinching, or self-intersections during morphing.

---

## 📄 License

Distributed under the [MIT License](LICENSE).
