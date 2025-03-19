// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // File upload validation
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const uploadBtn = document.getElementById('upload_btn');
            if (this.files.length > 0) {
                // Check file extension
                const fileName = this.files[0].name;
                const fileExt = fileName.split('.').pop().toLowerCase();
                const allowedExts = ['mp3', 'wav', 'mp4', 'm4a', 'ogg', 'flac'];
                
                if (!allowedExts.includes(fileExt)) {
                    alert('Invalid file format. Please select an MP3, WAV, MP4, M4A, OGG, or FLAC file.');
                    this.value = '';
                    uploadBtn.disabled = true;
                    return;
                }
                
                // Check file size (limit to 500MB, matching Flask config)
                const maxSize = 500 * 1024 * 1024; // 500MB
                if (this.files[0].size > maxSize) {
                    alert('File is too large. Maximum size is 500MB.');
                    this.value = '';
                    uploadBtn.disabled = true;
                    return;
                }
                
                uploadBtn.disabled = false;
            } else {
                uploadBtn.disabled = true;
            }
        });
    }
    
    // Custom instruction form
    const instructionForm = document.querySelector('form[action*="custom_instruction"]');
    if (instructionForm) {
        instructionForm.addEventListener('submit', function(e) {
            const nameInput = document.getElementById('name');
            const textInput = document.getElementById('instruction_text');
            
            if (!nameInput.value.trim() || !textInput.value.trim()) {
                e.preventDefault();
                alert('Please fill out both the name and instruction text fields.');
            }
        });
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            const closeButton = message.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });
    
    // Confirm deletion of transcriptions
    const deleteButtons = document.querySelectorAll('button[data-bs-target^="#deleteModal"]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const modalId = this.getAttribute('data-bs-target');
            const modal = document.querySelector(modalId);
            const deleteForm = modal.querySelector('form');
            
            // Add confirmation logic if needed
            deleteForm.addEventListener('submit', function() {
                const deleteButton = this.querySelector('button[type="submit"]');
                deleteButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Deleting...';
                deleteButton.disabled = true;
            });
        });
    });
    
    // Footer year
    const yearSpan = document.querySelector('.footer .text-muted');
    if (yearSpan) {
        const currentYear = new Date().getFullYear();
        yearSpan.textContent = yearSpan.textContent.replace(/\d{4}/, currentYear);
    }
});
