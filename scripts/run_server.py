#!/usr/bin/env python3
"""Run the Flask development server."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sta.web import create_app

if __name__ == "__main__":
    app = create_app()
    print("\n" + "=" * 50)
    print("STA STARSHIP SIMULATOR")
    print("=" * 50)
    print("\nStarting development server...")
    print("Open http://localhost:5001 in your browser")
    print("Press Ctrl+C to stop\n")
    app.run(debug=True, host="0.0.0.0", port=5001)
