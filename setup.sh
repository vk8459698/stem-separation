#!/bin/bash

echo " Setting up Stem Separation Tool..."

# Update system packages
echo " Updating system packages..."
sudo apt-get update -qq

# Install system dependencies
echo " Installing system dependencies..."
sudo apt-get install -y \
    python3-pip \
    ffmpeg \
    libsndfile1 \
    sox \
    libsox-fmt-all \
    git

# Install Python dependencies
echo " Installing Python packages..."
pip install requests

# Install Demucs (the main stem separation tool)
echo " Installing Demucs for stem separation..."
pip install demucs

# Create output directory
echo " Creating output directory..."
mkdir -p stem_outputs

echo " Setup complete!"
echo ""
echo " Usage Examples:"
echo "  python app.py song.mp3"
echo "  python app.py https://example.com/song.mp3"
echo ""
echo " What it does:"
echo "  - Separates audio into: vocals, drums, bass, piano, other"
echo "  - Supports MP3, WAV, FLAC and other formats"
echo "  - Downloads from URLs automatically"
echo "  - Saves stems with timestamps"