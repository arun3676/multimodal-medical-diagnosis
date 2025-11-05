"""
Groq VLM Router - Primary Vision Language Model for Medical Imaging
Routes: Groq Qwen2.5-VL-3B -> GPT-4o-mini -> Gemini Flash fallback
Single call magic: Image + symptoms -> Full diagnosis JSON
"""
import os
import base64
import logging
import re
from typing import Dict, Any, Optional
import httpx
from io import BytesIO
from PIL import Image
import time

# Import monitoring decorator
from app.core.monitoring_middleware import monitor_model_performance
from app.core.fresh_wandb_monitor import get_fresh_monitor
from app.config import settings

logger = logging.getLogger(__name__)


class VLMResponse:
    """Response wrapper that includes model information for monitoring."""
    
    def __init__(self, data: Dict[str, Any], provider: str, model: str):
        self.data = data
        self.model_info = {
            'provider': provider,
            'model': model
        }
        
        # Add monitoring attributes
        if 'critical_findings' in data:
            self.findings = data['critical_findings']
        if 'confidence_score' in data:
            self.confidence = data['confidence_score']
        if 'refusal_reason' in data:
            self.refusal_reason = data['refusal_reason']
    
    def __getitem__(self, key):
        return self.data[key]
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def __contains__(self, key):
        return key in self.data


