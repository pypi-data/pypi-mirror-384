# ✂️ MediaCrop - Visual FFmpeg Crop Tool

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/mediacrop.svg)](https://pypi.org/project/mediacrop/)
[![Downloads](https://static.pepy.tech/badge/mediacrop)](https://pepy.tech/project/mediacrop)
[![Last Commit](https://img.shields.io/github/last-commit/mallikmusaddiq1/mediacrop.svg)](https://github.com/mallikmusaddiq1/mediacrop/commits/main)
[![Stars](https://img.shields.io/github/stars/mallikmusaddiq1/mediacrop.svg)](https://github.com/mallikmusaddiq1/mediacrop/stargazers)
[![Instagram](https://img.shields.io/badge/Instagram-%40musaddiq.x7-E4405F?logo=instagram\&logoColor=white)](https://instagram.com/musaddiq.x7)

---

## 🧩 Overview

**MediaCrop** is a modern, lightweight **web-based visual tool** that allows you to get **FFmpeg crop coordinates** for any media file — whether it's a video, image, or even audio waveform — without the guesswork. Simply drag, resize, and instantly get your precise FFmpeg crop string.

The tool spins up a local web server, launching a sleek, dark-themed, and responsive interface right in your browser — delivering a fast, intuitive, and enjoyable user experience.

---

## 📖 The Story Behind MediaCrop

Working with **FFmpeg** is undeniably powerful, but often not straightforward. One of the most frustrating challenges for many users has always been **identifying the correct crop coordinates**. The typical workflow used to involve:

* Opening the file in a media player.
* Guessing coordinates by eye.
* Running the FFmpeg command.
* Repeating — again and again.

This repetitive trial-and-error method consumed valuable time and patience. It felt like trying to carve glass in the dark — each mistake meant starting from scratch.

**MediaCrop** was born from that frustration — designed as a **visual, drag-and-drop solution** to eliminate the struggle. You simply draw a box, and the tool instantly gives you an **FFmpeg-ready crop filter string**. No stress. No repetition. Just **pure accuracy with ease**.

Now, FFmpeg finally feels accessible, fluid, and precise — the way it was meant to be.

---

## 🖼️ Screenshot

A modern dark-themed interface, responsive across devices.

![MediaCrop Desktop Screenshot](Screenshots/Screenshot-1080x1979.png)

---

## ✨ Features

| Category      | Feature                              | Description                                                              |
| :------------ | :----------------------------------- | :----------------------------------------------------------------------- |
| **Interface** | 🌐 **Modern Web UI**                 | Elegant dark-themed interface accessible directly via your browser.      |
|               | 📱 **Fully Responsive**              | Works seamlessly on desktop, tablet, and mobile devices.                 |
|               | ⚙️ **Server Status Indicator (New)** | Real-time visual indicator showing backend status.                       |
| **Cropping**  | 🖱️ **Interactive Crop Box**         | Move and resize with 8 precision handles.                                |
|               | 📐 **Aspect Ratio Presets**          | Lock to standard or custom ratios: *16:9, 4:3, 1:1, Cinemascope,* etc.   |
|               | 🔄 **Rotation Alignment (New)**      | Quickly rotate by *90°, 180°, or 270°*.                                  |
| **Precision** | 📊 **Live Info Panel**               | Displays coordinates *(X, Y)*, width, height, and aspect ratio.          |
|               | ⌨️ **Keyboard Controls**             | Pixel-perfect movement and resizing via arrow keys.                      |
|               | 🎯 **Quick Center Button**           | Instantly centers the crop area.                                         |
| **Usability** | 🔧 **Quick Tools**                   | Toggle grid, reset, and center tools for efficient editing.              |
|               | 🖱️ **Context Menu**                 | Right-click the crop box for fast action access.                         |
|               | ✅ **Broad Format Support**           | Supports visual preview for multiple formats or manual coordinate entry. |
| **System**    | 🚀 **Zero Dependencies**             | Runs on Python’s standard library — no external installs required.       |
|               | 💻 **Cross-Platform**                | Works flawlessly on Windows, macOS, and Linux.                           |

---

### 🧠 Supported Preview Formats

MediaCrop can compute coordinates for **any FFmpeg-compatible file**, while offering in-browser preview for the following:

* **Images:** JPG, PNG, WEBP, AVIF, GIF, BMP, SVG, ICO
* **Videos:** MP4, WEBM, MOV, OGV
* **Audio:** MP3, WAV, FLAC, OGG, M4A, AAC, OPUS

---

## ⚙️ Installation

Requires **Python 3.7+**.

### Option 1: From PyPI (Recommended)

```bash
pip install mediacrop
```

### Option 2: From Source

```bash
# Clone the repository
git clone https://github.com/mallikmusaddiq1/mediacrop.git

# Navigate into the directory
cd mediacrop

# Install locally
pip install .
```

---

## 🚀 Usage

```bash
mediacrop "/path/to/your/mediafile.mp4"
```

* Use quotes if your path contains spaces.
* Your browser opens automatically at: `http://127.0.0.1:8000`.
* Adjust crop visually, apply ratio presets, or use grid tools.
* Click **Save Coordinates** to confirm.

  * A success notification will appear.
  * The FFmpeg crop string prints in the terminal.
* Press `Ctrl + C` to stop the server.

### Command-Line Options

| Option                        | Description                          |
| :---------------------------- | :----------------------------------- |
| `-p <port>` / `--port <port>` | Use a specific port (default: 8000). |
| `-v` / `--verbose`            | Enable detailed logs.                |
| `-h` / `--help`               | Display help message.                |

---

## 🎬 Using Output with FFmpeg

MediaCrop produces a ready-to-use crop string:

```bash
ffmpeg crop string: crop=1280:720:320:180
```

Apply it directly:

```bash
ffmpeg -i input.mp4 -vf "crop=1280:720:320:180" output_cropped.mp4
```

---

## ⌨️ Controls & Shortcuts

| Action           | Shortcut                    |
| :--------------- | :-------------------------- |
| Move Crop Box    | Click + Drag / Arrow Keys   |
| Fine Move (1px)  | Shift + Arrow Keys          |
| Resize Crop Box  | Drag edges or corners       |
| Toggle Grid      | G or 📐 Grid button         |
| Center Box       | C or 🎯 Center button       |
| Save Coordinates | Enter or 💾 Save button     |
| Toggle Help      | ❓ or Esc to close           |
| Context Menu     | Right-click on the crop box |

---

## 🤝 Contributing

Contributions are welcome and encouraged! Whether it’s a **bug fix, feature addition, or documentation improvement**, your input helps refine and expand MediaCrop.

### How to Contribute:

1. Fork this repository.
2. Create a new branch for your fix or feature.
3. Commit with a clear, descriptive message.
4. Open a Pull Request.

If you find value in this project, don’t forget to **star ⭐ it on GitHub** — every star fuels motivation for further development.

---

## 👨‍💻 Author Info

👤 **Name:** Mallik Mohammad Musaddiq

📧 **Email:** [mallikmusaddiq1@gmail.com](mailto:mallikmusaddiq1@gmail.com)

🌐 **GitHub:** [mallikmusaddiq1](https://github.com/mallikmusaddiq1)

🔗 **Project Repo:** [mallikmusaddiq1/mediacrop](https://github.com/mallikmusaddiq1/mediacrop)

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.