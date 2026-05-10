#!/bin/bash
# My Organizer — First-run setup script
# Run: bash setup.sh

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RESET='\033[0m'

echo ""
echo -e "${CYAN}╔══════════════════════════════════╗${RESET}"
echo -e "${CYAN}║      My Organizer — Setup        ║${RESET}"
echo -e "${CYAN}╚══════════════════════════════════╝${RESET}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Install from https://python.org"
    exit 1
fi
echo -e "${GREEN}✓${RESET} Python $(python3 --version)"

# Check Node
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Install from https://nodejs.org"
    exit 1
fi
echo -e "${GREEN}✓${RESET} Node $(node --version)"

# Install Python deps
echo ""
echo -e "${CYAN}Installing Python dependencies...${RESET}"
pip3 install -r requirements.txt --quiet
echo -e "${GREEN}✓${RESET} Python deps installed"

# Install Node deps
echo ""
echo -e "${CYAN}Installing Node dependencies...${RESET}"
npm install --quiet
echo -e "${GREEN}✓${RESET} Node deps installed"

# Setup config
if [ ! -f config.json ]; then
    cp config.example.json config.json
    echo -e "${YELLOW}⚠${RESET}  Created config.json — edit it with your API keys"
else
    echo -e "${GREEN}✓${RESET} config.json already exists"
fi

# Create storage dirs
mkdir -p storage
echo -e "${GREEN}✓${RESET} Storage directory ready"

echo ""
echo -e "${GREEN}✅ Setup complete!${RESET}"
echo ""
echo "Next steps:"
echo "  1. Edit config.json — add your Gemini API key and IMAP credentials"
echo "  2. Run: npm start"
echo ""
echo "Get a free Gemini API key at: https://aistudio.google.com"
echo ""
