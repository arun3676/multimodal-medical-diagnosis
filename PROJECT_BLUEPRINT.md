# Project Blueprint: Multimodal Medical Diagnosis Assistant

This document provides a comprehensive blueprint of the Multimodal Medical Diagnosis Assistant project. It is intended to give developers and AI models a clear understanding of the project's architecture, file structure, and core logic.

## 1. Project Overview

The Multimodal Medical Diagnosis Assistant is a Flask-based web application that leverages AI to analyze medical images (chest X-rays) and patient symptoms to provide diagnostic insights. It features two primary analysis modes: a "Fast" mode using a fine-tuned image classifier for pneumonia detection, and a "Detailed" mode that uses a Vision Language Model (VLM) for a comprehensive radiological report.

**Key Technologies:**

*   **Backend:** Flask
*   **Frontend:** HTML, CSS, JavaScript
*   **AI/ML:**
    *   **VLM:** OpenAI GPT-4o-mini, Google Gemini (fallback)
    *   **Image Classification:** Fine-tuned Vision Transformer (ViT) with LoRA
    *   **Audio Transcription:** OpenAI Whisper (via Groq)
*   **Deployment:** Configured for Vercel

## 2. High-Level Architecture

The application follows a standard client-server architecture:

1.  **Frontend (Client):** A user interacts with the web interface to upload an X-ray image and optionally provide symptoms via text or voice.
2.  **Backend (Flask Server):**
    *   Receives the request from the frontend.
    *   Handles file uploads and saves them temporarily.
    *   If audio is provided, it's transcribed to text using the `WhisperTranscriber`.
    *   Based on the selected analysis mode, it routes the request to the appropriate analysis module:
        *   **Fast Analysis:** `vision_classifier.py`
        *   **Detailed Analysis:** `groq_vlm_router.py`
    *   Returns the analysis results to the frontend as a JSON response.
3.  **AI Core Modules:**
    *   `groq_vlm_router.py`: Manages the interaction with external VLM providers (OpenAI, Gemini). It constructs the prompt, sends the image and symptoms, and parses the JSON response.
    *   `vision_classifier.py`: Loads and runs the fine-tuned ViT model for pneumonia classification.
    *   `whisper_transcriber.py`: Handles audio transcription.
    *   `model_cache.py`: Manages the local caching of Hugging Face models to avoid re-downloading.

## 3. File-by-File Breakdown

Here is a description of the key files and their roles in the project:

### Root Directory

*   **`run_app.py`**:
    *   **Purpose:** The main entry point to start the Flask application.
    *   **Logic:**
        *   Adds the project root to the system path.
        *   Checks for the presence of a `.env` file.
        *   Initializes and runs the Flask app created by `app.create_app()`.
        *   Performs a startup check to test if the fine-tuned model can be loaded.

*   **`requirements.txt`**:
    *   **Purpose:** Lists all the Python dependencies for the project.
    *   **Key Libraries:** `Flask`, `openai`, `google-generativeai`, `groq`, `torch`, `transformers`, `peft`, `Pillow`.

*   **`README.md`**:
    *   **Purpose:** Provides a general overview of the project, setup instructions, and usage guide.

*   **`vercel.json`**:
    *   **Purpose:** Configuration file for deploying the Flask application to the Vercel platform.

### `app/` Directory

*   **`routes.py`**:
    *   **Purpose:** Defines all the API endpoints and view functions for the Flask application.
    *   **Key Endpoints:**
        *   `/` (GET): Renders the main `index.html` page.
        *   `/api/analyze` (POST): The core endpoint for image analysis. It handles file uploads, sanitizes inputs, and calls the appropriate analysis function (`analyze_with_finetuned_model` or `analyze_with_vlm`) based on the `analysis_type`.
        *   `/api/transcribe` (POST): Handles audio file uploads and uses the `WhisperTranscriber` to get a text transcription of symptoms.
        *   `/health` (GET): A simple health check endpoint.

