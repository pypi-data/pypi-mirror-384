#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import time
import mimetypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse


# Set a more comprehensive list of mimetypes
mimetypes.init()
mimetypes.add_type('image/avif', '.avif')
mimetypes.add_type('video/quicktime', '.mov')
mimetypes.add_type('audio/mp4', '.m4a')
mimetypes.add_type('audio/flac', '.flac')
mimetypes.add_type('audio/aac', '.aac')
mimetypes.add_type('audio/opus', '.opus')


class CropHandler(BaseHTTPRequestHandler):
    """
    A custom HTTP request handler for serving media files and handling crop operations.
    Includes enhancements for file streaming, range requests (seeking), and verbose logging.
    """

    def log_message(self, format, *args):
        """Suppress logging if verbose is false."""
        if self.server.verbose:
            super().log_message(format, *args)

    def _get_media_type_info(self, file_path):
        """Determines media type and HTML tag based on file extension."""
        ext = os.path.splitext(file_path)[1].lower()

        # Formats that are natively supported by most modern web browsers
        supported_image_exts = [
            ".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".svg", ".ico", ".avif", ".tiff", ".tif", ".heic", ".heif", ".jxl"
        ]
        
        supported_video_exts = [
            ".mp4", ".webm", ".ogv", ".mov"
        ]
        
        supported_audio_exts = [
            ".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac", ".opus"
        ]

        cache_buster = int(time.time())
        media_tag = ""
        media_type = ""
        controls_html = ""

        if ext in supported_image_exts:
            media_tag = f'<img id="media" src="/file?v={cache_buster}" onload="initializeCrop()" draggable="false" alt="Media file" />'
            media_type = "image"
        elif ext in supported_video_exts:
            # Added "controls" attribute to video tag for native fallback, though custom controls are preferred.
            media_tag = f'<video id="media" preload="metadata" src="/file?v={cache_buster}" onloadedmetadata="initializeCrop()" draggable="false"></video>'
            media_type = "video"
            controls_html = '''
<div class="video-controls" id="videoControls">
  <button id="playPause" class="control-btn" title="Play/Pause">▶️</button>
  <div class="progress-container">
    <span id="currentTime">0:00</span>
    <input type="range" id="seekBar" class="seek-bar" min="0" max="100" value="0" step="any">
    <span id="duration">0:00</span>
  </div>
  <select id="playbackSpeed" class="control-select" title="Playback Speed">
    <option value="0.5">0.5x</option>
    <option value="0.75">0.75x</option>
    <option value="1" selected>1x</option>
    <option value="1.25">1.25x</option>
    <option value="1.5">1.5x</option>
    <option value="1.75">1.75x</option>
    <option value="2">2x</option>
  </select>
  <div class="volume-container">
    <button id="muteBtn" class="control-btn" title="Mute/Unmute">🔊</button>
    <input type="range" id="volumeBar" class="volume-bar" min="0" max="100" value="100" step="1" title="Volume">
  </div>
</div>'''
        elif ext in supported_audio_exts:
            # Audio media doesn't need to be wrapped with crop logic initially, but needs controls
            media_tag = f'<audio id="media" controls preload="metadata" src="/file?v={cache_buster}" onloadedmetadata="initializeCrop()"></audio>'
            media_type = "audio"
            # No custom controls for audio, rely on native 'controls' attribute or a simpler message
            media_tag = f'<audio id="media" controls preload="metadata" src="/file?v={cache_buster}" onloadedmetadata="initializeCrop()"></audio>'
            media_type = "audio"
            controls_html = "" # Custom controls removed, relying on native controls embedded in the tag for audio

        else:
            # Fallback for formats not previewable in the browser
            media_tag = '<div id="unsupported"><div class="unsupported-content"><div class="unsupported-icon">📁</div><div class="unsupported-text">Format not supported for preview</div><div class="unsupported-subtext">You can still set crop coordinates (default size: 500x300)</div></div></div>'
            media_type = "unsupported"
        
        return ext, media_tag, media_type, controls_html

    def do_GET(self):
        """Handles GET requests for the main page and media file."""
        path = urlparse(self.path).path
        ext, media_tag, media_type, controls_html = self._get_media_type_info(self.server.media_file)

        if path == "/":
            # --- HTML Generation ---
            media_wrapper_start = '<div id="media-wrapper">'
            crop_div = '<div id="crop" class="crop-box" style="left:50px;top:50px;width:200px;height:150px;" tabindex="0" role="img" aria-label="Crop selection area"><div class="resize-handle nw"></div><div class="resize-handle ne"></div><div class="resize-handle sw"></div><div class="resize-handle se"></div><div class="resize-handle n"></div><div class="resize-handle s"></div><div class="resize-handle w"></div><div class="resize-handle e"></div></div>'
            
            # Conditionally include the crop box for image/video/unsupported, not for pure audio (which is typically a control bar)
            if media_type in ["image", "video", "unsupported"]:
                media_section = media_wrapper_start + media_tag + crop_div + '</div>' + controls_html
            else: # Audio only
                # Wrap audio in container for consistent UI structure, but no crop box
                media_section = media_wrapper_start + media_tag + '</div>' + controls_html 
            
            # --- HTML Structure and Styles (Simplified for brevity, assuming the rest of the HTML/CSS is as in the prompt) ---
            
            # --- START HTML (including all the CSS and JS from the prompt) ---
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MediaCrop - Visual FFmpeg Crop Tool</title>
  <style>
    * {{ 
      box-sizing: border-box; 
      margin: 0; 
      padding: 0;
    }}
    
    :root {{
      --primary: #00ff41;
      --primary-hover: #00cc33;
      --primary-dark: #00aa2a;
      --bg-main: #0f0f0f;
      --bg-panel: #1a1a1a;
      --bg-control: #252525;
      --border: #333;
      --border-light: #444;
      --text-main: #ffffff;
      --text-muted: #aaa;
      --text-dim: #666;
      --shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
      --shadow-heavy: 0 8px 32px rgba(0, 0, 0, 0.6);
      --radius: 8px;
      --radius-large: 12px;
      --primary-rgb: 0, 255, 65;
    }}
    
    /* LIGHT THEME VARIABLES */
    .light-theme {{
        --primary: #008000;
        --primary-hover: #006400;
        --primary-dark: #004d00;
        --bg-main: #f0f0f0;
        --bg-panel: #ffffff;
        --bg-control: #e0e0e0;
        --border: #ccc;
        --border-light: #ddd;
        --text-main: #1a1a1a;
        --text-muted: #555;
        --text-dim: #888;
        --shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        --shadow-heavy: 0 8px 32px rgba(0, 0, 0, 0.15);
        --primary-rgb: 0, 128, 0; /* New RGB for dynamic shadows */
    }}
    /* END LIGHT THEME VARIABLES */
    
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      background: var(--bg-main);
      color: var(--text-main);
      user-select: none;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      transition: background-color 0.3s, color 0.3s;
    }}

    /* Header Bar */
    .header-bar {{
      background: var(--bg-panel);
      border-bottom: 1px solid var(--border);
      padding: 12px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
      height: 60px;
    }}
    
    .header-controls {{
        display: flex;
        align-items: center;
        gap: 20px;
    }}

    /* THEME TOGGLE BUTTON STYLES */
    #themeToggle {{
        background: var(--bg-control);
        border: 1px solid var(--border);
        color: var(--text-main);
        font-size: 20px;
        line-height: 1;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
    }}
    
    #themeToggle:hover {{
        background: var(--border);
        box-shadow: 0 0 10px rgba(var(--primary-rgb), 0.3);
    }}
    /* END THEME TOGGLE BUTTON STYLES */

    .app-title {{
      font-size: 18px;
      font-weight: 600;
      color: var(--primary);
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .app-title::before {{
      content: '✂️';
      font-size: 20px;
    }}

    .file-info {{
      display: flex;
      align-items: center;
      gap: 15px;
      font-size: 13px;
      color: var(--text-muted);
    }}

    .file-detail {{
      display: flex;
      align-items: center;
      gap: 5px;
    }}

    .file-detail-label {{
      color: var(--text-dim);
    }}

    .file-detail-value {{
      color: var(--text-main);
      font-weight: 500;
    }}

    /* Main Content Area */
    .main-content {{
      display: flex;
      flex: 1;
      min-height: 0;
    }}

    /* Left Sidebar */
    .sidebar {{
      width: 280px;
      background: var(--bg-panel);
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
    }}

    .sidebar-section {{
      border-bottom: 1px solid var(--border);
      padding: 20px;
    }}

    .sidebar-section:last-child {{
      border-bottom: none;
      flex: 1;
    }}

    .section-title {{
      font-size: 14px;
      font-weight: 600;
      color: var(--text-main);
      margin-bottom: 15px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .section-title::before {{
      font-size: 16px;
    }}

    .section-title.aspect::before {{ content: '📐'; }}
    .section-title.tools::before {{ content: '🔧'; }}
    .section-title.info::before {{ content: '📊'; }}

    /* Form Controls */
    .form-group {{
      margin-bottom: 15px;
    }}

    .form-group:last-child {{
      margin-bottom: 0;
    }}

    .form-label {{
      display: block;
      font-size: 13px;
      font-weight: 500;
      color: var(--text-muted);
      margin-bottom: 6px;
    }}

    .form-select, .form-input, .form-button {{
      width: 100%;
      padding: 10px 12px;
      background: var(--bg-control);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      color: var(--text-main);
      font-size: 13px;
      transition: all 0.2s ease;
    }}

    .form-select:focus, .form-input:focus {{
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 30%, transparent);
    }}

    .form-input {{
      text-align: center;
      font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
    }}

    .custom-ratio {{
      display: none;
      grid-template-columns: 1fr auto 1fr;
      gap: 8px;
      align-items: center;
      margin-top: 8px;
    }}

    .custom-ratio.visible {{
      display: grid;
    }}

    .ratio-separator {{
      color: var(--text-muted);
      font-weight: 500;
    }}

    .form-button {{
      background: linear-gradient(135deg, var(--primary), var(--primary-dark));
      color: #000;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: all 0.2s ease;
    }}

    .form-button:hover {{
      background: linear-gradient(135deg, var(--primary-hover), var(--primary));
      transform: translateY(-1px);
      box-shadow: 0 4px 12px color-mix(in srgb, var(--primary) 50%, transparent);
    }}

    .form-button:active {{
      transform: translateY(0);
    }}
    
    /* Light theme button color fix */
    .light-theme .form-button {{
        color: #ffffff;
    }}
    
    .light-theme .form-button:hover {{
        color: #ffffff;
    }}
    
    /* Override Save Button color for better contrast in Light Theme */
    #saveButton {{
      background: linear-gradient(135deg, #4CAF50, #45a049) !important;
      color: #ffffff !important;
    }}

    .button-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }}

    .button-grid .form-button {{
      font-size: 12px;
      padding: 8px 10px;
    }}

    /* Info Stats */
    .info-stats {{
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}

    .info-stat {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 13px;
    }}

    .info-stat-label {{
      color: var(--text-muted);
    }}

    .info-stat-value {{
      color: var(--primary);
      font-weight: 600;
      font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
    }}

    /* Media Viewer */
    .media-viewer {{
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 30px;
      position: relative;
      background: radial-gradient(circle at center, var(--bg-panel) 0%, var(--bg-main) 100%);
      min-height: 0;
      overflow: auto; 
      scrollbar-width: auto;
      scrollbar-color: var(--primary) var(--bg-control);
    }}
    
    /* Custom Green Scrollbars for Media Viewer */
    .media-viewer::-webkit-scrollbar {{
      width: 20px;
      height: 20px;
    }}

    .media-viewer::-webkit-scrollbar-track {{
      background: var(--bg-control);
    }}

    .media-viewer::-webkit-scrollbar-thumb {{
      background-color: var(--primary);
      border-radius: 8px;
      border: 4px solid var(--bg-control);
    }}

    .media-viewer::-webkit-scrollbar-thumb:hover {{
      background-color: var(--primary-hover);
    }}

    #container {{
      position: relative;
      border: 2px solid var(--border-light);
      border-radius: var(--radius-large);
      background: #000;
      box-shadow: var(--shadow-heavy);
      display: inline-block;
    }}
    
    .light-theme #container {{
        background: #333;
    }}

    #media-wrapper {{
        position: relative;
        display: inline-block;
        line-height: 0;
    }}

    img, video, audio {{
      display: block;
      max-width: none;
      user-select: none;
      -webkit-user-drag: none;
      -moz-user-drag: none;
      -o-user-drag: none;
      user-drag: none;
      /* Remove native controls from video to use custom ones, but not from audio */
      { "controls: none;" if media_type == "video" else "" } 
    }}

    #unsupported {{
      width: 500px;
      height: 300px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }}

    .unsupported-content {{
      text-align: center;
      padding: 40px;
    }}

    .unsupported-icon {{
      font-size: 48px;
      margin-bottom: 16px;
    }}

    .unsupported-text {{
      font-size: 18px;
      color: var(--text-main);
      margin-bottom: 8px;
      font-weight: 500;
    }}

    .unsupported-subtext {{
      font-size: 14px;
      color: var(--text-muted);
    }}

    /* Crop Box */
    .crop-box {{
      border: 2px dashed var(--primary);
      position: absolute;
      z-index: 50;
      box-sizing: border-box;
      min-width: 30px;
      min-height: 30px;
      cursor: grab;
      /* Dynamic crop box overlay/shadow */
      background: color-mix(in srgb, var(--primary) 15%, transparent); 
      box-shadow: 
        0 0 0 9999px color-mix(in srgb, var(--bg-main) 70%, transparent),
        inset 0 0 0 1px color-mix(in srgb, var(--primary) 30%, transparent);
      transition: box-shadow 0.2s ease;
    }}
    
    .light-theme .crop-box {{
        box-shadow: 
            0 0 0 9999px rgba(0, 0, 0, 0.4),
            inset 0 0 0 1px color-mix(in srgb, var(--primary) 50%, transparent);
    }}

    .crop-box:hover {{
      box-shadow: 
        0 0 0 9999px color-mix(in srgb, var(--bg-main) 75%, transparent),
        inset 0 0 0 1px color-mix(in srgb, var(--primary) 50%, transparent),
        0 0 20px color-mix(in srgb, var(--primary) 40%, transparent);
    }}

    .crop-box.dragging {{
      cursor: grabbing;
      box-shadow: 
        0 0 0 9999px color-mix(in srgb, var(--bg-main) 80%, transparent),
        inset 0 0 0 1px color-mix(in srgb, var(--primary) 70%, transparent),
        0 0 25px color-mix(in srgb, var(--primary) 60%, transparent);
    }}
    
    .light-theme .crop-box:hover, .light-theme .crop-box.dragging {{
        box-shadow: 
            0 0 0 9999px rgba(0, 0, 0, 0.5), 
            inset 0 0 0 1px color-mix(in srgb, var(--primary) 70%, transparent),
            0 0 25px color-mix(in srgb, var(--primary) 60%, transparent);
    }}


    .crop-box.show-grid::before {{
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-image: 
        linear-gradient(to right, color-mix(in srgb, var(--primary) 30%, transparent) 1px, transparent 1px),
        linear-gradient(to bottom, color-mix(in srgb, var(--primary) 30%, transparent) 1px, transparent 1px);
      background-size: 33.33% 33.33%;
      pointer-events: none;
    }}

    /* Resize Handles */
    .resize-handle {{
      position: absolute;
      background: var(--primary);
      width: 16px;
      height: 16px;
      border: 2px solid var(--bg-main);
      border-radius: 50%;
      z-index: 51;
      transition: all 0.2s ease;
      transform: translate(-50%, -50%);
    }}
    
    .light-theme .resize-handle {{
        border: 2px solid var(--bg-panel);
    }}


    .resize-handle:hover {{
      background: #fff;
      transform: translate(-50%, -50%) scale(1.3);
      box-shadow: 0 0 8px color-mix(in srgb, var(--primary) 50%, transparent);
    }}
    
    .light-theme .resize-handle:hover {{
        background: #000;
        box-shadow: 0 0 8px color-mix(in srgb, var(--primary) 70%, transparent);
    }}

    .resize-handle.nw {{ top: 0; left: 0; cursor: nw-resize; }}
    .resize-handle.ne {{ top: 0; right: 0; cursor: ne-resize; transform: translate(50%, -50%); }}
    .resize-handle.sw {{ bottom: 0; left: 0; cursor: sw-resize; transform: translate(-50%, 50%); }}
    .resize-handle.se {{ bottom: 0; right: 0; cursor: se-resize; transform: translate(50%, 50%); }}
    .resize-handle.n {{ top: 0; left: 50%; cursor: n-resize; }}
    .resize-handle.s {{ bottom: 0; left: 50%; cursor: s-resize; transform: translate(-50%, 50%); }}
    .resize-handle.w {{ left: 0; top: 50%; cursor: w-resize; }}
    .resize-handle.e {{ right: 0; top: 50%; cursor: e-resize; transform: translate(50%, -50%); }}

    /* Video Controls */
    .video-controls {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 20px;
      background: var(--bg-control);
      border-top: 1px solid var(--border-light);
      gap: 10px;
      flex-shrink: 0;
    }}

    .control-btn {{
      background: none;
      border: none;
      color: var(--text-main);
      font-size: 18px;
      cursor: pointer;
      padding: 5px;
      border-radius: var(--radius);
      transition: background 0.2s ease;
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    .control-btn:hover {{
      background: var(--border);
    }}

    .progress-container {{
      flex: 1;
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
    }}

    #currentTime, #duration {{
      font-size: 12px;
      color: var(--text-muted);
      min-width: 40px;
      font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
    }}

    .seek-bar {{
      flex: 1;
      height: 4px;
      background: var(--border);
      border-radius: 2px;
      outline: none;
      -webkit-appearance: none;
      cursor: pointer;
    }}

    .seek-bar::-webkit-slider-thumb {{
      -webkit-appearance: none;
      appearance: none;
      width: 12px;
      height: 12px;
      background: var(--primary);
      border-radius: 50%;
      cursor: pointer;
    }}

    .seek-bar::-moz-range-thumb {{
      width: 12px;
      height: 12px;
      background: var(--primary);
      border-radius: 50%;
      cursor: pointer;
      border: none;
    }}

    .control-select {{
      background: var(--bg-control);
      border: 1px solid var(--border);
      color: var(--text-main);
      padding: 5px 8px;
      border-radius: var(--radius);
      font-size: 12px;
      cursor: pointer;
    }}

    .volume-container {{
      display: flex;
      align-items: center;
      gap: 5px;
      min-width: 100px;
    }}

    .volume-bar {{
      width: 80px;
      height: 4px;
      background: var(--border);
      border-radius: 2px;
      outline: none;
      -webkit-appearance: none;
      cursor: pointer;
    }}

    .volume-bar::-webkit-slider-thumb {{
      -webkit-appearance: none;
      appearance: none;
      width: 12px;
      height: 12px;
      background: var(--primary);
      border-radius: 50%;
      cursor: pointer;
    }}

    .volume-bar::-moz-range-thumb {{
      width: 12px;
      height: 12px;
      background: var(--primary);
      border-radius: 50%;
      cursor: pointer;
      border: none;
    }}

    /* Loading Indicator */
    .loading {{
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: var(--bg-panel);
      padding: 30px 40px;
      border-radius: var(--radius-large);
      box-shadow: var(--shadow-heavy);
      z-index: 1000;
      text-align: center;
    }}

    .spinner {{
      width: 32px;
      height: 32px;
      border: 3px solid var(--border);
      border-top: 3px solid var(--primary);
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin: 0 auto 15px;
    }}

    @keyframes spin {{
      0% {{ transform: rotate(0deg); }}
      100% {{ transform: rotate(360deg); }}
    }}

    .loading-text {{
      font-size: 16px;
      font-weight: 500;
      color: var(--text-main);
    }}

    /* Help Modal */
    .help-modal {{
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.8);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      backdrop-filter: blur(4px);
    }}

    .help-content {{
      background: var(--bg-panel);
      border-radius: var(--radius-large);
      padding: 30px;
      max-width: 400px;
      box-shadow: var(--shadow-heavy);
      border: 1px solid var(--border);
    }}

    .help-title {{
      font-size: 20px;
      font-weight: 600;
      color: var(--primary);
      margin-bottom: 20px;
      text-align: center;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }}

    .help-title::before {{
      content: '⌨️';
      font-size: 24px;
    }}

    .help-shortcuts {{
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-bottom: 25px;
    }}

    .help-shortcut {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 14px;
    }}

    .help-shortcut-desc {{
      color: var(--text-muted);
    }}

    .help-shortcut-key {{
      background: var(--bg-control);
      color: var(--primary);
      padding: 4px 8px;
      border-radius: 4px;
      font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
      font-size: 12px;
      font-weight: 600;
    }}

    .help-close {{
      background: linear-gradient(135deg, var(--primary), var(--primary-dark));
      color: #000;
      border: none;
      padding: 12px 24px;
      border-radius: var(--radius);
      font-weight: 600;
      cursor: pointer;
      width: 100%;
      transition: all 0.2s ease;
    }}
    
    .light-theme .help-close {{
        color: #ffffff;
    }}


    .help-close:hover {{
      background: linear-gradient(135deg, var(--primary-hover), var(--primary));
      transform: translateY(-1px);
    }}

    /* Context Menu */
    .context-menu {{
      position: fixed;
      background: var(--bg-panel);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 8px 0;
      z-index: 300;
      display: none;
      box-shadow: var(--shadow);
      min-width: 180px;
    }}

    .context-item {{
      padding: 12px 16px;
      cursor: pointer;
      font-size: 14px;
      transition: background 0.2s ease;
      color: var(--text-main);
    }}

    .context-item:hover {{
      background: var(--bg-control);
      color: var(--primary);
    }}

    /* Notification */
    .notification {{
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: var(--bg-panel);
      color: var(--text-main);
      padding: 25px 35px;
      border-radius: var(--radius-large);
      z-index: 1000;
      box-shadow: var(--shadow-heavy);
      border: 1px solid var(--primary);
      text-align: center;
      max-width: 400px;
      animation: fadeInOut 3s forwards; /* Added animation */
    }}

    .notification-title {{
      font-size: 18px;
      font-weight: 600;
      color: var(--primary);
      margin-bottom: 15px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }}

    .notification-title::before {{
      content: '✅';
      font-size: 20px;
    }}

    .notification-code {{
      background: var(--bg-control);
      padding: 12px 16px;
      border-radius: var(--radius);
      font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
      font-size: 14px;
      color: var(--primary);
      margin: 15px 0;
      border: 1px solid var(--border);
      overflow-x: auto; /* Scroll for long command */
    }}

    .notification-subtitle {{
      font-size: 13px;
      color: var(--text-muted);
    }}
    
    @keyframes fadeInOut {{
        0% {{ opacity: 0; transform: translate(-50%, -50%) scale(0.9); }}
        10% {{ opacity: 1; transform: translate(-50%, -50%) scale(1); }}
        90% {{ opacity: 1; transform: translate(-50%, -50%) scale(1); }}
        100% {{ opacity: 0; transform: translate(-50%, -50%) scale(0.9); }}
    }}

    /* Responsive Design */
    @media (max-width: 1024px) {{
      .sidebar {{
        width: 250px;
      }}
      
      #container {{
        max-width: calc(100vw - 270px);
      }}
    }}

    @media (max-width: 768px) {{
      .header-bar {{
        flex-direction: column;
        height: auto;
        padding: 12px 15px;
        gap: 10px;
        flex-shrink: 0;
      }}
      
      .file-info {{
        gap: 10px;
        font-size: 12px;
      }}
      
      .main-content {{
        flex-direction: column;
      }}
      
      .sidebar {{
        width: 100%;
        border-right: none;
        border-bottom: 1px solid var(--border);
        flex-direction: row;
        overflow-x: auto;
        padding: 0;
        flex-shrink: 0;
        scrollbar-width: thin;
        scrollbar-color: var(--primary) var(--bg-control);
      }}

      .sidebar::-webkit-scrollbar {{
        height: 6px;
      }}
      .sidebar::-webkit-scrollbar-track {{
        background: var(--bg-control);
      }}
      .sidebar::-webkit-scrollbar-thumb {{
        background-color: var(--primary);
        border-radius: 6px;
      }}
      
      .sidebar-section {{
        min-width: 220px;
        border-right: 1px solid var(--border);
        border-bottom: none;
        flex-shrink: 0;
      }}
      
      .sidebar-section:last-child {{
        border-right: none;
      }}

      .media-viewer {{
        flex: 1;
        min-height: 0;
      }}
      
      #container {{
        max-width: 100%;
        max-height: 100%;
      }}

      /* UX IMPROVEMENT 3: Larger resize handles for easier touch interaction on mobile devices */
      .resize-handle {{
        width: 22px;
        height: 22px;
      }}

      .video-controls {{
        padding: 10px 15px;
        gap: 5px;
      }}

      .control-btn {{
        width: 35px;
        height: 35px;
        font-size: 16px;
      }}

      .progress-container {{
        gap: 5px;
      }}

      #currentTime, #duration {{
        min-width: 35px;
        font-size: 11px;
      }}

      .volume-container {{
        min-width: 80px;
      }}

      .volume-bar {{
        width: 60px;
      }}
    }}

    /* Utilities */
    .smooth-transition {{
      transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    .visually-hidden {{
      position: absolute;
      width: 1px;
      height: 1px;
      margin: -1px;
      padding: 0;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }}
  </style>
</head>
<body class="dark-theme"> <div class="loading" id="loadingIndicator">
    <div class="spinner"></div>
    <div class="loading-text">Loading media...</div>
  </div>

  <div class="header-bar">
    <div class="app-title">MediaCrop - Visual FFmpeg Crop Tool</div>
    <div class="header-controls">
      <button id="themeToggle" title="Toggle Dark/Light Theme">☀️</button>
      <div class="file-info">
        <div class="file-detail">
          <span class="file-detail-label">Format:</span>
          <span class="file-detail-value">{ext.upper().replace('.', '')}</span>
        </div>
        <div class="file-detail">
          <span class="file-detail-label">Type:</span>
          <span class="file-detail-value">{media_type.title()}</span>
        </div>
        <div class="file-detail">
          <span class="file-detail-label">Size:</span>
          <span class="file-detail-value" id="fileSizeInfo">Loading...</span>
        </div>
      </div>
    </div>
  </div>

  <div class="main-content">
    <div class="sidebar">
      <div class="sidebar-section">
        <div class="section-title aspect">Aspect Ratio</div>
        
        <div class="form-group">
          <label class="form-label" for="aspect">Preset</label>
          <select id="aspect" class="form-select">
            <option value="free">Free Form</option>
            <option value="1:1">1:1 (Square)</option>
            <option value="4:3">4:3 (Standard)</option>
            <option value="16:9">16:9 (Widescreen)</option>
            <option value="9:16">9:16 (Portrait)</option>
            <option value="3:2">3:2 (Photo)</option>
            <option value="5:4">5:4 (Large Format)</option>
            <option value="21:9">21:9 (Ultrawide)</option>
            <option value="2.35:1">2.35:1 (Cinemascope)</option>
            <option value="2.39:1">2.39:1 (Anamorphic)</option>
            <option value="original">Original</option>
            <option value="custom">Custom Ratio</option>
          </select>
        </div>
        
        <div class="custom-ratio" id="customRatio">
          <input type="text" id="customW" class="form-input" value="16" placeholder="W" inputmode="numeric">
          <div class="ratio-separator">:</div>
          <input type="text" id="customH" class="form-input" value="9" placeholder="H" inputmode="numeric">
        </div>
      </div>

      <div class="sidebar-section">
        <div class="section-title tools">Quick Tools</div>
        
        <div class="form-group">
          <div class="button-grid">
            <button class="form-button" onclick="toggleGrid()" title="Toggle Rule-of-Thirds Grid (G)">📐 Grid</button>
            <button class="form-button" onclick="centerCrop()" title="Center the Crop Box (C)">🎯 Center</button>
            <button class="form-button" onclick="resetCropSize()" title="Reset Crop Box Size & Position">🔄 Reset</button>
            <button class="form-button" onclick="toggleHelp()" title="Show Keyboard Shortcuts (?)">❓ Help</button>
          </div>
        </div>
        
        <div class="form-group">
          <button id="saveButton" class="form-button" onclick="saveCrop()" style="background: linear-gradient(135deg, #4CAF50, #45a049); font-size: 14px; padding: 12px;">
            💾 Save Coordinates
          </button>
        </div>
      </div>

      <div class="sidebar-section">
        <div class="section-title info">Crop Info</div>
        
        <div class="info-stats">
          <div class="info-stat">
            <span class="info-stat-label">Natural Res:</span>
            <span class="info-stat-value" id="naturalResInfo">N/A</span>
          </div>
          <div class="info-stat">
            <span class="info-stat-label">Position:</span>
            <span class="info-stat-value" id="positionInfo">(0, 0)</span>
          </div>
          <div class="info-stat">
            <span class="info-stat-label">Size:</span>
            <span class="info-stat-value" id="sizeInfo">200×150</span>
          </div>
          <div class="info-stat">
            <span class="info-stat-label">Ratio:</span>
            <span class="info-stat-value" id="ratioInfo">4:3</span>
          </div>
          <div class="info-stat">
            <span class="info-stat-label">Zoom:</span>
            <span class="info-stat-value" id="zoomInfo">100%</span>
          </div>
        </div>
      </div>
    </div>

    <div class="media-viewer">
      <div id="container">
        {media_section}
      </div>
    </div>
  </div>

  <div class="help-modal" id="helpModal">
    <div class="help-content">
      <div class="help-title">Keyboard Shortcuts</div>
      <div class="help-shortcuts">
        <div class="help-shortcut">
          <span class="help-shortcut-desc">Move crop box</span>
          <span class="help-shortcut-key">Arrow Keys</span>
        </div>
        <div class="help-shortcut">
          <span class="help-shortcut-desc">Fine adjustment</span>
          <span class="help-shortcut-key">Shift + Arrows</span>
        </div>
        <div class="help-shortcut">
          <span class="help-shortcut-desc">Zoom In/Out Media</span>
          <span class="help-shortcut-key">Mouse Wheel</span>
        </div>
        <div class="help-shortcut">
          <span class="help-shortcut-desc">Center crop box</span>
          <span class="help-shortcut-key">C</span>
        </div>
        <div class="help-shortcut">
          <span class="help-shortcut-desc">Toggle grid</span>
          <span class="help-shortcut-key">G</span>
        </div>
        <div class="help-shortcut">
          <span class="help-shortcut-desc">Save coordinates</span>
          <span class="help-shortcut-key">Enter</span>
        </div>
        <div class="help-shortcut">
          <span class="help-shortcut-desc">Close help</span>
          <span class="help-shortcut-key">Esc</span>
        </div>
      </div>
      <button class="help-close" onclick="toggleHelp()">Got it!</button>
    </div>
  </div>

  <div class="context-menu" id="contextMenu">
    <div class="context-item" onclick="centerCrop()">🎯 Center Crop Box</div>
    <div class="context-item" onclick="toggleGrid()">📐 Toggle Grid</div>
    <div class="context-item" onclick="resetCropSize()">🔄 Reset Size</div>
    <div class="context-item" onclick="saveCrop()">💾 Save Coordinates</div>
  </div>

  <script>
    // Enhanced global state management
    const elements = {{
      media: document.getElementById("media"),
      container: document.getElementById("container"),
      crop: document.getElementById("crop"),
      aspectSelect: document.getElementById("aspect"),
      customRatio: document.getElementById("customRatio"),
      customW: document.getElementById("customW"),
      customH: document.getElementById("customH"),
      positionInfo: document.getElementById("positionInfo"),
      sizeInfo: document.getElementById("sizeInfo"),
      ratioInfo: document.getElementById("ratioInfo"),
      naturalResInfo: document.getElementById("naturalResInfo"), // New
      zoomInfo: document.getElementById("zoomInfo"), // New
      fileSizeInfo: document.getElementById("fileSizeInfo"),
      loadingIndicator: document.getElementById("loadingIndicator"),
      helpModal: document.getElementById("helpModal"),
      contextMenu: document.getElementById("contextMenu"),
      mediaWrapper: document.getElementById("media-wrapper"),
      mediaViewer: document.querySelector(".media-viewer"),
      themeToggle: document.getElementById("themeToggle"),
      body: document.body
    }};

    // Enhanced state management
    const state = {{
      // Movement state
      isDragging: false,
      isResizing: false,
      resizeDirection: '',
      
      // Position tracking
      startMouseX: 0,
      startMouseY: 0,
      startCropLeft: 0,
      startCropTop: 0,
      startCropWidth: 0,
      startCropHeight: 0,
      
      // Dimensions
      mediaWidth: 0,
      mediaHeight: 0,
      naturalWidth: 0,
      naturalHeight: 0,
      
      // Aspect ratio
      aspectMode: "free",
      aspectRatio: null,
      
      // UI state
      isInitialized: false,
      showGrid: false,
      isHelpVisible: false,
      currentTheme: 'dark',
      
      // Performance
      lastUpdate: 0,
      animationFrame: null,
      
      // File info
      mediaType: "{media_type}",
      fileExtension: "{ext}",

      // Zoom and pinch
      zoom: 1,
      isPinching: false,
      pinchType: '',
      pinchInitialDist: 0,
      pinchInitialZoom: 0,
      pinchInitialWidth: 0,
      pinchInitialHeight: 0,
      pinchInitialLeft: 0,
      pinchInitialTop: 0,
      pinchInitialMid: {{x: 0, y: 0}},
      pinchInitialRelX: 0,
      pinchInitialRelY: 0,
      pinchInitialScrollLeft: 0,
      pinchInitialScrollTop: 0,

      // Auto scroll
      autoScrollActive: false,
      mouseX: 0,
      mouseY: 0
    }};
    
    // THEME TOGGLE LOGIC
    function initializeTheme() {{
        const storedTheme = localStorage.getItem('theme') || 'dark'; 
        setTheme(storedTheme);
    }}
    
    function setTheme(theme) {{
        state.currentTheme = theme;
        elements.body.classList.remove('dark-theme', 'light-theme');
        elements.body.classList.add(theme + '-theme');
        localStorage.setItem('theme', theme);
        
        elements.themeToggle.innerHTML = theme === 'dark' ? '☀️' : '🌙'; 
        elements.themeToggle.title = theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme';
    }}

    function toggleTheme() {{
        const newTheme = state.currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    }}
    // END THEME TOGGLE LOGIC

    // Utility functions
    const utils = {{
      // Debounce function for performance
      debounce(func, wait) {{
        let timeout;
        return function executedFunction(...args) {{
          const later = () => {{
            clearTimeout(timeout);
            func(...args);
          }};
          clearTimeout(timeout);
          timeout = setTimeout(later, wait);
        }};
      }},
      
      // Throttle function for smooth animations
      throttle(func, limit) {{
        let inThrottle;
        return function(...args) {{
          if (!inThrottle) {{
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
          }}
        }};
      }},
      
      // Get event coordinates (mouse/touch)
      getEventCoords(e) {{
        if (e.type.startsWith('touch')) {{
            // Handle multi-touch by only considering the first touch for non-pinch
            if (e.touches && e.touches.length > 0) {{
                return {{
                    x: e.touches[0].clientX,
                    y: e.touches[0].clientY
                }};
            }}
            return {{x: e.clientX, y: e.clientY}}; // Fallback (shouldn't happen for touchstart/move)
        }}
        return {{
          x: e.clientX,
          y: e.clientY
        }};
      }},
      
      // Calculate greatest common divisor for aspect ratio
      gcd(a, b) {{
        return b === 0 ? a : this.gcd(b, a % b);
      }},
      
      // Format file size
      formatFileSize(bytes) {{
        const sizes = ['B', 'KB', 'MB', 'GB'];
        if (bytes === 0) return '0 B';
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        // Use toLocaleString for better number formatting
        return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + sizes[i];
      }},
      
      // Smooth interpolation
      lerp(start, end, factor) {{
        return start + (end - start) * factor;
      }},

      // Get touch distance
      getDistance(t1, t2) {{
        return Math.sqrt(Math.pow(t2.clientX - t1.clientX, 2) + Math.pow(t2.clientY - t1.clientY, 2));
      }},

      // Get touch midpoint
      getMidpoint(t1, t2) {{
        return {{
          x: (t1.clientX + t2.clientX) / 2,
          y: (t1.clientY + t1.clientY) / 2
        }};
      }},

      // Format video time
      formatTime(seconds) {{
        if (isNaN(seconds) || seconds < 0) return '0:00';
        const totalSeconds = Math.floor(seconds);
        const hours = Math.floor(totalSeconds / 3600);
        const mins = Math.floor((totalSeconds % 3600) / 60);
        const secs = totalSeconds % 60;
        
        // Include hours only if duration is 1 hour or more
        if (hours > 0) {{
          return `${{hours}}:${{mins.toString().padStart(2, '0')}}:${{secs.toString().padStart(2, '0')}}`;
        }}
        return `${{mins}}:${{secs.toString().padStart(2, '0')}}`;
      }}
    }};

    // Custom video controls initialization
    function initVideoControls() {{
      const video = elements.media;
      const controls = document.getElementById('videoControls');
      if (!video || !controls) return;

      const playPause = document.getElementById('playPause');
      const seekBar = document.getElementById('seekBar');
      const currentTimeEl = document.getElementById('currentTime');
      const durationEl = document.getElementById('duration');
      const playbackSpeed = document.getElementById('playbackSpeed');
      const muteBtn = document.getElementById('muteBtn');
      const volumeBar = document.getElementById('volumeBar');

      // Play/Pause
      function togglePlayPause() {{
        if (video.paused) {{
          video.play().catch(e => console.log('Play error:', e));
        }} else {{
          video.pause();
        }}
      }}

      playPause.addEventListener('click', togglePlayPause);
      video.addEventListener('click', togglePlayPause); // Click video to play/pause

      video.addEventListener('play', () => playPause.textContent = '⏸️');
      video.addEventListener('pause', () => playPause.textContent = '▶️');
      video.addEventListener('ended', () => playPause.textContent = '▶️');

      // Seek bar
      let isSeeking = false;
      
      seekBar.addEventListener('mousedown', () => isSeeking = true);
      seekBar.addEventListener('mouseup', () => isSeeking = false);
      
      seekBar.addEventListener('input', (e) => {{
        const time = (e.target.value / 100) * video.duration;
        video.currentTime = time;
        currentTimeEl.textContent = utils.formatTime(time); // Update time instantly during drag
      }});

      video.addEventListener('timeupdate', () => {{
        if (video.duration) {{
            if (!isSeeking) {{
                const value = (video.currentTime / video.duration) * 100;
                seekBar.value = value;
            }}
            currentTimeEl.textContent = utils.formatTime(video.currentTime);
        }}
      }});

      // Duration
      video.addEventListener('loadedmetadata', () => {{
        durationEl.textContent = utils.formatTime(video.duration);
        seekBar.max = 100;
        // Also update natural resolution if available
        if (video.videoWidth && video.videoHeight) {{
            elements.naturalResInfo.textContent = `${{video.videoWidth}}×${{video.videoHeight}}`;
        }}
      }});

      // Playback speed
      playbackSpeed.addEventListener('change', (e) => {{
        video.playbackRate = parseFloat(e.target.value);
      }});

      // Volume
      volumeBar.addEventListener('input', (e) => {{
        video.volume = e.target.value / 100;
        video.muted = video.volume === 0;
        muteBtn.textContent = video.muted ? '🔇' : '🔊';
      }});

      muteBtn.addEventListener('click', () => {{
        video.muted = !video.muted;
        // Keep volume at last setting if unmuting
        if (!video.muted && video.volume === 0) video.volume = 1;
        volumeBar.value = video.volume * 100;
        muteBtn.textContent = video.muted ? '🔇' : '🔊';
      }});

      // Initial setup
      video.volume = 1;
      muteBtn.textContent = '🔊';
      playPause.textContent = '▶️';
    }}

    // Enhanced initialization
    function initializeCrop() {{
      // Use requestAnimationFrame for next tick stability
      requestAnimationFrame(() => {{ 
        if (state.isInitialized) return;

        updateMediaDimensions();
        updateFileInfo();
        
        if (state.mediaType === 'image' || state.mediaType === 'video' || state.mediaType === 'unsupported') {{
            positionCropBox();
            updateCropInfo();
            setMediaZoom(1);
        }}
        
        // Video-specific setup
        if (state.mediaType === 'video') {{
          initVideoControls();
          // Adjust container layout for video controls if media is a video
          elements.container.style.display = 'flex';
          elements.container.style.flexDirection = 'column';
          elements.mediaWrapper.style.flex = '1';
          elements.mediaWrapper.style.minHeight = '200px';
        }}
        
        // Image-specific setup (to get natural dimensions)
        if (state.mediaType === 'image' && elements.media) {{
            elements.naturalResInfo.textContent = `${{elements.media.naturalWidth}}×${{elements.media.naturalHeight}}`;
        }}


        state.isInitialized = true;
        hideLoading();
        
        // Initial focus for accessibility
        if (elements.crop) {{
            elements.crop.focus();
        }}
      }});
    }}

    function hideLoading() {{
      elements.loadingIndicator.style.display = 'none';
    }}

    // Enhanced media dimensions tracking
    function updateMediaDimensions() {{
        if (elements.media) {{
            state.mediaWidth = elements.media.offsetWidth;
            state.mediaHeight = elements.media.offsetHeight;
        }}
      
        if (state.mediaType === 'unsupported') {{
          state.mediaWidth = 500;
          state.mediaHeight = 300;
          state.naturalWidth = 500;
          state.naturalHeight = 300;
          // For unsupported, the image/video dimensions are the container dimensions
          elements.container.style.width = state.mediaWidth + 'px';
          elements.container.style.height = state.mediaHeight + 'px';
          elements.mediaWrapper.style.width = state.mediaWidth + 'px';
          elements.mediaWrapper.style.height = state.mediaHeight + 'px';
          return;
        }}
        
        if (!elements.media) return;

      
        // Get natural dimensions for scaling calculations
        if (elements.media.tagName === 'IMG') {{
          state.naturalWidth = elements.media.naturalWidth || state.mediaWidth;
          state.naturalHeight = elements.media.naturalHeight || state.mediaHeight;
        }} else if (elements.media.tagName === 'VIDEO') {{
          state.naturalWidth = elements.media.videoWidth || state.mediaWidth;
          state.naturalHeight = elements.media.videoHeight || state.mediaHeight;
        }} else if (elements.media.tagName === 'AUDIO') {{
            // For audio, we use default or an assumed minimal area for consistency
            state.naturalWidth = 500; 
            state.naturalHeight = 50; 
            elements.container.style.width = 'fit-content';
            elements.container.style.height = 'auto';
            return; // Skip crop box logic for audio
        }} else {{
          // Default for other media types
          state.naturalWidth = state.mediaWidth;
          state.naturalHeight = state.mediaHeight;
        }}
        
        // Update the media width/height based on current zoom * natural size
        if (elements.media) {{
            state.mediaWidth = elements.media.offsetWidth;
            state.mediaHeight = elements.media.offsetHeight;
        }}

        // Update natural resolution display
        elements.naturalResInfo.textContent = `${{state.naturalWidth}}×${{state.naturalHeight}}`;
    }}

    // File information display (HEAD request is better for just size)
    function updateFileInfo() {{
      fetch('/file', {{ method: 'HEAD' }})
        .then(response => {{
          const contentLength = response.headers.get('content-length');
          if (contentLength) {{
            elements.fileSizeInfo.textContent = utils.formatFileSize(parseInt(contentLength));
          }} else {{
             elements.fileSizeInfo.textContent = 'N/A';
          }}
        }})
        .catch(() => {{
          elements.fileSizeInfo.textContent = 'Error';
        }});
    }}

    // Enhanced crop box positioning
    function positionCropBox() {{
      if (state.mediaWidth === 0 || state.mediaHeight === 0 || !elements.crop) return;
      
      const cropWidth = Math.min(200, state.mediaWidth * 0.4);
      const cropHeight = Math.min(150, state.mediaHeight * 0.3);
      
      const centerX = (state.mediaWidth - cropWidth) / 2;
      const centerY = (state.mediaHeight - cropHeight) / 2;
      
      setCropDimensions(centerX, centerY, cropWidth, cropHeight);
    }}

    // Enhanced dimension setting with smooth transitions
    function setCropDimensions(left, top, width, height, smooth = false) {{
      if (!elements.crop) return;
      
      // Ensure minimum dimensions
      width = Math.max(30, width);
      height = Math.max(30, height);
      
      // Constrain to media bounds
      left = Math.max(0, Math.min(left, state.mediaWidth - width));
      top = Math.max(0, Math.min(top, state.mediaHeight - height));
      
      // Recalculate width/height after clamping position to ensure they don't exceed bounds
      width = Math.min(width, state.mediaWidth - left);
      height = Math.min(height, state.mediaHeight - top);
      
      const cropStyle = elements.crop.style;
      
      if (smooth) {{
        elements.crop.classList.add('smooth-transition');
        // Remove class after transition to re-enable instant updates during drag/resize
        setTimeout(() => elements.crop.classList.remove('smooth-transition'), 150);
      }}
      
      cropStyle.left = Math.round(left) + 'px';
      cropStyle.top = Math.round(top) + 'px';
      cropStyle.width = Math.round(width) + 'px';
      cropStyle.height = Math.round(height) + 'px';
      
      // Always call info update after setting dimensions
      updateCropInfo();
    }}

    // Enhanced aspect ratio handling
    function applyAspectRatio(width, height, maintainWidth = true) {{
      if (state.aspectMode === "free" || !state.aspectRatio || isNaN(state.aspectRatio)) {{
        return {{ width, height }};
      }}
      
      if (maintainWidth) {{
        height = Math.round(width / state.aspectRatio);
      }} else {{
        width = Math.round(height * state.aspectRatio);
      }}
      
      return {{ width, height }};
    }}

    // Enhanced info display with animations
    function updateCropInfo() {{
      if (!elements.crop) return;
      const left = parseInt(elements.crop.style.left) || 0;
      const top = parseInt(elements.crop.style.top) || 0;
      const width = parseInt(elements.crop.style.width) || 0;
      const height = parseInt(elements.crop.style.height) || 0;
      
      // Update position and size
      elements.positionInfo.textContent = `(${{left}}, ${{top}})`;
      elements.sizeInfo.textContent = `${{width}}×${{height}}`;
      elements.zoomInfo.textContent = `${{Math.round(state.zoom * 100)}}%`;
      
      // Calculate and display aspect ratio
      if (width && height) {{
        const gcd = utils.gcd(width, height);
        const ratioW = width / gcd;
        const ratioH = height / gcd;
        
        // Simplify common ratios
        let ratioText = `${{ratioW}}:${{ratioH}}`;
        if (ratioW === ratioH) ratioText = "1:1";
        else if (Math.abs(ratioW/ratioH - 16/9) < 0.05) ratioText = "≈ 16:9";
        else if (Math.abs(ratioW/ratioH - 4/3) < 0.05) ratioText = "≈ 4:3";
        else if (Math.abs(ratioW/ratioH - 3/2) < 0.05) ratioText = "≈ 3:2";
        else {{
            // Custom ratio, show as floating point W:H, limited to two decimal places
            const floatRatio = (width / height).toFixed(2);
            ratioText = `${{floatRatio}}:1`;
        }}
        
        elements.ratioInfo.textContent = ratioText;
      }}
    }}

    // Set media zoom
    function setMediaZoom(newZoom) {{
      if (state.mediaType !== 'image' && state.mediaType !== 'video') return;
      newZoom = Math.max(0.1, Math.min(10, newZoom)); // Constrain zoom from 10% to 1000%
      
      const oldZoom = state.zoom;
      if (newZoom === oldZoom) return;

      const factor = newZoom / oldZoom;
      state.zoom = newZoom;
      
      // Apply new dimensions to media
      if (elements.media && state.naturalWidth && state.naturalHeight) {{
        elements.media.style.width = (state.naturalWidth * newZoom) + 'px';
        elements.media.style.height = (state.naturalHeight * newZoom) + 'px';
      }}
      
      // Scale crop box position and size
      if (elements.crop) {{
        elements.crop.style.left = (parseFloat(elements.crop.style.left) * factor) + 'px';
        elements.crop.style.top = (parseFloat(elements.crop.style.top) * factor) + 'px';
        elements.crop.style.width = (parseFloat(elements.crop.style.width) * factor) + 'px';
        elements.crop.style.height = (parseFloat(elements.crop.style.height) * factor) + 'px';
      }}
      
      // Update dimensions after scaling
      updateMediaDimensions();
      updateCropInfo();
    }}

    // --- DRAG AND RESIZE HANDLERS ---

    // Enhanced dragging with smooth movement
    const dragHandlers = {{
      start(e) {{
        if (!elements.crop || e.target.classList.contains('resize-handle')) return;
        e.preventDefault();
        e.stopPropagation();
        
        // Check for pinch-to-resize (two fingers on crop box)
        if (e.type.startsWith('touch') && e.touches.length === 2) {{
          startPinch('crop', e);
          return;
        }} else if (e.type.startsWith('touch') && e.touches.length > 1) {{
          return; // Ignore three or more fingers
        }}
        
        const coords = utils.getEventCoords(e);
        state.isDragging = true;
        state.startMouseX = coords.x;
        state.startMouseY = coords.y;
        state.startCropLeft = parseFloat(elements.crop.style.left) || 0;
        state.startCropTop = parseFloat(elements.crop.style.top) || 0;
        
        elements.crop.classList.add('dragging');
        
        document.addEventListener('mousemove', dragHandlers.move, {{ passive: false }});
        document.addEventListener('mouseup', dragHandlers.stop);
        document.addEventListener('touchmove', dragHandlers.move, {{ passive: false }});
        document.addEventListener('touchend', dragHandlers.stop);
        
        // Start tracking mouse position for auto-scrolling
        document.addEventListener('mousemove', updateMousePos);
        document.addEventListener('touchmove', updateMousePosTouch, {{ passive: false }});
        startAutoScroll();
      }},
      
      move: utils.throttle((e) => {{
        if (!state.isDragging) return;
        
        e.preventDefault();
        const coords = utils.getEventCoords(e);
        
        // Calculate deltas based on mouse/touch position
        const deltaX = coords.x - state.startMouseX;
        const deltaY = coords.y - state.startMouseY;
        
        let newLeft = state.startCropLeft + deltaX;
        let newTop = state.startCropTop + deltaY;
        
        const currentWidth = parseFloat(elements.crop.style.width) || 0;
        const currentHeight = parseFloat(elements.crop.style.height) || 0;
        
        setCropDimensions(newLeft, newTop, currentWidth, currentHeight);
      }}, 16), // ~60fps throttling
      
      stop() {{
        state.isDragging = false;
        if (elements.crop) elements.crop.classList.remove('dragging');
        
        document.removeEventListener('mousemove', dragHandlers.move);
        document.removeEventListener('mouseup', dragHandlers.stop);
        document.removeEventListener('touchmove', dragHandlers.move);
        document.removeEventListener('touchend', dragHandlers.stop);
        
        document.removeEventListener('mousemove', updateMousePos);
        document.removeEventListener('touchmove', updateMousePosTouch);
        stopAutoScroll();
      }}
    }};

    // Enhanced resizing with smooth aspect ratio handling
    const resizeHandlers = {{
      start(e) {{
        e.preventDefault();
        e.stopPropagation();
        
        if (state.mediaType === 'audio' || !elements.crop) return;
        
        const coords = utils.getEventCoords(e);
        state.isResizing = true;
        state.resizeDirection = Array.from(e.target.classList).find(cls => cls !== 'resize-handle');
        state.startMouseX = coords.x;
        state.startMouseY = coords.y;
        
        // Store dimensions as numbers
        state.startCropLeft = parseFloat(elements.crop.style.left) || 0;
        state.startCropTop = parseFloat(elements.crop.style.top) || 0;
        state.startCropWidth = parseFloat(elements.crop.style.width) || 0;
        state.startCropHeight = parseFloat(elements.crop.style.height) || 0;
        
        document.addEventListener('mousemove', resizeHandlers.move, {{ passive: false }});
        document.addEventListener('mouseup', resizeHandlers.stop);
        document.addEventListener('touchmove', resizeHandlers.move, {{ passive: false }});
        document.addEventListener('touchend', resizeHandlers.stop);
        
        // Start tracking mouse position for auto-scrolling
        document.addEventListener('mousemove', updateMousePos);
        document.addEventListener('touchmove', updateMousePosTouch, {{ passive: false }});
        startAutoScroll();
      }},
      
      move: utils.throttle((e) => {{
        if (!state.isResizing || !elements.crop) return;
        
        e.preventDefault();
        const coords = utils.getEventCoords(e);
        
        // Calculate deltas based on mouse/touch position
        const deltaX = coords.x - state.startMouseX;
        const deltaY = coords.y - state.startMouseY;
        
        const {{ startCropLeft, startCropTop, startCropWidth, startCropHeight, resizeDirection, aspectRatio, aspectMode }} = state;

        let newLeft = startCropLeft;
        let newTop = startCropTop;
        let newWidth = startCropWidth;
        let newHeight = startCropHeight;

        // 1. Calculate unconstrained dimensions
        if (resizeDirection.includes('e')) {{
            newWidth = startCropWidth + deltaX;
        }}
        if (resizeDirection.includes('w')) {{
            newWidth = startCropWidth - deltaX;
        }}
        if (resizeDirection.includes('s')) {{
            newHeight = startCropHeight + deltaY;
        }}
        if (resizeDirection.includes('n')) {{
            newHeight = startCropHeight - deltaY;
        }}

        // 2. Apply aspect ratio constraints
        if (aspectRatio && aspectMode !== "free") {{
            const isHorizontalHandle = resizeDirection.includes('e') || resizeDirection.includes('w');
            const isVerticalHandle = resizeDirection.includes('n') || resizeDirection.includes('s');

            if (isHorizontalHandle && !isVerticalHandle) {{
                // Horizontal only resize (n/s/w/e) -> constrain height
                newHeight = newWidth / aspectRatio;
            }} else if (isVerticalHandle && !isHorizontalHandle) {{
                // Vertical only resize (n/s/w/e) -> constrain width
                newWidth = newHeight * aspectRatio;
            }} else {{ 
                // Corner resize (nw, ne, sw, se) -> use the larger movement direction
                const horizontalMovement = Math.abs(newWidth - startCropWidth);
                const verticalMovement = Math.abs(newHeight - startCropHeight);
                
                if (horizontalMovement > verticalMovement) {{
                    newHeight = newWidth / aspectRatio;
                }} else {{
                    newWidth = newHeight * aspectRatio;
                }}
            }}
        }}
        
        // 3. Recalculate position based on the final, constrained dimensions.
        if (resizeDirection.includes('n')) {{
            // New top = Old top + (Old height - New constrained height)
            newTop = startCropTop + (startCropHeight - newHeight);
        }}
        if (resizeDirection.includes('w')) {{
            // New left = Old left + (Old width - New constrained width)
            newLeft = startCropLeft + (startCropWidth - newWidth);
        }}
        
        setCropDimensions(newLeft, newTop, newWidth, newHeight);
      }}, 16),
      
      stop() {{
        state.isResizing = false;
        
        document.removeEventListener('mousemove', resizeHandlers.move);
        document.removeEventListener('mouseup', resizeHandlers.stop);
        document.removeEventListener('touchmove', resizeHandlers.move);
        document.removeEventListener('touchend', resizeHandlers.stop);
        
        document.removeEventListener('mousemove', updateMousePos);
        document.removeEventListener('touchmove', updateMousePosTouch);
        stopAutoScroll();
      }}
    }};
    
    // --- ZOOM / PINCH HANDLERS ---

    // Mouse wheel zoom handler (for media-viewer)
    function handleMouseWheelZoom(e) {{
      if (state.mediaType === 'audio') return;
      e.preventDefault();

      // Zoom factor calculation: 10% change per scroll tick
      const zoomFactor = e.deltaY < 0 ? 1.1 : 1 / 1.1;
      const newZoom = state.zoom * zoomFactor;
      
      // Calculate scroll position offset for zoom center
      const viewer = elements.mediaViewer;
      const rect = viewer.getBoundingClientRect();
      
      // Mouse position relative to viewer (before scrolling)
      const relativeX = e.clientX - rect.left;
      const relativeY = e.clientY - rect.top;

      // Mouse position relative to media content (including current scroll)
      const contentX = viewer.scrollLeft + relativeX;
      const contentY = viewer.scrollTop + relativeY;

      // Set the new zoom level
      setMediaZoom(newZoom);

      // Re-calculate the content position after zoom and set new scroll position
      const newContentX = contentX * (newZoom / state.zoom);
      const newContentY = contentY * (newZoom / state.zoom);

      // Scroll to keep the content under the mouse cursor
      viewer.scrollLeft = newContentX - relativeX;
      viewer.scrollTop = newContentY - relativeY;
    }}

    // Pinch handlers (for touch screens)
    function startPinch(type, e) {{
      if (e.touches.length !== 2) return;
      if (type === 'media' && state.mediaType !== 'image' && state.mediaType !== 'video') return;
      
      state.isPinching = true;
      state.pinchType = type;
      state.pinchInitialDist = utils.getDistance(e.touches[0], e.touches[1]);
      
      if (type === 'crop') {{
        state.pinchInitialWidth = parseFloat(elements.crop.style.width);
        state.pinchInitialHeight = parseFloat(elements.crop.style.height);
        state.pinchInitialLeft = parseFloat(elements.crop.style.left);
        state.pinchInitialTop = parseFloat(elements.crop.style.top);
      }} else {{ // media pinch
        state.pinchInitialZoom = state.zoom;
        state.pinchInitialMid = utils.getMidpoint(e.touches[0], e.touches[1]);
        const viewerRect = elements.mediaViewer.getBoundingClientRect();
        state.pinchInitialRelX = state.pinchInitialMid.x - viewerRect.left;
        state.pinchInitialRelY = state.pinchInitialMid.y - viewerRect.top;
        state.pinchInitialScrollLeft = elements.mediaViewer.scrollLeft;
        state.pinchInitialScrollTop = elements.mediaViewer.scrollTop;
      }}
      document.addEventListener('touchmove', handlePinchMove, {{ passive: false }});
      document.addEventListener('touchend', handlePinchEnd);
    }}

    function handlePinchMove(e) {{
      if (!state.isPinching || e.touches.length !== 2) return;
      e.preventDefault();
      
      const newDist = utils.getDistance(e.touches[0], e.touches[1]);
      const factor = newDist / state.pinchInitialDist;
      
      if (state.pinchType === 'crop') {{
        // Pinch-to-Resize Crop Box
        let newWidth = state.pinchInitialWidth * factor;
        let newHeight = state.pinchInitialHeight * factor;
        
        // Apply aspect ratio
        const dims = applyAspectRatio(newWidth, newHeight);
        newWidth = dims.width;
        newHeight = dims.height;
        
        // Center the resize effect
        const deltaW = newWidth - state.pinchInitialWidth;
        const deltaH = newHeight - state.pinchInitialHeight;
        const newLeft = state.pinchInitialLeft - deltaW / 2;
        const newTop = state.pinchInitialTop - deltaH / 2;
        
        setCropDimensions(newLeft, newTop, newWidth, newHeight);
      }} else {{
        // Pinch-to-Zoom Media
        const newZoom = state.pinchInitialZoom * factor;
        const oldZoom = state.zoom;
        setMediaZoom(newZoom);
        
        // Pan/Scroll to keep the midpoint centered
        const newFactor = newZoom / oldZoom;
        const viewer = elements.mediaViewer;
        
        viewer.scrollLeft = state.pinchInitialScrollLeft * newFactor + state.pinchInitialRelX * (newFactor - 1);
        viewer.scrollTop = state.pinchInitialScrollTop * newFactor + state.pinchInitialRelY * (newFactor - 1);
      }}
    }}

    function handlePinchEnd() {{
      state.isPinching = false;
      state.pinchType = '';
      document.removeEventListener('touchmove', handlePinchMove);
      document.removeEventListener('touchend', handlePinchEnd);
    }}
    
    function handleMediaTouchStart(e) {{
      // Prevent default browser zoom/scroll on media wrapper
      if (e.touches.length === 2 && state.mediaType !== 'audio') {{
        e.preventDefault();
        startPinch('media', e);
      }} else if (e.touches.length === 1 && state.mediaType !== 'audio') {{
        // Single touch for panning
        // We'll let the browser handle single-touch panning/scrolling, 
        // unless it interferes with dragHandlers (which it shouldn't if touchstart on media-wrapper is used for pinch only)
      }}
    }}

    // --- AUTO-SCROLL LOGIC ---

    function updateMousePos(e) {{
      // For mouse events
      state.mouseX = e.clientX;
      state.mouseY = e.clientY;
    }}

    function updateMousePosTouch(e) {{
      // For touch events
      if (e.touches.length > 0) {{
        state.mouseX = e.touches[0].clientX;
        state.mouseY = e.touches[0].clientY;
      }}
    }}

    function startAutoScroll() {{
      if (state.autoScrollActive) return; // Prevent multiple loops
      state.autoScrollActive = true;
      autoScrollLoop();
    }}

    function stopAutoScroll() {{
      state.autoScrollActive = false;
    }}

    // Animation loop for smooth auto-scrolling
    function autoScrollLoop() {{
      if (!state.autoScrollActive) return;
      
      const viewer = elements.mediaViewer;
      const rect = viewer.getBoundingClientRect();
      const edgeSize = 50; // Pixels from the edge to start scrolling
      const scrollSpeed = 10;
      
      let dx = 0, dy = 0;
      
      // Horizontal Scroll Logic
      if (state.mouseX < rect.left + edgeSize) {{
        // Scroll left, speed up as cursor gets closer to the edge
        dx = -scrollSpeed * ((rect.left + edgeSize - state.mouseX) / edgeSize);
      }} else if (state.mouseX > rect.right - edgeSize) {{
        // Scroll right
        dx = scrollSpeed * ((state.mouseX - (rect.right - edgeSize)) / edgeSize);
      }}
      
      // Vertical Scroll Logic
      if (state.mouseY < rect.top + edgeSize) {{
        // Scroll up
        dy = -scrollSpeed * ((rect.top + edgeSize - state.mouseY) / edgeSize);
      }} else if (state.mouseY > rect.bottom - edgeSize) {{
        // Scroll down
        dy = scrollSpeed * ((state.mouseY - (rect.bottom - edgeSize)) / edgeSize);
      }}
      
      if (dx !== 0 || dy !== 0) {{
        // Apply scroll
        viewer.scrollLeft += dx;
        viewer.scrollTop += dy;
        
        // IMPORTANT: Adjust the drag/resize start position so the crop box stays locked to the cursor
        state.startMouseX -= dx;
        state.startMouseY -= dy;
        
        // Re-run the drag/resize move logic to update crop box position
        if (state.isDragging || state.isResizing) {{
            // We fake a mouse move event using the latest cursor position, 
            // but the deltas for drag/resize are calculated from the adjusted startMouseX/Y
            const fakeEvent = {{ clientX: state.mouseX, clientY: state.mouseY }};
            if (state.isDragging) {{
                dragHandlers.move(fakeEvent);
            }} else if (state.isResizing) {{
                resizeHandlers.move(fakeEvent);
            }}
        }}
      }}
      
      // Continue the loop
      requestAnimationFrame(autoScrollLoop);
    }}

    // --- UTILITY / UI FUNCTIONS ---

    // Keyboard navigation support
    function handleKeyboard(e) {{
      if (state.isHelpVisible && e.key === 'Escape') {{
        toggleHelp();
        return;
      }}
      
      if (state.isHelpVisible || state.mediaType === 'audio' || !elements.crop) return;
      
      const step = e.shiftKey ? 1 : 10; // Fine adjustment with Shift
      const currentLeft = parseFloat(elements.crop.style.left) || 0;
      const currentTop = parseFloat(elements.crop.style.top) || 0;
      const currentWidth = parseFloat(elements.crop.style.width) || 0;
      const currentHeight = parseFloat(elements.crop.style.height) || 0;
      
      let newLeft = currentLeft;
      let newTop = currentTop;
      
      switch (e.key) {{
        case 'ArrowLeft':
          e.preventDefault();
          newLeft = Math.max(0, currentLeft - step);
          break;
        case 'ArrowRight':
          e.preventDefault();
          newLeft = Math.min(state.mediaWidth - currentWidth, currentLeft + step);
          break;
        case 'ArrowUp':
          e.preventDefault();
          newTop = Math.max(0, currentTop - step);
          break;
        case 'ArrowDown':
          e.preventDefault();
          newTop = Math.min(state.mediaHeight - currentHeight, currentTop + step);
          break;
        case 'c':
        case 'C':
          e.preventDefault();
          centerCrop();
          break;
        case 'g':
        case 'G':
          e.preventDefault();
          toggleGrid();
          break;
        case 'Enter':
          // Only save if the focus is on the crop box, not an input field
          if (document.activeElement === elements.crop) {{
            e.preventDefault();
            saveCrop();
          }}
          break;
        default:
          return;
      }}
      
      if (newLeft !== currentLeft || newTop !== currentTop) {{
        setCropDimensions(newLeft, newTop, currentWidth, currentHeight, true);
        
        // Auto-scroll the viewer if the crop box moves near the edge
        const viewer = elements.mediaViewer;
        const cropRect = elements.crop.getBoundingClientRect();
        const viewerRect = viewer.getBoundingClientRect();
        
        const scrollMargin = 50; // Pixels from the edge to trigger a scroll
        
        // Horizontal scroll
        if (cropRect.left < viewerRect.left + scrollMargin) {{
            viewer.scrollLeft -= step;
        }} else if (cropRect.right > viewerRect.right - scrollMargin) {{
            viewer.scrollLeft += step;
        }}
        
        // Vertical scroll
        if (cropRect.top < viewerRect.top + scrollMargin) {{
            viewer.scrollTop -= step;
        }} else if (cropRect.bottom > viewerRect.bottom - scrollMargin) {{
            viewer.scrollTop += step;
        }}
      }}
    }}

    function toggleGrid() {{
      state.showGrid = !state.showGrid;
      if(elements.crop) elements.crop.classList.toggle('show-grid', state.showGrid);
    }}

    function centerCrop() {{
      if (state.mediaType === 'audio' || !elements.crop) return;
      
      const currentWidth = parseFloat(elements.crop.style.width) || 0;
      const currentHeight = parseFloat(elements.crop.style.height) || 0;
      
      const centerX = (state.mediaWidth - currentWidth) / 2;
      const centerY = (state.mediaHeight - currentHeight) / 2;
      
      setCropDimensions(centerX, centerY, currentWidth, currentHeight, true);

      // Scroll the container to bring the newly centered crop box into view.
      const viewer = document.querySelector('.media-viewer'); 
      viewer.scrollLeft = centerX + (currentWidth / 2) - (viewer.clientWidth / 2);
      viewer.scrollTop = centerY + (currentHeight / 2) - (viewer.clientHeight / 2);
    }}

    function resetCropSize() {{
      if (state.mediaType === 'audio' || !elements.crop) return;
      setMediaZoom(1); // Reset zoom level
      positionCropBox();
      elements.aspectSelect.value = "free";
      state.aspectMode = "free";
      state.aspectRatio = null;
      elements.customRatio.classList.remove('visible');
    }}

    function toggleHelp() {{
      state.isHelpVisible = !state.isHelpVisible;
      elements.helpModal.style.display = state.isHelpVisible ? 'flex' : 'none';
      if (!state.isHelpVisible && elements.crop) {{
        elements.crop.focus(); // Return focus to crop box on close
      }}
    }}

    // Context menu handling
    function showContextMenu(e) {{
      if (state.mediaType === 'audio' || !elements.crop) return;
      e.preventDefault();
      const menu = elements.contextMenu;
      menu.style.display = 'block';
      // Ensure menu is not off-screen
      let left = e.clientX;
      let top = e.clientY;
      if (left + menu.offsetWidth > window.innerWidth) left = window.innerWidth - menu.offsetWidth - 10;
      if (top + menu.offsetHeight > window.innerHeight) top = window.innerHeight - menu.offsetHeight - 10;
      
      menu.style.left = left + 'px';
      menu.style.top = top + 'px';
      
      document.addEventListener('click', hideContextMenu, {{ once: true }});
    }}

    function hideContextMenu() {{
      if (elements.contextMenu) {{
        elements.contextMenu.style.display = 'none';
      }}
    }}

    // Aspect ratio handling
    function handleAspectRatioChange(e) {{
      state.aspectMode = e.target.value;
      
      if (state.aspectMode === "custom") {{
        elements.customRatio.classList.add('visible');
        updateCustomAspectRatio();
      }} else {{
        elements.customRatio.classList.remove('visible');
        
        if (state.aspectMode === "free") {{
          state.aspectRatio = null;
        }} else if (state.aspectMode === "original") {{
          if (state.naturalWidth && state.naturalHeight) {{
            state.aspectRatio = state.naturalWidth / state.naturalHeight;
          }} else {{
            state.aspectRatio = null;
          }}
        }} else {{
          const parts = state.aspectMode.split(":");
          state.aspectRatio = parseFloat(parts[0]) / parseFloat(parts[1]);
        }}
        // Automatically apply the selected aspect ratio to the crop box
        applyCurrentAspectRatio();
      }}
    }}

    function updateCustomAspectRatio() {{
      const w = parseFloat(elements.customW.value);
      const h = parseFloat(elements.customH.value);
      
      if (isNaN(w) || isNaN(h) || h === 0) {{
          state.aspectRatio = null;
          return;
      }}
      
      state.aspectRatio = w / h;
      if (state.aspectMode === "custom") {{
        applyCurrentAspectRatio();
      }}
    }}

    function applyCurrentAspectRatio() {{
      if (!state.aspectRatio || !state.isInitialized || state.mediaType === 'audio' || !elements.crop) return;
      
      const currentLeft = parseFloat(elements.crop.style.left) || 0;
      const currentTop = parseFloat(elements.crop.style.top) || 0;
      const currentWidth = parseFloat(elements.crop.style.width) || 0;
      
      // Base the new height on the current width to maintain the position of the left edge
      const newHeight = Math.round(currentWidth / state.aspectRatio);
      
      // Check if new height is valid and fits
      if (newHeight > 30 && newHeight <= state.mediaHeight) {{
        setCropDimensions(currentLeft, currentTop, currentWidth, newHeight, true);
      }} else {{
        // If the new height is too big, base the calculation on current height (maintaining top edge)
        const currentHeight = parseFloat(elements.crop.style.height) || 0;
        const newWidth = Math.round(currentHeight * state.aspectRatio);
        setCropDimensions(currentLeft, currentTop, newWidth, currentHeight, true);
      }}
    }}

    // Enhanced save function with better scaling
    function saveCrop() {{
      if (state.mediaType === 'audio' || !elements.crop) {{
        alert("Crop function is not applicable for this media type.");
        return;
      }}
      
      // Ensure media dimensions are up-to-date
      updateMediaDimensions();
      
      const left = parseFloat(elements.crop.style.left) || 0;
      const top = parseFloat(elements.crop.style.top) || 0;
      const width = parseFloat(elements.crop.style.width) || 0;
      const height = parseFloat(elements.crop.style.height) || 0;
      
      // Calculate precise scaling factors from displayed size to natural size
      let scaleX = 1, scaleY = 1;
      
      if (state.naturalWidth && state.naturalHeight && state.mediaWidth && state.mediaHeight) {{
        // Scale factor: Natural Size / Displayed Size
        scaleX = state.naturalWidth / state.mediaWidth;
        scaleY = state.naturalHeight / state.mediaHeight;
      }}
      
      // Apply scaling to get the final pixel coordinates for FFmpeg
      const finalX = Math.round(left * scaleX);
      const finalY = Math.round(top * scaleY);
      const finalW = Math.round(width * scaleX);
      const finalH = Math.round(height * scaleY);
      
      // Post data to server
      fetch("/save", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{ 
          x: finalX, 
          y: finalY, 
          w: finalW, 
          h: finalH,
          scaleX: scaleX,
          scaleY: scaleY,
          mediaType: state.mediaType
        }})
      }})
      .then(response => {{
        if (response.ok) {{
          // Create and show a more informative notification
          const notification = document.createElement('div');
          notification.className = 'notification';
          notification.innerHTML = `
            <div class="notification-title">Crop Saved Successfully!</div>
            <div class="notification-code">crop=${{finalW}}:${{finalH}}:${{finalX}}:${{finalY}}</div>
            <div class="notification-subtitle">FFmpeg command printed to terminal.</div>
          `;
          
          document.body.appendChild(notification);
          // Set a timeout to fade out and remove the notification
          setTimeout(() => document.body.removeChild(notification), 3000);
        }} else {{
          response.json().then(data => alert("Error: " + (data.message || "Could not save crop parameters"))).catch(() => alert("Error: Could not save crop parameters"));
        }}
      }})
      .catch(error => {{
        alert("Network Error: " + error.message);
      }});
    }}

    // Window resize handler with debouncing
    const handleWindowResize = utils.debounce(() => {{
      if (!state.isInitialized) return;
      
      // Re-evaluate displayed media dimensions
      updateMediaDimensions();
      updateCropInfo();
      
      // Adjust crop box if it's outside the new bounds (e.g. if the image was scaled down by the browser)
      if (elements.crop) {{
        const left = parseFloat(elements.crop.style.left) || 0;
        const top = parseFloat(elements.crop.style.top) || 0;
        const width = parseFloat(elements.crop.style.width) || 0;
        const height = parseFloat(elements.crop.style.height) || 0;
        
        // Use setCropDimensions to auto-clamp if necessary
        setCropDimensions(left, top, width, height, true);
      }}
    }}, 200);

    // Event listener setup
    function setupEventListeners() {{
      // Theme toggle
      elements.themeToggle.addEventListener("click", toggleTheme);
      
      // Crop box interactions
      if (elements.crop) {{
        elements.crop.addEventListener("mousedown", dragHandlers.start);
        elements.crop.addEventListener("touchstart", dragHandlers.start, {{ passive: false }});
        elements.crop.addEventListener("contextmenu", showContextMenu);
        elements.crop.addEventListener("dblclick", centerCrop);
      
        // Resize handles
        document.querySelectorAll('.resize-handle').forEach(handle => {{
          handle.addEventListener("mousedown", resizeHandlers.start);
          handle.addEventListener("touchstart", resizeHandlers.start, {{ passive: false }});
        }});
      }}
      
      // Media wrapper for outside touches (pinch-to-zoom)
      if (elements.mediaWrapper) {{
          elements.mediaWrapper.addEventListener("touchstart", handleMediaTouchStart, {{ passive: false }});
      }}
      
      // Mouse wheel zoom listener
      if (elements.mediaViewer) {{
          elements.mediaViewer.addEventListener("wheel", handleMouseWheelZoom, {{ passive: false }});
      }}
      
      // Aspect ratio controls
      elements.aspectSelect.addEventListener("change", handleAspectRatioChange);
      elements.customW.addEventListener("input", utils.debounce(updateCustomAspectRatio, 300));
      elements.customH.addEventListener("input", utils.debounce(updateCustomAspectRatio, 300));
      
      // Keyboard navigation
      document.addEventListener("keydown", handleKeyboard);
      
      // Window resize
      window.addEventListener("resize", handleWindowResize);
      
      // Prevent unwanted selections and context menus
      document.addEventListener("selectstart", e => {{
        if (state.isDragging || state.isResizing) e.preventDefault();
      }});
      
      // Click outside to hide context menu
      document.addEventListener("click", (e) => {{
        if (elements.contextMenu && !elements.contextMenu.contains(e.target)) {{
          hideContextMenu();
        }}
      }});

      // Close help modal when clicking outside
      elements.helpModal.addEventListener('click', (e) => {{
        if (e.target === elements.helpModal) {{
          toggleHelp();
        }}
      }});
    }}

    // Initialize everything when DOM is ready
    document.addEventListener("DOMContentLoaded", function() {{
      initializeTheme(); // Initialize theme first
      setupEventListeners();
      
      if (elements.media) {{
        // Use loadedmetadata for video/audio, complete/canplay for image fallback
        if (elements.media.complete || elements.media.readyState >= 2) {{
          initializeCrop();
        }} else {{
          elements.media.addEventListener('loadedmetadata', initializeCrop);
          elements.media.addEventListener('canplay', initializeCrop);
          // Fallback for some images where load event is sufficient
          elements.media.addEventListener('load', initializeCrop);
        }}
      }} else {{
        // For unsupported formats, still initialize UI
        setTimeout(() => {{
          initializeCrop();
        }}, 100);
      }}
    }});
  </script>
