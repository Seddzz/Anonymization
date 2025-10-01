// Result page JavaScript functionality
// This file handles all interactive features for the result page

document.addEventListener('DOMContentLoaded', function() {
    // Load template data from the script tag
    const templateDataScript = document.getElementById('template-data');
    let templateData = {};
    
    try {
        templateData = JSON.parse(templateDataScript.textContent);
    } catch (e) {
        console.error('Failed to parse template data:', e);
        templateData = {
            originalMapping: {},
            originalText: '',
            sourceText: '',
            currentWorkflowType: 'Unknown'
        };
    }

    // Global variables
    window.templateData = templateData;
    
    console.log('[DEBUG] Template data:', templateData);

    // Initialize tabs
    initializeTabs();
    
    // Initialize button event listeners
    initializeButtons();
    
    // Show the default tab
    showTab('anonymized');
});

function initializeTabs() {
    // Add click event listeners to tab buttons
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabId = this.id.replace('Tab', '');
            showTab(tabId);
        });
    });
}

function initializeButtons() {
    // Copy button
    const copyButton = document.getElementById('copyButton');
    if (copyButton) {
        copyButton.addEventListener('click', copyToClipboard);
    }
    
    // Reprocess button
    const reprocessButton = document.getElementById('reprocessButton');
    if (reprocessButton) {
        reprocessButton.addEventListener('click', reprocessWithSelection);
    }
    
    // Select all button
    const selectAllButton = document.getElementById('selectAllButton');
    if (selectAllButton) {
        selectAllButton.addEventListener('click', selectAllEntities);
    }
    
    // Clear all button
    const clearAllButton = document.getElementById('clearAllButton');
    if (clearAllButton) {
        clearAllButton.addEventListener('click', clearAllEntities);
    }
    
    // Copy live result button
    const copyLiveButton = document.getElementById('copyLiveButton');
    if (copyLiveButton) {
        copyLiveButton.addEventListener('click', copyLiveResult);
    }
    
    // Add change listeners to checkboxes
    const checkboxes = document.querySelectorAll('#entityTypeControls input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateEntitySelection);
    });
}

function showTab(tabName) {
    console.log('Switching to tab:', tabName);
    
    // Hide all tab contents
    const contents = document.getElementsByClassName('tab-content');
    for (let i = 0; i < contents.length; i++) {
        contents[i].style.display = 'none';
        contents[i].classList.add('hidden');
    }
    
    // Reset all tab buttons
    const buttons = document.getElementsByClassName('tab-button');
    for (let i = 0; i < buttons.length; i++) {
        buttons[i].classList.remove('border-blue-600', 'text-blue-600');
        buttons[i].classList.add('border-transparent', 'text-gray-500');
    }
    
    // Show selected tab
    const targetContent = document.getElementById(tabName + 'Content');
    if (targetContent) {
        targetContent.style.display = 'block';
        targetContent.classList.remove('hidden');
        console.log('Showed tab:', tabName + 'Content');
    }
    
    // Activate selected button
    const targetButton = document.getElementById(tabName + 'Tab');
    if (targetButton) {
        targetButton.classList.add('border-blue-600', 'text-blue-600');
        targetButton.classList.remove('border-transparent', 'text-gray-500');
        console.log('Activated button:', tabName + 'Tab');
    }
}

function copyToClipboard() {
    const textArea = document.getElementById('resultText');
    if (!textArea) {
        alert('No text to copy');
        return;
    }
    
    textArea.select();
    textArea.setSelectionRange(0, 99999); // For mobile devices
    
    try {
        document.execCommand('copy');
        
        // Show success feedback
        const button = document.getElementById('copyButton');
        const originalHTML = button.innerHTML;  // Save complete HTML structure
        button.innerHTML = 'Copied!';  // Simple text for feedback
        button.classList.add('bg-green-600');
        button.classList.remove('bg-blue-600', 'hover:bg-blue-700');
        
        setTimeout(() => {
            button.innerHTML = originalHTML;  // Restore complete HTML structure
            button.classList.remove('bg-green-600');
            button.classList.add('bg-blue-600', 'hover:bg-blue-700');
        }, 2000);
    } catch (err) {
        console.error('Failed to copy text: ', err);
        alert('Failed to copy text. Please select and copy manually.');
    }
}

function updateEntitySelection() {
    console.log('Entity selection updated');
    // Could add preview logic here in the future
}

function selectAllEntities() {
    const checkboxes = document.querySelectorAll('#entityTypeControls input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = true);
    updateEntitySelection();
    console.log('All entities selected');
}

function clearAllEntities() {
    const checkboxes = document.querySelectorAll('#entityTypeControls input[type="checkbox"]');
    checkboxes.forEach(cb => cb.checked = false);
    updateEntitySelection();
    console.log('All entities cleared');
}

function getSelectedEntityTypes() {
    const checkboxes = document.querySelectorAll('#entityTypeControls input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

function reprocessWithSelection() {
    const selectedTypes = getSelectedEntityTypes();
    
    if (selectedTypes.length === 0) {
        alert('Please select at least one entity type to anonymize.');
        return;
    }
    
    // Show loading state
    const button = document.getElementById('reprocessButton');
    const originalButtonText = button.textContent;
    button.textContent = 'Processing...';
    button.disabled = true;
    
    // Get data from template
    const liveTextArea = document.getElementById('livePreviewText');
    const liveText = liveTextArea ? liveTextArea.value : '';
    const currentWorkflowType = window.templateData.currentWorkflowType;
    
    // Determine detection method from current workflow
    let detectionMethod = 'spacy'; // default
    if (currentWorkflowType.toLowerCase().includes('llm')) {
        detectionMethod = 'llm';
    }
    
    // Prepare form data
    const formData = new FormData();
    formData.append('text', liveText);
    formData.append('detection_method', detectionMethod);
    selectedTypes.forEach(type => {
        formData.append('entity_types', type);
    });
    
    // Send request to reprocess
    fetch('/custom-anonymize', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.redirected) {
            // Backend redirects to waiting page for background processing
            window.location.href = response.url;
        } else {
            return response.json();
        }
    })
    .then(data => {
        if (data && !data.success) {
            alert('Error: ' + (data.error || 'Unknown error occurred'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while reprocessing. Please try again.');
    })
    .finally(() => {
        // Restore button state
        button.textContent = originalButtonText;
        button.disabled = false;
    });
}

function copyLiveResult() {
    const liveText = document.getElementById('livePreviewText');
    if (!liveText) {
        alert('No live preview text to copy');
        return;
    }
    
    liveText.select();
    liveText.setSelectionRange(0, 99999);
    
    try {
        document.execCommand('copy');
        
        // Show success feedback
        const button = document.getElementById('copyLiveButton');
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        
        setTimeout(() => {
            button.textContent = originalText;
        }, 2000);
    } catch (err) {
        console.error('Failed to copy live result: ', err);
        alert('Failed to copy text. Please select and copy manually.');
    }
}

// Make functions globally available for any inline calls
window.showTab = showTab;
window.copyToClipboard = copyToClipboard;
window.selectAllEntities = selectAllEntities;
window.clearAllEntities = clearAllEntities;
window.reprocessWithSelection = reprocessWithSelection;
window.copyLiveResult = copyLiveResult;