// Medical Imaging Platform - Neutral Minimalist Design
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initializeApp();
    
    // Set current date and time
    updateDateTime();
    
    // Setup tabs functionality
    setupTabs();

    // Handle "Run Detailed Analysis" button
    const runDetailedAnalysisBtn = document.getElementById('runDetailedAnalysisBtn');
    if (runDetailedAnalysisBtn) {
        runDetailedAnalysisBtn.addEventListener('click', () => {
            const filename = runDetailedAnalysisBtn.dataset.filename;
            if (!filename) {
                showNotification('Cannot re-analyze: filename not found.', 'error');
                return;
            }

            // Show loading state
            runDetailedAnalysisBtn.disabled = true;
            runDetailedAnalysisBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running Detailed Analysis...';
            showNotification('Running detailed analysis...', 'info');

            // Make API call to re-analyze
            fetch('/api/re_analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ filename: filename })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Update UI with new results
                    displayAnalysisResults(data);
                    updateVLMProvider(data.vision_provider || 'unknown');
                    showNotification('Detailed analysis complete!', 'success');
                    
                    // Hide the button after use
                    runDetailedAnalysisBtn.style.display = 'none';
                } else {
                    showNotification(`Detailed analysis failed: ${data.error}`, 'error');
                    runDetailedAnalysisBtn.disabled = false;
                    runDetailedAnalysisBtn.innerHTML = '<i class="fas fa-microscope"></i> Run Detailed Analysis';
                }
            })
            .catch(error => {
                console.error('Error re-analyzing:', error);
                showNotification(`An error occurred: ${error.message}`, 'error');
                runDetailedAnalysisBtn.disabled = false;
                runDetailedAnalysisBtn.innerHTML = '<i class="fas fa-microscope"></i> Run Detailed Analysis';
            });
        });
    }
});

function setupTabs() {
    const tabTriggers = document.querySelectorAll('.tabs-trigger');
    const tabContents = document.querySelectorAll('.tabs-content');
    
    tabTriggers.forEach(trigger => {
        trigger.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            // Remove active class from all triggers and contents
            tabTriggers.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked trigger and corresponding content
            this.classList.add('active');
            const targetContent = document.getElementById(targetTab + '-tab');
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });
}

function initializeApp() {
    // File upload handling
    setupFileUpload();

    // UI controls
    setupUIControls();

    // Analysis form handling
    setupAnalysisForm();

    // Manual analysis trigger setup
    setupManualAnalysis();

    // NEW: Voice recording setup
    setupVoiceRecording();

    // NEW: Analysis mode toggle setup
    setupAnalysisModeToggle();
}

function updateDateTime() {
    const now = new Date();
    const dateOptions = { weekday: 'short', month: 'short', day: 'numeric' };
    const timeOptions = { hour: 'numeric', minute: '2-digit', hour12: true };
    
    // Update patient info
    const patientDateEl = document.getElementById('patientDate');
    const patientTimeEl = document.getElementById('patientTime');
    
    if (patientDateEl) {
        patientDateEl.textContent = now.toLocaleDateString('en-US', dateOptions);
    }
    if (patientTimeEl) {
        patientTimeEl.textContent = now.toLocaleTimeString('en-US', timeOptions);
    }
}

function setupFileUpload() {
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseBtn');
    const uploadArea = document.getElementById('uploadArea');
    
    if (!browseBtn || !fileInput || !uploadArea) return;
    
    // Browse button click
    browseBtn.addEventListener('click', () => {
        fileInput.click();
    });
    
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
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
    
    // Store file for analysis
    window.currentFile = file;
    
    // Reveal manual analysis button
    const manualAnalyzeBtn = document.getElementById('manualAnalyzeBtn');
    if (manualAnalyzeBtn) {
        manualAnalyzeBtn.style.display = 'inline-flex';
        manualAnalyzeBtn.disabled = false;
        if (manualAnalyzeBtn.dataset.defaultHtml) {
            manualAnalyzeBtn.innerHTML = manualAnalyzeBtn.dataset.defaultHtml;
        }
    }

    // Display image
    displayImage(file);

    // Display image and wait for voice command
    setTimeout(() => {
        showImagePreviewState();
        showNotification('Image loaded. Use the voice button or manual analysis to begin.', 'info');
    }, 800);
}

