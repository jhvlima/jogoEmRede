#!/usr/bin/env python3
"""
Simple HTTP server to serve the HTML client for testing
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

PORT = 8000
DIRECTORY = "client"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def main():
    # Check if client directory exists
    if not os.path.exists(DIRECTORY):
        print(f"Error: Directory '{DIRECTORY}' not found!")
        sys.exit(1)
    
    # Check if index.html exists
    index_path = os.path.join(DIRECTORY, "index.html")
    if not os.path.exists(index_path):
        print(f"Error: {index_path} not found!")
        sys.exit(1)
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"Serving HTML client at http://localhost:{PORT}")
            print(f"Serving files from: {os.path.abspath(DIRECTORY)}")
            print(f"Open your browser and go to: http://localhost:{PORT}")
            print("Press Ctrl+C to stop the server")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()