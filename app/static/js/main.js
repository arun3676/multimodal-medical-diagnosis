/**
 * Enhanced JavaScript for MediScan AI Medical Diagnosis System
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.forEach(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // File upload preview
    const fileInput = document.getElementById('xray_image');
    if (fileInput) {
        fileInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file) {
                // Display file name
                const fileLabel = document.querySelector('label[for="xray_image"]');
                fileLabel.innerHTML = `<i class="fas fa-file-medical-alt me-2"></i>Selected: ${file.name}`;
                
                // Preview the image if it's an image file
                if (file.type.match('image.*')) {
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        // Create preview container if it doesn't exist
                        let previewContainer = document.getElementById('image-preview-container');
                        if (!previewContainer) {
                            previewContainer = document.createElement('div');
                            previewContainer.id = 'image-preview-container';
                            previewContainer.className = 'mt-3 text-center';
                            fileInput.parentNode.parentNode.appendChild(previewContainer);
                        }
                        
                        // Add the image preview
                        previewContainer.innerHTML = `
                            <div class="card">
                                <div class="card-header bg-light">
                                    <h6 class="mb-0">Image Preview</h6>
                                </div>
                                <div class="card-body p-2">
                                    <img src="${e.target.result}" class="img-fluid" style="max-height: 200px;" alt="Preview">
                                </div>
                            </div>
                        `;
                    }
                    
                    reader.readAsDataURL(file);
                }
            }
        });
    }
    
    // Form validation with enhanced feedback
    const analysisForm = document.querySelector('form[action*="analyze"]');
    if (analysisForm) {
        analysisForm.addEventListener('submit', function(event) {
            const fileInput = this.querySelector('input[type="file"]');
            
            if (!fileInput.files || fileInput.files.length === 0) {
                event.preventDefault();
                
                // Create alert if not exists
                let alertContainer = document.getElementById('file-alert');
                if (!alertContainer) {
                    alertContainer = document.createElement('div');
                    alertContainer.id = 'file-alert';
                    alertContainer.className = 'alert alert-danger mt-2';
                    fileInput.parentNode.parentNode.appendChild(alertContainer);
                }
                
                alertContainer.innerHTML = '<i class="fas fa-exclamation-circle me-2"></i>Please select an X-ray image to analyze.';
                return false;
            }
            
            const fileSize = fileInput.files[0].size;
            const maxSize = 16 * 1024 * 1024; // 16MB
            
            if (fileSize > maxSize) {
                event.preventDefault();
                
                // Create alert if not exists
                let alertContainer = document.getElementById('file-alert');
                if (!alertContainer) {
                    alertContainer = document.createElement('div');
                    alertContainer.id = 'file-alert';
                    alertContainer.className = 'alert alert-danger mt-2';
                    fileInput.parentNode.parentNode.appendChild(alertContainer);
                }
                
                alertContainer.innerHTML = '<i class="fas fa-exclamation-circle me-2"></i>File size exceeds the 16MB limit. Please select a smaller file.';
                return false;
            }
            
            // Add loading indicator
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                Analyzing... Please wait
            `;
            submitBtn.disabled = true;
            
            // Add progress bar
            const progressBar = document.createElement('div');
            progressBar.className = 'progress medical-progress mt-3';
            progressBar.innerHTML = `
                <div class="progress-bar progress-bar-striped progress-bar-animated bg-primary" 
                     role="progressbar" style="width: 0%" aria-valuenow="0" 
                     aria-valuemin="0" aria-valuemax="100"></div>
            `;
            submitBtn.parentNode.appendChild(progressBar);
            
            // Simulate progress (in a real app, this would be based on actual progress)
            let progress = 0;
            const interval = setInterval(function() {
                progress += Math.random() * 15;
                if (progress > 100) progress = 100;
                
                const progressElement = progressBar.querySelector('.progress-bar');
                progressElement.style.width = `${progress}%`;
                progressElement.setAttribute('aria-valuenow', progress);
                
                if (progress >= 100) {
                    clearInterval(interval);
                }
            }, 500);
        });
    }
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-warning)');
    alerts.forEach(alert => {
        setTimeout(() => {
            // Check if the alert still exists in the DOM
            if (document.body.contains(alert)) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });
    
    // Download PDF functionality in results page
    const downloadPDFBtn = document.getElementById('downloadPDF');
    if (downloadPDFBtn) {
        downloadPDFBtn.addEventListener('click', function() {
            // Show loading state
            const originalText = this.innerHTML;
            this.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                Generating PDF...
            `;
            this.disabled = true;
            
            // Simulate PDF generation (would be AJAX call to server in production)
            setTimeout(() => {
                // Reset button state
                this.innerHTML = originalText;
                this.disabled = false;
                
                // Show success message
                const alert = document.createElement('div');
                alert.className = 'alert alert-success alert-dismissible fade show mt-3';
                alert.innerHTML = `
                    <i class="fas fa-check-circle me-2"></i>
                    PDF report generated successfully! The download should start automatically.
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                `;
                
                // Add alert to the page
                this.closest('.card-body').appendChild(alert);
                
                // Auto-dismiss after 5 seconds
                setTimeout(() => {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }, 5000);
                
                // Simulate file download
                const link = document.createElement('a');
                link.href = '#';
                link.download = 'MediScan_Report.pdf';
                link.click();
            }, 2000);
        });
    }
    
    // Medical terms highlighting and explanations
    const diagnosisOutput = document.querySelector('.diagnosis-output');
    if (diagnosisOutput) {
        // List of common medical terms and their explanations
        const medicalTerms = {
            'pneumonia': 'Inflammation of the lungs, typically caused by infection.',
            'pneumothorax': 'Air in the pleural space causing lung collapse.',
            'atelectasis': 'Collapse or closure of the lung resulting in reduced or absent gas exchange.',
            'cardiomegaly': 'Enlargement of the heart.',
            'effusion': 'Fluid collection in a body cavity, particularly the pleural space.',
            'consolidation': 'The lungs filling with fluid instead of air.',
            'infiltrate': 'Substance that abnormally accumulates in tissue or cells.',
            'opacity': 'Area that appears more white or dense on X-ray.',
            'hilar': 'Relating to the hilum, the region where vessels and nerves enter an organ.',
            'pleural': 'Relating to the pleura, the membrane that envelops the lungs.',
            'diaphragm': 'The dome-shaped muscle that separates the thorax from the abdomen.',
            'costophrenic': 'Relating to the costophrenic angle, the point where the diaphragm meets the ribs.',
            'mediastinum': 'The central compartment of the thoracic cavity.',
            'bilateral': 'Affecting both sides of the body or an organ.',
            'edema': 'Swelling caused by excess fluid trapped in body tissues.'
        };
        
        // Check for these terms in the text and add explanations
        const content = diagnosisOutput.innerHTML;
        let newContent = content;
        
        for (const [term, explanation] of Object.entries(medicalTerms)) {
            // Use regex to find the term with word boundaries (to avoid partial matches)
            const regex = new RegExp(`\\b${term}\\b`, 'gi');
            if (regex.test(content)) {
                // Replace the term with a span having tooltip
                newContent = newContent.replace(regex, `<span class="medical-term" data-bs-toggle="tooltip" data-bs-placement="top" title="${explanation}">$&</span>`);
            }
        }
        
        // Update the content
        if (newContent !== content) {
            diagnosisOutput.innerHTML = newContent;
            
            // Reinitialize tooltips
            const newTooltips = [].slice.call(diagnosisOutput.querySelectorAll('[data-bs-toggle="tooltip"]'));
            newTooltips.forEach(function(tooltipEl) {
                return new bootstrap.Tooltip(tooltipEl);
            });
        }
    }
});