function showAnalyzingState() {
    const uploadSection = document.getElementById('uploadSection');
    const analyzingSection = document.getElementById('analyzingSection');
    const imageDisplaySection = document.getElementById('imageDisplaySection');
    
    if (uploadSection) uploadSection.style.display = 'none';
    if (analyzingSection) analyzingSection.style.display = 'flex';
    if (imageDisplaySection) imageDisplaySection.style.display = 'none';

    showAnalysisLoadingState();
}

function showImagePreviewState() {
    const uploadSection = document.getElementById('uploadSection');
    const analyzingSection = document.getElementById('analyzingSection');
    const imageDisplaySection = document.getElementById('imageDisplaySection');
    
    if (uploadSection) uploadSection.style.display = 'none';
    if (analyzingSection) analyzingSection.style.display = 'none';
    if (imageDisplaySection) imageDisplaySection.style.display = 'block';
    
    // Hide analysis complete badge
    const badge = document.getElementById('analysisCompleteBadge2');
    if (badge) badge.style.display = 'none';
}

function showImageDisplayState() {
    const uploadSection = document.getElementById('uploadSection');
    const analyzingSection = document.getElementById('analyzingSection');
    const imageDisplaySection = document.getElementById('imageDisplaySection');
    
    if (uploadSection) uploadSection.style.display = 'none';
    if (analyzingSection) analyzingSection.style.display = 'none';
    if (imageDisplaySection) imageDisplaySection.style.display = 'block';
    
    // Show analysis complete badge
    const badge = document.getElementById('analysisCompleteBadge2');
    if (badge) badge.style.display = 'flex';
}

function displayImage(file) {
    const reader = new FileReader();
    const uploadedImageEl = document.getElementById('uploadedImage');
    
    reader.onload = function(e) {
        if (uploadedImageEl) {
            uploadedImageEl.src = e.target.result;
            console.log('✅ Image displayed successfully');
            
            // Show image preview (without "Analysis Complete" badge)
            setTimeout(() => {
                showImagePreviewState();
            }, 800);
        }
    };
    
    reader.onerror = function() {
        console.error('❌ Failed to read image file');
        showNotification('Failed to display image', 'error');
    };
    
    reader.readAsDataURL(file);
}

function showAnalysisLoadingState() {
    const emptyState = document.querySelector('.empty-state');
    const loadingState = document.querySelector('.loading-state');
    const resultsState = document.querySelector('.results-state');
    
    if (emptyState) emptyState.style.display = 'none';
    if (loadingState) loadingState.style.display = 'flex';
    if (resultsState) resultsState.style.display = 'none';
}

function showAnalysisResultsState() {
    const emptyState = document.querySelector('.empty-state');
    const loadingState = document.querySelector('.loading-state');
    const resultsState = document.querySelector('.results-state');
    
    if (emptyState) emptyState.style.display = 'none';
    if (loadingState) loadingState.style.display = 'none';
    if (resultsState) resultsState.style.display = 'block';
}

function setupUIControls() {
    // Reset Analysis button
    const resetAnalysisBtn = document.getElementById('resetAnalysisBtn');
    if (resetAnalysisBtn) {
        resetAnalysisBtn.addEventListener('click', () => {
            resetApplication();
        });
    }
}

function setupAnalysisForm() {
    const analysisForm = document.getElementById('analysisForm');
    const analysisFileInput = document.getElementById('analysisFileInput');
    
    if (analysisForm && analysisFileInput) {
        // Form will be submitted programmatically
    }
}

// NEW: Manual analysis setup
function setupManualAnalysis() {
    const manualAnalyzeBtn = document.getElementById('manualAnalyzeBtn');
    if (!manualAnalyzeBtn) return;

    manualAnalyzeBtn.dataset.defaultHtml = manualAnalyzeBtn.innerHTML;

    manualAnalyzeBtn.addEventListener('click', () => {
        if (!window.currentFile) {
            showNotification('Please upload an image before starting analysis.', 'warning');
            return;
        }

        showNotification('Starting analysis without voice input...', 'info');
        analyzeImage(window.currentFile);
    });
}

