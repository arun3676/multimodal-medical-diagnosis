import os
from google.cloud import vision
from dotenv import load_dotenv

# Set the credentials file path
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"C:\Users\ARUN\Downloads\research engineer\multimodal\credentials\google_credentials.json"

def analyze_image(image_path):
    try:
        # Initialize Google Cloud Vision client
        client = vision.ImageAnnotatorClient()
        
        # Read the image file
        with open(image_path, "rb") as image_file:
            content = image_file.read()
        
        # Create a Vision Image object
        image = vision.Image(content=content)
        
        # Perform text detection
        response = client.text_detection(image=image)
        annotations = response.text_annotations
        
        # Return the detected text
        if annotations:
            return annotations[0].description
        else:
            return "No text found in the image."
            
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

# Test the function
if __name__ == "__main__":
    # Your image path
    image_path = r"C:\Users\ARUN\Downloads\research engineer\multimodal\xray.jpg"
    
    # Analyze the image
    result = analyze_image(image_path)
    
    # Print the result
    print("Detected Text:")
    print(result)