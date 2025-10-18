# ✂️ MediaCrop - Visual FFmpeg Crop Tool

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/mediacrop.svg)](https://pypi.org/project/mediacrop/)
[![Downloads](https://static.pepy.tech/badge/mediacrop)](https://pepy.tech/project/mediacrop)
[![Last Commit](https://img.shields.io/github/last-commit/mallikmusaddiq1/mediacrop.svg)](https://github.com/mallikmusaddiq1/mediacrop/commits/main)
[![Stars](https://img.shields.io/github/stars/mallikmusaddiq1/mediacrop.svg)](https://github.com/mallikmusaddiq1/mediacrop/stargazers)
[![Instagram](https://img.shields.io/badge/Instagram-%40musaddiq.x7-E4405F?logo=instagram\&logoColor=white)](https://instagram.com/musaddiq.x7)

**MediaCrop** is a modern, lightweight, web-based visual tool that helps you get FFmpeg crop coordinates for any media file (video, image, or audio) with zero guesswork. Just drag, resize, and get the exact crop string you need.

The tool runs a local server and opens a sleek, responsive interface in your browser, providing an intuitive and powerful user experience.

---

## 📖 The Story Behind MediaCrop

Working with **FFmpeg** is powerful, but not always simple. One of the most frustrating parts for many users is **finding the right crop coordinates**. Traditionally, this involved a tedious cycle of:

* Opening the media in a player.
* Guessing the pixel coordinates.
* Running the FFmpeg command.
* Repeating until it looked right.

This trial-and-error process wastes time and energy. People would spend hours tweaking numbers blindly, feeling stuck between the complexity of FFmpeg and the lack of a simple GUI. It was like trying to cut glass in the dark—every small mistake meant starting over.

I created **MediaCrop** to solve this exact pain. A **visual, drag-and-drop solution** that ends the frustration. With MediaCrop, you just draw a box, and the tool gives you the **FFmpeg-ready crop filter string**. No stress. No repeated guessing. Just **precision with ease**.

And that is why users across platforms have found it a relief—because finally, FFmpeg feels less like a maze and more like a tool you can actually control.

---

## 🖼️ MediaCrop Desktop Screenshot

A modern, dark-themed interface that's fully responsive and works on any device.

![MediaCrop Desktop Screenshot](Screenshots/Screenshot-1080x1979.png)

---

## ✨ Features

* **🌐 Modern Web Interface:** Sleek, dark-themed UI that runs in your browser. No extra GUI installation needed.
* **📱 Fully Responsive:** Works seamlessly on both desktop and mobile devices.
* **🖱️ Interactive Crop Box:** Drag to move and resize with 8 handles for precision.
* **📐 Advanced Aspect Ratios:** Lock the crop box to presets like 16:9, 4:3, 1:1, Cinemascope, or custom ratios.
* **📊 Live Info Panel:** Instantly see crop box position (X, Y), size, and aspect ratio.
* **🔧 Quick Tools:** One-click to center, toggle grid, reset selection, or view help.
* **⌨️ Full Keyboard Control:** Pixel-perfect adjustments with arrow keys and shortcuts.
* **🖱️ Context Menu:** Right-click for quick access to common actions.
* **✅ Broad Format Support:** Preview many common media formats, or set coordinates even if preview is unsupported.
* **🚀 Zero Dependencies:** Pure Python standard library. No external `pip` installs required.
* **💻 Cross-Platform:** Works on Windows, macOS, and Linux.

---

### Supported Preview Formats

MediaCrop can generate coordinates for **any** file FFmpeg supports, but provides in-browser preview for these formats:

* **Images:** `JPG`, `PNG`, `WEBP`, `AVIF`, `GIF`, `BMP`, `SVG`, `ICO`
* **Videos:** `MP4`, `WEBM`, `MOV`, `OGV`
* **Audio:** `MP3`, `WAV`, `FLAC`, `OGG`, `M4A`, `AAC`, `OPUS`

---

## ⚙️ Installation

You only need **Python 3.7+** installed on your system.

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

Using the tool is simple:

```bash
mediacrop "/path/to/your/mediafile.mp4"  
```

* Use quotes `""` if the path contains spaces.
* Your default browser will open at [http://127.0.0.1:8000](http://127.0.0.1:8000).
* Adjust the crop box visually, apply aspect ratio presets, grid, and tools as needed.
* Click **Save Coordinates**:

  * A notification will confirm success.
  * The crop filter string is printed in the terminal.
* Press **Ctrl+C** to stop the server.

### Command-Line Options

* `-p <port>`, `--port <port>`: Use a specific port (default: 8000).
* `-v`, `--verbose`: Show detailed server logs.
* `-h`, `--help`: Show help message.

---

## 🎬 Using the Output with FFmpeg

MediaCrop provides a perfectly formatted FFmpeg crop string.

**Example Output:**

Use it with FFmpeg:

```bash
ffmpeg -i input.mp4 -vf "crop=1280:720:320:180" output_cropped.mp4  
```

---

## ⌨️ Controls & Shortcuts

| Action           | Control                        |
| ---------------- | ------------------------------ |
| Move Crop Box    | Click & Drag / Arrow Keys      |
| Fine Move (1px)  | Shift + Arrow Keys             |
| Resize Crop Box  | Drag one of the 8 handles      |
| Toggle Grid      | `G` or 📐 Grid button          |
| Center Crop Box  | `C` or 🎯 Center button        |
| Save Coordinates | `Enter` or 💾 Save button      |
| Open/Close Help  | ❓ Help button / `Esc` to close |
| Context Menu     | Right-click on crop box        |

---

## 🤝 Contribution

Contributions are more than welcome! If you find bugs, want new features, or have ideas to improve MediaCrop, feel free to:

1. **Fork** the repository.
2. **Create** a new branch with your feature or fix.
3. **Commit** your changes with clear messages.
4. **Open a Pull Request**.

Every contribution matters, whether it’s a bug fix, feature request, or even just improving the documentation. Together, we can make MediaCrop the go-to visual tool for FFmpeg lovers.

If you like this project, don’t forget to **leave a star ⭐** on GitHub—it really helps the project grow and motivates further development!

---

## 👨‍💻 Author Info:

👤 Name:
**Mallik Mohammad Musaddiq**

📧 Email:
[mallikmusaddiq1@gmail.com](mailto:mallikmusaddiq1@gmail.com)

🌐 GitHub:
[mallikmusaddiq1](https://github.com/mallikmusaddiq1)

🔗 Project Repo:
[mallikmusaddiq1/mediacrop](https://github.com/mallikmusaddiq1/mediacrop)

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.