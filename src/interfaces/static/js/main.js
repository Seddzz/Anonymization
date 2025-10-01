// Clean JavaScript for SecureDoc - Data Privacy Tool
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Only run if we're on the main page
    if (document.getElementById('textForm')) {
        setupFileUpload();
        setupFormValidation();
        setupTextInput();
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
    e.currentTarget.classList.add('border-blue-400', 'bg-blue-50');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('border-blue-400', 'bg-blue-50');
}

function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('border-blue-400', 'bg-blue-50');
    handleFiles(e.dataTransfer.files);
}

function handleFiles(files) {
    if (files.length === 0) return;
    
    const file = files[0];
    const uploadBtn = document.getElementById('uploadBtn');
    const dropzoneContent = document.getElementById('dropzoneContent');
    
    // Validate file type
    const allowedTypes = ['.txt', '.docx', '.pdf'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
        alert('Please select a valid file type: TXT, DOCX, or PDF');
        return;
    }
    
    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB in bytes
    if (file.size > maxSize) {
        alert('File size must be less than 10MB');
        return;
    }
    
    // Update UI to show selected file
    const fileName = file.name;
    const fileSize = (file.size / 1024 / 1024).toFixed(2);
    
    dropzoneContent.innerHTML = `
        <div class="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
            <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
        </div>
        <p class="text-lg font-medium mb-2 text-gray-700">${fileName}</p>
        <p class="text-gray-500 text-sm">${fileSize} MB • Ready to upload</p>
    `;
    
    // Enable upload button
    uploadBtn.disabled = false;
    uploadBtn.classList.remove('bg-gray-300', 'cursor-not-allowed');
    uploadBtn.classList.add('bg-green-600', 'hover:bg-green-700');
}

function setupFormValidation() {
    const textForm = document.getElementById('textForm');
    const fileForm = document.getElementById('fileForm');
    
    if (textForm) {
        textForm.addEventListener('submit', function(e) {
            const textInput = document.getElementById('textInput');
            if (!textInput.value.trim()) {
                e.preventDefault();
                alert('Please enter some text to anonymize.');
                textInput.focus();
            } 
            // Form will submit normally and redirect to loading page
        });
    }
    
    if (fileForm) {
        fileForm.addEventListener('submit', function(e) {
            const fileInput = document.getElementById('fileInput');
            if (!fileInput.files || fileInput.files.length === 0) {
                e.preventDefault();
                alert('Please select a file to upload.');
            } 
            // Form will submit normally and redirect to loading page
        });
    }
}

function setupTextInput() {
    const textInput = document.getElementById('textInput');
    if (!textInput) return;
    
    // Auto-resize textarea and enable/disable button based on content
    function handleTextInputEvent() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';

        const maxLength = 10000;
        const remaining = maxLength - this.value.length;
        const submitBtn = document.getElementById('textSubmitBtn');

        if (remaining < 100) {
            if (!document.getElementById('charCounter')) {
                const counter = document.createElement('div');
                counter.id = 'charCounter';
                counter.className = 'text-sm text-gray-500 mt-2 text-right';
                this.parentNode.appendChild(counter);
            }
            document.getElementById('charCounter').textContent = `${remaining} characters remaining`;
        } else {
            const counter = document.getElementById('charCounter');
            if (counter) counter.remove();
        }

        // Enable/disable submit button based on content
        if (this.value.trim().length > 0) {
            submitBtn.disabled = false;
            submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        } else {
            submitBtn.disabled = true;
            submitBtn.classList.add('opacity-50', 'cursor-not-allowed');
        }
    }

    // Character counter (optional)
    const maxLength = 10000;
    textInput.setAttribute('maxlength', maxLength);

    textInput.addEventListener('input', handleTextInputEvent);
    textInput.addEventListener('change', handleTextInputEvent);
    textInput.addEventListener('paste', function(e) {
        // Wait for paste to complete
        setTimeout(() => handleTextInputEvent.call(this, e), 0);
    });

    // On page load, always check and update button state (handles autofill, browser restore, etc)
    window.addEventListener('DOMContentLoaded', () => handleTextInputEvent.call(textInput));
    window.addEventListener('pageshow', () => handleTextInputEvent.call(textInput));
    // Also run immediately in case of direct script load
    setTimeout(() => handleTextInputEvent.call(textInput), 0);
}

// Utility function for smooth scrolling
function smoothScrollTo(element) {
    element.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
    });
}

// Privacy-focused messaging
const privacyMessages = [
    "Your data is processed locally and never stored",
    "Zero-retention policy ensures complete privacy", 
    "Advanced AI removes personal information safely",
    "Secure processing protects your sensitive data"
];

function showPrivacyMessage() {
    const message = privacyMessages[Math.floor(Math.random() * privacyMessages.length)];
    console.log(`🔒 SecureDoc: ${message}`);
}