// NEW: Voice Recording Setup
function setupVoiceRecording() {
    const voiceRecordBtn = document.getElementById('voiceRecordBtn');
    const audioInput = document.getElementById('audioInput');
    
    if (!voiceRecordBtn || !audioInput) return;
    
    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];
    
    // Click handler for voice button
    voiceRecordBtn.addEventListener('click', () => {
        if (!isRecording) {
            startVoiceRecording();
        } else {
            stopVoiceRecording();
        }
    });
    
    async function startVoiceRecording() {
        try {
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Update UI
            isRecording = true;
            voiceRecordBtn.classList.add('recording');
            voiceRecordBtn.innerHTML = '<i class="fas fa-stop size-4 text-white drop-shadow-sm"></i>';
            voiceRecordBtn.style.background = 'linear-gradient(135deg, rgba(239, 68, 68, 0.8) 0%, rgba(220, 38, 38, 0.7) 100%)';
            
            // Start recording
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };
            
            mediaRecorder.onstop = () => {
                processAudioRecording();
            };
            
            mediaRecorder.start();
            showNotification('Recording started... Speak clearly', 'info');
            
        } catch (error) {
            console.error('Error accessing microphone:', error);
            showNotification('Microphone access denied', 'error');
            resetVoiceButton();
        }
    }
    
    function stopVoiceRecording() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
        
        resetVoiceButton();
        showNotification('Processing voice recording...', 'info');
    }
    
    function resetVoiceButton() {
        isRecording = false;
        voiceRecordBtn.classList.remove('recording');
        voiceRecordBtn.innerHTML = '<i class="fas fa-microphone size-4 text-white drop-shadow-sm"></i>';
        voiceRecordBtn.style.background = 'linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.1) 100%)';
    }
    
    function processAudioRecording() {
        // Create audio blob
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        const audioFile = new File([audioBlob], 'recording.wav', { type: 'audio/wav' });
        
        // Transcribe with Whisper
        transcribeAudio(audioFile);
    }
}

// NEW: Analysis Mode Toggle Setup
function setupAnalysisModeToggle() {
    const fastModeRadio = document.getElementById('fastMode');
    const detailedModeRadio = document.getElementById('detailedMode');
    const fastModeDescription = document.getElementById('fastModeDescription');
    const detailedModeDescription = document.getElementById('detailedModeDescription');
    
    if (!fastModeRadio || !detailedModeRadio || !fastModeDescription || !detailedModeDescription) {
        console.warn('Analysis mode toggle elements not found');
        return;
    }
    
    // Set default analysis type
    window.analysisType = 'fast';
    
    // Handle mode changes
    fastModeRadio.addEventListener('change', () => {
        if (fastModeRadio.checked) {
            window.analysisType = 'fast';
            fastModeDescription.style.display = 'block';
            detailedModeDescription.style.display = 'none';
            showNotification('Analysis mode: Fast (Quick pneumonia detection)', 'info');
        }
    });
    
    detailedModeRadio.addEventListener('change', () => {
        if (detailedModeRadio.checked) {
            window.analysisType = 'detailed';
            fastModeDescription.style.display = 'none';
            detailedModeDescription.style.display = 'block';
            showNotification('Analysis mode: Detailed (Comprehensive VLM analysis)', 'info');
        }
    });
}

