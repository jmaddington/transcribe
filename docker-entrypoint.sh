#!/bin/bash
# More robust entrypoint script with better error handling and validation
set -e

echo "============================================="
echo "Starting Legal Audio Transcription Application"
echo "============================================="

# Function for error handling
handle_error() {
    echo "ERROR: $1"
    exit 1
}

echo "Checking system and permissions..."

# Create and validate directories with proper ownership
echo "Setting up directories..."
for dir in /app/uploads /app/temp_audio /app/logs; do
    mkdir -p $dir || handle_error "Failed to create directory: $dir"
    
    # Verify current user can write to the directory
    if ! touch "$dir/.write_test" 2>/dev/null; then
        handle_error "Permission denied: Cannot write to $dir"
    else
        rm "$dir/.write_test"
        echo "✓ Directory $dir is writable"
    fi
done

# Verify environment
echo "Verifying environment..."
echo "Python version: $(python --version)"
echo "Gunicorn version: $(gunicorn --version)"

# Verify required system dependencies
echo "Checking system dependencies..."

# Verify ffmpeg is installed
if command -v ffmpeg &> /dev/null; then
    echo "✓ FFmpeg is available: $(ffmpeg -version | head -n 1)"
else
    handle_error "FFmpeg is not installed or not in PATH!"
fi

# Check if curl is available (used for healthchecks)
if command -v curl &> /dev/null; then
    echo "✓ curl is available: $(curl --version | head -n 1)"
else
    handle_error "curl is not installed or not in PATH!"
fi

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "WARNING: OPENAI_API_KEY environment variable is not set!"
    echo "Transcription functionality will not work properly."
elif [[ "$OPENAI_API_KEY" == "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" ]]; then
    echo "WARNING: You're using the placeholder OpenAI API key."
    echo "For production, please set a valid key in .env.prod."
else
    echo "✓ OpenAI API key is configured"
fi

# Clean stale temporary files from previous runs
echo "Cleaning up stale temporary files..."
find /app/temp_audio -type f -name "*.temp.*" -mtime +1 -delete 2>/dev/null || true
echo "✓ Cleanup complete"

# Prepare database directory
echo "Preparing database directory..."
mkdir -p /app/db
if ! touch "/app/db/.write_test" 2>/dev/null; then
    handle_error "Permission denied: Cannot write to database directory"
else
    rm "/app/db/.write_test"
    echo "✓ Database directory is writable"
fi

# Initialize database
echo "Initializing database..."
if python -c "from database import init_db; init_db()"; then
    echo "✓ Database initialization complete"
    # Verify database is writable
    if python -c "from database import get_all_custom_instructions; get_all_custom_instructions()"; then
        echo "✓ Database is readable and writable"
    else
        handle_error "Database verification failed - cannot read from database"
    fi
else
    handle_error "Database initialization failed!"
fi

echo "Environment setup complete, starting application..."
echo "Starting with command: $@"
echo "============================================="

# Execute the command passed to the script (default: start the app with gunicorn)
exec "$@"
