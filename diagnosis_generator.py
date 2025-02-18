import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_diagnosis(image_text, symptoms):
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        return "Error: OpenAI API key not found in .env file"
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    try:
        prompt = f"""
        Medical Image Analysis Results:
        {image_text}

        Patient Symptoms:
        {symptoms}

        Based on the above, list the top 3 possible diagnoses in order of likelihood. 
        Explain each briefly in simple terms.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating diagnosis: {str(e)}"

# Test the function if run directly
if __name__ == "__main__":
    # Test with your image
    from vision_analyzer import analyze_image
    
    image_path = r"C:\Users\ARUN\Downloads\research engineer\multimodal\xray.jpg"
    image_text = analyze_image(image_path)
    
    # Read symptoms
    symptoms_path = r"C:\Users\ARUN\Downloads\research engineer\multimodal\symptoms.txt"
    with open(symptoms_path, "r") as f:
        symptoms = f.read()
    
    # Generate and print diagnosis
    diagnosis = generate_diagnosis(image_text, symptoms)
    print("\nDiagnosis Suggestions:")
    print(diagnosis)