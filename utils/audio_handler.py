import os
import tempfile
import subprocess
import math
from typing import List, Dict, Any, Optional, Tuple
import shutil
from pydub import AudioSegment

from utils.openai_client import MAX_FILE_SIZE, check_file_size

# Directory for temporary files
TEMP_AUDIO_DIR = "temp_audio"
# Directory for uploaded files
UPLOAD_DIR = "uploads"

def ensure_directories_exist():
    """Ensure that temporary and upload directories exist."""
    for directory in [TEMP_AUDIO_DIR, UPLOAD_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)

def save_uploaded_file(file, filename: str) -> str:
    """
    Save an uploaded file to the uploads directory.
    
    Args:
        file: File object from Flask request
        filename: Name of the file
        
    Returns:
        Path to the saved file
    """
    ensure_directories_exist()
    file_path = os.path.join(UPLOAD_DIR, filename)
    file.save(file_path)
    return file_path

def get_audio_duration(file_path: str) -> float:
    """
    Get the duration of an audio file in seconds using FFmpeg.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        Duration in seconds
    """
    cmd = [
        "ffprobe", 
        "-v", "error", 
        "-show_entries", "format=duration", 
        "-of", "default=noprint_wrappers=1:nokey=1", 
        file_path
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if result.returncode != 0:
        raise ValueError(f"Error getting audio duration: {result.stderr}")
    
    return float(result.stdout.strip())

def split_audio_file(file_path: str) -> List[str]:
    """
    Split audio file into chunks of appropriate size for Whisper API.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        List of paths to the split audio files
    """
    ensure_directories_exist()
    
    # Calculate file size and determine if splitting is needed
    if check_file_size(file_path):
        return [file_path]  # No need to split
    
    # Get audio duration
    duration = get_audio_duration(file_path)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Calculate how many chunks we need
    # Add a 5% margin to be safe
    num_chunks = math.ceil(file_size / (MAX_FILE_SIZE * 0.95))
    
    # Calculate chunk duration in seconds
    chunk_duration = duration / num_chunks
    
    # Create temporary directory for chunks
    temp_dir = tempfile.mkdtemp(dir=TEMP_AUDIO_DIR)
    
    # Split audio file using FFmpeg
    file_name = os.path.basename(file_path)
    file_name_without_ext, ext = os.path.splitext(file_name)
    
    chunk_files = []
    
    for i in range(num_chunks):
        start_time = i * chunk_duration
        chunk_file = os.path.join(temp_dir, f"{file_name_without_ext}_chunk_{i}{ext}")
        
        # Use FFmpeg to extract chunk
        cmd = [
            "ffmpeg",
            "-i", file_path,
            "-ss", str(start_time),
            "-t", str(chunk_duration),
            "-c", "copy",  # Copy without re-encoding
            chunk_file
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            raise ValueError(f"Error splitting audio file: {result.stderr.decode('utf-8')}")
        
        chunk_files.append(chunk_file)
    
    return chunk_files

def cleanup_temp_files(file_paths: List[str]):
    """
    Clean up temporary files and directories.
    
    Args:
        file_paths: List of file paths to clean up
    """
    for file_path in file_paths:
        if os.path.exists(file_path) and TEMP_AUDIO_DIR in file_path:
            # Remove the file
            os.remove(file_path)
            
            # Check if directory is empty and remove it
            dir_path = os.path.dirname(file_path)
            if os.path.exists(dir_path) and not os.listdir(dir_path):
                os.rmdir(dir_path)

def get_file_type(file_path: str) -> str:
    """
    Get the file type/format using FFmpeg.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        File type/format
    """
    cmd = [
        "ffprobe", 
        "-v", "error", 
        "-select_streams", "a:0", 
        "-show_entries", "stream=codec_name", 
        "-of", "default=noprint_wrappers=1:nokey=1", 
        file_path
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if result.returncode != 0:
        raise ValueError(f"Error getting file type: {result.stderr}")
    
    return result.stdout.strip()
