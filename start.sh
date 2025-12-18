#!/bin/bash
# STA Starship Simulator - Local Server Launcher
# Run this script on your Raspberry Pi to start the game server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "  STA Starship Simulator"
echo "========================================"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"
pip install -q -r requirements.txt

# Get the Pi's IP address for display
IP_ADDR=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}Server starting!${NC}"
echo "========================================"
echo "Players can connect at:"
echo ""
echo "  http://${IP_ADDR}:5001"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

# Run the Flask app, accessible from other devices on the network
FLASK_APP=sta.web.app:create_app flask run --host=0.0.0.0 --port=5001
