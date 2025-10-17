#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse


class CropHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        if self.server.verbose:
            super().log_message(format, *args)

    def do_GET(self):
        path = urlparse(self.path).path
        ext = os.path.splitext(self.server.media_file)[1].lower()

        # Formats that are natively supported by most modern web browsers
        supported_image_exts = [
            ".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".svg", ".ico", ".avif"
        ]
      
        supported_video_exts = [
            ".mp4", ".webm", ".ogv", ".mov" # MOV support can depend on the codec
        ]
      
        supported_audio_exts = [
            ".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac", ".opus"
        ]

        if path == "/":
            # Add a cache buster to the media URL to prevent browser caching issues
            cache_buster = int(time.time())
          
            # Determine media type and create appropriate tag
            if ext in supported_image_exts:
                media_tag = f'<img id="media" src="/file?v={cache_buster}" onload="initializeCrop()" draggable="false" alt="Media file" />'
                media_type = "image"
            elif ext in supported_video_exts:
                media_tag = f'<video id="media" controls preload="metadata" src="/file?v={cache_buster}" onloadeddata="initializeCrop()" draggable="false"></video>'
                media_type = "video"
            elif ext in supported_audio_exts:
                media_tag = f'<audio id="media" controls preload="metadata" src="/file?v={cache_buster}" onloadeddata="initializeCrop()"></audio>'
                media_type = "audio"
            else:
                # Fallback for formats not previewable in the browser
                media_tag = '<div id="unsupported"><div class="unsupported-content"><div class="unsupported-icon">📁</div><div class="unsupported-text">Format not supported for preview</div><div class="unsupported-subtext">You can still set crop coordinates</div></div></div>'
                media_type = "unsupported"

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
    }}
  
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      background: var(--bg-main);
      color: var(--text-main);
      user-select: none;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
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
      box-shadow: 0 0 0 3px rgba(0, 255, 65, 0.1);
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
      box-shadow: 0 4px 12px rgba(0, 255, 65, 0.3);
    }}

    .form-button:active {{
      transform: translateY(0);
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
      background: radial-gradient(circle at center, #1a1a1a 0%, var(--bg-main) 100%);
      min-height: 0;
      overflow: auto; /* FIXED: Scrollbars now live here, outside the media content */
      /* Firefox scrollbar styling */
      scrollbar-width: auto;
      scrollbar-color: var(--primary) var(--bg-control);
    }}
  
    /* FIXED: Custom Green Scrollbars for Media Viewer */
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
      /* overflow: auto;  <-- REMOVED to prevent inner scrollbars */
      background: #000;
      box-shadow: var(--shadow-heavy);
      /* max-width/height removed to allow container to grow to media size */
      display: inline-block; /* Makes container wrap the media-wrapper */
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
      background: rgba(0, 255, 65, 0.08);
      box-shadow: 
        0 0 0 9999px rgba(0, 0, 0, 0.7),
        inset 0 0 0 1px rgba(0, 255, 65, 0.3);
      transition: box-shadow 0.2s ease;
    }}

    .crop-box:hover {{
      box-shadow: 
        0 0 0 9999px rgba(0, 0, 0, 0.75),
        inset 0 0 0 1px rgba(0, 255, 65, 0.5),
        0 0 20px rgba(0, 255, 65, 0.4);
    }}

    .crop-box.dragging {{
      cursor: grabbing;
      box-shadow: 
        0 0 0 9999px rgba(0, 0, 0, 0.8),
        inset 0 0 0 1px rgba(0, 255, 65, 0.7),
        0 0 25px rgba(0, 255, 65, 0.6);
    }}

    .crop-box.show-grid::before {{
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-image: 
        linear-gradient(to right, rgba(0, 255, 65, 0.3) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(0, 255, 65, 0.3) 1px, transparent 1px);
      background-size: 33.33% 33.33%;
      pointer-events: none;
    }}

    /* Resize Handles */
    .resize-handle {{
      position: absolute;
      background: var(--primary);
      width: 16px;
      height: 16px;
      border: 2px solid #000;
      border-radius: 50%;
      z-index: 51;
      transition: all 0.2s ease;
      transform: translate(-50%, -50%);
    }}

    .resize-handle:hover {{
      background: #fff;
      transform: translate(-50%, -50%) scale(1.3);
      box-shadow: 0 0 8px rgba(0, 255, 65, 0.5);
    }}

    .resize-handle.nw {{ top: 0; left: 0; cursor: nw-resize; }}
    .resize-handle.ne {{ top: 0; right: 0; cursor: ne-resize; transform: translate(50%, -50%); }}
    .resize-handle.sw {{ bottom: 0; left: 0; cursor: sw-resize; transform: translate(-50%, 50%); }}
    .resize-handle.se {{ bottom: 0; right: 0; cursor: se-resize; transform: translate(50%, 50%); }}
    .resize-handle.n {{ top: 0; left: 50%; cursor: n-resize; }}
    .resize-handle.s {{ bottom: 0; left: 50%; cursor: s-resize; transform: translate(-50%, 50%); }}
    .resize-handle.w {{ left: 0; top: 50%; cursor: w-resize; }}
    .resize-handle.e {{ right: 0; top: 50%; cursor: e-resize; transform: translate(50%, -50%); }}

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
    }}

    .notification-subtitle {{
      font-size: 13px;
      color: var(--text-muted);
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
<body>
  <div class="loading" id="loadingIndicator">
    <div class="spinner"></div>
    <div class="loading-text">Loading media...</div>
  </div>

  <div class="header-bar">
    <div class="app-title">MediaCrop - Visual FFmpeg Crop Tool</div>
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
          <input type="text" id="customW" class="form-input" value="16" placeholder="W">
          <div class="ratio-separator">:</div>
          <input type="text" id="customH" class="form-input" value="9" placeholder="H">
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
          <button class="form-button" onclick="saveCrop()" style="background: linear-gradient(135deg, #4CAF50, #45a049); font-size: 14px; padding: 12px;">
            💾 Save Coordinates
          </button>
        </div>
      </div>

      <div class="sidebar-section">
        <div class="section-title info">Crop Info</div>
      
        <div class="info-stats">
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
        </div>
      </div>
    </div>

    <div class="media-viewer">
      <div id="container">
        <div id="media-wrapper">
          {media_tag}
          <div id="crop" class="crop-box" style="left:50px;top:50px;width:200px;height:150px;" tabindex="0" role="img" aria-label="Crop selection area">
            <div class="resize-handle nw"></div>
            <div class="resize-handle ne"></div>
            <div class="resize-handle sw"></div>
            <div class="resize-handle se"></div>
            <div class="resize-handle n"></div>
            <div class="resize-handle s"></div>
            <div class="resize-handle w"></div>
            <div class="resize-handle e"></div>
          </div>
        </div>
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
      fileSizeInfo: document.getElementById("fileSizeInfo"),
      loadingIndicator: document.getElementById("loadingIndicator"),
      helpModal: document.getElementById("helpModal"),
      contextMenu: document.getElementById("contextMenu"),
      mediaWrapper: document.getElementById("media-wrapper"),
      mediaViewer: document.querySelector(".media-viewer")
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
          return {{
            x: e.touches[0].clientX,
            y: e.touches[0].clientY
          }};
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
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
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
          y: (t1.clientY + t2.clientY) / 2
        }};
      }}
    }};

    // Enhanced initialization
    function initializeCrop() {{
      setTimeout(() => {{
        updateMediaDimensions();
        updateFileInfo();
        positionCropBox();
        updateCropInfo();
        setMediaZoom(1);
        state.isInitialized = true;
        hideLoading();
      
        // Initial focus for accessibility
        elements.crop.focus();
      }}, 150);
    }}

    function hideLoading() {{
      elements.loadingIndicator.style.display = 'none';
    }}

    // Enhanced media dimensions tracking
    function updateMediaDimensions() {{
      if (!elements.media) {{
        // For unsupported formats
        if (state.mediaType === 'unsupported') {{
          state.mediaWidth = 500;
          state.mediaHeight = 300;
          state.naturalWidth = 500;
          state.naturalHeight = 300;
        }}
        return;
      }}
    
      const mediaRect = elements.media.getBoundingClientRect();
      state.mediaWidth = elements.media.scrollWidth;
      state.mediaHeight = elements.media.scrollHeight;
    
      // Get natural dimensions for scaling calculations
      if (elements.media.tagName === 'IMG') {{
        state.naturalWidth = elements.media.naturalWidth || state.mediaWidth;
        state.naturalHeight = elements.media.naturalHeight || state.mediaHeight;
      }} else if (elements.media.tagName === 'VIDEO') {{
        state.naturalWidth = elements.media.videoWidth || state.mediaWidth;
        state.naturalHeight = elements.media.videoHeight || state.mediaHeight;
      }} else {{
        // For audio or unsupported, use container dimensions
        state.naturalWidth = state.mediaWidth;
        state.naturalHeight = state.mediaHeight;
      }}
    }}

    // File information display
    function updateFileInfo() {{
      // Get file size via HTTP HEAD request
      fetch('/file', {{ method: 'HEAD' }})
        .then(response => {{
          const contentLength = response.headers.get('content-length');
          if (contentLength) {{
            elements.fileSizeInfo.textContent = utils.formatFileSize(parseInt(contentLength));
          }}
        }})
        .catch(() => {{
          elements.fileSizeInfo.textContent = 'Unknown';
        }});
    }}

    // Enhanced crop box positioning
    function positionCropBox() {{
      if (state.mediaWidth === 0 || state.mediaHeight === 0) return;
    
      const cropWidth = Math.min(200, state.mediaWidth * 0.4);
      const cropHeight = Math.min(150, state.mediaHeight * 0.3);
    
      // Adjust positioning based on scrollable container
      const container = elements.container;
      const startX = container.scrollLeft + (container.clientWidth - cropWidth) / 2;
      const startY = container.scrollTop + (container.clientHeight - cropHeight) / 2;

      const centerX = Math.max(0, startX);
      const centerY = Math.max(0, startY);
    
      setCropDimensions(centerX, centerY, cropWidth, cropHeight);
    }}

    // Enhanced dimension setting with smooth transitions - FIXED: No padding for edge access
    function setCropDimensions(left, top, width, height, smooth = false) {{
      // Ensure minimum dimensions
      width = Math.max(30, width);
      height = Math.max(30, height);
    
      // Constrain to media bounds without padding - crop box can reach exact edges
      left = Math.max(0, Math.min(left, state.mediaWidth - width));
      top = Math.max(0, Math.min(top, state.mediaHeight - height));
      width = Math.min(width, state.mediaWidth - left);
      height = Math.min(height, state.mediaHeight - top);
    
      // Apply dimensions with optional smooth transition
      const cropStyle = elements.crop.style;
    
      if (smooth && state.animationFrame) {{
        cancelAnimationFrame(state.animationFrame);
      }}
    
      if (smooth) {{
        elements.crop.classList.add('smooth-transition');
        setTimeout(() => elements.crop.classList.remove('smooth-transition'), 200);
      }}
    
      cropStyle.left = Math.round(left) + 'px';
      cropStyle.top = Math.round(top) + 'px';
      cropStyle.width = Math.round(width) + 'px';
      cropStyle.height = Math.round(height) + 'px';
    }}

    // Enhanced aspect ratio handling
    function applyAspectRatio(width, height, maintainWidth = true) {{
      if (state.aspectMode === "free" || !state.aspectRatio) {{
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
      const left = parseInt(elements.crop.style.left) || 0;
      const top = parseInt(elements.crop.style.top) || 0;
      const width = parseInt(elements.crop.style.width) || 0;
      const height = parseInt(elements.crop.style.height) || 0;
    
      // Update position and size
      elements.positionInfo.textContent = `(${{left}}, ${{top}})`;
      elements.sizeInfo.textContent = `${{width}}×${{height}}`;
    
      // Calculate and display aspect ratio
      if (width && height) {{
        const gcd = utils.gcd(width, height);
        const ratioW = width / gcd;
        const ratioH = height / gcd;
      
        // Simplify common ratios
        let ratioText = `${{ratioW}}:${{ratioH}}`;
        if (ratioW === ratioH) ratioText = "1:1";
        else if (Math.abs(ratioW/ratioH - 16/9) < 0.1) ratioText = "16:9";
        else if (Math.abs(ratioW/ratioH - 4/3) < 0.1) ratioText = "4:3";
        else if (Math.abs(ratioW/ratioH - 3/2) < 0.1) ratioText = "3:2";
      
        elements.ratioInfo.textContent = ratioText;
      }}
    }}

    // Set media zoom
    function setMediaZoom(newZoom) {{
      if (state.mediaType !== 'image' && state.mediaType !== 'video') return;
      newZoom = Math.max(0.1, Math.min(10, newZoom));
      const oldZoom = state.zoom;
      state.zoom = newZoom;
      if (elements.media) {{
        elements.media.style.width = (state.naturalWidth * newZoom) + 'px';
        elements.media.style.height = (state.naturalHeight * newZoom) + 'px';
      }}
      const factor = newZoom / oldZoom;
      elements.crop.style.left = (parseFloat(elements.crop.style.left) * factor) + 'px';
      elements.crop.style.top = (parseFloat(elements.crop.style.top) * factor) + 'px';
      elements.crop.style.width = (parseFloat(elements.crop.style.width) * factor) + 'px';
      elements.crop.style.height = (parseFloat(elements.crop.style.height) * factor) + 'px';
      updateMediaDimensions();
      updateCropInfo();
    }}

    // Enhanced dragging with smooth movement
    const dragHandlers = {{
      start(e) {{
        if (e.target.classList.contains('resize-handle')) return;
        e.preventDefault();
        e.stopPropagation();
        if (e.type.startsWith('touch') && e.touches.length === 2) {{
          startPinch('crop', e);
          return;
        }} else if (e.type.startsWith('touch') && e.touches.length > 1) {{
          return;
        }}
        const coords = utils.getEventCoords(e);
        state.isDragging = true;
        state.startMouseX = coords.x;
        state.startMouseY = coords.y;
        state.startCropLeft = parseInt(elements.crop.style.left) || 0;
        state.startCropTop = parseInt(elements.crop.style.top) || 0;
      
        elements.crop.classList.add('dragging');
      
        // Add event listeners
        document.addEventListener('mousemove', dragHandlers.move, {{ passive: false }});
        document.addEventListener('mouseup', dragHandlers.stop);
        document.addEventListener('touchmove', dragHandlers.move, {{ passive: false }});
        document.addEventListener('touchend', dragHandlers.stop);
        document.addEventListener('mousemove', updateMousePos);
        document.addEventListener('touchmove', updateMousePos);
        startAutoScroll();
      }},
    
      move: utils.throttle((e) => {{
        if (!state.isDragging) return;
      
        e.preventDefault();
        const coords = utils.getEventCoords(e);
        const deltaX = coords.x - state.startMouseX;
        const deltaY = coords.y - state.startMouseY;
      
        let newLeft = state.startCropLeft + deltaX;
        let newTop = state.startCropTop + deltaY;
      
        const currentWidth = parseInt(elements.crop.style.width) || 0;
        const currentHeight = parseInt(elements.crop.style.height) || 0;
      
        setCropDimensions(newLeft, newTop, currentWidth, currentHeight);
        updateCropInfo();
      }}, 16), // 60fps throttling
    
      stop() {{
        state.isDragging = false;
        elements.crop.classList.remove('dragging');
      
        // Remove event listeners
        document.removeEventListener('mousemove', dragHandlers.move);
        document.removeEventListener('mouseup', dragHandlers.stop);
        document.removeEventListener('touchmove', dragHandlers.move);
        document.removeEventListener('touchend', dragHandlers.stop);
        document.removeEventListener('mousemove', updateMousePos);
        document.removeEventListener('touchmove', updateMousePos);
        stopAutoScroll();
      }}
    }};

    // Enhanced resizing with smooth aspect ratio handling
    const resizeHandlers = {{
      start(e) {{
        e.preventDefault();
        e.stopPropagation();
      
        const coords = utils.getEventCoords(e);
        state.isResizing = true;
        state.resizeDirection = Array.from(e.target.classList).find(cls => cls !== 'resize-handle');
        state.startMouseX = coords.x;
        state.startMouseY = coords.y;
        state.startCropLeft = parseInt(elements.crop.style.left) || 0;
        state.startCropTop = parseInt(elements.crop.style.top) || 0;
        state.startCropWidth = parseInt(elements.crop.style.width) || 0;
        state.startCropHeight = parseInt(elements.crop.style.height) || 0;
      
        document.addEventListener('mousemove', resizeHandlers.move, {{ passive: false }});
        document.addEventListener('mouseup', resizeHandlers.stop);
        document.addEventListener('touchmove', resizeHandlers.move, {{ passive: false }});
        document.addEventListener('touchend', resizeHandlers.stop);
        document.addEventListener('mousemove', updateMousePos);
        document.addEventListener('touchmove', updateMousePos);
        startAutoScroll();
      }},
    
      // FIXED: Reworked resize logic to prevent crop box from shifting position during corner resize.
      move: utils.throttle((e) => {{
        if (!state.isResizing) return;
      
        e.preventDefault();
        const coords = utils.getEventCoords(e);
        const deltaX = coords.x - state.startMouseX;
        const deltaY = coords.y - state.startMouseY;
      
        const {{ startCropLeft, startCropTop, startCropWidth, startCropHeight, resizeDirection, aspectRatio, aspectMode }} = state;

        let newLeft = startCropLeft;
        let newTop = startCropTop;
        let newWidth = startCropWidth;
        let newHeight = startCropHeight;

        // Calculate initial dimension changes based on mouse movement
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

        // Apply aspect ratio constraints
        if (aspectRatio && aspectMode !== "free") {{
            const isHorizontalResize = resizeDirection === 'e' || resizeDirection === 'w';
            const isVerticalResize = resizeDirection === 'n' || resizeDirection === 's';

            if (isHorizontalResize) {{
                newHeight = newWidth / aspectRatio;
            }} else if (isVerticalResize) {{
                newWidth = newHeight * aspectRatio;
            }} else {{ // Corner resize
                // Let the horizontal change dictate the vertical change for consistency
                newHeight = newWidth / aspectRatio;
            }}
        }}
      
        // Recalculate position based on the final, constrained dimensions.
        // This ensures the opposite corner/edge stays anchored correctly.
        if (resizeDirection.includes('n')) {{
            newTop = startCropTop + (startCropHeight - newHeight);
        }}
        if (resizeDirection.includes('w')) {{
            newLeft = startCropLeft + (startCropWidth - newWidth);
        }}
      
        setCropDimensions(newLeft, newTop, newWidth, newHeight);
        updateCropInfo();
      }}, 16),
    
      stop() {{
        state.isResizing = false;
      
        document.removeEventListener('mousemove', resizeHandlers.move);
        document.removeEventListener('mouseup', resizeHandlers.stop);
        document.removeEventListener('touchmove', resizeHandlers.move);
        document.removeEventListener('touchend', resizeHandlers.stop);
        document.removeEventListener('mousemove', updateMousePos);
        document.removeEventListener('touchmove', updateMousePos);
        stopAutoScroll();
      }}
    }};

    // Auto scroll functions
    function updateMousePos(e) {{
      const coords = {{ x: e.clientX, y: e.clientY }};
      state.mouseX = coords.x;
      state.mouseY = coords.y;
    }}

    function updateMousePosTouch(e) {{
      const coords = utils.getEventCoords(e);
      state.mouseX = coords.x;
      state.mouseY = coords.y;
    }}

    function startAutoScroll() {{
      state.autoScrollActive = true;
      autoScrollLoop();
    }}

    function stopAutoScroll() {{
      state.autoScrollActive = false;
    }}

    function autoScrollLoop() {{
      if (!state.autoScrollActive) return;
      const viewer = elements.mediaViewer;
      const rect = viewer.getBoundingClientRect();
      const edgeSize = 50;
      const scrollSpeed = 10;
      let dx = 0, dy = 0;
      if (state.mouseX < rect.left + edgeSize) {{
        dx = -scrollSpeed * ((rect.left + edgeSize - state.mouseX) / edgeSize);
      }} else if (state.mouseX > rect.right - edgeSize) {{
        dx = scrollSpeed * ((state.mouseX - (rect.right - edgeSize)) / edgeSize);
      }}
      if (state.mouseY < rect.top + edgeSize) {{
        dy = -scrollSpeed * ((rect.top + edgeSize - state.mouseY) / edgeSize);
      }} else if (state.mouseY > rect.bottom - edgeSize) {{
        dy = scrollSpeed * ((state.mouseY - (rect.bottom - edgeSize)) / edgeSize);
      }}
      if (dx !== 0 || dy !== 0) {{
        viewer.scrollLeft += dx;
        viewer.scrollTop += dy;
        state.startMouseX -= dx;
        state.startMouseY -= dy;
        if (state.isDragging) {{
          dragHandlers.move({{ clientX: state.mouseX, clientY: state.mouseY }});
        }} else if (state.isResizing) {{
          resizeHandlers.move({{ clientX: state.mouseX, clientY: state.mouseY }});
        }}
      }}
      requestAnimationFrame(autoScrollLoop);
    }}

    // Pinch handlers
    function startPinch(type, e) {{
      if (type === 'media' && state.mediaType !== 'image' && state.mediaType !== 'video') return;
      state.isPinching = true;
      state.pinchType = type;
      state.pinchInitialDist = utils.getDistance(e.touches[0], e.touches[1]);
      if (type === 'crop') {{
        state.pinchInitialWidth = parseInt(elements.crop.style.width);
        state.pinchInitialHeight = parseInt(elements.crop.style.height);
        state.pinchInitialLeft = parseInt(elements.crop.style.left);
        state.pinchInitialTop = parseInt(elements.crop.style.top);
      }} else {{
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
        let newWidth = state.pinchInitialWidth * factor;
        let newHeight = state.pinchInitialHeight * factor;
        const dims = applyAspectRatio(newWidth, newHeight);
        newWidth = dims.width;
        newHeight = dims.height;
        const deltaW = newWidth - state.pinchInitialWidth;
        const deltaH = newHeight - state.pinchInitialHeight;
        const newLeft = state.pinchInitialLeft - deltaW / 2;
        const newTop = state.pinchInitialTop - deltaH / 2;
        setCropDimensions(newLeft, newTop, newWidth, newHeight);
        updateCropInfo();
      }} else {{
        const newZoom = state.pinchInitialZoom * factor;
        setMediaZoom(newZoom);
        const newFactor = newZoom / state.pinchInitialZoom;
        elements.mediaViewer.scrollLeft = state.pinchInitialScrollLeft * newFactor + state.pinchInitialRelX * (newFactor - 1);
        elements.mediaViewer.scrollTop = state.pinchInitialScrollTop * newFactor + state.pinchInitialRelY * (newFactor - 1);
      }}
    }}

    function handlePinchEnd() {{
      state.isPinching = false;
      state.pinchType = '';
      document.removeEventListener('touchmove', handlePinchMove);
      document.removeEventListener('touchend', handlePinchEnd);
    }}

    // Mouse wheel zoom handler
    function handleMouseWheelZoom(e) {{
      // Yeh browser ko page scroll karne se rokta hai
      e.preventDefault();

      // Scroll up (deltaY < 0) matlab zoom in
      // Scroll down (deltaY > 0) matlab zoom out
      const zoomFactor = e.deltaY < 0 ? 1.1 : 1 / 1.1;
    
      const newZoom = state.zoom * zoomFactor;
    
      // Aapka banaya hua zoom function call karein
      setMediaZoom(newZoom);
    }}

    function handleMediaTouchStart(e) {{
      if (e.touches.length === 2) {{
        e.preventDefault();
        startPinch('media', e);
      }}
    }}

    // Keyboard navigation support
    function handleKeyboard(e) {{
      if (state.isHelpVisible && e.key === 'Escape') {{
        toggleHelp();
        return;
      }}
    
      if (state.isHelpVisible) return;
    
      const step = e.shiftKey ? 1 : 10; // Fine adjustment with Shift
      const currentLeft = parseInt(elements.crop.style.left) || 0;
      const currentTop = parseInt(elements.crop.style.top) || 0;
      const currentWidth = parseInt(elements.crop.style.width) || 0;
      const currentHeight = parseInt(elements.crop.style.height) || 0;
    
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
          e.preventDefault();
          saveCrop();
          break;
        default:
          return;
      }}
    
      if (newLeft !== currentLeft || newTop !== currentTop) {{
        setCropDimensions(newLeft, newTop, currentWidth, currentHeight, true);
        updateCropInfo();
      }}
    }}

    // UI Enhancement functions
    function toggleGrid() {{
      state.showGrid = !state.showGrid;
      elements.crop.classList.toggle('show-grid', state.showGrid);
    }}

    // FIXED: This function now centers the crop box relative to the entire media,
    // not just the visible portion, and scrolls it into view.
    function centerCrop() {{
      const currentWidth = parseInt(elements.crop.style.width) || 0;
      const currentHeight = parseInt(elements.crop.style.height) || 0;
    
      // Calculate the true center based on the full media dimensions.
      const centerX = (state.mediaWidth - currentWidth) / 2;
      const centerY = (state.mediaHeight - currentHeight) / 2;
    
      setCropDimensions(centerX, centerY, currentWidth, currentHeight, true);
      updateCropInfo();

      // Scroll the container to bring the newly centered crop box into view.
      const container = document.querySelector('.media-viewer'); // Scroll the correct element
      container.scrollLeft = centerX + (currentWidth / 2) - (container.clientWidth / 2);
      container.scrollTop = centerY + (currentHeight / 2) - (container.clientHeight / 2);
    }}

    function resetCropSize() {{
      positionCropBox();
      updateCropInfo();
    }}

    function toggleHelp() {{
      state.isHelpVisible = !state.isHelpVisible;
      elements.helpModal.style.display = state.isHelpVisible ? 'flex' : 'none';
    }}

    // Context menu handling
    function showContextMenu(e) {{
      e.preventDefault();
      const menu = elements.contextMenu;
      menu.style.display = 'block';
      menu.style.left = e.clientX + 'px';
      menu.style.top = e.clientY + 'px';
    
      // Hide menu when clicking elsewhere
      document.addEventListener('click', hideContextMenu, {{ once: true }});
    }}

    function hideContextMenu() {{
      if (elements.contextMenu) {{
        elements.contextMenu.style.display = 'none';
      }}
    }}

    // Enhanced aspect ratio handling
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
        // UX IMPROVEMENT 1: Automatically apply the selected aspect ratio to the crop box
        applyCurrentAspectRatio();
      }}
    }}

    function updateCustomAspectRatio() {{
      const w = parseFloat(elements.customW.value) || 1;
      const h = parseFloat(elements.customH.value) || 1;
      state.aspectRatio = w / h;
      if (state.aspectMode === "custom") {{
        applyCurrentAspectRatio();
      }}
    }}

    function applyCurrentAspectRatio() {{
      if (!state.aspectRatio || !state.isInitialized) return;
    
      const currentLeft = parseInt(elements.crop.style.left) || 0;
      const currentTop = parseInt(elements.crop.style.top) || 0;
      const currentWidth = parseInt(elements.crop.style.width) || 0;
      // Let's base the new height on the current width to maintain position and size as much as possible
      const newHeight = Math.round(currentWidth / state.aspectRatio);
    
      setCropDimensions(currentLeft, currentTop, currentWidth, newHeight, true);
      updateCropInfo();
    }}

    // Enhanced save function with better scaling
    function saveCrop() {{
      updateMediaDimensions();
    
      const left = parseInt(elements.crop.style.left) || 0;
      const top = parseInt(elements.crop.style.top) || 0;
      const width = parseInt(elements.crop.style.width) || 0;
      const height = parseInt(elements.crop.style.height) || 0;
    
      // Calculate precise scaling factors
      let scaleX = 1, scaleY = 1;
    
      if (state.naturalWidth && state.naturalHeight && state.mediaWidth && state.mediaHeight) {{
        scaleX = state.naturalWidth / state.mediaWidth;
        scaleY = state.naturalHeight / state.mediaHeight;
      }}
    
      const finalX = Math.round(left * scaleX);
      const finalY = Math.round(top * scaleY);
      const finalW = Math.round(width * scaleX);
      const finalH = Math.round(height * scaleY);
    
      // Enhanced feedback
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
          // Create a more informative notification
          const notification = document.createElement('div');
          notification.className = 'notification';
          notification.innerHTML = `
            <div class="notification-title">Crop Saved Successfully!</div>
            <div class="notification-code">crop=${{finalW}}:${{finalH}}:${{finalX}}:${{finalY}}</div>
            <div class="notification-subtitle">Check your terminal for the full command</div>
          `;
        
          document.body.appendChild(notification);
          setTimeout(() => document.body.removeChild(notification), 3000);
        }} else {{
          alert("Error: Could not save crop parameters");
        }}
      }})
      .catch(error => {{
        alert("Network Error: " + error.message);
      }});
    }}

    // Window resize handler with debouncing
    const handleWindowResize = utils.debounce(() => {{
      updateMediaDimensions();
      updateCropInfo();
    
      // Adjust crop box if it's outside bounds
      const left = parseInt(elements.crop.style.left) || 0;
      const top = parseInt(elements.crop.style.top) || 0;
      const width = parseInt(elements.crop.style.width) || 0;
      const height = parseInt(elements.crop.style.height) || 0;
    
      if (left + width > state.mediaWidth || top + height > state.mediaHeight) {{
        setCropDimensions(left, top, width, height, true);
      }}
    }}, 300);

    // Event listener setup
    function setupEventListeners() {{
      // Crop box interactions
      elements.crop.addEventListener("mousedown", dragHandlers.start);
      elements.crop.addEventListener("touchstart", dragHandlers.start, {{ passive: false }});
      elements.crop.addEventListener("contextmenu", showContextMenu);
      elements.crop.addEventListener("dblclick", centerCrop);
    
      // Resize handles
      document.querySelectorAll('.resize-handle').forEach(handle => {{
        handle.addEventListener("mousedown", resizeHandlers.start);
        handle.addEventListener("touchstart", resizeHandlers.start, {{ passive: false }});
      }});
    
      // Media wrapper for outside touches
      elements.mediaWrapper.addEventListener("touchstart", handleMediaTouchStart, {{ passive: false }});
    
      // Mouse wheel zoom listener
      elements.mediaViewer.addEventListener("wheel", handleMouseWheelZoom, {{ passive: false }});
    
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
      setupEventListeners();
    
      // Initialize when media is ready
      if (elements.media) {{
        if (elements.media.complete || elements.media.readyState >= 2) {{
          initializeCrop();
        }} else {{
          // For video/audio that need time to load
          elements.media.addEventListener('loadedmetadata', initializeCrop);
          elements.media.addEventListener('canplay', initializeCrop);
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
              
                mime_types = {
                    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp',
                    '.gif': 'image/gif', '.bmp': 'image/bmp', '.tiff': 'image/tiff', '.tif': 'image/tiff',
                    '.avif': 'image/avif', '.heic': 'image/heic', '.heif': 'image/heif', '.jxl': 'image/jxl',
                    '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.mp4': 'video/mp4', '.webm': 'video/webm',
                    '.mov': 'video/quicktime', '.ogv': 'video/ogg', '.mp3': 'audio/mpeg', '.wav': 'audio/wav',
                    '.ogg': 'audio/ogg', '.m4a': 'audio/mp4', '.flac': 'audio/flac', '.aac': 'audio/aac',
                    '.opus': 'audio/opus'
                }
                mime_type = mime_types.get(ext, 'application/octet-stream')

                range_header = self.headers.get('Range')
                if range_header:
                    # Handle Range request (for video seeking)
                    try:
                        start_str, end_str = range_header.replace('bytes=', '').split('-')
                        start = int(start_str) if start_str else 0
                        end = int(end_str) if end_str else file_size - 1
                      
                        if start >= file_size or end >= file_size or start > end:
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
                            while remaining > 0:
                                chunk_size = min(remaining, 65536) # 64KB chunks
                                chunk = f.read(chunk_size)
                                if not chunk: break
                                self.wfile.write(chunk)
                                remaining -= len(chunk)
                    except ValueError:
                        self.send_error(400, "Invalid Range header")
                else:
                    # Handle full file request by streaming
                    self.send_response(200)
                    self.send_header("Content-type", mime_type)
                    self.send_header("Content-Length", str(file_size))
                    self.send_header("Accept-Ranges", "bytes")
                    self.send_header("Last-Modified", self.date_time_string(os.path.getmtime(self.server.media_file)))
                    self.end_headers()
                  
                    with open(self.server.media_file, 'rb') as f:
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
        """Handle HEAD requests for file size information"""
        if urlparse(self.path).path == "/file":
            try:
                file_size = os.path.getsize(self.server.media_file)
                self.send_response(200)
                self.send_header("Content-Length", str(file_size))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
            except Exception as e:
                self.send_error(404, str(e))
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/save":
            try:
                length = int(self.headers.get("Content-Length", 0))
                if length > 10000:
                    self.send_error(413, "Payload too large")
                    return
                  
                body = self.rfile.read(length)
                data = json.loads(body.decode("utf-8"))
              
                required_fields = ['w', 'h', 'x', 'y']
                for field in required_fields:
                    if field not in data or not isinstance(data[field], (int, float)) or data[field] < 0:
                        self.send_error(400, f"Invalid {field} parameter")
                        return
              
                # IMPROVEMENT: Generate and print the full FFmpeg command to the terminal.
                w = int(data['w'])
                h = int(data['h'])
                x = int(data['x'])
                y = int(data['y'])

                path_part, ext_part = os.path.splitext(self.server.media_file)
                output_file = f"{path_part}_cropped{ext_part}"

                # Construct the command with quoted paths to handle spaces
                ffmpeg_command = f'\nffmpeg -i "{self.server.media_file}" -vf "crop={w}:{h}:{x}:{y}" "{output_file}"'
              
                print(ffmpeg_command)
              
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                # Keep the original JSON response to avoid changing web view behavior
                self.wfile.write(json.dumps({
                    "success": True,
                    "message": "Crop parameters saved successfully",
                    "crop_filter": f"crop={w}:{h}:{x}:{y}",
                    "timestamp": self.date_time_string()
                }).encode("utf-8"))
              
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON data")
            except KeyError as e:
                self.send_error(400, f"Missing required field: {e}")
            except Exception as e:
                self.send_error(500, f"Server error: {str(e)}")
        else:
            self.send_error(404, "Not Found")

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Range")
        self.end_headers()
