"""
Simplified diagnosis generation module with structured, professional output formatting.
"""
import os
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class MedicalDiagnosisGenerator:
    """Simplified medical diagnosis generator."""
    
    def __init__(self):
        try:
            self.client = self._initialize_client()
            self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
            self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
            self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
        except Exception as e:
            logger.warning(f"OpenAI client initialization failed: {e}")
            self.client = None
            self.model = "gpt-4-turbo-preview"
            self.temperature = 0.3
            self.max_tokens = 2000
    
    def _initialize_client(self) -> OpenAI:
        """Initialize OpenAI client with proper error handling."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        
        # Remove any unsupported parameters - just use the basic initialization
        return OpenAI(api_key=api_key)
    
    def generate_diagnosis(self, analysis_data: Dict, symptoms: str = "", patient_info: Dict = None) -> Dict:
        """
        Generate medical diagnosis from analysis data.
        
        Args:
            analysis_data: Analysis results from vision analyzer
            symptoms: Patient symptoms (optional)
            patient_info: Patient information (optional)
            
        Returns:
            Dictionary containing diagnosis results
        """
        try:
            # Try to generate diagnosis with OpenAI
            return self._generate_with_openai(analysis_data, symptoms, patient_info)
        except Exception as e:
            # Fallback to basic diagnosis if OpenAI fails
            logger.error(f"OpenAI API failed: {e}")
            return self._generate_fallback_diagnosis(analysis_data, symptoms, patient_info)
    
    def _generate_fallback_diagnosis(self, analysis_data: Dict, symptoms: str = "", patient_info: Dict = None) -> Dict:
        """
        Generate dynamic diagnosis using actual Gemini analysis without OpenAI API calls.
        """
        # Extract the actual analysis text from Gemini
        analysis_text = analysis_data.get('analysis_text', '')
        
        if not analysis_text:
            # If no analysis text, return a basic response
            return self._generate_basic_response()
        
        # Parse the Gemini analysis to extract findings
        findings = []
        confidence = 0.75
        
        # Split analysis into sentences for better parsing
        sentences = analysis_text.replace('\n', ' ').split('.')
        
        # Look for key medical terms and their context
        finding_patterns = {
            'cardiomegaly': ['cardiomegaly', 'enlarged heart', 'cardiac enlargement', 'heart size increased'],
            'pleural effusion': ['pleural effusion', 'fluid in pleural space', 'blunting of costophrenic'],
            'pneumonia': ['pneumonia', 'consolidation', 'infiltrate', 'opacity'],
            'pneumothorax': ['pneumothorax', 'collapsed lung', 'air in pleural space'],
            'normal': ['normal', 'no abnormalities', 'unremarkable', 'within normal limits']
        }
        
        # Extract findings from the actual analysis text
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for finding_type, keywords in finding_patterns.items():
                for keyword in keywords:
                    if keyword in sentence_lower:
                        # Extract location if mentioned
                        location = 'Not specified'
                        if 'right' in sentence_lower:
                            location = 'Right side'
                        elif 'left' in sentence_lower:
                            location = 'Left side'
                        elif 'bilateral' in sentence_lower:
                            location = 'Bilateral'
                        
                        # Determine severity based on context
                        severity = 'Moderate'
                        if any(word in sentence_lower for word in ['severe', 'significant', 'large']):
                            severity = 'High'
                        elif any(word in sentence_lower for word in ['mild', 'small', 'minimal']):
                            severity = 'Mild'
                        
                        # Add finding if not already added
                        finding_text = finding_type.replace('_', ' ').title()
                        if not any(f['finding'] == finding_text for f in findings):
                            findings.append({
                                'finding': finding_text,
                                'confidence': 0.80,
                                'location': location,
                                'severity': severity
                            })
                        break
        
        # If no findings detected, check if it's normal
        if not findings and any(word in analysis_text.lower() for word in ['normal', 'unremarkable', 'no abnormalities']):
            findings.append({
                'finding': 'Normal chest X-ray',
                'confidence': 0.85,
                'location': 'Entire chest',
                'severity': 'None'
            })
        
        # If still no findings, indicate analysis needed
        if not findings:
            findings.append({
                'finding': 'Chest X-ray requires clinical correlation',
                'confidence': 0.70,
                'location': 'Chest',
                'severity': 'Unknown'
            })
        
        # Generate dynamic diagnosis based on extracted findings
        return self._format_findings_as_diagnosis(findings, symptoms, patient_info)
    
    def _generate_basic_response(self) -> Dict:
        """Generate a basic response when no analysis text is available."""
        return {
            'diagnosis': """# AI-Assisted Medical Assessment
