import os
import logging
import subprocess
import sys
from datetime import datetime
import requests
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_audio(url_or_path):
    """Download audio file if it's a URL, otherwise return the local path"""
    if url_or_path.startswith(('http://', 'https://')):
        logger.info(f"Downloading audio from URL: {url_or_path}")
        
        # Extract filename from URL
        parsed_url = urlparse(url_or_path)
        filename = os.path.basename(parsed_url.path)
        if not filename or '.' not in filename:
            filename = "downloaded_audio.mp3"
        
        try:
            with requests.get(url_or_path, stream=True) as r:
                r.raise_for_status()
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            logger.info(f"Downloaded to: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            return None
    else:
        # It's a local file path
        if os.path.exists(url_or_path):
            return url_or_path
        else:
            logger.error(f"Local file not found: {url_or_path}")
            return None

def stem_separation(audio_file):
    """
    Separate audio into stems using Demucs
    Returns list of stem file paths
    """
    logger.info(f"Starting stem separation for: {audio_file}")
    
    # Create output directory
    stem_outputs_dir = "stem_outputs"
    if not os.path.exists(stem_outputs_dir):
        logger.info(f"Creating directory: {stem_outputs_dir}")
        os.makedirs(stem_outputs_dir)
    
    # Build demucs command
    demucs_command = [
        "demucs",
        "-o", stem_outputs_dir,
        "-n", "htdemucs_6s",
        "--mp3",
        audio_file
    ]
    
    logger.info(f"Running command: {' '.join(demucs_command)}")
    
    try:
        result = subprocess.run(demucs_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Demucs completed successfully")
            logger.info(result.stdout)
        else:
            logger.error(f"Demucs failed: {result.stderr}")
            return []
        
        # Find the output files
        filename_base = os.path.splitext(os.path.basename(audio_file))[0]
        output_dir = os.path.join(stem_outputs_dir, "htdemucs_6s", filename_base)
        
        if not os.path.exists(output_dir):
            logger.error(f"Output directory not found: {output_dir}")
            return []
        
        # Get all stem files
        stem_files = []
        for file in os.listdir(output_dir):
            if file.endswith(('.wav', '.mp3')):
                full_path = os.path.join(output_dir, file)
                # Rename with timestamp
                new_path = rename_stem_file(full_path)
                stem_files.append(new_path)
        
        logger.info(f"Generated {len(stem_files)} stem files")
        return stem_files
        
    except Exception as e:
        logger.error(f"Error during stem separation: {e}")
        return []

def rename_stem_file(filepath):
    """Rename stem file with timestamp"""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")
    
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    name, ext = os.path.splitext(filename)
    
    new_filename = f"{name}_{timestamp}{ext}"
    new_filepath = os.path.join(directory, new_filename)
    
    try:
        os.rename(filepath, new_filepath)
        logger.info(f"Renamed: {filename} -> {new_filename}")
        return new_filepath
    except Exception as e:
        logger.error(f"Error renaming file: {e}")
        return filepath

def print_results(stem_files):
    """Print results in a nice format"""
    if not stem_files:
        print(" No stems were generated")
        return
    
    print(f"\n Stem separation complete! Generated {len(stem_files)} files:")
    print("-" * 60)
    
    for i, stem_file in enumerate(stem_files, 1):
        filename = os.path.basename(stem_file)
        size_mb = os.path.getsize(stem_file) / (1024 * 1024)
        print(f"{i:2d}. {filename} ({size_mb:.2f} MB)")
    
    print(f"\n All files saved in: {os.path.dirname(stem_files[0])}")

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python app.py <audio_file_or_url>")
        print("Examples:")
        print("  python app.py song.mp3")
        print("  python app.py https://example.com/song.mp3")
        sys.exit(1)
    
    audio_input = sys.argv[1]
    
    print(" Stem Separation Tool")
    print("=" * 40)
    
    # Download or verify file
    audio_file = download_audio(audio_input)
    if not audio_file:
        print(" Failed to get audio file")
        sys.exit(1)
    
    # Perform stem separation
    stem_files = stem_separation(audio_file)
    
    # Print results
    print_results(stem_files)
    
    # Clean up downloaded file if it was a URL
    if audio_input.startswith(('http://', 'https://')) and os.path.exists(audio_file):
        try:
            os.remove(audio_file)
            logger.info(f"Cleaned up downloaded file: {audio_file}")
        except Exception as e:
            logger.warning(f"Could not clean up file: {e}")

if __name__ == "__main__":
    main()