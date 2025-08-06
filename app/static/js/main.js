// XR Health - Professional Medical Imaging Software
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initializeApp();
    
    // Set current date
    document.getElementById('currentDate').textContent = new Date().toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric'
    });
});

function initializeApp() {
    // File upload handling
    setupFileUpload();
    
    // Viewer controls
    setupViewerControls();
    
    // Analysis button
    setupAnalysisButton();
    
    // Investigation type selector
    setupInvestigationType();
}

function setupFileUpload() {
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseBtn');
    const uploadArea = document.getElementById('uploadArea');
    const imageContainer = document.getElementById('imageContainer');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    // Browse button click
    browseBtn.addEventListener('click', () => {
        fileInput.click();
    });
    
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--accent-blue)';
        uploadArea.style.background = 'var(--card-bg)';
    });
    
    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--border-color)';
        uploadArea.style.background = 'var(--darker-bg)';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--border-color)';
        uploadArea.style.background = 'var(--darker-bg)';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    // Validate file type
    if (!file.type.startsWith('image/')) {
        showNotification('Please select a valid image file.', 'error');
        return;
    }
    
    // Validate file size (16MB limit)
    if (file.size > 16 * 1024 * 1024) {
        showNotification('File size must be less than 16MB.', 'error');
        return;
    }
    
    // Display image
    displayImage(file);
    
    // Show analyze buttons
    document.getElementById('analyzeBtn').style.display = 'flex';
    document.getElementById('freshAnalyzeBtn').style.display = 'flex';
    
    // Store file for analysis
    window.currentFile = file;
}

function displayImage(file) {
    const reader = new FileReader();
    const imageContainer = document.getElementById('imageContainer');
    
    reader.onload = function(e) {
        imageContainer.innerHTML = `
            <div class="medical-image">
                <img src="${e.target.result}" alt="Medical Image" style="max-width: 100%; max-height: 100%; object-fit: contain;">
            </div>
        `;
        

    };
    
    reader.readAsDataURL(file);
}



function setupAnalysisButton() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const freshAnalyzeBtn = document.getElementById('freshAnalyzeBtn');
    
    analyzeBtn.addEventListener('click', () => {
        if (window.currentFile) {
            analyzeImage(window.currentFile);
        } else {
            showNotification('Please upload an image first.', 'error');
        }
    });
    
    freshAnalyzeBtn.addEventListener('click', () => {
        if (window.currentFile) {
            freshAnalyzeImage(window.currentFile);
        } else {
            showNotification('Please upload an image first.', 'error');
        }
    });
}

function analyzeImage(file) {
    // Show loading modal
    showLoadingModal();
    
    // Create form data
    const formData = new FormData();
    formData.append('xray_image', file);
    formData.append('symptoms', '');
    
    // Start timer
    const startTime = Date.now();
    
    // Send to server
    fetch('/api/analyze', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Hide loading modal
        hideLoadingModal();
        
        // Update analysis time and date
        const analysisTime = ((Date.now() - startTime) / 1000).toFixed(1);
        document.getElementById('analysisTime').textContent = `${analysisTime}s`;
        document.getElementById('analysisDate').textContent = new Date().toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
        
        // Display results
        displayAnalysisResults(data);
        
        showNotification('Analysis completed successfully!', 'success');
    })
    .catch(error => {
        hideLoadingModal();
        console.error('Error:', error);
        console.error('Error details:', error.message);
        showNotification(`Analysis failed: ${error.message}`, 'error');
    });
}

function freshAnalyzeImage(file) {
    // Show loading modal
    showLoadingModal();
    
    // Create form data for fresh analysis
    const formData = new FormData();
    formData.append('xray_image', file);
    
    // Get patient information if available
    const symptoms = document.getElementById('symptomsInput')?.value || '';
    const age = document.getElementById('ageInput')?.value || '';
    const gender = document.getElementById('genderInput')?.value || '';
    const history = document.getElementById('historyInput')?.value || '';
    
    formData.append('symptoms', symptoms);
    formData.append('patient_age', age);
    formData.append('patient_gender', gender);
    formData.append('medical_history', history);
    
    // Start timer
    const startTime = Date.now();
    
    // Send to analysis endpoint
    fetch('/analyze', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log('Fresh analysis response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // For fresh analysis, we expect a redirect to results page
        if (response.redirected) {
            window.location.href = response.url;
        } else {
            return response.json();
        }
    })
    .then(data => {
        // Hide loading modal
        hideLoadingModal();
        
        if (data) {
            // Update analysis time and date
            const analysisTime = ((Date.now() - startTime) / 1000).toFixed(1);
            document.getElementById('analysisTime').textContent = `${analysisTime}s`;
            document.getElementById('analysisDate').textContent = new Date().toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
            
            // Display results
            displayAnalysisResults(data);
            
            showNotification('Fresh analysis completed successfully!', 'success');
        }
    })
    .catch(error => {
        hideLoadingModal();
        console.error('Fresh analysis error:', error);
        showNotification(`Fresh analysis failed: ${error.message}`, 'error');
    });
}