*   **`core/groq_vlm_router.py`**:
    *   **Purpose:** Manages the detailed analysis workflow using VLMs.
    *   **Logic:**
        *   Defines a provider order (e.g., OpenAI then Gemini) for fallback.
        *   Contains a detailed JSON-based prompt designed to guide the VLM to act as a radiologist.
        *   Encodes the input image to a base64 string.
        *   Calls the VLM providers in the specified order until a successful response is received.
        *   Parses and normalizes the JSON response from the VLM to a consistent format for the frontend.

*   **`core/vision_classifier.py`**:
    *   **Purpose:** Handles the "Fast Analysis" mode for pneumonia detection.
    *   **Logic:**
        *   Implements a singleton pattern (`get_classifier`) to ensure only one instance of the model is loaded.
        *   Loads a pre-trained Vision Transformer (`google/vit-base-patch16-224-in21k`) and applies LoRA weights from a specified Hugging Face repo (`arunn7/vit-base-patch16-224-in21k-medical-xray-lora`).
        *   Preprocesses the input image and performs inference.
        *   Returns a prediction ('NORMAL' or 'PNEUMONIA') with a confidence score.

*   **`core/whisper_transcriber.py`**:
    *   **Purpose:** Transcribes spoken symptoms from an audio file.
    *   **Logic:**
        *   Uses the Groq API to access the Whisper model for fast transcription.
        *   Includes a simple keyword-based symptom extraction logic to summarize the transcription.

*   **`core/model_cache.py`**:
    *   **Purpose:** Manages the local caching of Hugging Face models.
    *   **Logic:**
        *   Sets the `HF_HOME` environment variable to a local `models_cache` directory.
        *   Provides utility functions to check if a model is cached, which helps in avoiding repeated downloads.

### `app/static/` Directory

*   **`css/style.css`**:
    *   **Purpose:** Contains all the styling for the web application, defining the visual appearance of the components.

*   **`js/main.js`**:
    *   **Purpose:** The main JavaScript file that controls the frontend interactivity.
    *   **Logic:**
        *   Handles file uploads via drag-and-drop and the browse button.
        *   Manages the voice recording functionality.
        *   Listens for the analysis mode toggle ('Fast' vs. 'Detailed').
        *   Makes the `fetch` requests to the `/api/analyze` and `/api/transcribe` endpoints.
        *   Dynamically updates the UI to display the analysis results, including findings, recommendations, and confidence scores.

## 4. Key Workflows

### Workflow 1: Detailed Analysis with Voice Symptoms

1.  **User uploads an image:** The frontend displays the image preview.
2.  **User records voice symptoms:** `main.js` captures the audio and sends it to the `/api/transcribe` endpoint.
3.  **Backend transcribes audio:** `whisper_transcriber.py` processes the audio and returns the transcribed symptoms.
4.  **Frontend receives transcription:** `main.js` stores the symptoms and automatically triggers the analysis.
5.  **Frontend sends analysis request:** An API call is made to `/api/analyze` with the image and transcribed symptoms, with `analysis_type` set to 'detailed'.
6.  **Backend routes to VLM:** `routes.py` calls `analyze_with_vlm`, which uses the `GroqVLMRouter`.
7.  **VLM Router executes:** It tries OpenAI first. If it fails, it tries Gemini.
8.  **Backend returns results:** The normalized JSON from the VLM is sent back to the frontend.
9.  **Frontend displays results:** `main.js` parses the JSON and updates the UI with the detailed findings and recommendations.

### Workflow 2: Fast Analysis (Manual)

1.  **User uploads an image.**
2.  **User selects 'Fast' analysis mode.**
3.  **User clicks the 'Analyze Image' button.**
4.  **Frontend sends analysis request:** An API call is made to `/api/analyze` with `analysis_type` set to 'fast'.
5.  **Backend routes to classifier:** `routes.py` calls `analyze_with_finetuned_model`, which uses the `PneumoniaClassifier`.
6.  **Classifier predicts:** `vision_classifier.py` loads the ViT+LoRA model and predicts if the image shows pneumonia.
7.  **Backend returns results:** A simplified JSON response with the prediction and confidence score is sent to the frontend.
8.  **Frontend displays results:** The UI is updated to show the 'PNEUMONIA' or 'NORMAL' status.