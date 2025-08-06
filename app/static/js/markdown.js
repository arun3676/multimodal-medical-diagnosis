/**
 * Simple Markdown parser for MediScan AI reports
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get the diagnosis content element
    const diagnosisContent = document.getElementById('diagnosis-content');
    
    if (diagnosisContent) {
        // Get the raw content
        let content = diagnosisContent.innerHTML;
        
        // Process headers (in order of specificity)
        content = content.replace(/^# (.*?)$/gm, '<h1>$1</h1>');
        content = content.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
        content = content.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
        content = content.replace(/^#### (.*?)$/gm, '<h4>$1</h4>');
        
        // Process horizontal rules
        content = content.replace(/^---$/gm, '<hr>');
        
        // Process bold text first (before italics to avoid conflicts)
        content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Process italics (single asterisks that aren't part of bold)
        content = content.replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, '<em>$1</em>');
        
        // Process lists - improved handling
        content = content.replace(/^[\s]*[-*] (.*?)$/gm, '<li>$1</li>');
        content = content.replace(/^[\s]*(\d+)\. (.*?)$/gm, '<li><strong>$1.</strong> $2</li>');
        
        // Wrap consecutive list items in ul tags
        content = content.replace(/(<li>.*?<\/li>(?:\s*<li>.*?<\/li>)*)/gs, '<ul>$1</ul>');
        
        // Process paragraphs - split by double newlines and wrap non-header content
        const lines = content.split('\n');
        let processedLines = [];
        let inParagraph = false;
        
        for (let line of lines) {
            line = line.trim();
            
            // Check if line is a header, list, or other special element
            const isSpecialElement = line.match(/^<(h[1-6]|hr|ul|li|\/ul)/);
            
            if (line === '') {
                // Empty line - close paragraph if open
                if (inParagraph) {
                    processedLines[processedLines.length - 1] += '</p>';
                    inParagraph = false;
                }
                continue;
            } else if (isSpecialElement) {
                // Special element - close paragraph if open
                if (inParagraph) {
                    processedLines[processedLines.length - 1] += '</p>';
                    inParagraph = false;
                }
                processedLines.push(line);
            } else {
                // Regular text - start paragraph if not already in one
                if (!inParagraph) {
                    processedLines.push('<p>' + line);
                    inParagraph = true;
                } else {
                    processedLines[processedLines.length - 1] += ' ' + line;
                }
            }
        }
        
        // Close final paragraph if still open
        if (inParagraph) {
            processedLines[processedLines.length - 1] += '</p>';
        }
        
        content = processedLines.join('\n');
        
        // Clean up any duplicate or empty paragraphs
        content = content.replace(/<p>\s*<\/p>/g, '');
        content = content.replace(/<p>(<[^>]+>)\s*<\/p>/g, '$1');
        
        // Add section containers for better styling
        content = content.replace(/<h2>(.*?)<\/h2>/g, '<div class="report-section"><h2>$1</h2><div class="section-content">');
        content = content.replace(/<h1>(.*?)<\/h1>/g, '</div></div><h1>$1</h1><div class="report-section"><div class="section-content">');
        
        // Fix the structure
        content = content.replace(/^<\/div><\/div>/, '');
        content += '</div></div>';
        
        // Add main container
        content = '<div class="medical-report-container">' + content + '</div>';
        
        // Update the content
        diagnosisContent.innerHTML = content;
        
        // Highlight medical terms
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
                'mediastinal': 'Relating to the mediastinum, the central compartment of the thoracic cavity.',
                'bilateral': 'Affecting both sides of the body or an organ.',
                'edema': 'Swelling caused by excess fluid trapped in body tissues.',
                'pulmonary': 'Relating to the lungs.',
                'biopsy': 'Procedure to remove a piece of tissue for examination.',
                'oncologist': 'Doctor who specializes in cancer treatment.',
                'pulmonologist': 'Doctor who specializes in lung conditions.',
                'radiographic': 'Related to the technique of using radiation to view internal structures.'
            };
            
            // Get all text nodes in the container
            const walker = document.createTreeWalker(
                diagnosisOutput,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );
            
            const nodesToReplace = [];
            let node;
            
            // Collect all nodes that need replacement
            while (node = walker.nextNode()) {
                const parent = node.parentNode;
                
                // Skip if parent is already a medical term span
                if (parent.classList && parent.classList.contains('medical-term')) {
                    continue;
                }
                
                for (const [term, explanation] of Object.entries(medicalTerms)) {
                    // Use regex to find the term with word boundaries
                    const regex = new RegExp(`\\b${term}\\b`, 'gi');
                    if (regex.test(node.textContent)) {
                        nodesToReplace.push({ node, term, explanation });
                    }
                }
            }
            
            // Replace nodes with highlighted versions
            nodesToReplace.forEach(({ node, term, explanation }) => {
                const regex = new RegExp(`\\b(${term})\\b`, 'gi');
                const parts = node.textContent.split(regex);
                
                if (parts.length === 1) return; // No matches found
                
                const fragment = document.createDocumentFragment();
                
                parts.forEach((part, i) => {
                    if (i % 2 === 0) {
                        // Regular text
                        fragment.appendChild(document.createTextNode(part));
                    } else {
                        // Matched term
                        const span = document.createElement('span');
                        span.className = 'medical-term';
                        span.setAttribute('data-bs-toggle', 'tooltip');
                        span.setAttribute('data-bs-placement', 'top');
                        span.setAttribute('title', explanation);
                        span.textContent = part;
                        fragment.appendChild(span);
                    }
                });
                
                node.parentNode.replaceChild(fragment, node);
            });
            
            // Initialize tooltips
            const tooltips = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltips.forEach(function(tooltipEl) {
                return new bootstrap.Tooltip(tooltipEl);
            });
        }
    }
});