</body>
</html>"""
            # --- END HTML ---
            
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        elif path == "/file":
            # IMPROVEMENT: Stream file in chunks for large media and handle Range requests for seeking.
            try:
                if not os.path.exists(self.server.media_file) or not os.access(self.server.media_file, os.R_OK):
                    self.send_error(404, f"File not found or not readable: {self.server.media_file}")
                    return

                file_size = os.path.getsize(self.server.media_file)
                ext = os.path.splitext(self.server.media_file)[1].lower()
                mime_type = mimetypes.guess_type(self.server.media_file)[0] or 'application/octet-stream'


                range_header = self.headers.get('Range')
                if range_header:
                    # Handle Range request (for video seeking/streaming)
                    try:
                        # Clean and parse the range header
                        range_header = range_header.strip().lower().replace('bytes=', '')
                        
                        # Handle multiple ranges or complex scenarios by simply rejecting them (browser typically sends single)
                        if ',' in range_header:
                             self.send_error(416) # Range Not Satisfiable
                             return
                             
                        start_str, end_str = range_header.split('-')
                        start = int(start_str) if start_str else 0
                        end = int(end_str) if end_str else file_size - 1
                        
                        # Sanity checks
                        if start < 0 or end < start or end >= file_size:
                            self.send_response(416) # Range Not Satisfiable
                            self.send_header('Content-Range', f'bytes */{file_size}')
                            self.end_headers()
                            return
                        
                        length = end - start + 1
                        self.send_response(206) # Partial Content
                        self.send_header('Content-type', mime_type)
                        self.send_header('Accept-Ranges', 'bytes')
                        self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                        self.send_header('Content-Length', str(length))
                        self.send_header("Last-Modified", self.date_time_string(os.path.getmtime(self.server.media_file)))
                        self.end_headers()

                        with open(self.server.media_file, 'rb') as f:
                            f.seek(start)
                            remaining = length
                            # Chunk size for partial content
                            chunk_size = 65536 # 64KB chunks
                            while remaining > 0:
                                chunk = f.read(min(remaining, chunk_size))
                                if not chunk: break
                                self.wfile.write(chunk)
                                remaining -= len(chunk)
                    except ValueError:
                        self.send_error(400, "Invalid Range header format")
                else:
                    # Handle full file request by streaming
                    self.send_response(200)
                    self.send_header("Content-type", mime_type)
                    self.send_header("Content-Length", str(file_size))
                    self.send_header("Accept-Ranges", "bytes")
                    self.send_header("Last-Modified", self.date_time_string(os.path.getmtime(self.server.media_file)))
                    self.end_headers()
                    
                    with open(self.server.media_file, 'rb') as f:
                        # Chunk size for full content stream (larger for better throughput)
                        chunk_size = 1024 * 1024 # 1MB chunks
                        while True:
                            chunk = f.read(chunk_size)
                            if not chunk: break
                            self.wfile.write(chunk)
                            
            except FileNotFoundError:
                self.send_error(404, f"File not found: {self.server.media_file}")
            except PermissionError:
                self.send_error(403, f"Permission denied: {self.server.media_file}")
            except BrokenPipeError:
                if self.server.verbose: self.log_message("Client disconnected (Broken Pipe).")
            except Exception as e:
                self.send_error(500, f"File error: {str(e)}")
                
        else:
            self.send_error(404, "Not Found")

    def do_HEAD(self):
        """Handle HEAD requests for file size information (used by JS to get fileSizeInfo)"""
        if urlparse(self.path).path == "/file":
            try:
                # Ensure the file is accessible before reporting size
                if not os.path.exists(self.server.media_file) or not os.access(self.server.media_file, os.R_OK):
                    self.send_error(404, "File not found or not readable")
                    return
                
                file_size = os.path.getsize(self.server.media_file)
                ext = os.path.splitext(self.server.media_file)[1].lower()
                mime_type = mimetypes.guess_type(self.server.media_file)[0] or 'application/octet-stream'
                
                self.send_response(200)
                self.send_header("Content-Length", str(file_size))
                self.send_header("Content-Type", mime_type)
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Last-Modified", self.date_time_string(os.path.getmtime(self.server.media_file)))
                self.end_headers()
            except Exception as e:
                self.send_error(500, f"Error getting file info: {str(e)}")
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        """Handles POST request to save crop coordinates and print FFmpeg command."""
        if self.path == "/save":
            try:
                length = int(self.headers.get("Content-Length", 0))
                if length > 10000:
                    self.send_error(413, "Payload too large")
                    return
                    
                body = self.rfile.read(length)
                data = json.loads(body.decode("utf-8"))
                
                # --- Input Validation ---
                required_fields = ['w', 'h', 'x', 'y']
                for field in required_fields:
                    if field not in data or not isinstance(data[field], (int, float)) or data[field] < 0:
                        self.send_error(400, f"Invalid or missing {field} parameter")
                        return
                
                # Ensure integer conversion for FFmpeg
                w = int(data['w'])
                h = int(data['h'])
                x = int(data['x'])
                y = int(data['y'])

                # --- FFmpeg Command Generation (Enhanced) ---
                input_file_path = self.server.media_file
                path_part, ext_part = os.path.splitext(input_file_path)
                
                # Use a cleaner, numbered or descriptive output file name to prevent overwrite on multiple runs
                i = 1
                while True:
                    output_file_name = f"{path_part}_crop_{w}x{h}_{i}{ext_part}"
                    if not os.path.exists(output_file_name):
                        break
                    i += 1
                
                # Use quoted paths for robustness against spaces and special characters in file names
                # Added '-c:a copy -c:v copy' for stream copy to avoid re-encoding if possible, 
                # but this might be incompatible with the crop filter for all video formats. 
                # A safer command uses '-c:v libx264 -crf 23 -preset veryfast' for a good balance of speed/quality.
                # Let's provide the simplest, most compatible command.
                
                # The video filter is applied to the video stream, so we must re-encode video.
                # If it's an image, the '-vcodec png' or similar is implicitly used by ffmpeg when output format is image.
                
                if data.get('mediaType') == 'video':
                    # Best practice for video: re-encode H.264
                    ffmpeg_command = f'\nffmpeg -i "{input_file_path}" -vf "crop={w}:{h}:{x}:{y}" -c:v libx264 -preset veryfast -crf 23 -c:a aac -b:a 192k "{output_file_name}"\n'
                elif data.get('mediaType') == 'image':
                    # Best practice for image (simple crop, same format)
                    ffmpeg_command = f'\nffmpeg -i "{input_file_path}" -vf "crop={w}:{h}:{x}:{y}" -q:v 1 "{output_file_name}"\n'
                else:
                    # Generic fallback (stream copy audio, re-encode video/other)
                    # NOTE: A simple stream copy (-c copy) *will fail* if cropping a video.
                    ffmpeg_command = f'\nffmpeg -i "{input_file_path}" -vf "crop={w}:{h}:{x}:{y}" -c:v libx264 -preset veryfast -crf 23 -c:a copy "{output_file_name}"\n'

                print(ffmpeg_command)
                
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                
                # Send back the crop filter string for the notification
                self.wfile.write(json.dumps({
                    "success": True,
                    "message": "Crop parameters saved successfully",
                    "crop_filter": f"crop={w}:{h}:{x}:{y}",
                    "timestamp": self.date_time_string()
                }).encode("utf-8"))
                
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON data in request body")
            except KeyError as e:
                self.send_error(400, f"Missing required field: {e}")
            except Exception as e:
                # Print exception to server console for debugging
                print(f"Server POST Error: {e}")
                self.send_error(500, f"Server error: {str(e)}")
        else:
            self.send_error(404, "Not Found")

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Range")
        self.send_header("Access-Control-Max-Age", "86400") # Cache preflight for 24h
        self.end_headers()