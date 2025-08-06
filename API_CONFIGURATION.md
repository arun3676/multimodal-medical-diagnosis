# API Configuration and Troubleshooting

## Required API Keys

This application uses multiple AI services and requires the following API keys:

### 1. OpenAI API Key
- **Purpose**: Generates medical diagnoses and reports
- **Required**: Yes
- **How to get**: Visit [OpenAI Platform](https://platform.openai.com/api-keys)
- **Environment variable**: `OPENAI_API_KEY`

### 2. Google Gemini API Key
- **Purpose**: Analyzes medical images (chest X-rays)
- **Required**: Yes (currently the default image analyzer)
- **How to get**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Environment variable**: `GEMINI_API_KEY`

### 3. Google Cloud Vision API (Alternative)
- **Purpose**: Alternative image analyzer (not currently used)
- **Required**: No
- **How to get**: Set up Google Cloud Project with Vision API enabled
- **Environment variable**: `GOOGLE_APPLICATION_CREDENTIALS` or `GOOGLE_CREDENTIALS_JSON`

## Environment Setup

1. Copy `environment-variables-template.txt` to `.env`
2. Fill in your API keys:
   ```
   OPENAI_API_KEY=your_actual_openai_api_key
   GEMINI_API_KEY=your_actual_gemini_api_key
   SECRET_KEY=your_strong_random_secret_key
   ```

## Common Errors and Solutions

### 1. "Gemini API error: 503 - The model is overloaded"
- **Cause**: High demand on Google's Gemini service
- **Solution**: 
  - Wait 5-10 minutes and try again
  - The app now automatically retries with progressive backoff
  - Consider switching to Google Cloud Vision API for more reliability

### 2. "ModuleNotFoundError: No module named 'flask_limiter'"
- **Cause**: Missing Python dependencies
- **Solution**: Run `pip install -r requirements.txt`

### 3. "Rate limit exceeded"
- **Cause**: Too many API requests in a short time
- **Solution**:
  - Wait before making another request
  - Check your API quota and billing status
  - The app limits requests to 10 per hour per user

### 4. "GEMINI_API_KEY not found in environment variables"
- **Cause**: Missing or incorrectly set API key
- **Solution**:
  - Ensure your `.env` file contains `GEMINI_API_KEY=your_key`
  - Restart the application after adding the key
  - Verify the key is valid by testing it manually

### 5. "Service configuration error"
- **Cause**: Invalid API keys or service unavailable
- **Solution**:
  - Verify all API keys are correctly set
  - Check that your APIs are enabled and have available quota
  - Contact support if the issue persists

## Switching Between Image Analyzers

The application currently uses Gemini API for image analysis. To switch to Google Cloud Vision:

1. Edit `app/routes.py` line 25:
   ```python
   # Change from:
   from app.core.vision_analyzer_gemini import GeminiImageAnalyzer
   
   # To:
   from app.core.vision_analyzer import MedicalImageAnalyzer
   ```

2. Update the analyzer initialization on line 31:
   ```python
   # Change from:
   image_analyzer = GeminiImageAnalyzer()
   
   # To:
   image_analyzer = MedicalImageAnalyzer()
   ```

3. Set up Google Cloud credentials in your `.env` file

## Rate Limits and Quotas

- **Gemini API**: Varies by tier, typically 15 requests per minute for free tier
- **OpenAI API**: Varies by tier and model
- **Application**: Limited to 10 analysis requests per hour per user

## Performance Optimization

1. **Image Size**: Keep images under 5MB for faster processing
2. **Format**: JPEG images typically process faster than PNG
3. **Caching**: Results are cached to avoid repeated API calls for the same image
4. **Retry Logic**: Automatic retries handle temporary service outages

## Support

If you continue experiencing issues:
1. Check the application logs for detailed error messages
2. Verify your API keys are valid and have sufficient quota
3. Ensure all dependencies are installed correctly
4. Try the alternative image analyzer if Gemini is consistently overloaded 