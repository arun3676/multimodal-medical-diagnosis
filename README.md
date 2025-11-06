# Multimodal Medical Diagnosis Assistant

This is an advanced AI-powered web application designed to assist with medical diagnosis by analyzing chest X-ray images and patient-reported symptoms. The system leverages a suite of cutting-edge AI models, including Vision Language Models (VLMs) and a fine-tuned image classifier, to provide both rapid and in-depth diagnostic insights.

## ✨ Key Features

- **🖼️ Multimodal Analysis**: Integrates visual data (X-ray images) with textual data (patient symptoms) for a comprehensive diagnostic context.
- **🤖 Dual Analysis Modes**:
  - **Fast Analysis**: Utilizes a fine-tuned `ViT-based` model (`arunn7/vit-base-patch16-224-in21k-medical-xray-lora`) for near-instant classification of Pneumonia vs. Normal.
  - **Detailed Analysis**: Employs a powerful Vision Language Model (VLM) for an in-depth radiological report.
- **🧠 Advanced VLM Routing**: 
  - Prioritizes **OpenAI's GPT-4o-mini** for its state-of-the-art reasoning capabilities.
  - Features a fallback chain to **Google's Gemini** to ensure high availability.
- **🩺 Expert-Level AI Prompting**: The VLM is guided by a sophisticated prompt engineered to act as an expert radiologist. It specifically checks for four critical pneumonia indicators:
  1.  **Consolidation**
  2.  **Air Bronchogram**
  3.  **Pleural Effusion**
  4.  **Infiltrate**
- **🎤 Audio Symptom Transcription**: Uses **OpenAI Whisper** to transcribe spoken patient symptoms, making input seamless and accessible.
- **🛡️ Realistic Confidence Scoring**: The AI provides a confidence score (0.0 to 1.0) for each finding, indicating its certainty level for a more reliable and transparent analysis.
- **🌐 Web Interface**: A clean, user-friendly interface built with Flask and vanilla JavaScript for easy interaction.

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **AI Models**:
  - **Primary VLM**: OpenAI GPT-4o-mini
  - **Fallback VLM**: Google Gemini
  - **Classifier**: Hugging Face Transformers (ViT)
  - **Audio**: OpenAI Whisper
- **Frontend**: HTML, CSS, JavaScript
- **Dependencies**: `requests`, `Pillow`, `python-dotenv`, `torch`, `transformers`

## ⚙️ Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd multimodal-medical-diagnosis
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/Scripts/activate  # On Windows
    # . .venv/bin/activate  # On macOS/Linux
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in the project root. This is crucial for connecting to the AI services. Add your API keys:
    ```env
    # .env

    # --- API Keys ---
    OPENAI_API_KEY="your_openai_api_key_here"
    GEMINI_API_KEY="your_google_gemini_api_key_here"
    GROQ_API_KEY="your_groq_api_key_here" # For Whisper transcription

    # --- VLM Provider Order ---
    # Determines the sequence of AI models for detailed analysis.
    # The system will try them in order until one succeeds.
    VISION_PROVIDER_ORDER="openai,gemini"
    ```

## ▶️ Running the Application

Once the setup is complete, run the Flask application:

```bash
python run_app.py
```

The application will be available at `http://127.0.0.1:5000`.

## 📝 Usage

1.  **Open the web interface** in your browser.
2.  **Upload a chest X-ray image** (.jpeg, .png).
3.  **(Optional)** Enter patient symptoms in the text box or use the microphone to record them.
4.  **Choose an Analysis Type**:
    - `Fast Analysis` for a quick classification.
    - `Detailed Analysis` for a full radiological report from the VLM.
5.  **View the results** displayed on the page. For detailed analysis, this will include the status and confidence for the four key pneumonia findings.
