import os
import io
import uuid
from datetime import datetime
from flask import Flask, request, render_template, jsonify, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename

from database import init_db, get_all_transcriptions, get_transcription
from database import save_custom_instruction, get_all_custom_instructions, get_custom_instruction, delete_custom_instruction
from database import save_transcription, delete_transcription

from utils.audio_handler import save_uploaded_file, get_audio_duration, split_audio_file, cleanup_temp_files, get_file_type
from utils.openai_client import transcribe_audio, post_process_transcription, check_file_size
from utils.export_utils import generate_pdf, export_plaintext

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload size

# Initialize database
init_db()

# Allowed file extensions
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'mp4', 'm4a', 'ogg', 'flac'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html', 
                          transcriptions=get_all_transcriptions(),
                          custom_instructions=get_all_custom_instructions())

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and transcription."""
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Get custom instruction ID
        custom_instruction_id = request.form.get('custom_instruction_id')
        if custom_instruction_id:
            custom_instruction_id = int(custom_instruction_id)
            custom_instruction_obj = get_custom_instruction(custom_instruction_id)
            custom_instruction = custom_instruction_obj['instruction_text']
        else:
            # Get default instruction
            instructions = get_all_custom_instructions()
            custom_instruction = instructions[0]['instruction_text'] if instructions else ""
            custom_instruction_id = instructions[0]['id'] if instructions else None
        
        # Generate a unique filename to prevent collisions
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        
        # Save the uploaded file
        file_path = save_uploaded_file(file, unique_filename)
        
        try:
            # Get audio duration
            duration = get_audio_duration(file_path)
            
            # Get audio format
            file_type = get_file_type(file_path)
            
            # Split file if needed
            chunk_files = split_audio_file(file_path)
            
            # Transcribe each chunk
            transcription_parts = []
            for chunk_file in chunk_files:
                transcription_text = transcribe_audio(chunk_file)
                transcription_parts.append(transcription_text)
            
            # Combine transcriptions
            whisper_transcription = " ".join(transcription_parts)
            
            # Post-process with GPT-4o
            processed_transcription = post_process_transcription(whisper_transcription, custom_instruction)
            
            # Save to database
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            
            transcription_id = save_transcription(
                filename=original_filename,
                file_type=file_type,
                audio_data=audio_data,
                whisper_transcription=whisper_transcription,
                processed_transcription=processed_transcription,
                duration_seconds=duration,
                custom_instruction_id=custom_instruction_id
            )
            
            # Clean up temporary files
            if len(chunk_files) > 1:
                cleanup_temp_files(chunk_files)
            
            flash('Transcription completed successfully!', 'success')
            return redirect(url_for('view_transcription', transcription_id=transcription_id))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    flash('File type not allowed')
    return redirect(url_for('index'))

@app.route('/transcription/<int:transcription_id>')
def view_transcription(transcription_id):
    """View a specific transcription."""
    transcription = get_transcription(transcription_id)
    if not transcription:
        flash('Transcription not found')
        return redirect(url_for('index'))
    
    return render_template('view_transcription.html', 
                          transcription=transcription,
                          custom_instructions=get_all_custom_instructions())

@app.route('/transcription/<int:transcription_id>/delete', methods=['POST'])
def delete_transcription_route(transcription_id):
    """Delete a transcription."""
    success = delete_transcription(transcription_id)
    if success:
        flash('Transcription deleted successfully', 'success')
    else:
        flash('Error deleting transcription', 'error')
    
    return redirect(url_for('index'))

@app.route('/export/<int:transcription_id>/<format>')
def export_transcription(transcription_id, format):
    """Export a transcription to PDF or plaintext."""
    transcription = get_transcription(transcription_id)
    if not transcription:
        flash('Transcription not found')
        return redirect(url_for('index'))
    
    try:
        filename = transcription['original_filename'].rsplit('.', 1)[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == 'pdf':
            output_path = f"{filename}_{timestamp}.pdf"
            filepath = generate_pdf(transcription, output_path)
            return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))
        
        elif format == 'text':
            output_path = f"{filename}_{timestamp}.txt"
            filepath = export_plaintext(transcription, output_path)
            return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))
        
        else:
            flash('Invalid export format')
            return redirect(url_for('view_transcription', transcription_id=transcription_id))
            
    except Exception as e:
        flash(f'Error exporting transcription: {str(e)}', 'error')
        return redirect(url_for('view_transcription', transcription_id=transcription_id))

@app.route('/custom_instructions')
def custom_instructions():
    """View all custom instructions."""
    return render_template('custom_instructions.html', 
                          custom_instructions=get_all_custom_instructions())

@app.route('/custom_instruction', methods=['POST'])
def add_custom_instruction():
    """Add a new custom instruction."""
    name = request.form.get('name')
    instruction_text = request.form.get('instruction_text')
    
    if not name or not instruction_text:
        flash('Name and instruction text are required', 'error')
        return redirect(url_for('custom_instructions'))
    
    instruction_id = save_custom_instruction(name, instruction_text)
    
    flash('Custom instruction added successfully', 'success')
    return redirect(url_for('custom_instructions'))

@app.route('/custom_instruction/<int:instruction_id>/delete', methods=['POST'])
def delete_custom_instruction_route(instruction_id):
    """Delete a custom instruction."""
    success = delete_custom_instruction(instruction_id)
    if success:
        flash('Custom instruction deleted successfully', 'success')
    else:
        flash('Error deleting custom instruction', 'error')
    
    return redirect(url_for('custom_instructions'))

if __name__ == '__main__':
    app.run(debug=True)
