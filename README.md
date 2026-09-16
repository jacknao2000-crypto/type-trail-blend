# Type Trail Blend 2.0 — 矢量混合动态海报引擎 (Illustrator Blend Tool Engine)

[English Documentation](README_EN.md) · [Live Interactive Showcase / 在线交互体验](https://jacknao2000-crypto.github.io/type-trail-blend/preview.html)

**Type Trail** 是一个由代码与数学驱动的动态矢量混合海报生成引擎，在浏览器与视频渲染中完整复现并革新了 Adobe Illustrator「混合工具 (Blend Tool)」效果。

在 **v2.0 里程碑版本** 中，引擎实现了重大飞跃：**从单闭合西文字母混合，全面突破至中文书法字形拓扑映射、图像化艺术字视觉提取（Computer Vision Trace）以及革新性的「字内 10 步等高线 + 字际流体缎带」双层双重混合机制（Dual-Level Blend）**。

---

## 🌟 Type Trail 2.0 核心突破 (What's New in v2.0)

1. **图形化汉字视觉提取管线（Vision-based Graphical Character Extraction）**：
   - 彻底突破对本地安装字体（TTF/OTF）的依赖；
   - 支持直接从设计师手绘图、海报切片、书法拓片（PNG/JPG）中提取字形，利用自适应二值化、形态学滚轮闭合与 RDP 多边形拟合，自动提取出平滑高保真封闭矢量环。
2. **双层双重混合架构（Dual-Level Blend Engine）**：
   - **微观 Level 1（字内 10 步等高线）**：基于 Shapely 骨架缓冲算法，在每个汉字笔画内部向心生成 **严格 10 层向心同心线束**，形成如同高山等高线、流体波纹般的 3D 浮雕立体质感；
   - **宏观 Level 2（字际流体缎带）**：构建穿越画面的蛇形 S-Curve 动线，跨越多个字符实现连绵不绝的流光缎带混合。
3. **中文拓扑对偶映射（Chinese Vector Morphing）**：
   - 针对中文多环结构，研发了弧长等距重采样与欧氏循环相位极小化算法，实现零扭曲、零打结的汉字字形平滑演进。
4. **全套 HyperFrames 质量门禁认证**：
   - 100% 通过 WCAG AA 文本对比度测试；0 lint 错误；GPU 硬件加速 60fps/30fps 极速 MP4 导出。

---

## 🎨 代表作成果展厅 (Showcase Gallery)

### 1. 旗舰作 03：上善若水 (Shang Shan Ruo Shui) — 图像提取与双层混合
- **技术亮点**：从用户提供的《上善若水》山水海报中自动提取字形；每个汉字包含 **严格 10 层向心等高线（Level 1）**，宏观由 **68 层空间缎带以 S 形蛇形穿插连通（Level 2）**。
- **色彩意境**：青苍（上） $\to$ 翡翠（善） $\to$ 琥珀（若） $\to$ 蔚蓝（水）。

| 7.0 秒动态视频预览 | 1080×1440 最终静态海报 |
| :---: | :---: |
| ![上善若水动态预览](assets/shangshanruoshui_anim.gif) | ![上善若水静态海报](assets/shangshanruoshui_static_poster.png) |

---

### 2. 代表作 02：风水 (Feng Shui) — 中文 TrueType 拓扑矢量混合
- **技术亮点**：解析 SimHei 字库矢量，发现「风」与「水」天然具备 **恰好 2 个独立闭合环** 的对偶特征，实现 1 对 1 纯粹流体变形，32 层细线渐变丝线（气乘风则散，界水则止）。

| 5.0 秒动态视频预览 | 1080×1440 最终静态海报 |
| :---: | :---: |
| ![风水动态预览](assets/fengshui_anim.gif) | ![风水静态海报](assets/fengshui_static_poster.png) |

---

### 3. 代表作 01：DESIGN (Flagship v1.1) — 西文蛇形全词混合
- **技术亮点**：对角 6 字母折返穿插（D → E → S → I → G → N），131 层高精矢量切片，D 字内孔渐进消融矩阵，瑞士国际版式。

| 6.0 秒动态视频预览 | 1080×1440 最终静态海报 |
| :---: | :---: |
| ![DESIGN 动态预览](assets/design_anim.gif) | ![DESIGN 静态海报](assets/design_static_poster.png) |

---

## 📂 项目工程结构

```
type-trail-blend/
├── assets/                          # 高清海报、动态 GIF 与对比图
│   ├── design_static_poster.png
│   ├── design_anim.gif
│   ├── fengshui_static_poster.png
│   ├── fengshui_anim.gif
│   ├── shangshanruoshui_static_poster.png
│   ├── shangshanruoshui_anim.gif
│   └── input_artwork.png            # 原始山水艺术字输入
├── examples/
│   ├── fengshui/                    # 「风水」中文双字完整工程与视频
│   │   ├── build_composition.py
│   │   ├── index.html
│   │   ├── preview.html
│   │   └── type_trail_fengshui.mp4
│   └── shangshanruoshui/            # 「上善若水」图形双层混合工程与视频
│       ├── build_composition.py
│       ├── index.html
│       ├── preview.html
│       └── type_trail_shangshanruoshui.mp4
├── fonts/                           # 本地字体文件
│   └── arialbd.ttf
├── build_composition.py             # 西文任意词汇 CLI 混合脚本 (v1.1)
├── index.html                       # DESIGN 主工程
├── preview.html                     # 多作品交互式三合一播放器 (Showcase v2.0)
├── hyperframes.json                 # 1080x1440 渲染配置
└── README.md                        # 中文文档
```

---

## 🚀 快速上手 (Quick Start)

### 1. 环境准备
```bash
pip install -r requirements.txt  # 或安装: cairo numpy fonttools shapely opencv-python ruff
npm install -g hyperframes       # 安装 HyperFrames 渲染器
```

### 2. 运行示例工程

#### 渲染「上善若水」图形双层混合：
```bash
cd examples/shangshanruoshui
python build_composition.py --inner-steps 10 --seg-steps 22 --duration 7.0
npx hyperframes check
npx hyperframes render --output type_trail_shangshanruoshui.mp4
```

#### 渲染「风水」中文矢量混合：
```bash
cd examples/fengshui
python build_composition.py --steps 30 --duration 5.0 --style gradient
npx hyperframes check
npx hyperframes render --output type_trail_fengshui.mp4
```

#### 渲染西文任意词汇（如 FUTURE）：
```bash
python build_composition.py --text "FUTURE" --steps 26 --duration 6.0
npx hyperframes check
npx hyperframes render --output type_trail_future.mp4
```

---

## 🧮 算法与数学实现原理

1. **图像自适应轮廓提取 (Computer Vision Pipeline)**：
   - 灰度化 $\to$ 自适应阈值二值化 $\to$ 形态学闭合核运算 $\to$ `cv2.findContours`；
   - 结合 **Ramer-Douglas-Peucker (RDP)** 多边形曲线拟合，消除像素阶梯并抽离为数学闭合环。
2. **微观向心等高线算法 (Inward Concentric Skeletons)**：
   - 使用 `shapely.Polygon.buffer(-d)`，在步长 $d \in [0, d_{\max}]$ 产生等距平行内收缩轮廓；
   - 自动识别多凸起断开后的多岛几何（MultiPolygon），保持每个山峰与水纹的层次感。
3. **弧长等距重采样与相位极小化 (Cyclic Phase Minimization)**：
   - 沿累计折线弧长采样 $N$ 个等距点，消除不同线段由于曲率差异导致的密度不均；
   - 求解循环移位量：
     $$\min_{s \in [0, N-1]} \sum_{i=0}^{N-1} \|A_i - B_{(i + s) \bmod N}\|^2$$
     彻底消除多边形过渡时的翻折扭曲。

---

## 📄 开源许可

MIT License © 2026 Type Trail Blend Contributors.
