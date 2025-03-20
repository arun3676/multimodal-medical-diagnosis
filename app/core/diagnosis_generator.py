"""
Enhanced diagnosis generation module with structured, professional output formatting.
"""
import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def generate_diagnosis(image_analysis, symptoms, model="gpt-4"):
    """
    Generate diagnosis suggestions with structured, professional output.
    """
    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        error_msg = "OpenAI API key not found in environment variables"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    try:
        # Enhanced medical prompt with proper output structure
        system_prompt = """You are a medical AI assistant with expertise in radiological image analysis. 
Your role is to help interpret medical imaging data and provide educational information.

IMPORTANT GUIDELINES:
1. Format your responses using clear headings (##), bullet points, and numbered lists
2. Use concise language and structured sections that are easy to scan
3. Bold important findings or conclusions
4. This is for EDUCATIONAL PURPOSES ONLY and not for clinical diagnosis
5. Use standard radiological terminology and assessment patterns
"""
        
        user_prompt = f"""
I'm analyzing a medical imaging result for educational purposes. Please provide a clear, structured interpretation with proper formatting.

TECHNICAL ANALYSIS RESULTS:
{image_analysis}

PATIENT PRESENTATION:
{symptoms}

Please structure your response with the following sections, using markdown formatting:

## TECHNICAL ASSESSMENT
* [Bulleted list of observations about image quality and technical aspects]

## KEY FINDINGS
* [Clear, bulleted list of the most important visual findings]

## IMPRESSION
* [Numbered list of possible interpretations in order of likelihood]

## RECOMMENDATIONS
* [Bulleted list of suggested next steps or additional studies]

## EDUCATIONAL NOTES
* [Brief notes about what can be learned from this case]

## LIMITATIONS
* [Short list of key limitations of this analysis]

Make sure the output is highly structured, easy to scan, and professional-looking.
"""
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        error_msg = f"Error generating diagnosis: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

def generate_enhanced_interpretation(findings_dict, symptoms, model="gpt-4"):
    """
    Generate a beautifully structured medical interpretation using detailed findings data.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        error_msg = "OpenAI API key not found in environment variables"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    client = OpenAI(api_key=api_key)
    
    try:
        # Format metrics in a readable way
        metrics_str = "\n".join([f"- {k}: {v}" for k, v in findings_dict.get('metrics', {}).items()])
        
        # Warning if the image might not be an X-ray
        is_xray_warning = ""
        if not findings_dict.get('is_likely_xray', True):
            is_xray_warning = "WARNING: The submitted image does not appear to be a standard medical X-ray. This may significantly affect interpretation accuracy."
        
        system_prompt = """You are a medical AI assistant with expertise in radiological image analysis.
You must format your response as a professionally structured report with clear sections, bullet points, and highlights.

FORMATTING GUIDELINES:
1. Use markdown formatting with section headers (##) and subheaders (###)
2. Use bulleted lists (*) for findings and recommendations
3. Use numbered lists (1.) for differential diagnoses or interpretations
4. Bold (**text**) for important findings or conclusions
5. Keep sections concise and scannable
6. Use medical terminology but explain complex terms when first introduced
7. Clearly separate sections with whitespace
"""
        
        user_prompt = f"""
I need a professionally formatted radiology educational report based on the following data:

{is_xray_warning}

DETECTED OBJECTS/STRUCTURES:
{", ".join(findings_dict.get('objects', ['None detected']))}

DETECTED FEATURES:
{", ".join(findings_dict.get('features', ['None detected']))}

IMAGE METRICS:
{metrics_str}

PATIENT SYMPTOMS:
{symptoms}

Create a structured report with these exact sections (use these exact headings):

## TECHNICAL ASSESSMENT
[Quality of image, positioning, exposure, etc.]

## KEY FINDINGS
[Bulleted list of most important observations]

## IMPRESSION
[Numbered list of possible interpretations in order of likelihood]

## RECOMMENDATIONS
[Bulleted list of suggested next steps]

## EDUCATIONAL NOTES
[Brief notes on radiological principles relevant to this case]

## LIMITATIONS
[Limitations of this analysis]

Format this output to look highly professional and easy to scan quickly.
"""
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        error_msg = f"Error generating enhanced interpretation: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)