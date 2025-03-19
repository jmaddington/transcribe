import os
import time
import tempfile
from typing import List, Dict, Any, Optional

import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Maximum file size for Whisper API in bytes (25MB)
MAX_FILE_SIZE = 25 * 1024 * 1024

def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribe audio file using OpenAI's Whisper model.
    
    Args:
        audio_file_path: Path to the audio file
        
    Returns:
        Transcription text
    """
    try:
        with open(audio_file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        return response.text
    except Exception as e:
        print(f"Error transcribing audio: {str(e)}")
        raise

def post_process_transcription(transcription: str, custom_instruction: str) -> str:
    """
    Post-process transcription using GPT-4o model.
    
    Args:
        transcription: Raw transcription text
        custom_instruction: Custom instruction for post-processing
        
    Returns:
        Processed transcription text
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": custom_instruction},
                {"role": "user", "content": transcription}
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error post-processing transcription: {str(e)}")
        raise

def check_file_size(file_path: str) -> bool:
    """
    Check if the file size is within the Whisper API limit.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if the file size is within the limit, False otherwise
    """
    file_size = os.path.getsize(file_path)
    return file_size <= MAX_FILE_SIZE
