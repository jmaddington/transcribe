import sqlite3
import os
import datetime
import traceback
from typing import Dict, List, Optional, Any, Tuple

from utils.logging_config import get_db_logger

# Initialize logger
logger = get_db_logger()

# Use db directory for database to work with Docker bind mounts
DB_DIR = os.path.join(os.getcwd(), "db")
os.makedirs(DB_DIR, exist_ok=True)
DATABASE_FILE = os.path.join(DB_DIR, "transcriptions.db")

def init_db():
    """Initialize the database and create tables if they don't exist."""
    logger.info(f"Initializing database: {DATABASE_FILE}")
    
    try:
        # Check if database file exists
        db_exists = os.path.exists(DATABASE_FILE)
        if db_exists:
            logger.info(f"Database file exists: {DATABASE_FILE}")
        else:
            logger.info(f"Creating new database file: {DATABASE_FILE}")
        
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Create custom_instructions table
        logger.info("Creating custom_instructions table if not exists")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_instructions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            instruction_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create transcriptions table
        logger.info("Creating transcriptions table if not exists")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transcriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            original_audio BLOB,
            whisper_transcription TEXT,
            processed_transcription TEXT,
            duration_seconds FLOAT,
            custom_instruction_id INTEGER,
            FOREIGN KEY (custom_instruction_id) REFERENCES custom_instructions (id)
        )
        ''')
        
        # Insert default custom instruction if none exists
        logger.info("Checking for default custom instruction")
        cursor.execute("SELECT COUNT(*) FROM custom_instructions")
        count = cursor.fetchone()[0]
        
        if count == 0:
            logger.info("No custom instructions found, adding default instruction")
            default_instruction = (
                "Default",
                "This is an automated transcript of a legal proceeding or notes with a client. "
                "Please add paragraphs, clean up grammar and spelling. Because it is an automated "
                "transcription some words may have been transcribed wrong, please use good judgment "
                "and change words if you think you need to."
            )
            cursor.execute(
                "INSERT INTO custom_instructions (name, instruction_text) VALUES (?, ?)",
                default_instruction
            )
            logger.info("Default instruction added successfully")
        else:
            logger.info(f"Found {count} existing custom instructions")
        
        conn.commit()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def get_db_connection():
    """Get a connection to the database."""
    try:
        logger.debug(f"Opening database connection to {DATABASE_FILE}")
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def save_custom_instruction(name: str, instruction_text: str) -> int:
    """Save a new custom instruction to the database."""
    logger.info(f"Saving new custom instruction: {name}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.debug(f"Instruction text length: {len(instruction_text)} characters")
        
        cursor.execute(
            "INSERT INTO custom_instructions (name, instruction_text) VALUES (?, ?)",
            (name, instruction_text)
        )
        
        instruction_id = cursor.lastrowid
        logger.info(f"Custom instruction saved with ID: {instruction_id}")
        
        conn.commit()
        return instruction_id
    except Exception as e:
        logger.error(f"Error saving custom instruction: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def get_all_custom_instructions() -> List[Dict[str, Any]]:
    """Get all custom instructions from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM custom_instructions ORDER BY name")
    instructions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return instructions

def get_custom_instruction(instruction_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific custom instruction by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM custom_instructions WHERE id = ?", (instruction_id,))
    instruction = cursor.fetchone()
    conn.close()
    return dict(instruction) if instruction else None

def delete_custom_instruction(instruction_id: int) -> bool:
    """Delete a custom instruction by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM custom_instructions WHERE id = ?", (instruction_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def save_transcription(
    filename: str,
    file_type: str,
    audio_data: bytes,
    whisper_transcription: str,
    processed_transcription: str,
    duration_seconds: float,
    custom_instruction_id: Optional[int] = None
) -> int:
    """Save a transcription to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO transcriptions (
            original_filename,
            file_type,
            original_audio,
            whisper_transcription,
            processed_transcription,
            duration_seconds,
            custom_instruction_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            filename,
            file_type,
            audio_data,
            whisper_transcription,
            processed_transcription,
            duration_seconds,
            custom_instruction_id
        )
    )
    transcription_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return transcription_id

def get_all_transcriptions() -> List[Dict[str, Any]]:
    """Get all transcriptions from the database (without audio data)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 
            t.id, t.original_filename, t.file_type, t.created_at, 
            t.whisper_transcription, t.processed_transcription, 
            t.duration_seconds, t.custom_instruction_id, c.name as instruction_name
        FROM transcriptions t
        LEFT JOIN custom_instructions c ON t.custom_instruction_id = c.id
        ORDER BY t.created_at DESC
        """
    )
    transcriptions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return transcriptions

def get_transcription(transcription_id: int, include_audio: bool = False) -> Optional[Dict[str, Any]]:
    """Get a specific transcription by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if include_audio:
        query = "SELECT * FROM transcriptions WHERE id = ?"
    else:
        query = "SELECT id, original_filename, file_type, created_at, whisper_transcription, processed_transcription, duration_seconds, custom_instruction_id FROM transcriptions WHERE id = ?"
    
    cursor.execute(query, (transcription_id,))
    transcription = cursor.fetchone()
    conn.close()
    
    return dict(transcription) if transcription else None

def delete_transcription(transcription_id: int) -> bool:
    """Delete a transcription by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transcriptions WHERE id = ?", (transcription_id,))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success