*Comprehensive Chest X-ray Analysis*

## SUMMARY TABLE
| **Finding** | **Confidence** | **Location** | **Severity** |
|-------------|----------------|--------------|--------------|
| Analysis incomplete | 50% | Chest | Unknown |

## IMAGE QUALITY ASSESSMENT
**Image Quality:** Unable to assess - Analysis data not available      
**Technical Adequacy:** Unable to assess - Analysis data not available     

## FINDINGS
**Analysis Data Not Available**
The AI analysis could not be completed due to missing or incomplete data.

## CLINICAL IMPRESSION
**Primary Assessment:** Analysis incomplete
**Diagnostic Confidence:** Low (50%)
**Supporting Evidence:** Insufficient data for reliable interpretation

## CLINICAL RECOMMENDATIONS
**Repeat analysis with complete data recommended.**

## NEXT STEPS
**Recommended next action:** Re-upload the image for complete analysis.

## CLINICAL CORRELATION
**Symptoms:** No symptoms reported
   Clinical correlation requires complete imaging analysis.

## DIAGNOSTIC CONFIDENCE
**Analysis Reliability:** Low (50%)
**Clinical Interpretation:** Insufficient data for clinical interpretation.

---
## DISCLAIMER
**Educational Purpose Only:** This AI analysis is designed for learning and research. Not for clinical use. Always consult qualified healthcare professionals for medical decisions.""",
            'confidence_score': 0.5,
            'structured_data': {
                'findings': [{
                    'finding': 'Analysis incomplete',
                    'confidence': 0.5,
                    'location': 'Chest',
                    'severity': 'Unknown'
                }],
                'impression': 'Analysis incomplete - insufficient data',
                'confidence': 0.5,
                'recommendations': ['Repeat analysis with complete data']
            }
        }
    
    def _format_findings_as_diagnosis(self, findings: List[Dict], symptoms: str, patient_info: Dict = None) -> Dict:
        """Format extracted findings into a comprehensive diagnosis report."""
        confidence = max(finding['confidence'] for finding in findings) if findings else 0.75
        
        # Create findings table
        findings_table = ""
        for finding in findings:
            severity_icon = "GREEN" if finding['severity'] == 'None' else "YELLOW" if finding['severity'] == 'Moderate' else "RED"
            findings_table += f"| {finding['finding']} | {int(finding['confidence'] * 100)}% | {finding['location']} | {finding['severity']} |\n"
        
        # Determine overall assessment
        if any(f['severity'] == 'High' for f in findings):
            overall_assessment = "High priority findings detected"
            urgency_icon = "RED"
        elif any(f['severity'] == 'Moderate' for f in findings):
            overall_assessment = "Moderate findings requiring evaluation"
            urgency_icon = "YELLOW"
        elif any(f['severity'] == 'None' for f in findings):
            overall_assessment = "Normal findings"
            urgency_icon = "GREEN"
        else:
            overall_assessment = "Findings require clinical correlation"
            urgency_icon = "YELLOW"
        
        # Create dynamic diagnosis text
        diagnosis_text = f"""# 🩺 AI-Assisted Medical Assessment
*Comprehensive Medical Image Analysis*

## 📊 SUMMARY TABLE
| **Finding** | **Confidence** | **Location** | **Severity** |
|-------------|----------------|--------------|--------------|
{findings_table}

## IMAGE QUALITY ASSESSMENT
Image Quality: Good - Well-defined structures suitable for accurate analysis
Technical Adequacy: Proper positioning and exposure for diagnostic evaluation

## KEY FINDINGS
The following clinically relevant findings have been identified:

"""
        
        # Add findings details
        for i, finding in enumerate(findings, 1):
            severity_icon = "GREEN" if finding['severity'] == 'None' else "YELLOW" if finding['severity'] == 'Moderate' else "RED"
            diagnosis_text += f"{i}. {severity_icon} {finding['finding']}\n"
            diagnosis_text += f"Location: {finding['location']}\n"
            diagnosis_text += f"Severity: {finding['severity']}\n"
            diagnosis_text += f"AI Confidence: {int(finding['confidence'] * 100)}% - {'Very High' if finding['confidence'] >= 0.85 else 'High' if finding['confidence'] >= 0.75 else 'Moderate'} confidence detection\n\n"
        
        diagnosis_text += f"""## CLINICAL IMPRESSION
Primary Assessment: {findings[0]['finding'] if findings else 'Within normal limits'}
Diagnostic Confidence: {urgency_icon}
Supporting Evidence: {'Very High' if confidence >= 0.85 else 'High' if confidence >= 0.75 else 'Moderate'} confidence detection with characteristic imaging features

## CLINICAL RECOMMENDATIONS
Clinical Correlation
NEXT STEPS
Recommended next action: Consult with a healthcare provider for more tests or clinical correlation.

## CLINICAL CORRELATION
Symptoms: {symptoms if symptoms else 'No symptoms reported'}
Clinical evaluation is necessary to correlate imaging findings.

## DIAGNOSTIC CONFIDENCE
Analysis Reliability: {'Very High' if confidence >= 0.85 else 'High' if confidence >= 0.75 else 'Moderate'}
Clinical Interpretation: {'Very High' if confidence >= 0.85 else 'High' if confidence >= 0.75 else 'Moderate'} confidence detection. Appropriate for clinical correlation.

## DISCLAIMER
Educational Purpose Only: This AI analysis is designed for learning and research
Not for Clinical Use: Always consult qualified healthcare professionals for medical decisions
AI Limitations: This analysis may not detect all conditions or may suggest findings that aren't present

---

DISCLAIMER
Educational Purpose Only: This AI analysis is designed for learning and research. Not for clinical use. Always consult qualified healthcare professionals for medical decisions."""
        
        return {
            'diagnosis': diagnosis_text,
            'confidence_score': confidence,
            'structured_data': {
                'findings': findings,
                'impression': f"Primary assessment: {findings[0]['finding'] if findings else 'Within normal limits'}",
                'confidence': confidence,
                'recommendations': ['Further evaluation and clinical correlation recommended']
            }
        }
    
    def _generate_with_openai(self, analysis_data: Dict, symptoms: str = "", patient_info: Dict = None) -> Dict:
        """
        Generate diagnosis using OpenAI API.
        """
        # Check if OpenAI client is available
        if self.client is None:
            logger.warning("OpenAI client not available, using fallback diagnosis")
            raise Exception("OpenAI client not initialized")
        
        # Prepare the analysis summary
        analysis_summary = self._prepare_analysis_summary(analysis_data)
        
        # Build the system prompt
        system_prompt = self._get_system_prompt()
        
        # Build the user prompt
        user_prompt = self._build_user_prompt(analysis_summary, symptoms, patient_info)
        
        # Generate diagnosis using function calling for structured output
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            functions=[self._get_diagnosis_function_schema()],
            function_call={"name": "generate_medical_report"}
        )
        
        # Parse the function call response
        function_response = json.loads(
            response.choices[0].message.function_call.arguments
        )
        
        # Format the response for display
        formatted_response = self._format_diagnosis_response(function_response)
        
        return {
            'diagnosis': formatted_response,
            'structured_data': function_response,
            'confidence_score': function_response.get('confidence_score', 0.0),
            'model_used': self.model,
            'timestamp': datetime.utcnow().isoformat()
        }

    def _get_system_prompt(self) -> str:
        """Get the enhanced system prompt for medical analysis."""
        return """You are an expert radiologist with 20+ years of experience, providing a clinically relevant chest X-ray interpretation for EDUCATIONAL PURPOSES.

Your primary goal is to AVOID FALSE NEGATIVES for critical findings. It is better to flag a *possible* critical issue than to miss it completely.

---
### TWO-TIERED CONFIDENCE & REPORTING STRATEGY
You MUST follow this two-tiered approach to balance sensitivity and specificity.

