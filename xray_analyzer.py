import os
from google.cloud import vision
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import time
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Set up credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"C:\Users\ARUN\Downloads\research engineer\multimodal\credentials\google_credentials.json"

def analyze_chest_xray(image_path):
    """
    Analyzes a single chest X-ray image using Google Cloud Vision API.
    """
    try:
        client = vision.ImageAnnotatorClient()
        
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        
        # Get both object detection and general image labels
        objects = client.object_localization(image=image).localized_object_annotations
        labels = client.label_detection(image=image).label_annotations
        
        findings = {
            'objects': [f"{obj.name} ({obj.score:.2%})" for obj in objects],
            'features': [f"{label.description} ({label.score:.2%})" for label in labels],
            'raw_scores': {
                'objects': {obj.name: obj.score for obj in objects},
                'labels': {label.description: label.score for label in labels}
            }
        }
        
        return findings
    
    except Exception as e:
        print(f"Error analyzing image {image_path}: {str(e)}")
        return None

def generate_medical_interpretation(findings):
    """
    Uses GPT-4 to interpret the X-ray findings.
    """
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        findings_text = "\nObjects detected:\n" + "\n".join(findings['objects'])
        findings_text += "\n\nImage features:\n" + "\n".join(findings['features'])
        
        prompt = f"""
        As a medical AI assistant, analyze this chest X-ray:

        {findings_text}

        Please provide:
        1. Key observations from the X-ray
        2. Potential medical conditions suggested by these findings
        3. Recommended follow-up steps or additional tests if needed

        Keep in mind this is an AI interpretation and should be verified by a healthcare professional.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error generating interpretation: {str(e)}"

def find_all_images(directory):
    """
    Recursively finds all PNG images in the directory and its subdirectories.
    """
    image_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.png'):
                image_files.append(os.path.join(root, file))
    return image_files

def process_images(base_dir, batch_size=5, start_index=0):
    """
    Processes images in batches and saves results periodically.
    
    Args:
        base_dir: Base directory containing images
        batch_size: Number of images to process in each batch
        start_index: Index to start processing from (for resuming)
    """
    # Create results directory if it doesn't exist
    results_dir = os.path.join(base_dir, 'analysis_results')
    os.makedirs(results_dir, exist_ok=True)
    
    # Find all images
    all_images = find_all_images(base_dir)
    total_images = len(all_images)
    
    print(f"Found {total_images} images. Starting from index {start_index}")
    
    # Process images in batches
    current_batch = []
    batch_num = start_index // batch_size + 1
    
    for i, image_path in enumerate(all_images[start_index:], start=start_index):
        print(f"\nProcessing image {i+1} of {total_images}: {os.path.basename(image_path)}")
        
        # Analyze image
        findings = analyze_chest_xray(image_path)
        
        if findings:
            # Generate medical interpretation
            interpretation = generate_medical_interpretation(findings)
            
            # Store results
            result = {
                'image_path': image_path,
                'image_name': os.path.basename(image_path),
                'findings': findings,
                'interpretation': interpretation,
                'processed_at': datetime.now().isoformat()
            }
            
            current_batch.append(result)
            
            # Save batch when it reaches batch_size
            if len(current_batch) >= batch_size:
                save_batch(current_batch, results_dir, batch_num)
                current_batch = []
                batch_num += 1
            
            # Small delay to avoid API rate limits
            time.sleep(1)
        
        # Save progress file
        save_progress(i + 1, results_dir)
    
    # Save any remaining results
    if current_batch:
        save_batch(current_batch, results_dir, batch_num)

def save_batch(batch, results_dir, batch_num):
    """
    Saves a batch of results to a JSON file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"batch_{batch_num}_{timestamp}.json"
    filepath = os.path.join(results_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(batch, f, indent=2)
    
    print(f"\nSaved batch {batch_num} to {filename}")

def save_progress(current_index, results_dir):
    """
    Saves the current progress to a file.
    """
    progress_file = os.path.join(results_dir, 'progress.txt')
    with open(progress_file, 'w') as f:
        f.write(str(current_index))

def load_progress(results_dir):
    """
    Loads the progress from the last run.
    """
    progress_file = os.path.join(results_dir, 'progress.txt')
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            return int(f.read().strip())
    return 0

if __name__ == "__main__":
    # Base directory containing your X-rays
    base_dir = r"C:\Users\ARUN\Downloads\research engineer\multimodal\images_010"
    
    # Create results directory
    results_dir = os.path.join(base_dir, 'analysis_results')
    os.makedirs(results_dir, exist_ok=True)
    
    # Load progress from last run
    start_index = load_progress(results_dir)
    
    # Process images in batches of 5
    print("Starting X-ray analysis...")
    process_images(base_dir, batch_size=5, start_index=start_index)
    
    print("\nAnalysis complete!")