import os
import logging
import subprocess
import sys
import requests
from urllib.parse import urlparse
import shutil

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

def vocals_instrumentals_separation(audio_file):
    """
    Separate audio into vocals and instrumentals using Demucs
    Returns dict with vocals and instrumentals file paths
    """
    logger.info(f"Starting vocals/instrumentals separation for: {audio_file}")
    
    # Create temp output directory
    temp_output = "temp_separation"
    if not os.path.exists(temp_output):
        os.makedirs(temp_output)
    
    # Use demucs with --two-stems=vocals
    demucs_command = [
        "demucs",
        "-o", temp_output,
        "-n", "htdemucs",
        "--two-stems=vocals",
        "--mp3",
        audio_file
    ]
    
    logger.info(f"Running demucs: {' '.join(demucs_command)}")
    
    try:
        result = subprocess.run(demucs_command, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Demucs failed: {result.stderr}")
            return {}
        
        logger.info("Demucs completed successfully")
        
        # Find the output files
        filename_base = os.path.splitext(os.path.basename(audio_file))[0]
        output_dir = os.path.join(temp_output, "htdemucs", filename_base)
        
        if not os.path.exists(output_dir):
            logger.error(f"Output directory not found: {output_dir}")
            return {}
        
        # Find vocals and no_vocals files
        vocals_source = None
        instrumentals_source = None
        
        for file in os.listdir(output_dir):
            if file.endswith(('.wav', '.mp3')):
                if 'vocals' in file and 'no_vocals' not in file:
                    vocals_source = os.path.join(output_dir, file)
                elif 'no_vocals' in file:
                    instrumentals_source = os.path.join(output_dir, file)
        
        if not vocals_source or not instrumentals_source:
            logger.error("Could not find both vocals and instrumentals files")
            return {}
        
        # Copy to simple names in current directory
        vocals_final = "only_vocals.mp3"
        instrumentals_final = "only_instrumentals.mp3"
        
        shutil.copy2(vocals_source, vocals_final)
        shutil.copy2(instrumentals_source, instrumentals_final)
        
        # Clean up temp directory
        shutil.rmtree(temp_output)
        
        logger.info("Files created: only_vocals.mp3 and only_instrumentals.mp3")
        
        return {
            'vocals': vocals_final,
            'instrumentals': instrumentals_final
        }
        
    except Exception as e:
        logger.error(f"Error during separation: {e}")
        return {}

def print_results(result):
    """Print results"""
    if not result:
        print("No files were generated")
        return
    
    print(f"\nSeparation complete! Generated 2 files:")
    print("-" * 40)
    
    if 'vocals' in result:
        vocals_size = os.path.getsize(result['vocals']) / (1024 * 1024)
        print(f"1. only_vocals.mp3 ({vocals_size:.2f} MB)")
    
    if 'instrumentals' in result:
        instrumentals_size = os.path.getsize(result['instrumentals']) / (1024 * 1024)
        print(f"2. only_instrumentals.mp3 ({instrumentals_size:.2f} MB)")

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python app.py <audio_file_or_url>")
        print("Examples:")
        print("  python app.py song.mp3")
        print("  python app.py https://example.com/song.mp3")
        sys.exit(1)
    
    audio_input = sys.argv[1]
    
    print("Vocals & Instrumentals Separator")
    print("=" * 40)
    
    # Download or verify file
    audio_file = download_audio(audio_input)
    if not audio_file:
        print("Failed to get audio file")
        sys.exit(1)
    
    # Perform separation
    result = vocals_instrumentals_separation(audio_file)
    
    # Print results
    print_results(result)
    
    # Clean up downloaded file if it was a URL
    if audio_input.startswith(('http://', 'https://')) and os.path.exists(audio_file):
        try:
            os.remove(audio_file)
            logger.info(f"Cleaned up downloaded file: {audio_file}")
        except Exception as e:
            logger.warning(f"Could not clean up file: {e}")

if __name__ == "__main__":
    main()