function analyzeImage(file) {
    // NEW: Show analyzing state at the start of the actual analysis
    showAnalyzingState();

    // Disable manual button while processing
    const manualAnalyzeBtn = document.getElementById('manualAnalyzeBtn');
    if (manualAnalyzeBtn) {
        manualAnalyzeBtn.disabled = true;
        manualAnalyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span style="margin-left: 0.5rem;">Analyzing...</span>';
    }
    // Update analysis time and date
    const startTime = Date.now();
    
    // Get voice symptoms if available
    const voiceSymptoms = window.voiceSymptoms || '';
    
    // Create form data
    const formData = new FormData();
    formData.append('xray_image', file);
    formData.append('symptoms', voiceSymptoms); // Use voice symptoms
    formData.append('patient_age', '');
    formData.append('patient_gender', '');
    formData.append('medical_history', '');
    
    // NEW: Add analysis type from toggle
    const analysisType = window.analysisType || 'fast';
    formData.append('analysis_type', analysisType);
    
    // Send to server
    fetch('/api/analyze', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Show analyzed image state
        showImageDisplayState();
        
        // Update analysis time
        const analysisTime = ((Date.now() - startTime) / 1000).toFixed(1);
        const analysisTimeEl = document.getElementById('analysisTime');
        if (analysisTimeEl) {
            analysisTimeEl.textContent = `${analysisTime}s`;
        }
        
        // Show analysis complete badge
        const completeBadge = document.querySelector('.analysis-complete-badge');
        if (completeBadge) {
            completeBadge.style.display = 'flex';
        }
        
        // Update VLM provider display
        updateVLMProvider(data.vision_provider || 'unknown');
        
        // Display results
        displayAnalysisResults(data);
        
        showNotification('Analysis completed successfully!', 'success');

        // Re-enable manual analysis button so user can run another mode (e.g., detailed)
        if (manualAnalyzeBtn) {
            manualAnalyzeBtn.disabled = false;
            if (manualAnalyzeBtn.dataset.defaultHtml) {
                manualAnalyzeBtn.innerHTML = manualAnalyzeBtn.dataset.defaultHtml;
            } else {
                manualAnalyzeBtn.innerHTML = '<i class="fas fa-heartbeat"></i><span style="margin-left: 0.5rem;">Analyze Image</span>';
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification(`Analysis failed: ${error.message}`, 'error');
        
        // Reset to upload state on error
        resetToUploadState();

        // Restore manual button to allow retry
        if (manualAnalyzeBtn) {
            manualAnalyzeBtn.disabled = false;
            if (manualAnalyzeBtn.dataset.defaultHtml) {
                manualAnalyzeBtn.innerHTML = manualAnalyzeBtn.dataset.defaultHtml;
            } else {
                manualAnalyzeBtn.innerHTML = '<i class="fas fa-heartbeat"></i><span style="margin-left: 0.5rem;">Analyze Image</span>';
            }
        }
    });
}

function transcribeAudio(audioFile) {
    const formData = new FormData();
    formData.append('audio_file', audioFile);
    
    fetch('/api/transcribe', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Store transcribed symptoms globally
            window.voiceSymptoms = data.symptoms;
            
            // Update UI with transcription
            updateVoiceTranscriptionUI(data);
            
            showNotification('Voice transcription completed!', 'success');
            console.log('✅ Voice symptoms extracted:', data.symptoms);

            // NEW: Trigger analysis if an image is present
            if (window.currentFile) {
                showNotification('Starting analysis with image and voice symptoms...', 'info');
                analyzeImage(window.currentFile);
            } else {
                showNotification('Please upload an image before starting analysis.', 'warning');
            }
        } else {
            showNotification(`Transcription failed: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error transcribing audio:', error);
        showNotification(`Transcription failed: ${error.message}`, 'error');
    });
}

// NEW: Update Voice Transcription UI
function updateVoiceTranscriptionUI(data) {
    const voiceTranscription = document.getElementById('voiceTranscription');
    const transcribedText = document.getElementById('transcribedText');
    const audioDuration = document.getElementById('audioDuration');
    
    if (voiceTranscription && transcribedText && audioDuration) {
        // Show transcription section
        voiceTranscription.classList.remove('hidden');
        
        // Update text
        transcribedText.textContent = data.symptoms || 'No symptoms detected';
        audioDuration.textContent = `${data.duration.toFixed(1)}s`;
        
        // Add animation
        voiceTranscription.style.animation = 'slideIn 0.5s ease-out';
    }
}

// NEW: Update VLM Provider Display
function updateVLMProvider(provider) {
    const vlmProviderEl = document.getElementById('vlmProvider');
    const providerBadgeEl = document.getElementById('providerBadge');
    
    if (!vlmProviderEl || !providerBadgeEl) return;
    
    const providerConfig = {
        'fine_tuned_model': {
            name: 'Fine-tuned ViT (LoRA)',
            badge: 'AI MODEL',
            badgeStyle: 'background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(124, 58, 237, 0.1) 100%); color: #4c1d95; border: 1px solid rgba(139, 92, 246, 0.3);'
        },
        'groq': {
            name: 'Groq Qwen2.5-VL-3B',
            badge: 'ALTERNATE',
            badgeStyle: 'background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(20, 184, 166, 0.1) 100%); color: #065f46; border: 1px solid rgba(16, 185, 129, 0.3);'
        },
        'openai': {
            name: 'OpenAI GPT-4o-mini',
            badge: 'PRIMARY',
            badgeStyle: 'background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.1) 100%); color: #1e3a8a; border: 1px solid rgba(59, 130, 246, 0.3);'
        },
        'gemini': {
            name: 'Gemini Flash',
            badge: 'FINAL',
            badgeStyle: 'background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(217, 119, 6, 0.1) 100%); color: #78350f; border: 1px solid rgba(245, 158, 11, 0.3);'
        },
        'unknown': {
            name: 'Unknown Provider',
            badge: 'ERROR',
            badgeStyle: 'background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.1) 100%); color: #7f1d1d; border: 1px solid rgba(239, 68, 68, 0.3);'
        }
    };
    
    const config = providerConfig[provider.toLowerCase()] || providerConfig['unknown'];
    
    vlmProviderEl.textContent = config.name;
    providerBadgeEl.textContent = config.badge;
    providerBadgeEl.style.cssText = config.badgeStyle + ' ml-2 px-2 py-0.5 rounded-full text-xs font-medium';
    
    console.log(`🤖 VLM Provider: ${config.name} (${config.badge})`);
}

function displayAnalysisResults(data) {
    if (data.success) {
        // Show results state
        showAnalysisResultsState();
        
        // Update overall assessment
        updateOverallAssessment(data.overall_assessment || 'ANALYSIS COMPLETE');
        
        // Update confidence score
        updateConfidenceScore(data.confidence_score || 87);
        
        // Update diagnosis text (includes symptom response)
        updateDiagnosisText(data.diagnosis || '');
        
        // Update findings from API response
        const findings = data.findings || [];
        updateFindings(findings);
        
        // Update recommendations from API response
        const recommendations = data.recommendations || [];
        updateRecommendations(recommendations);
        
        console.log('✅ Results displayed successfully');
        console.log('📊 Findings:', findings.length, 'Recommendations:', recommendations.length);
    } else {
        showNotification(`Analysis failed: ${data.error || 'Unknown error'}`, 'error');
        console.error('❌ Analysis failed:', data.error);
    }
}

function updateDiagnosisText(diagnosis) {
    const diagnosisReportEl = document.getElementById('diagnosisReport');
    const diagnosisTextEl = document.getElementById('diagnosisText');
    
    if (diagnosisReportEl && diagnosisTextEl) {
        if (diagnosis && diagnosis.trim()) {
            // Format the diagnosis text - convert markdown-style bold to HTML
            const formattedDiagnosis = diagnosis
                .replace(/\*\*(.*?)\*\*/g, '<strong style="color: var(--neutral-900);">$1</strong>')
                .replace(/\n\n/g, '\n')
                .replace(/^- (.+)$/gm, '• $1');
            
            diagnosisTextEl.innerHTML = formattedDiagnosis;
            diagnosisReportEl.style.display = 'block';
            console.log('📝 Diagnosis text updated successfully');
        } else {
            diagnosisReportEl.style.display = 'none';
        }
    }
}

function updateOverallAssessment(assessment) {
    const assessmentEl = document.getElementById('overallAssessment');
    if (assessmentEl) {
        assessmentEl.textContent = assessment.toUpperCase();
        console.log('📋 Overall Assessment:', assessment);
    }
}

function updateConfidenceScore(confidence) {
    const confidenceScoreEl = document.querySelector('.confidence-score');
    const confidenceBarEl = document.querySelector('.confidence-bar');
    
    if (confidenceScoreEl) {
        confidenceScoreEl.textContent = `${confidence}%`;
    }
    
    if (confidenceBarEl) {
        setTimeout(() => {
            confidenceBarEl.style.width = `${confidence}%`;
        }, 100);
    }
}

function escapeHtml(text) {
    if (text === null || text === undefined) {
        return '';
    }

    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

const pulmonaryTermExplanations = {
    "Consolidation": "Dense lung area usually from infection or fluid filling the air spaces.",
    "Pleural Effusion": "Fluid build-up between the lung and chest wall causing blunted angles.",
    "Infiltrate": "Patchy hazy material in the lungs, often from infection or inflammation.",
    "Nodule/Mass": "Rounded spot that may represent a benign lump or tumor needing review.",
    "Atelectasis": "Portion of lung has collapsed, reducing air and volume in that region.",
    "Pneumothorax": "Air trapped outside the lung causing partial collapse and sharp chest pain.",
    "Interstitial Markings": "Thickened lines in the lungs from scarring or extra fluid.",
    "Air Bronchogram": "Air-filled bronchi visible against dense lung tissue, common in pneumonia."
};

function getTooltipMarkup(term) {
    const explanation = pulmonaryTermExplanations[term];
    if (!explanation) {
        return escapeHtml(term);
    }
    const safeTerm = escapeHtml(term);
    const safeExplanation = escapeHtml(explanation);
    return `<span class="tooltip-term" data-tooltip="${safeExplanation}">${safeTerm}</span>`;
}

function updateFindings(findings) {
    const overviewContainer = document.getElementById('overviewFindings');
    const detailedContainer = document.getElementById('detailedFindings');

    if (!overviewContainer || !detailedContainer) {
        console.error('❌ Findings containers not found');
        return;
    }

    overviewContainer.innerHTML = '';
    detailedContainer.innerHTML = '';

    // No default findings - only show what the AI actually detected
    if (!findings || findings.length === 0) {
        console.log('ℹ️ No findings provided by AI model');
        overviewContainer.innerHTML = '<p style="color: var(--neutral-500); text-align: center; padding: 2rem;">No specific findings reported by the AI model.</p>';
        detailedContainer.innerHTML = '<p style="color: var(--neutral-500); text-align: center; padding: 2rem;">No detailed findings available.</p>';
        return;
    }

    const normalizedFindings = findings.map((finding, index) => {
            const number = String(index + 1).padStart(2, '0');
            const category = (finding.category || finding.region || 'GENERAL').toString().toUpperCase();
            const rawTitle = finding.title || finding.name || finding.region || `Finding ${number}`;
            const title = getTooltipMarkup(rawTitle);
            const confidence = Number(finding.confidence || finding.score || 90);
            const severity = (finding.severity || 'normal').toLowerCase();
            const description = finding.description || finding.observation || finding.summary || 'No description available.';
            let details = finding.details || finding.points || finding.highlights || finding.notes;
            if (typeof details === 'string') {
                details = [details];
            }
            if (!Array.isArray(details) || details.length === 0) {
                details = [description];
            }

            return {
                number,
                category,
                title,
                confidence,
                severity,
                description,
                details
            };
        });

    normalizedFindings.forEach((finding, index) => {
        const overviewCard = document.createElement('div');
        overviewCard.className = 'finding-card animate-slide-in';
        overviewCard.style.animationDelay = `${index * 0.1}s`;
        overviewCard.innerHTML = `
            <div class="finding-card-content">
                <div class="finding-header">
                    <div>
                        <span class="badge badge-outline" style="font-size: 0.75rem; letter-spacing: var(--tracking-wide);">${finding.category}</span>
                    </div>
                    <div class="finding-number">${finding.number}</div>
                </div>
                <h4 class="finding-title">${finding.title}</h4>
                <div class="finding-confidence-row">
                    <span class="finding-confidence-label">Confidence</span>
                    <span class="finding-confidence-value">${finding.confidence}%</span>
                </div>
                <div class="progress" style="height: 0.5rem;">
                    <div class="progress-bar" style="width: ${Math.min(finding.confidence, 100)}%; background-color: var(--neutral-900);"></div>
                </div>
                <p class="finding-summary">${finding.description}</p>
            </div>
        `;
        overviewContainer.appendChild(overviewCard);

        const detailedCard = document.createElement('div');
        detailedCard.className = 'card detailed-finding animate-slide-in-left';
        detailedCard.style.animationDelay = `${index * 0.1}s`;
        detailedCard.innerHTML = `
            <div class="detailed-finding-content">
                <div class="detailed-finding-main">
                    <div class="detailed-finding-number">${finding.number}</div>
                    <div class="detailed-finding-body">
                        <div class="detailed-finding-header">
                            <div>
                                <span class="badge badge-outline" style="font-size: 0.75rem; letter-spacing: var(--tracking-widest); margin-bottom: 0.75rem;">${finding.category}</span>
                                <h4 class="detailed-finding-title">${finding.title}</h4>
                                <span class="badge badge-outline" style="font-size: 0.75rem; letter-spacing: var(--tracking-wide);">${finding.severity.toUpperCase()}</span>
                            </div>
                            <div class="text-right">
                                <p style="color: var(--neutral-500); font-size: 0.875rem; letter-spacing: var(--tracking-wide); margin-bottom: 0.5rem;">CONFIDENCE</p>
                                <p style="font-size: 2rem; font-weight: 500; color: var(--neutral-900);">${finding.confidence}%</p>
                            </div>
                        </div>

                        <p class="detailed-finding-description">${finding.description}</p>

                        <div class="separator separator-horizontal" style="margin: 2rem 0;"></div>

                        <div class="assessment-points">
                            <p class="assessment-points-title">KEY ASSESSMENT POINTS</p>
                            <div class="space-y-4">
                                ${finding.details.map(detail => `
                                    <div class="assessment-point">
                                        <div class="assessment-point-bullet"></div>
                                        <p class="assessment-point-text">${detail}</p>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        detailedContainer.appendChild(detailedCard);
    });

    console.log('✅ Findings updated:', normalizedFindings.length, 'items');
}

function updateRecommendations(recommendations) {
    const recommendationsContainer = document.getElementById('recommendationsList');
    if (!recommendationsContainer) {
        console.error('❌ Recommendations container not found');
        return;
    }

    recommendationsContainer.innerHTML = '';

    const defaultRecommendations = [
        {
            priority: 'HIGH',
            category: 'Clinical Correlation',
            text: 'Correlate findings with patient symptoms, medical history, and clinical presentation. Physical examination recommended.',
            timeline: 'Immediate'
        },
        {
            priority: 'MEDIUM',
            category: 'Follow-up Imaging',
            text: 'Consider repeat chest radiograph in 6 months to monitor the mild left cardiac border prominence.',
            timeline: '6 months'
        }
    ];

    const normalizedRecommendations = (recommendations && recommendations.length > 0)
        ? recommendations.map((recommendation) => {
            if (typeof recommendation === 'string') {
                return {
                    priority: 'MEDIUM',
                    category: 'Recommendation',
                    text: recommendation,
                    timeline: 'As needed'
                };
            }

            return {
                priority: (recommendation.priority || 'MEDIUM').toUpperCase(),
                category: recommendation.category || recommendation.type || 'Recommendation',
                text: recommendation.text || recommendation.recommendation || 'No recommendation details provided.',
                timeline: recommendation.timeline || recommendation.follow_up || 'As needed'
            };
        })
        : defaultRecommendations;

    normalizedRecommendations.forEach((rec, index) => {
        const item = document.createElement('div');
        item.className = 'recommendation-item animate-slide-in-left';
        if (index > 0) {
            item.style.animationDelay = `${index * 0.1}s`;
        }

        const priorityClass = rec.priority === 'HIGH'
            ? 'priority-high'
            : rec.priority === 'LOW'
                ? 'priority-low'
                : 'priority-medium';

        item.innerHTML = `
            <div class="recommendation-header">
                <span class="badge badge-outline ${priorityClass}" style="font-size: 0.75rem; letter-spacing: var(--tracking-widest);">${rec.priority} PRIORITY</span>
                <span class="badge badge-outline" style="font-size: 0.75rem; letter-spacing: var(--tracking-wide); border-color: var(--neutral-300);">${rec.category}</span>
                <span class="badge badge-outline" style="font-size: 0.75rem; margin-left: auto; border-color: var(--neutral-300);">
                    <i class="fas fa-clock" style="font-size: 0.75rem; margin-right: 0.25rem;"></i>
                    ${rec.timeline}
                </span>
            </div>
            <p class="recommendation-text" style="margin-top: 1rem;">${rec.text}</p>
        `;

        recommendationsContainer.appendChild(item);
    });
}

function resetToUploadState() {
    const uploadSection = document.getElementById('uploadSection');
    const analyzingSection = document.getElementById('analyzingSection');
    const imageDisplaySection = document.getElementById('imageDisplaySection');
    const completeBadge = document.querySelector('.analysis-complete-badge');
    
    if (uploadSection) uploadSection.style.display = 'block';
    if (analyzingSection) analyzingSection.style.display = 'none';
    if (imageDisplaySection) imageDisplaySection.style.display = 'none';
    if (completeBadge) completeBadge.style.display = 'none';
    
    // Reset analysis results to empty state
    const emptyState = document.querySelector('.empty-state');
    const loadingState = document.querySelector('.loading-state');
    const resultsState = document.querySelector('.results-state');
    
    if (emptyState) emptyState.style.display = 'flex';
    if (loadingState) loadingState.style.display = 'none';
    if (resultsState) resultsState.style.display = 'none';
}

function resetApplication() {
    // Reset file input
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.value = '';
    }
    
    // Reset image
    const uploadedImageEl = document.getElementById('uploadedImage');
    if (uploadedImageEl) {
        uploadedImageEl.src = '';
    }
    
    // Reset analysis info
    const analysisTimeEl = document.getElementById('analysisTime');
    if (analysisTimeEl) {
        analysisTimeEl.textContent = '--';
    }
    
    // Reset voice symptoms
    window.voiceSymptoms = '';
    const voiceTranscription = document.getElementById('voiceTranscription');
    if (voiceTranscription) {
        voiceTranscription.classList.add('hidden');
    }
    
    // Reset VLM provider display
    const vlmProviderEl = document.getElementById('vlmProvider');
    const providerBadgeEl = document.getElementById('providerBadge');
    if (vlmProviderEl) vlmProviderEl.textContent = 'Groq VLM';
    if (providerBadgeEl) {
        providerBadgeEl.textContent = 'PRIMARY';
        providerBadgeEl.style.cssText = 'ml-2 px-2 py-0.5 rounded-full text-xs font-medium; background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(20, 184, 166, 0.1) 100%); color: #065f46; border: 1px solid rgba(16, 185, 129, 0.3);';
    }

    const manualAnalyzeBtn = document.getElementById('manualAnalyzeBtn');
    if (manualAnalyzeBtn) {
        manualAnalyzeBtn.style.display = 'none';
        manualAnalyzeBtn.disabled = false;
        if (manualAnalyzeBtn.dataset.defaultHtml) {
            manualAnalyzeBtn.innerHTML = manualAnalyzeBtn.dataset.defaultHtml;
        }
    }

    // Reset to upload state
    resetToUploadState();
    
    // Clear current file
    window.currentFile = null;
    
    // Update date/time
    updateDateTime();
    
    showNotification('Application reset successfully', 'success');
}

function performSearch(query) {
    if (query.trim() === '') {
        showNotification('Please enter a search term', 'warning');
        return;
    }
    
    showNotification(`Searching for: ${query}`, 'info');
    // In a real application, this would search through patient records
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 0.5rem;
        padding: 1rem 1.5rem;
        color: #1e293b;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        z-index: 1001;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transform: translateX(100%);
        transition: transform 0.3s ease;
        backdrop-filter: blur(10px);
    `;
    
    // Set icon based on type
    let icon = 'info-circle';
    let iconColor = '#3b82f6';
    switch(type) {
        case 'success':
            icon = 'check-circle';
            iconColor = '#10b981';
            break;
        case 'error':
            icon = 'exclamation-circle';
            iconColor = '#ef4444';
            break;
        case 'warning':
            icon = 'exclamation-triangle';
            iconColor = '#f59e0b';
            break;
        case 'info':
        default:
            icon = 'info-circle';
            iconColor = '#3b82f6';
            break;
    }
    
    notification.innerHTML = `
        <i class="fas fa-${icon}" style="color: ${iconColor};"></i>
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

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + O to open file
    if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
        e.preventDefault();
        document.getElementById('fileInput')?.click();
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
        resetApplication();
        document.getElementById('fileInput')?.click();
    }
});