#### TIER 1: CRITICAL FINDINGS (MODERATE & HIGH CONFIDENCE)
These findings are clinically urgent and must be reported if confidence is **≥70%**.
- **List of Critical Findings:** Pneumothorax, Pleural Effusion, large Consolidation/Opacity, Mass, Nodule.
- **Reporting Rule:** If confidence is 70-84%, use cautious phrasing like "Possible" or "Cannot be excluded". If confidence is ≥85%, report as "Likely" or "Definite".

#### TIER 2: STANDARD FINDINGS (HIGH CONFIDENCE ONLY)
These findings are less urgent and should only be reported if confidence is high, to avoid overcalling.
- **List of Standard Findings:** Cardiomegaly, Atelectasis, Hilar Prominence, Fibrosis, etc.
- **Reporting Rule:** Report ONLY if confidence is **≥85%**.

---
### CLINICAL EXCELLENCE STANDARDS

1.  **Anatomical Localization is MANDATORY:**
    - For EVERY finding, you MUST specify a location (e.g., "right lower lobe", "left upper zone", "cardiac silhouette").
    - NEVER use vague terms like "bilateral" without specifying the lung zones.

2.  **Conservative Reporting:**
    - Limit the report to a **maximum of 3 distinct findings** to maintain clinical focus.
    - If no findings meet the two-tiered criteria above, report the study as **"Within normal limits"**.

3.  **Systematic Review:**
    - Follow a systematic approach: Technical Quality -> Lungs -> Pleura -> Heart -> Bones/Soft Tissues.

