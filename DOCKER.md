# Docker Deployment Guide (Updated 2025)

This document provides detailed information about the modernized Docker setup for the Legal Audio Transcription Tool.

## Docker Configuration Overview

The application has been containerized with several key components using the latest best practices:

1. **Application Container** - Running the Flask app with Gunicorn 21.2.0 as the production WSGI server on Python 3.12
2. **Caddy Reverse Proxy** (optional) - Caddy 2.7.6 providing HTTP/3, automatic HTTPS, modern security headers, and proper request handling
3. **Volume Persistence** - For database, uploads, and temporary files
4. **Environment Configuration** - Securely managing credentials and settings with modern Flask configuration
5. **Performance Optimizations** - Worker configuration, request limits, and Python optimization flags

## Deployment Options

### Simple Deployment

The `docker-compose.simple.yml` file provides a streamlined setup without a reverse proxy:

```bash
docker-compose -f docker-compose.simple.yml up -d
```

Access the application at `http://localhost:8000`

### Full Deployment with Caddy

The main `docker-compose.yml` includes Caddy as a reverse proxy:

```bash
docker-compose up -d
```

Access the application using the domain you configured in the Caddyfile.

## Configuration Files

- **Dockerfile**: Container definition with Python 3.12, optimized Gunicorn settings, and proper environment configuration
- **docker-compose.yml**: Docker Compose 3.9 multi-container setup with Caddy 2.7.6
- **docker-compose.simple.yml**: Simplified Docker Compose 3.9 setup without Caddy
- **Caddyfile**: Caddy reverse proxy configuration with HTTP/3 and modern security headers
- **.env.prod**: Production environment variables using modern Flask configuration
- **docker-entrypoint.sh**: Container startup script for proper initialization

## Volume Management

The Docker setup uses named volumes for data persistence:

- `./data/transcriptions.db:/app/transcriptions.db`: SQLite database
- `uploads`: Uploaded audio files
- `temp_audio`: Temporary processing files
- `logs`: Application logs

## Security Considerations

1. **Non-root User**: The application runs as a non-root user inside the container
2. **Environment Variables**: API keys are stored as environment variables, not in the container
3. **HTTPS with Caddy**: Automatic TLS certificate management
4. **Security Headers**: Configured in Caddy to enhance web security

## System Requirements

- Docker Engine 24.0.0+
- Docker Compose 2.20.0+
- At least 2GB of RAM
- 10GB+ free disk space (if processing large audio files)

## Scaling Considerations

For high-traffic deployments, consider:

1. Adjusting the number of Gunicorn workers in the Dockerfile (currently 4)
2. Increasing container resource limits in docker-compose.yml
3. Using a dedicated database server instead of SQLite
4. Implementing a dedicated object storage for uploads and exports

## Updating the Application

To update the application:

1. Pull the latest code changes
2. Rebuild the Docker image:
   ```bash
   docker-compose build
   ```
3. Restart the containers:
   ```bash
   docker-compose down && docker-compose up -d
   ```

## Troubleshooting

### Common Issues

1. **Database Permission Errors**: Check that the data directory exists and has proper permissions
2. **OpenAI API Issues**: Verify your API key is correctly set in `.env.prod`
3. **Large File Upload Problems**: Adjust timeouts in Caddy and Gunicorn as needed

### Logs

View container logs:
```bash
docker-compose logs -f app  # Application logs
docker-compose logs -f caddy  # Caddy logs