class GroqVLMRouter:
    """Groq VLM Router with fallback chain for medical image analysis."""
    
    def __init__(self, http_client: httpx.Client):
        self.http_client = http_client
        self.groq_api_key = settings.GROQ_API_KEY
        self.openai_api_key = settings.OPENAI_API_KEY
        self.gemini_api_key = settings.GEMINI_API_KEY
        self.monitor = get_fresh_monitor()

        self.provider_order = settings.VISION_PROVIDER_ORDER
        logger.info("Vision provider order: %s", " -> ".join(self.provider_order))
        
        # Enhanced medical imaging prompt focused on pneumonia-specific findings
        self.base_prompt = """You are a JSON-generation AI. Your ONLY task is to generate valid JSON that follows the exact structure provided below. Do not add any explanations, markdown, or text outside the JSON.

PATIENT SYMPTOMS: {symptoms}

Generate a JSON object with this exact structure and these exact field names:
{{
  "is_medical_image": true,
  "image_type": "chest_xray",
  "provided_symptoms": "{symptoms}",
  "critical_findings": [
    {{
      "term": "Consolidation",
      "status": "present|absent|uncertain",
      "confidence": 0.0,
      "radiology_summary": "Describe what you see",
      "severity": "none|mild|moderate|severe"
    }},
    {{
      "term": "Air Bronchogram",
      "status": "present|absent|uncertain",
      "confidence": 0.0,
      "radiology_summary": "Describe what you see",
      "severity": "none|mild|moderate|severe"
    }},
    {{
      "term": "Pleural Effusion",
      "status": "present|absent|uncertain",
      "confidence": 0.0,
      "radiology_summary": "Describe what you see",
      "severity": "none|mild|moderate|severe"
    }},
    {{
      "term": "Infiltrate",
      "status": "present|absent|uncertain",
      "confidence": 0.0,
      "radiology_summary": "Describe what you see",
      "severity": "none|mild|moderate|severe"
    }}
  ],
  "symptom_response": "Acknowledge the symptoms and explain what they might indicate medically.",
  "symptom_correlation": "Explain how the symptoms relate to your X-ray findings.",
  "overall_impression": "Your medical conclusion based on both image and symptoms.",
  "patient_friendly_summary": "Simple explanation for the patient.",
  "priority_recommendations": [
    {{
      "action": "Recommended action",
      "urgency": "routine|urgent|emergency",
      "rationale": "Why this is needed"
    }}
  ],
  "confidence_score": 0.0,
  "urgency": "routine|urgent|emergency"
}}

Analyze the chest X-ray image and fill in the JSON fields above. The 'symptom_response' field is REQUIRED and must be filled with a meaningful response to the reported symptoms."""

    def _encode_image_to_base64(self, image_path: str) -> str:
        """Convert image file to base64 string."""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large (max 1024x1024 for VLM)
                max_size = 1024
                if img.width > max_size or img.height > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Convert to base64
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                return img_base64
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            raise

    @monitor_model_performance
    def _call_groq_vlm(self, image_base64: str, symptoms: str = "") -> Optional[Dict[str, Any]]:
        """Primary: Groq - Currently no vision models available."""
        logger.warning("Groq does not currently support vision models in their API")
        return None

    @monitor_model_performance
    def _call_openai_vlm(self, image_base64: str, symptoms: str = "") -> Optional[Dict[str, Any]]:
        """Primary: OpenAI GPT-4o-mini."""
        logger.info("🤖 Calling OpenAI GPT-4o-mini for vision analysis...")
        
        if not self.openai_api_key:
            logger.warning("OpenAI API key not configured")
            return None
            
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            prompt = self.base_prompt.format(symptoms=symptoms or "No specific symptoms provided")
            logger.info(f"📝 OpenAI prompt length: {len(prompt)} characters")
            logger.info(f"📝 Prompt preview (first 200 chars): {prompt[:200]}...")
            
            logger.info(f"🖼️ Image size: {len(image_base64)} base64 characters")
            logger.info(f"📤 Sending request to OpenAI API...")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                            }
                        ]
                    }
                ],
                max_tokens=4096,
                temperature=0.1
            )
            
            logger.info(f"📥 OpenAI response received!")
            logger.info(f"📊 Response model: {response.model}")
            logger.info(f"📊 Usage: {response.usage}")
            
            # Check if OpenAI refused to respond (new API field)
            message = response.choices[0].message
            if hasattr(message, 'refusal') and message.refusal:
                logger.warning(f"❌ OpenAI refused to analyze: {message.refusal}")
                return None
            
            content = message.content
            logger.info(f"📝 Response content length: {len(content) if content else 0} characters")
            
            # Log the raw response for debugging
            if content:
                logger.info(f"📋 Raw OpenAI response (first 500 chars): {content[:500]}")
            else:
                logger.error("❌ OpenAI returned empty content")
                return None
            
            # Check if response was truncated (finish_reason)
            finish_reason = response.choices[0].finish_reason
            logger.info(f"🏁 Finish reason: {finish_reason}")
            if finish_reason == 'length':
                logger.warning("⚠️ Response was truncated due to max_tokens limit")
            elif finish_reason == 'content_filter':
                logger.error("❌ Response blocked by content filter")
                return None
            
            # Check if OpenAI refused to analyze
            refusal_phrases = [
                "unable to provide",
                "cannot analyze", 
                "not a medical professional",
                "consult a healthcare",
                "medical advice"
            ]
            
            if any(phrase in content.lower() for phrase in refusal_phrases):
                logger.error("❌ OpenAI refused to analyze medical image")
                return None
            
            # Parse JSON response
            logger.info("🔍 Parsing JSON response...")
            try:
                import json
                # Use regex to find the JSON block, ignoring markdown fences
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if not json_match:
                    logger.error("❌ No JSON object found in OpenAI response")
                    logger.error(f"📋 Full response content: {repr(content)}")
                    return None

                json_content = json_match.group(0)
                logger.info(f"✅ JSON extracted (first 200 chars): {json_content[:200]}")
                
                diagnosis_data = json.loads(json_content)
                diagnosis_data['provider'] = 'openai'
                diagnosis_data['model'] = 'gpt-4o-mini'
                
                # Debug: Log the findings count
                findings_count = len(diagnosis_data.get('critical_findings', []))
                logger.info(f"✅ OpenAI VLM analysis successful - {findings_count} findings returned")
                if findings_count == 0:
                    logger.warning("⚠️ OpenAI returned 0 findings - this may cause 'No specific findings' message")
                else:
                    # Log each finding for debugging
                    logger.info("📋 Detailed findings from OpenAI:")
                    for i, finding in enumerate(diagnosis_data.get('critical_findings', [])[:4]):  # Log first 4 findings
                        logger.info(f"   {i+1}. {finding.get('term', 'Unknown')}: {finding.get('status', 'Unknown')} (conf: {finding.get('confidence', 0):.2f})")
                        logger.info(f"      Summary: {finding.get('radiology_summary', 'None')[:100]}...")
                
                return VLMResponse(diagnosis_data, 'openai', 'gpt-4o-mini')
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse OpenAI JSON response: {e}")
                logger.error(f"📋 Invalid JSON content: {json_content[:500]}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error calling OpenAI VLM: {e}")
            logger.error(f"📋 Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"📋 Full traceback: {traceback.format_exc()}")
            return None

    @monitor_model_performance
    def _call_gemini_vlm(self, image_base64: str, symptoms: str = "") -> Optional[Dict[str, Any]]:
        """Final fallback: Gemini 2.5 Flash."""
        if not self.gemini_api_key:
            logger.warning("Gemini API key not configured")
            return None
            
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)
            
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = self.base_prompt.format(symptoms=symptoms or "No specific symptoms provided")
            
            # Decode base64 to image
            image_data = base64.b64decode(image_base64)
            import PIL.Image
            image = PIL.Image.open(BytesIO(image_data))
            
            response = model.generate_content([prompt, image])
            content = response.text
            
            # Log the raw response for debugging
            logger.debug(f"Gemini raw response (first 500 chars): {content[:500]}")
            
            # Check if content is None or empty
            if not content:
                logger.error("Gemini returned empty content")
                return None
            
            # Parse JSON response
            try:
                import json
                # Use regex to find the JSON block, ignoring markdown fences
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if not json_match:
                    logger.error("No JSON object found in Gemini response")
                    logger.error(f"Full response content: {repr(content)}")
                    return None

                json_content = json_match.group(0)
                logger.debug(f"Extracted JSON (first 200 chars): {json_content[:200]}")
                diagnosis_data = json.loads(json_content)
                diagnosis_data['provider'] = 'gemini'
                diagnosis_data['model'] = 'gemini-1.5-flash-latest'
                
                logger.info("✅ Gemini VLM fallback successful")
                return VLMResponse(diagnosis_data, 'gemini', 'gemini-1.5-flash-latest')
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini JSON response: {e}")
                logger.error(f"Invalid JSON content: {json_content[:500]}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling Gemini VLM: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.debug(f"Full traceback: {traceback.format_exc()}")
            return None

    def analyze_medical_image(self, image_path: str, symptoms: str = "") -> Dict[str, Any]:
        """
        Analyze medical image using VLM router with fallback chain.
        
        Args:
            image_path: Path to medical image file
            symptoms: Patient symptoms to consider in analysis
            
        Returns:
            Dictionary with comprehensive diagnosis data
        """
        start_time = time.time()
        
        logger.info("\n" + "="*80)
        logger.info("🏥 MEDICAL IMAGE ANALYSIS STARTED")
        logger.info("="*80)
        logger.info(f"📁 Image Path: {image_path}")
        logger.info(f"🩺 Symptoms: '{symptoms}'")
        logger.info(f"🔧 Provider Order: {' -> '.join(self.provider_order)}")
        logger.info(f"🔑 API Keys Status: OpenAI={'✅' if self.openai_api_key else '❌'}, Gemini={'✅' if self.gemini_api_key else '❌'}")
        logger.info("-"*80)
        
        try:
            # Encode image
            logger.info("📸 Encoding image to base64...")
            image_base64 = self._encode_image_to_base64(image_path)
            logger.info(f"✅ Image encoded successfully (length: {len(image_base64)} chars)")
            
            provider_map = {
                "groq": self._call_groq_vlm,
                "openai": self._call_openai_vlm,
                "gemini": self._call_gemini_vlm,
            }

            logger.info(f"\n🔄 Starting VLM analysis with provider order: {' -> '.join(self.provider_order)}")
            
            for provider in self.provider_order:
                logger.info(f"\n🔍 Attempting vision provider: {provider.upper()}")
                logger.info("-"*40)
                
                call_fn = provider_map.get(provider)
                if call_fn is None:
                    logger.warning(f"❌ Unknown vision provider '{provider}' in VISION_PROVIDER_ORDER")
                    continue

                logger.info(f"📞 Calling {provider.upper()} API...")
                result = call_fn(image_base64, symptoms)
                
                if result:
                    logger.info(f"✅ {provider.upper()} analysis successful!")
                    # Extract data from VLMResponse if needed
                    if isinstance(result, VLMResponse):
                        result_data = result.data
                    else:
                        result_data = result
                    
                    logger.info(f"📊 Raw result keys: {list(result_data.keys())}")
                    
                    # Validate critical findings
                    critical_findings = result_data.get('critical_findings', [])
                    logger.info(f"\n🔍 CRITICAL FINDINGS VALIDATION:")
                    logger.info(f"   Number of findings: {len(critical_findings)}")
                    
                    if critical_findings:
                        required_findings = ['Consolidation', 'Air Bronchogram', 'Pleural Effusion', 'Infiltrate']
                        found_findings = [f.get('term', 'Unknown') for f in critical_findings]
                        
                        logger.info(f"   Required findings: {required_findings}")
                        logger.info(f"   AI returned: {found_findings}")
                        
                        # Check each required finding
                        for req_finding in required_findings:
                            matching = [f for f in critical_findings if f.get('term') == req_finding]
                            if matching:
                                f = matching[0]
                                logger.info(f"   ✅ {req_finding}: {f.get('status', 'Unknown')} (confidence: {f.get('confidence', 0):.2f})")
                                logger.info(f"      Summary: {f.get('radiology_summary', 'None')[:100]}...")
                            else:
                                logger.warning(f"   ❌ {req_finding}: MISSING from AI response!")
                        
                        # Check for realistic confidence values
                        logger.info(f"\n📈 CONFIDENCE ANALYSIS:")
                        for f in critical_findings:
                            confidence = f.get('confidence', 0)
                            status = f.get('status', 'Unknown')
                            term = f.get('term', 'Unknown')
                            
                            # Validate confidence ranges
                            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                                logger.warning(f"   ⚠️  {term}: Invalid confidence {confidence} (should be 0.0-1.0)")
                            elif status == 'absent' and confidence > 0.9:
                                logger.info(f"   ✅ {term}: High confidence ({confidence:.2f}) for absent - realistic")
                            elif status == 'present' and confidence > 0.5:
                                logger.info(f"   ✅ {term}: Good confidence ({confidence:.2f}) for present")
                            elif status == 'uncertain' and 0.3 <= confidence <= 0.7:
                                logger.info(f"   ✅ {term}: Appropriate uncertainty ({confidence:.2f})")
                            else:
                                logger.info(f"   🔍 {term}: {status} with {confidence:.2f} confidence")
                    
                    # Check overall impression for AI-generated content
                    overall_impression = result_data.get('overall_impression', '')
                    if overall_impression:
                        logger.info(f"\n📝 OVERALL IMPRESSION (first 200 chars):")
                        logger.info(f"   {overall_impression[:200]}...")
                        
                        # Check for template phrases
                        template_phrases = [
                            "No consolidation identified - lung fields appear clear",
                            "No air bronchograms visible - lung fields are clear", 
                            "No pleural effusion noted - costophrenic angles are sharp",
                            "No infiltrates observed - lung fields are clear"
                        ]
                        
                        template_found = any(phrase in overall_impression for phrase in template_phrases)
                        if template_found:
                            logger.warning(f"   ⚠️  TEMPLATE PHRASES DETECTED - may not be real AI analysis!")
                        else:
                            logger.info(f"   ✅ Appears to be genuine AI-generated analysis")
                    
                    logger.info(f"\n🔄 Normalizing response for frontend...")
                    # Extract data from VLMResponse if needed
                    if isinstance(result, VLMResponse):
                        result_data = result.data
                    else:
                        result_data = result
                    
                    normalized_result = self._normalize_vlm_response(result_data)
                    
                    # Calculate processing time and log to W&B
                    processing_time = time.time() - start_time
                    
                    # Get image metadata for monitoring
                    try:
                        with Image.open(image_path) as img:
                            image_metadata = {
                                'width': img.width,
                                'height': img.height,
                                'format': img.format or 'unknown'
                            }
                    except:
                        image_metadata = {'width': 0, 'height': 0, 'format': 'unknown'}
                    
                    # Log successful VLM analysis to W&B
                    self.monitor.log_prediction(
                        model_name=f"vlm_{provider}",
                        prediction=normalized_result.get('overall_impression', 'Analysis completed')[:100],
                        confidence=normalized_result.get('confidence_score', 0) / 100,
                        processing_time=processing_time,
                        image_metadata=image_metadata
                    )
                    
                    # Log model performance metrics
                    findings_count = len(normalized_result.get('findings', []))
                    self.monitor.log_model_performance(
                        model_name=f"vlm_{provider}",
                        metrics={
                            'findings_count': findings_count,
                            'urgency_score': 1 if normalized_result.get('urgency') == 'urgent' else 0,
                            'has_symptoms': 1 if symptoms else 0,
                            'response_length': len(str(normalized_result.get('diagnosis', '')))
                        }
                    )
                    
                    logger.info(f"✅ Analysis completed via {provider.upper()}")
                    logger.info("="*80)
                    return normalized_result
                else:
                    logger.warning(f"❌ {provider.upper()} failed or returned None")
                    logger.info(f"   Checking next provider...")

            # All providers failed
            processing_time = time.time() - start_time
            logger.error(f"\n❌ ALL VLM PROVIDERS FAILED!")
            
            # Log failure to W&B
            self.monitor.log_error(
                error_type="vlm_providers_failed",
                error_message="All VLM providers unavailable",
                context={
                    "processing_time": processing_time,
                    "providers_tried": self.provider_order,
                    "image_path": image_path
                }
            )
            
            logger.info("="*80)
            return {
                "error": "All VLM providers unavailable",
                "provider": "none",
                "is_medical_image": False,
                "diagnosis": "Unable to analyze image due to service unavailability",
                "confidence_score": 0.0
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"\n❌ CRITICAL ERROR in VLM router analysis: {e}")
            import traceback
            logger.error(f"📋 Full traceback:")
            logger.error(traceback.format_exc())
            
            # Log critical error to W&B
            self.monitor.log_error(
                error_type="vlm_router_error",
                error_message=str(e),
                context={
                    "processing_time": processing_time,
                    "image_path": image_path,
                    "exception_type": type(e).__name__
                }
            )
            
            logger.info("="*80)
            return {
                "error": str(e),
                "provider": "error",
                "is_medical_image": False,
                "diagnosis": f"Analysis failed: {str(e)}",
                "confidence_score": 0.0
            }

    def _normalize_vlm_response(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize provider responses into a unified pulmonary-centric schema."""

        if not isinstance(raw_result, dict):
            logger.error("Unexpected VLM response format: %s", type(raw_result))
            return {
                "provider": "unknown",
                "is_medical_image": False,
                "diagnosis": "Unable to parse model response.",
                "confidence_score": 0,
                "findings": [],
                "critical_findings": [],
                "recommendations": [],
                "priority_recommendations": [],
                "urgency": "routine",
            }

        provider = raw_result.get("provider", "unknown")
        model = raw_result.get("model", raw_result.get("model_used"))
        image_type = raw_result.get("image_type", "unknown")
        symptoms = raw_result.get("provided_symptoms", "")
        overall_impression = raw_result.get("overall_impression") or raw_result.get("diagnosis")
        symptom_response = raw_result.get("symptom_response")
        symptom_correlation = raw_result.get("symptom_correlation")
        patient_summary = raw_result.get("patient_friendly_summary") or raw_result.get("plain_language_summary")
        urgency = raw_result.get("urgency", "routine")
        extended_findings = raw_result.get("extended_findings") or []

        # Debug logging to see what fields we received
        logger.info("🔍 DEBUG: Raw AI response keys: %s", list(raw_result.keys()))
        logger.info("🔍 DEBUG: symptom_response present: %s", symptom_response is not None)
        logger.info("🔍 DEBUG: symptom_correlation present: %s", symptom_correlation is not None)
        if symptom_response:
            logger.info("🔍 DEBUG: symptom_response content: %s", symptom_response[:200])
        if symptom_correlation:
            logger.info("🔍 DEBUG: symptom_correlation content: %s", symptom_correlation[:200])

        # Normalize confidence score to percentage for UI consistency
        raw_confidence = raw_result.get("confidence_score")
        if isinstance(raw_confidence, (int, float)):
            confidence_score = max(0, min(100, round(raw_confidence * 100))) if raw_confidence <= 1 else round(raw_confidence)
        else:
            confidence_score = 0

        critical_findings_raw = raw_result.get("critical_findings") or []
        if not critical_findings_raw and isinstance(raw_result.get("findings"), list):
            critical_findings_raw = raw_result["findings"]

        # Only use findings actually provided by the model
        # Don't add missing findings with "not provided" status

        normalized_findings = []
        for finding in critical_findings_raw:
            if not isinstance(finding, dict):
                continue

            term = finding.get("term", "Pulmonary Finding")
            status = finding.get("status", "uncertain")
            severity_value = finding.get("severity", "none").lower()
            severity = "normal" if status == "absent" and severity_value in {"none", "normal"} else severity_value

            finding_confidence = finding.get("confidence")
            if isinstance(finding_confidence, (int, float)):
                finding_confidence_pct = max(0, min(100, round(finding_confidence * 100))) if finding_confidence <= 1 else round(finding_confidence)
            else:
                finding_confidence_pct = 50

            radiology_summary = finding.get("radiology_summary") or "No radiology summary provided."
            plain_summary = finding.get("plain_language_summary") or "No patient explanation provided."

            details = [item for item in [plain_summary, f"Status: {status.title()}"] if item]

            normalized_findings.append({
                "term": term,
                "status": status,
                "category": "LUNGS",
                "title": term,
                "severity": severity,
                "confidence": finding_confidence_pct,
                "radiology_summary": radiology_summary,
                "plain_language_summary": plain_summary,
                "description": radiology_summary,
                "details": details,
            })

        recommendations_raw = raw_result.get("priority_recommendations") or raw_result.get("recommendations") or []
        normalized_recommendations = []
        for recommendation in recommendations_raw:
            if isinstance(recommendation, str):
                normalized_recommendations.append({
                    "priority": "MEDIUM",
                    "category": "Clinical",
                    "text": recommendation,
                    "timeline": "As needed",
                })
                continue

            if not isinstance(recommendation, dict):
                continue

            normalized_recommendations.append({
                "priority": (recommendation.get("urgency") or recommendation.get("priority") or "routine").upper(),
                "category": recommendation.get("category") or recommendation.get("action") or "Recommendation",
                "text": recommendation.get("rationale") or recommendation.get("text") or recommendation.get("action") or "No recommendation details provided.",
                "timeline": recommendation.get("follow_up_timeline") or recommendation.get("timeline") or "As needed",
                "action": recommendation.get("action"),
                "urgency": recommendation.get("urgency"),
            })

        diagnosis_sections = []
        if symptom_response:
            logger.info("✅ Adding symptom_response to diagnosis: %s", symptom_response[:100])
            diagnosis_sections.append(f"**Regarding Your Symptoms:** {symptom_response}")
        else:
            logger.warning("⚠️ symptom_response is empty or None - will not appear in output")
            
        if overall_impression:
            diagnosis_sections.append(f"**Overall Impression:** {overall_impression}")
        if symptom_correlation:
            logger.info("✅ Adding symptom_correlation to diagnosis: %s", symptom_correlation[:100])
            diagnosis_sections.append(f"**Symptom Correlation:** {symptom_correlation}")
        if patient_summary:
            diagnosis_sections.append(f"**Patient-Friendly Summary:** {patient_summary}")

        if normalized_findings:
            diagnosis_sections.append("**Pulmonary Findings:**")
            for finding in normalized_findings:
                diagnosis_sections.append(
                    f"- {finding['term']}: {finding['status'].title()} (Confidence {finding['confidence']}%) - {finding['radiology_summary']}"
                )

        diagnosis_text = "\n".join(diagnosis_sections) if diagnosis_sections else (
            overall_impression or "No significant abnormalities detected."
        )
        
        logger.info("📝 Final diagnosis_text length: %d characters", len(diagnosis_text))
        logger.info("📝 Diagnosis sections count: %d", len(diagnosis_sections))

        return {
            "provider": provider,
            "model": model,
            "is_medical_image": raw_result.get("is_medical_image", True),
            "image_type": image_type,
            "provided_symptoms": symptoms,
            "overall_impression": overall_impression,
            "patient_friendly_summary": patient_summary,
            "extended_findings": extended_findings,
            "critical_findings": normalized_findings,
            "findings": normalized_findings,
            "recommendations": normalized_recommendations,
            "priority_recommendations": normalized_recommendations,
            "urgency": urgency,
            "confidence_score": confidence_score,
            "confidence_probability": raw_confidence if isinstance(raw_confidence, (int, float)) else None,
            "diagnosis": diagnosis_text,
        }