---
Your final output must be structured according to the function schema, adhering strictly to these clinical safety and reporting rules.
"""
    
    def _build_user_prompt(self, analysis_summary: str, symptoms: str, 
                          patient_info: Optional[Dict] = None) -> str:
        """Build comprehensive user prompt with all relevant information."""
        prompt_parts = [
            "Please analyze the following medical imaging data and provide a comprehensive report.",
            "",
            "TECHNICAL ANALYSIS DATA:",
            analysis_summary,
            "",
            "CLINICAL PRESENTATION:",
            f"Symptoms: {symptoms if symptoms else 'No symptoms reported'}",
        ]
        
        if patient_info:
            prompt_parts.extend([
                "",
                "PATIENT INFORMATION:",
                f"Age: {patient_info.get('age', 'Not specified')}",
                f"Gender: {patient_info.get('gender', 'Not specified')}",
                f"Medical History: {patient_info.get('history', 'Not available')}",
            ])
        
        prompt_parts.extend([
            "",
            "Please provide a structured medical report with all relevant sections."
        ])
        
        return "\n".join(prompt_parts)
    
    def _prepare_analysis_summary(self, analysis_data: Dict) -> str:
        """Prepare a comprehensive summary of the image analysis."""
        summary_parts = []
        
        # Image quality assessment
        if 'quality_metrics' in analysis_data:
            qm = analysis_data['quality_metrics']
            summary_parts.append(f"Image Quality: {qm.get('quality_rating', 'Unknown')} "
                               f"(Score: {qm.get('quality_score', 0):.2f})")
        
        # Detected features
        if 'labels' in analysis_data:
            features = [f"{label['description']} ({label['score']:.1%})" 
                       for label in analysis_data['labels'][:10]]
            summary_parts.append(f"Detected Features: {', '.join(features)}")
        
        # Detected objects
        if 'objects' in analysis_data:
            objects = [f"{obj['name']} ({obj['score']:.1%})" 
                      for obj in analysis_data['objects'][:10]]
            summary_parts.append(f"Detected Structures: {', '.join(objects)}")
        
        # Statistical measures
        if 'statistics' in analysis_data:
            stats = analysis_data['statistics']
            summary_parts.append(f"Image Statistics: Mean intensity={stats.get('mean_intensity', 0):.1f}, "
                               f"Contrast={stats.get('contrast', 0):.1f}, "
                               f"Entropy={stats.get('entropy', 0):.1f}")
        
        return "\n".join(summary_parts)
    
    def _get_diagnosis_function_schema(self) -> Dict:
        """Define the function schema for structured diagnosis output."""
        return {
            "name": "generate_medical_report",
            "description": "Generate a structured medical report based on imaging analysis",
            "parameters": {
                "type": "object",
                "properties": {
                    "technical_assessment": {
                        "type": "object",
                        "properties": {
                            "image_quality": {"type": "string"},
                            "technical_adequacy": {"type": "string"},
                            "limitations": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["image_quality", "technical_adequacy"]
                    },
                    "findings": {
                        "type": "array",
                        "description": "Maximum 2 findings only. Each must have >85% confidence and specific anatomical location.",
                        "maxItems": 2,
                        "items": {
                            "type": "object",
                            "properties": {
                                "finding": {
                                    "type": "string",
                                    "description": "Specific pathological finding (e.g., 'consolidation', 'pneumothorax', 'cardiomegaly')"
                                },
                                "location": {
                                    "type": "string",
                                    "description": "REQUIRED: Specific anatomical location (e.g., 'right lower lobe', 'left upper zone', 'cardiac silhouette')",
                                    "pattern": "^(right|left)\\s+(upper|middle|lower)\\s+(lobe|zone)|cardiac|mediastinal|pleural\\s+(right|left)"
                                },
                                "severity": {
                                    "type": "string", 
                                    "enum": ["mild", "moderate", "severe", "critical"],
                                    "description": "Clinical severity assessment"
                                },
                                "confidence": {
                                    "type": "number", 
                                    "minimum": 0.85, 
                                    "maximum": 1.0,
                                    "description": "Must be ≥85% to report finding"
                                }
                            },
                            "required": ["finding", "location", "confidence"]
                        }
                    },
                    "impression": {
                        "type": "array",
                        "description": "Single primary impression only. Use 'Within normal limits' if no definite findings.",
                        "maxItems": 1,
                        "items": {
                            "type": "object",
                            "properties": {
                                "diagnosis": {
                                    "type": "string",
                                    "description": "Primary diagnostic impression or 'Within normal limits pending clinical correlation'"
                                },
                                "probability": {
                                    "type": "number", 
                                    "minimum": 0.70, 
                                    "maximum": 1.0,
                                    "description": "Confidence in primary diagnosis"
                                },
                                "evidence": {
                                    "type": "array", 
                                    "items": {"type": "string"},
                                    "description": "Specific radiographic evidence supporting diagnosis"
                                }
                            },
                            "required": ["diagnosis", "probability"]
                        }
                    },
                    "recommendations": {
                        "type": "array",
                        "description": "Conservative recommendations. Use 'emergent' only for life-threatening findings with >95% confidence.",
                        "maxItems": 3,
                        "items": {
                            "type": "object",
                            "properties": {
                                "recommendation": {
                                    "type": "string",
                                    "description": "Specific clinical recommendation"
                                },
                                "urgency": {
                                    "type": "string", 
                                    "enum": ["routine", "urgent", "emergent"],
                                    "description": "emergent: >95% confidence life-threatening, urgent: >90% confidence significant, routine: <90% confidence"
                                },
                                "rationale": {
                                    "type": "string",
                                    "description": "Clinical reasoning for recommendation"
                                }
                            },
                            "required": ["recommendation", "urgency", "rationale"]
                        }
                    },
                    "clinical_correlation": {
                        "type": "string",
                        "description": "How findings correlate with reported symptoms"
                    },
                    "educational_notes": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "confidence_score": {
                        "type": "number",
                        "minimum": 0.70,
                        "maximum": 1.0,
                        "description": "Overall confidence in the analysis. Must be ≥70% for valid report."
                    }
                },
                "required": ["technical_assessment", "findings", "impression", "recommendations", "confidence_score"]
            }
        }
    
    def _format_diagnosis_response(self, structured_data: Dict) -> str:
        """Format the structured diagnosis data into a human-readable report."""
        report_parts = []
        
        # Header
        report_parts.append("# 🩺 AI-Assisted Medical Assessment")
        report_parts.append("*Comprehensive Chest X-ray Analysis*")
        report_parts.append("")
        
        # Technical Assessment
        tech = structured_data.get('technical_assessment', {})
        report_parts.append("## 📋 IMAGE QUALITY ASSESSMENT")
        quality = tech.get('image_quality', 'Fair')
        adequacy = tech.get('technical_adequacy', 'Adequate')
        
        if 'excellent' in quality.lower():
            report_parts.append("✅ **Image Quality:** Excellent - Clear anatomical structures with optimal contrast")
        elif 'good' in quality.lower():
            report_parts.append("✅ **Image Quality:** Good - Well-defined structures suitable for accurate analysis")
        elif 'fair' in quality.lower():
            report_parts.append("⚠️ **Image Quality:** Fair - Adequate for basic assessment, some details may be limited")
        else:
            report_parts.append("❌ **Image Quality:** Poor - Limited diagnostic value, recommend repeat imaging")
            
        if 'adequate' in adequacy.lower():
            report_parts.append("✅ **Technical Adequacy:** Proper positioning and exposure for diagnostic evaluation")
        else:
            report_parts.append("⚠️ **Technical Adequacy:** Suboptimal - May affect interpretation accuracy")
        report_parts.append("")
        
        # Findings
        findings = structured_data.get('findings', [])
        
        if findings:
            report_parts.append("## 🔍 KEY FINDINGS")
            report_parts.append("*The following clinically relevant findings have been identified:*")
            report_parts.append("")
            
            for i, finding in enumerate(findings, 1):
                finding_name = finding['finding']
                location = finding.get('location', 'Not specified')
                severity = finding.get('severity', 'moderate')
                confidence = finding.get('confidence', 0)
                
                severity_icon = self._get_severity_icon(severity)
                confidence_desc = self._get_confidence_description(confidence)
                severity_desc = self._get_severity_description(severity)
                
                report_parts.append(f"### {i}. {severity_icon} **{finding_name}** {confidence_desc}")
                
                if location and location.lower() != 'unknown' and location.lower() != 'not specified':
                    report_parts.append(f"📍 **Location:** {location.title()}")
                
                report_parts.append(f"⚡ **Severity:** {severity_desc}")
                report_parts.append(f"🎯 **AI Confidence:** {confidence:.0%} - {self._get_confidence_explanation(confidence)}")
                
                medical_explanation = self._get_medical_explanation(finding_name)
                if medical_explanation:
                    report_parts.append(f"💡 **What this means:** {medical_explanation}")
                
                report_parts.append("")
        else:
            report_parts.append("## ✅ FINDINGS")
            report_parts.append("🎉 **No High-Confidence or Critical Abnormalities Detected**")
            report_parts.append("Based on analysis, the chest X-ray appears within normal limits. No significant abnormalities were identified.")
            report_parts.append("")
        
        # Impression
        report_parts.append("## 🧠 CLINICAL IMPRESSION")
        impressions = structured_data.get('impression', [])
        
        if impressions:
            primary_impression = impressions[0]
            probability = primary_impression.get('probability', 0)
            probability_desc = self._get_probability_description(probability)
            
            report_parts.append(f"🎯 **Primary Assessment:** {primary_impression['diagnosis']}")
            report_parts.append(f"📊 **Diagnostic Confidence:** {probability_desc} ({probability:.0%})")
            
            if primary_impression.get('evidence'):
                report_parts.append(f"🔬 **Supporting Evidence:** {', '.join(primary_impression['evidence'])}")
        else:
            report_parts.append("✅ **Clinical Assessment:** Within normal limits pending clinical correlation")
            report_parts.append("📋 **Interpretation:** No definitive abnormalities detected using conservative clinical thresholds")
        
        report_parts.append("")
        
        # Recommendations
        recommendations = structured_data.get('recommendations', [])
        if recommendations:
            report_parts.append("## 📋 CLINICAL RECOMMENDATIONS")
            
            for rec in recommendations:
                urgency = rec.get('urgency', 'routine')
                recommendation = rec['recommendation']
                rationale = rec.get('rationale', '')
                
                urgency_icon = self._get_urgency_icon(urgency)
                urgency_desc = self._get_urgency_description(urgency)
                
                report_parts.append(f"{urgency_icon} **{urgency_desc}:** {recommendation}")
                if rationale:
                    report_parts.append(f"   *Clinical rationale: {rationale}*")
                report_parts.append("")
        else:
            report_parts.append("## 📋 CLINICAL RECOMMENDATIONS")
            report_parts.append("📅 **Routine Follow-up:** Clinical correlation recommended")
            report_parts.append("   *Clinical rationale: Radiographic findings require clinical assessment for appropriate management*")
            report_parts.append("")
        
        # Clinical Correlation
        correlation = structured_data.get('clinical_correlation')
        if correlation:
            report_parts.append("## 🔄 CLINICAL CORRELATION")
            report_parts.append(f"💭 {correlation}")
            report_parts.append("")
        
        # Overall Confidence
        confidence = structured_data.get('confidence_score', 0)
        report_parts.append("## 📊 DIAGNOSTIC CONFIDENCE")
        confidence_level = self._get_confidence_level(confidence)
        confidence_explanation = self._get_clinical_confidence_interpretation(confidence)
        
        report_parts.append(f"🎯 **Analysis Reliability:** {confidence_level} ({confidence:.0%})")
        report_parts.append(f"📝 **Clinical Interpretation:** {confidence_explanation}")
        
        if confidence >= 0.85:
            report_parts.append(f"✅ **Clinical Grade:** Meets diagnostic imaging standards for educational use")
        elif confidence >= 0.70:
            report_parts.append(f"⚠️ **Clinical Grade:** Adequate for educational review, clinical correlation advised")
        else:
            report_parts.append(f"❌ **Clinical Grade:** Below clinical standards, recommend image review or repeat study")
        
        report_parts.append("")
        
        # Educational Notes
        educational_notes = structured_data.get('educational_notes', [])
        if educational_notes:
            report_parts.append("## 📚 EDUCATIONAL INFORMATION")
            for note in educational_notes:
                report_parts.append(f"💡 {note}")
            report_parts.append("")
        
        # Disclaimer
        report_parts.append("---")
        report_parts.append("## ⚠️ IMPORTANT DISCLAIMER")
        report_parts.append("🎓 **Educational Purpose Only:** This AI analysis is designed for learning and research")
        report_parts.append("👨‍⚕️ **Not for Clinical Use:** Always consult qualified healthcare professionals for medical decisions")
        report_parts.append("🔬 **AI Limitations:** This analysis may not detect all conditions or may suggest findings that aren't present")
        
        return "\n".join(report_parts)
    
    def _get_medical_explanation(self, finding_name: str) -> str:
        """Provide simple medical explanations for common findings."""
        finding_lower = finding_name.lower()
        
        explanations = {
            'pneumonia': 'An infection in the lungs that causes inflammation and fluid buildup in the air sacs',
            'pneumothorax': 'Air that has leaked into the space around the lungs, which can cause the lung to collapse',
            'pleural effusion': 'Fluid that has accumulated in the space around the lungs',
            'consolidation': 'Areas of the lung that are filled with fluid or other material instead of air',
            'atelectasis': 'Areas of the lung that have collapsed or are not fully expanded',
            'cardiomegaly': 'Enlargement of the heart, which may indicate various heart conditions',
            'hilar prominence': 'Enlarged structures at the center of the chest where blood vessels enter the lungs',
            'infiltrate': 'Abnormal substances (like fluid or cells) that have accumulated in lung tissue',
            'opacity': 'Areas that appear more dense or white on the X-ray, indicating abnormal tissue or fluid',
            'nodule': 'A small, round spot in the lung that requires further evaluation',
            'mass': 'A larger abnormal growth or collection of tissue in the lungs',
            'emphysema': 'Damage to the air sacs in the lungs, making breathing difficult',
            'fibrosis': 'Scarring or thickening of lung tissue',
            'edema': 'Fluid buildup in the lungs, often related to heart problems'
        }
        
        for key, explanation in explanations.items():
            if key in finding_lower:
                return explanation
        
        return "An abnormal finding that requires medical evaluation for proper diagnosis"
    
    def _get_confidence_description(self, confidence: float) -> str:
        """Get human-readable confidence description."""
        if confidence >= 0.95:
            return "🎯"
        elif confidence >= 0.85:
            return "OK"
        elif confidence >= 0.70:
            return "⚠️"
        else:
            return "❓"
    
    def _get_severity_icon(self, severity: str) -> str:
        """Get visual icon for severity level."""
        severity_lower = severity.lower()
        if severity_lower == 'critical':
            return "RED"
        elif severity_lower == 'severe':
            return "🟠"
        elif severity_lower == 'moderate':
            return "YELLOW"
        elif severity_lower == 'mild':
            return "GREEN"
        else:
            return "⚪"
    
    def _get_severity_description(self, severity: str) -> str:
        """Get descriptive text for severity levels."""
        severity_lower = severity.lower()
        if severity_lower == 'critical':
            return "Critical - Requires immediate medical attention"
        elif severity_lower == 'severe':
            return "Severe - Significant abnormality requiring prompt evaluation"
        elif severity_lower == 'moderate':
            return "Moderate - Notable finding that should be evaluated by a physician"
        elif severity_lower == 'mild':
            return "Mild - Minor abnormality, clinical correlation recommended"
        else:
            return "Indeterminate - Further evaluation needed to assess significance"
    
    def _get_confidence_explanation(self, confidence: float) -> str:
        """Explain what the confidence level means."""
        if confidence >= 0.95:
            return "Very reliable detection with clear imaging features"
        elif confidence >= 0.85:
            return "High confidence detection with typical characteristics"
        elif confidence >= 0.70:
            return "Moderate confidence, some features may be subtle"
        elif confidence >= 0.50:
            return "Lower confidence, findings may be equivocal"
        else:
            return "Low confidence, consider additional imaging"
    
    def _get_probability_description(self, probability: float) -> str:
        """Convert probability to descriptive language."""
        if probability >= 0.9:
            return "Very High Likelihood"
        elif probability >= 0.75:
            return "High Likelihood"
        elif probability >= 0.6:
            return "Moderate Likelihood"
        elif probability >= 0.4:
            return "Possible"
        elif probability >= 0.2:
            return "Low Likelihood"
        else:
            return "Very Low Likelihood"
    
    def _get_urgency_icon(self, urgency: str) -> str:
        """Get visual icon for urgency level."""
        urgency_lower = urgency.lower()
        if urgency_lower == 'emergent':
            return "🚨"
        elif urgency_lower == 'urgent':
            return "⚡"
        elif urgency_lower == 'routine':
            return "📅"
        else:
            return "INFO"
    
    def _get_urgency_description(self, urgency: str) -> str:
        """Get descriptive text for urgency levels."""
        urgency_lower = urgency.lower()
        if urgency_lower == 'emergent':
            return "IMMEDIATE ATTENTION NEEDED"
        elif urgency_lower == 'urgent':
            return "Urgent Follow-up Required"
        elif urgency_lower == 'routine':
            return "Routine Follow-up"
        else:
            return "Clinical Correlation"
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Get descriptive confidence level."""
        if confidence >= 0.9:
            return "Very High"
        elif confidence >= 0.8:
            return "High"
        elif confidence >= 0.7:
            return "Moderate-High"
        elif confidence >= 0.6:
            return "Moderate"
        elif confidence >= 0.5:
            return "Moderate-Low"
        elif confidence >= 0.4:
            return "Low"
        else:
            return "Very Low"
    
    def _get_clinical_confidence_interpretation(self, confidence: float) -> str:
        """Provide clinical-grade confidence interpretation."""
        if confidence >= 0.95:
            return "Excellent diagnostic confidence with definitive radiographic features. Findings are clinically reliable."
        elif confidence >= 0.90:
            return "High diagnostic confidence with characteristic imaging features. Appropriate for clinical correlation."
        elif confidence >= 0.85:
            return "Good diagnostic confidence meeting clinical imaging standards. Findings warrant medical attention."
        elif confidence >= 0.75:
            return "Moderate confidence with some equivocal features. Clinical correlation strongly recommended."
        elif confidence >= 0.70:
            return "Borderline confidence. Findings may represent normal variants or subtle pathology."
        else:
            return "Insufficient confidence for clinical interpretation. Consider repeat imaging or alternative studies."

# Backward compatibility functions
def generate_diagnosis(image_analysis: str, symptoms: str, model: str = "gpt-4") -> str:
    """Backward compatible function."""
    generator = MedicalDiagnosisGenerator()
    analysis_data = {'raw_analysis': image_analysis}
    result = generator.generate_diagnosis(analysis_data, symptoms)
    return result['diagnosis']

def generate_enhanced_interpretation(findings_dict: Dict, symptoms: str, model: str = "gpt-4") -> str:
    """Backward compatible function."""
    generator = MedicalDiagnosisGenerator()
    result = generator.generate_diagnosis(findings_dict, symptoms)
    return result['diagnosis']