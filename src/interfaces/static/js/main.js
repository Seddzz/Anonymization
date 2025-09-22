// Clean JavaScript for SecureDoc - Data Privacy Tool
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    // Reset button state if returning via back/forward navigation
    window.addEventListener('pageshow', function(event) {
        // Only run on the main page with the text form
        const submitBtn = document.getElementById('textSubmitBtn');
        if (submitBtn) {
            resetButtonFromProgressBar(submitBtn);
        }
        const uploadBtn = document.getElementById('uploadBtn');
        if (uploadBtn) {
            resetButtonFromProgressBar(uploadBtn);
        }
    });
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
            } else {
                // Transform button into progress bar and allow form submission
                const submitBtn = document.getElementById('textSubmitBtn');
                const detectionMethod = document.querySelector('input[name="detector"]:checked').value;
                
                transformButtonToProgressBar(submitBtn, detectionMethod, 'text');
                // Form will submit normally and redirect to loading page
            }
        });
    }
    
    if (fileForm) {
        fileForm.addEventListener('submit', function(e) {
            const fileInput = document.getElementById('fileInput');
            if (!fileInput.files || fileInput.files.length === 0) {
                e.preventDefault();
                alert('Please select a file to upload.');
            } else {
                // Transform button into progress bar and allow form submission
                const uploadBtn = document.getElementById('uploadBtn');
                const detectionMethod = document.querySelector('input[name="detector"]:checked').value;
                
                transformButtonToProgressBar(uploadBtn, detectionMethod, 'file');
                // Form will submit normally and redirect to loading page
            }
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

// Transform button into simple progress bar
function transformButtonToProgressBar(button, detectionMethod, type) {
    if (!button) return;
    
    // Store original button content
    button.setAttribute('data-original-text', button.innerHTML);
    button.disabled = true;
    
    // Determine processing time based on method
    const isLLM = detectionMethod === 'llm';
    const processingTime = isLLM ? 35 : 8; // seconds - more realistic timing
    
    // Replace button content with progress bar
    button.innerHTML = `
        <div class="flex items-center justify-between">
            <span class="text-sm">${isLLM ? '🤖 AI Processing...' : '⚡ Processing...'}</span>
            <span id="percent-${button.id}" class="text-sm font-bold">0%</span>
        </div>
        <div class="mt-2 w-full bg-white bg-opacity-30 rounded-full h-3">
            <div id="bar-${button.id}" class="bg-white h-3 rounded-full transition-all duration-700 ease-out" style="width: 0%"></div>
        </div>
    `;
    
    // Start the progress animation
    animateProgress(button.id, processingTime);
}

// Animate the progress bar
function animateProgress(buttonId, totalTime) {
    const progressBar = document.getElementById(`bar-${buttonId}`);
    const percentText = document.getElementById(`percent-${buttonId}`);
    if (!progressBar || !percentText) return;
    let progress = 0;
    const updateInterval = 800; // Update every 800ms
    const incrementPerUpdate = (100 / totalTime) * (updateInterval / 1000);
    let fadeInterval = null;
    const progressInterval = setInterval(() => {
        // Add some randomness but keep it moving forward
        const randomIncrement = incrementPerUpdate + (Math.random() - 0.5) * 2;
        progress = Math.min(progress + Math.max(randomIncrement, 0.5), 95);
        // Update the UI
        progressBar.style.width = `${progress}%`;
        percentText.textContent = `${Math.round(progress)}%`;
        // Stop at 95% - let the server complete it
        if (progress >= 95) {
            clearInterval(progressInterval);
            percentText.textContent = '95%';
            // Add fade animation to progress bar
            progressBar.classList.add('progress-fade');
            let opacity = 1;
            fadeInterval = setInterval(() => {
                opacity = opacity === 1 ? 0.5 : 1;
                progressBar.style.opacity = opacity;
            }, 700);
        }
    }, updateInterval);
    // Store interval for cleanup
    window[`progressInterval_${buttonId}`] = progressInterval;
    window[`fadeInterval_${buttonId}`] = fadeInterval;
}

// Reset button to original state (for error handling)
function resetButtonFromProgressBar(button) {
    if (!button) return;
    
    const originalText = button.getAttribute('data-original-text');
    if (originalText) {
        button.innerHTML = originalText;
        button.disabled = false;
        button.removeAttribute('data-original-text');
        
        // Clear any running intervals
        const intervalId = window[`progressInterval_${button.id}`];
        if (intervalId) {
            clearInterval(intervalId);
            delete window[`progressInterval_${button.id}`];
        }
    }
}

// Utility function for smooth scrolling
function smoothScrollTo(element) {
    element.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
    });
}

// Global loading overlay for LLM processing
function showGlobalLoading() {
    // Create loading overlay if it doesn't exist
    let overlay = document.getElementById('globalLoadingOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'globalLoadingOverlay';
        overlay.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        overlay.innerHTML = `
            <div class="bg-white rounded-lg p-8 max-w-md mx-4 text-center">
                <div class="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <h3 class="text-xl font-semibold text-gray-800 mb-2">AI Processing</h3>
                <p class="text-gray-600 mb-4">Our advanced AI is analyzing your content...</p>
                <div class="text-sm text-gray-500">
                    <p>🤖 Using Mistral LLM for accurate detection</p>
                    <p>⏱️ This may take 30-60 seconds</p>
                    <p>☕ Please be patient while we ensure quality results</p>
                </div>
                <div class="mt-4 bg-gray-200 rounded-full h-2">
                    <div class="bg-blue-600 h-2 rounded-full animate-pulse" style="width: 75%"></div>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
    }
    overlay.style.display = 'flex';
}

function hideGlobalLoading() {
    const overlay = document.getElementById('globalLoadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// Setup timeout warning for LLM processing (works with progress bars)
function setupTimeoutWarning() {
    // Show extended time warning after 45 seconds
    setTimeout(() => {
        updateProgressMessage('Taking longer than expected... Please wait');
    }, 45000);
    
    // Show additional info after 75 seconds
    setTimeout(() => {
        updateProgressMessage('Complex analysis in progress... Almost done');
    }, 75000);
}

function updateProgressMessage(message) {
    // Update both text and file progress messages if they exist
    const textProgress = document.getElementById('progress-text-textSubmitBtn');
    const fileProgress = document.getElementById('progress-text-uploadBtn');
    
    if (textProgress) {
        textProgress.textContent = message;
    }
    if (fileProgress) {
        fileProgress.textContent = message;
    }
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