function displayAnalysisResults(data) {
    const analysisResults = document.getElementById('analysisResults');
    
    console.log('Display results data:', data);
    
    if (data.success) {
        // Parse markdown and display
        const formattedResults = parseMarkdown(data.diagnosis);
        analysisResults.innerHTML = `
            <div class="analysis-results">
                ${formattedResults}
            </div>
        `;
        console.log('✅ Results displayed successfully');
    } else {
        analysisResults.innerHTML = `
            <div class="analysis-error">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Analysis failed: ${data.error || 'Unknown error'}</p>
            </div>
        `;
        console.error('❌ Analysis failed:', data.error);
    }
}

function parseMarkdown(text) {
    // Simple markdown parser for medical reports
    return text
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/✅/g, '<span class="confidence-high">✅</span>')
        .replace(/⚠️/g, '<span class="confidence-medium">⚠️</span>')
        .replace(/❌/g, '<span class="confidence-low">❌</span>')
        .replace(/🔴/g, '<span class="confidence-low">🔴</span>')
        .replace(/🟠/g, '<span class="confidence-medium">🟠</span>')
        .replace(/🟡/g, '<span class="confidence-medium">🟡</span>')
        .replace(/🟢/g, '<span class="confidence-high">🟢</span>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/^\s*-\s*(.*$)/gim, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
}



function setupViewerControls() {
    // Reset view button
    document.getElementById('resetView').addEventListener('click', () => {
        resetApplication();
    });
    
    // Add New Scan button
    document.querySelector('.btn-secondary').addEventListener('click', () => {
        addNewScan();
    });
    
    // Profile button
    document.querySelectorAll('.btn-secondary')[1].addEventListener('click', () => {
        showProfile();
    });
    
    // Search functionality
    const searchInput = document.querySelector('.search-bar input');
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch(searchInput.value);
        }
    });
}

function showLoadingModal() {
    const modal = document.getElementById('loadingModal');
    modal.style.display = 'flex';
}

function hideLoadingModal() {
    const modal = document.getElementById('loadingModal');
    modal.style.display = 'none';
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    // Set icon based on type
    let icon = 'info-circle';
    switch(type) {
        case 'success':
            icon = 'check-circle';
            break;
        case 'error':
            icon = 'exclamation-circle';
            break;
        case 'warning':
            icon = 'exclamation-triangle';
            break;
        case 'info':
        default:
            icon = 'info-circle';
            break;
    }
    
    notification.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// Application Control Functions
function resetApplication() {
    // Reset image container
    const imageContainer = document.getElementById('imageContainer');
    imageContainer.innerHTML = `
        <div class="upload-area" id="uploadArea">
            <div class="upload-content">
                <i class="fas fa-cloud-upload-alt"></i>
                <h3>Upload Medical Image</h3>
                <p>Drag and drop your X-ray image here or click to browse</p>
                <button class="btn-primary" id="browseBtn">
                    <i class="fas fa-folder-open"></i>
                    Browse Files
                </button>
            </div>
            <input type="file" id="fileInput" accept="image/*" style="display: none;">
        </div>
    `;
    
    // Reset analysis results
    const analysisResults = document.getElementById('analysisResults');
    analysisResults.innerHTML = `
        <div class="placeholder-message">
            <i class="fas fa-robot"></i>
            <p>Upload an image to begin AI analysis</p>
        </div>
    `;
    
    // Reset info
    document.getElementById('analysisDate').textContent = '--';
    document.getElementById('analysisTime').textContent = '--';
    
    // Hide analyze buttons
    document.getElementById('analyzeBtn').style.display = 'none';
    document.getElementById('freshAnalyzeBtn').style.display = 'none';
    
    // Clear current file
    window.currentFile = null;
    
    // Re-setup file upload
    setupFileUpload();
    
    showNotification('Application reset successfully', 'success');
}

function addNewScan() {
    // Clear current state
    resetApplication();
    
    // Focus on file input
    document.getElementById('fileInput').click();
    
    showNotification('Ready for new scan', 'info');
}

function showProfile() {
    showNotification('Profile feature coming soon!', 'info');
}

function performSearch(query) {
    if (query.trim() === '') {
        showNotification('Please enter a search term', 'warning');
        return;
    }
    
    showNotification(`Searching for: ${query}`, 'info');
    // In a real application, this would search through patient records
}

function setupInvestigationType() {
    const investigationSelect = document.querySelector('.medical-select');
    if (investigationSelect) {
        investigationSelect.addEventListener('change', (e) => {
            const selectedType = e.target.value;
            showNotification(`Analysis mode changed to: ${selectedType}`, 'info');
            
            // Update analysis mode
            window.analysisMode = selectedType;
        });
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + O to open file
    if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
        e.preventDefault();
        document.getElementById('fileInput').click();
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        hideLoadingModal();
    }
    
    // Enter to analyze when image is loaded
    if (e.key === 'Enter' && window.currentFile) {
        analyzeImage(window.currentFile);
    }
    
    // Ctrl/Cmd + R to reset
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault();
        resetApplication();
    }
    
    // Ctrl/Cmd + N for new scan
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        addNewScan();
    }
});