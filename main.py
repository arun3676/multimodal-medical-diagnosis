from vision_analyzer import analyze_image
from diagnosis_generator import generate_diagnosis

def main():
    try:
        # Your file paths
        image_path = r"C:\Users\ARUN\Downloads\research engineer\multimodal\xray.jpg"
        symptoms_path = r"C:\Users\ARUN\Downloads\research engineer\multimodal\symptoms.txt"
        
        # Get image analysis
        print("Analyzing image...")
        image_text = analyze_image(image_path)
        print("\nImage Analysis Results:")
        print(image_text)
        
        # Read symptoms
        print("\nReading symptoms...")
        with open(symptoms_path, "r") as f:
            symptoms = f.read()
        print(symptoms)
        
        # Generate diagnosis
        print("\nGenerating diagnosis...")
        diagnosis = generate_diagnosis(image_text, symptoms)
        print("\nDiagnosis Suggestions:")
        print(diagnosis)
        
    except Exception as e:
        print(f"Error in main workflow: {str(e)}")

if __name__ == "__main__":
    main()