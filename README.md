# Legal Audio Transcription Tool

A Flask-based web application for transcribing and processing legal audio recordings using OpenAI's Whisper and GPT-4o models.

## Features

- **Audio Transcription**: Upload and transcribe MP3, WAV, MP4, M4A, OGG, and FLAC audio files
- **Large File Handling**: Automatically splits large files to meet OpenAI API size limits
- **AI Post-Processing**: Uses GPT-4o to clean up, format, and enhance raw transcriptions
- **Custom Instructions**: Create and save custom post-processing instructions for different types of legal recordings
- **Export Options**: Download transcriptions as PDF or plain text files
- **Transcription History**: Browse and manage all previous transcriptions
- **SQLite Database**: Store transcriptions and custom instructions locally

## Prerequisites

### For Local Development
- Python 3.9+
- FFmpeg (for audio file processing)
- OpenAI API key

### For Docker Deployment
- Docker and Docker Compose
- OpenAI API key

## Installation

### Local Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd transcribe
   ```

2. Create and activate a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

### Docker Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd transcribe
   ```

2. Edit the `.env.prod` file to add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

3. Create the data directory:
   ```
   mkdir -p data
   ```

## Usage

### Local Usage

1. Start the Flask application:
   ```
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

### Docker Usage

#### Simple Setup (Without Reverse Proxy)

1. Start the application:
   ```
   docker-compose -f docker-compose.simple.yml up -d
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:8000/
   ```

#### Full Setup (With Caddy Reverse Proxy)

1. Edit the Caddyfile to set your domain name and email for HTTPS certificates:
   ```
   # Change transcribe.example.com to your actual domain
   ```

2. Start the application:
   ```
   docker-compose up -d
   ```

3. Access the application using your configured domain name.

#### Stopping the Application

```
docker-compose down  # or docker-compose -f docker-compose.simple.yml down
```

Once the application is running, you can upload an audio file, select post-processing instructions, and submit for transcription.

## Project Structure

```
transcribe/
├── app.py                  # Main Flask application
├── database.py             # SQLite database operations
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables for local development
├── .env.prod               # Environment variables for Docker deployment
├── .gitignore              # Git ignore file
├── Dockerfile              # Docker container definition
├── docker-compose.yml      # Docker Compose with Caddy setup
├── docker-compose.simple.yml # Docker Compose without Caddy
├── docker-entrypoint.sh    # Container startup script
├── Caddyfile               # Caddy reverse proxy configuration
├── static/                 # Static assets
│   ├── css/                # CSS files
│   └── js/                 # JavaScript files
├── templates/              # HTML templates
│   ├── base.html           # Base template
│   ├── index.html          # Homepage
│   ├── view_transcription.html  # Transcription view
│   └── custom_instructions.html  # Custom instructions management
├── utils/                  # Utility modules
│   ├── audio_handler.py    # Audio file processing
│   ├── export_utils.py     # Export functionality
│   └── openai_client.py    # OpenAI API integration
├── uploads/                # Uploaded audio files (created at runtime)
└── temp_audio/             # Temporary files for processing (created at runtime)
```

## Technologies Used

- **Backend**: Flask, SQLite, FFmpeg
- **Frontend**: Bootstrap 5, Font Awesome
- **AI**: OpenAI Whisper (speech-to-text), GPT-4o (post-processing)
- **PDF Generation**: ReportLab

## Important Notes

- The application requires an OpenAI API key with access to both Whisper and GPT-4o models
- Transcription of large audio files may take some time and consume API credits
- FFmpeg must be installed on the system for audio file processing
