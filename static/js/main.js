// Minimal JavaScript for anonymization app
// Only includes essential functionality

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Only run if we're on the index page
    if (document.getElementById('textForm')) {
        setupFileUpload();
        setupFormValidation();
    }
}

function setupFileUpload() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    
    if (!dropzone || !fileInput || !uploadBtn) return;
    
    // Click to upload
    dropzone.addEventListener('click', () => fileInput.click());
    
    // Drag and drop events
    dropzone.addEventListener('dragover', handleDragOver);
    dropzone.addEventListener('dragleave', handleDragLeave);
    dropzone.addEventListener('drop', handleDrop);
    
    // File input change
    fileInput.addEventListener('change', (e) => handleFiles(e.target.files));
}

function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
}

function handleFiles(files) {
    if (files.length === 0) return;
    
    const file = files[0];
    const validTypes = ['text/plain', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    const maxSize = 10 * 1024 * 1024; // 10MB
    
    // Validation
    if (!validTypes.includes(file.type)) {
        showAlert('Please select a valid file type (.txt, .docx, or .pdf)');
        return;
    }
    
    if (file.size > maxSize) {
        showAlert('File size must be less than 10MB');
        return;
    }
    
    // Update UI to show selected file
    updateDropzoneUI(file);
    enableUploadButton();
}

function updateDropzoneUI(file) {
    const dropzoneContent = document.getElementById('dropzoneContent');
    if (!dropzoneContent) return;
    
    dropzoneContent.innerHTML = `
        <svg class="mx-auto w-12 h-12 text-green-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <p class="text-lg font-medium mb-2">${file.name}</p>
        <p class="text-gray-400">${formatFileSize(file.size)}</p>
    `;
}

function enableUploadButton() {
    const uploadBtn = document.getElementById('uploadBtn');
    if (!uploadBtn) return;
    
    uploadBtn.disabled = false;
    uploadBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    uploadBtn.classList.add('hover-scale');
}

function setupFormValidation() {
    const textForm = document.getElementById('textForm');
    const fileForm = document.getElementById('fileForm');
    
    if (textForm) {
        textForm.addEventListener('submit', validateTextForm);
    }
    
    if (fileForm) {
        fileForm.addEventListener('submit', validateFileForm);
    }
}

function validateTextForm(e) {
    const textInput = document.getElementById('textInput');
    if (!textInput || !textInput.value.trim()) {
        e.preventDefault();
        showAlert('Please enter some text to anonymize.');
        return;
    }
    showLoadingState(e.target);
}

function validateFileForm(e) {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput || !fileInput.files.length) {
        e.preventDefault();
        showAlert('Please select a file to upload.');
        return;
    }
    showLoadingState(e.target);
}

function showLoadingState(form) {
    const buttons = form.querySelectorAll('button[type="submit"]');
    buttons.forEach(btn => {
        btn.innerHTML = '<div class="spinner mx-auto"></div>';
        btn.disabled = true;
    });
    
    // Disable all inputs
    const inputs = form.querySelectorAll('input, textarea');
    inputs.forEach(input => input.disabled = true);
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showAlert(message) {
    // Simple alert for now - can be replaced with a nicer modal later
    alert(message);
}

// Copy to clipboard functionality (for results page)
function copyToClipboard(text) {
    if (!text) {
        const textElement = document.querySelector('#anonymizedContent pre');
        text = textElement ? textElement.textContent : '';
    }
    
    if (navigator.clipboard) {
        return navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
        } catch (err) {
            console.error('Copy failed:', err);
        }
        document.body.removeChild(textArea);
        return Promise.resolve();
    }
}