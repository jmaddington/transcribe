import os
import time
import tempfile
import traceback
from typing import List, Dict, Any, Optional

import openai
from dotenv import load_dotenv

from utils.logging_config import get_api_logger

# Initialize logger
logger = get_api_logger()

# Load environment variables
logger.info("Loading environment variables")
load_dotenv()
logger.info("Environment variables loaded")

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY is required but not found in environment variables")

logger.info("Initializing OpenAI client")
client = openai.OpenAI(api_key=api_key)
logger.info("OpenAI client initialized")

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
    logger.info(f"Starting transcription for file: {audio_file_path}")
    
    try:
        # Check if file exists
        if not os.path.exists(audio_file_path):
            logger.error(f"File not found: {audio_file_path}")
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        # Log file size
        file_size = os.path.getsize(audio_file_path)
        file_size_mb = file_size / (1024 * 1024)  # Convert to MB
        logger.info(f"File size: {file_size_mb:.2f} MB")
        
        # Check if file is within size limits
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"File exceeds Whisper API size limit (25MB): {file_size_mb:.2f} MB")
        
        start_time = time.time()
        logger.info("Sending request to OpenAI Whisper API")
        
        with open(audio_file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Transcription completed in {elapsed_time:.2f} seconds")
        
        # Log some stats about the transcription
        text_length = len(response.text)
        logger.info(f"Transcription generated {text_length} characters")
        
        return response.text
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        logger.error(traceback.format_exc())
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
    logger.info("Starting GPT-4o post-processing")
    
    try:
        # Log transcription length and instruction
        transcription_length = len(transcription)
        instruction_length = len(custom_instruction)
        logger.info(f"Transcription length: {transcription_length} characters")
        logger.info(f"Custom instruction length: {instruction_length} characters")
        
        # Log a snippet of the transcription for debugging
        logger.info(f"Transcription snippet: {transcription[:100]}...")
        
        start_time = time.time()
        logger.info("Sending request to OpenAI GPT-4o API")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": custom_instruction},
                {"role": "user", "content": transcription}
            ],
            temperature=0.3,
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Post-processing completed in {elapsed_time:.2f} seconds")
        
        processed_text = response.choices[0].message.content
        processed_length = len(processed_text)
        logger.info(f"Processed transcription length: {processed_length} characters")
        
        # Log a snippet of the processed text
        logger.info(f"Processed text snippet: {processed_text[:100]}...")
        
        return processed_text
    except Exception as e:
        logger.error(f"Error post-processing transcription: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def check_file_size(file_path: str) -> bool:
    """
    Check if the file size is within the Whisper API limit.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if the file size is within the limit, False otherwise
    """
    logger.info(f"Checking file size for: {file_path}")
    
    try:
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)  # Convert to MB
        
        is_within_limit = file_size <= MAX_FILE_SIZE
        
        if is_within_limit:
            logger.info(f"File size is within limit: {file_size_mb:.2f} MB / 25 MB")
        else:
            logger.warning(f"File size exceeds limit: {file_size_mb:.2f} MB / 25 MB")
        
        return is_within_limit
    except Exception as e:
        logger.error(f"Error checking file size: {str(e)}")
        logger.error(traceback.format_exc())
        raise
