#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import webbrowser
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

# Import our custom modules
from http_handler import CropHandler
from utils import get_file_info

# Global variables
media_file = None
verbose = False

__version__ = "2.5.0"

def print_help():
    """Prints the detailed help message for the script."""
    print("\nmediacrop - Visual FFmpeg Crop Tool")
    print("=" * 50)
    print("A web-based visual tool to get FFmpeg crop coordinates for media files.")
    print("\nUsage:")
    print("""  mediacrop <media_file>
                        Path to the video or image.""")
    print("\nOptions:")
    print("  -h, --help            Show this help message and exit.")
    print("  -v, --verbose         Show detailed server logs.")
    print("  -p N, --port N        Use a specific port for the server (default: 8000).")
    print("  --host HOST           Specify host address (default: 127.0.0.1).")
    print("  --version             Show current version and exit.")
    print("\nSupported Preview Formats:")
    print("  Images : JPG, PNG, WEBP, AVIF, GIF, BMP, SVG, ICO")
    print("  Videos : MP4, WEBM, MOV, OGV")
    print("  Audio  : MP3, WAV, FLAC, OGG, M4A, AAC, OPUS")
    print(f"\nAuthor Info:")
    print(f"  Name   : Mallik Mohammad Musaddiq")
    print(f"  GitHub : https://github.com/mallikmusaddiq1/mediacrop")
    print(f"  Email  : mallikmusaddiq1@gmail.com")

def main():
    # --version flag ka check sabse pehle add kiya gaya hai.
    if "--version" in sys.argv:
        print(f"mediacrop {__version__}")
        sys.exit(0)

    # Check for help flag first
    if "--help" in sys.argv or "-h" in sys.argv:
        print_help()
        sys.exit(0)

    # Enhanced command line handling
    if len(sys.argv) < 2 or sys.argv[1].startswith('-'):
        print("Error: No media file specified.")
        print("Usage: mediacrop <media_file> [options]")
        print("Use 'mediacrop --help' for more information.")
        sys.exit(1)

    global media_file, verbose
    media_file = os.path.abspath(sys.argv[1])
    if not os.path.exists(media_file):
        print(f"Error: File not found - {media_file}")
        sys.exit(1)

    if not os.access(media_file, os.R_OK):
        print(f"Error: Permission denied - {media_file}")
        sys.exit(1)

    # Parse arguments
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    port = 8000
    host = "127.0.0.1"
  
    port_arg = None
    if "--port" in sys.argv:
        port_arg = "--port"
    elif "-p" in sys.argv:
        port_arg = "-p"

    if port_arg:
        try:
            port_index = sys.argv.index(port_arg) + 1
            if port_index < len(sys.argv):
                port = int(sys.argv[port_index])
                if not (1024 <= port <= 65535):
                    raise ValueError("Port must be between 1024 and 65535")
        except (ValueError, IndexError):
            print("Error: Invalid port number provided.")
            sys.exit(1)

    if "--host" in sys.argv:
        try:
            host_index = sys.argv.index("--host") + 1
            if host_index < len(sys.argv):
                host = sys.argv[host_index]
        except IndexError:
            print("Error: No host provided after --host.")
            sys.exit(1)

    # Get file information
    file_info = get_file_info(media_file)
    if file_info:
        # Note: Fixed a small bug in original - it was using 'file_info['size']' but defined as 'size'
        file_size_gb = file_info['size'] / (1024 * 1024 * 1024)
        file_size_mb = file_info['size'] / (1024 * 1024)
      
        if file_size_gb >= 1:
            size_str = f"{file_size_gb:.2f} GB"
        else:
            size_str = f"{file_size_mb:.2f} MB"

        print(f"File   : {file_info['name']}")
        print(f"Size   : {size_str}")
        print(f"Format : {file_info['extension'].upper().replace('.', '')}")
  
    # Find available port
    original_port = port
    server = None
    for attempt in range(10):
        try:
            server = HTTPServer((host, port), CropHandler)
            server.media_file = media_file  # Pass global to handler
            server.verbose = verbose
            break
        except OSError as e:
            if attempt == 0 and port != original_port:
                print(f"Port {original_port} busy, trying {port}")
            port += 1
    else:
        print("Error: Could not find available port, try default")
        sys.exit(1)
  
    url = f"http://{host}:{port}"
  
    try:
        if not verbose:
            print(f"Server : {url}")
            print(f"Open {url} in browser...")
            print()
            print("Tips:")
            print("   • Drag crop box to move anywhere")
            print("   • Use arrow keys for precision") 
            print("   • Press 'G' for grid overlay")
            print("   • Press 'C' to center crop")
            print("   • Right-click for more options")
            print()
            print("Click 'Save Coordinates' when ready")
            print("Press Ctrl+C to stop server")
            print("-" * 50)
      
        # Open browser
        webbrowser.open(url)
      
        # Start server
        if verbose:
            print(f"Server running on port {port}")
            print(f"Serving file: {media_file}")
            print(f"Open {url} in browser...")
      
        server.serve_forever()
      
    except KeyboardInterrupt:
        print("\nServer stopped")
        if server:
            server.server_close()
        sys.exit(0)
    except Exception as e:
        print(f"Server error: {e}")
        if server:
            server.server_close()
        sys.exit(1)


if __name__ == "__main__":
    main()
