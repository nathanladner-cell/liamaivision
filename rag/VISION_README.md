# Vision-based Electrical Glove Label Scanner

A web application that uses AI vision to automatically extract information from electrical glove labels through camera photos.

## Features

- 📷 **Camera Integration**: Take photos directly from device camera
- 🧠 **AI-Powered Analysis**: Uses OpenAI GPT-4o Vision for intelligent text extraction
- 🔍 **Google Cloud Vision**: Optional OCR enhancement with Google Cloud Vision API
- 📝 **Auto-Population**: Automatically fills form fields with extracted data
- 💾 **Data Persistence**: Saves analysis results for later reference
- 📱 **Responsive Design**: Works on desktop and mobile devices

## Form Fields

The application extracts and populates the following information from glove labels:
- **Manufacturer**: Company that made the gloves (e.g., Ansell, Honeywell)
- **Class**: Electrical protection class (00, 0, 1, 2, 3, 4)
- **Size**: Glove size (7, 8, 9, 10, 11, 12, etc.)
- **Color**: Glove color (Red, Yellow, Black, etc.)

## Quick Start

### 1. Install Dependencies
```bash
cd /Users/natelad/Desktop/ampAI/rag
python3 -m pip install -r vision_requirements.txt
```

### 2. Set Up Environment Variables
Copy the example environment file and edit it with your API keys:
```bash
cp vision_env_example.txt .env
# Edit .env with your actual API keys
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key (required)

Optional environment variables:
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to Google Cloud service account JSON
- `GOOGLE_PROJECT_ID`: Your Google Cloud Project ID
- `OPENAI_MODEL`: OpenAI model to use (default: gpt-4o)
- `FLASK_DEBUG`: Enable debug mode (default: False)

### 3. Run the Application
```bash
# Using the startup script
python3 run_vision.py

# Or directly
python3 vision_app.py
```

### 4. Open in Browser
Navigate to: http://localhost:5000

## Setup Scripts

### Automated Setup
```bash
python3 setup_vision.py
```

This script will:
- Install required dependencies
- Check environment configuration
- Create a `.env` template file
- Test imports and connectivity

### Manual Setup

1. **Install Dependencies**:
   ```bash
   pip install flask openai python-dotenv google-cloud-vision pillow
   ```

2. **OpenAI API Setup**:
   - Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
   - Set `OPENAI_API_KEY` in your environment

3. **Google Cloud Vision (Optional)**:
   - Create a [Google Cloud Project](https://console.cloud.google.com/)
   - Enable the Vision API
   - Create a service account and download JSON credentials
   - Set `GOOGLE_APPLICATION_CREDENTIALS` and `GOOGLE_PROJECT_ID`

## How to Use

1. **Take Photo**: Click the "Take Photo of Glove Label" button
2. **Grant Camera Access**: Allow camera permissions when prompted
3. **Capture Label**: Take a clear photo of the electrical glove label
4. **Automatic Analysis**: The AI analyzes the image and extracts information
5. **Review Results**: Check the populated form fields
6. **Save Analysis**: Click "Save Analysis" to store the results

## API Endpoints

- `GET /`: Main application page
- `POST /api/analyze-image`: Analyze uploaded image
- `POST /api/save-analysis`: Save analysis results
- `GET /api/get-analyses`: Retrieve saved analyses
- `GET /health`: Health check endpoint

## Technical Details

### Vision Analysis Pipeline

1. **Image Capture**: HTML5 camera API captures photo
2. **Google Cloud Vision** (optional): OCR text extraction
3. **OpenAI GPT-4o Vision**: Intelligent analysis of label content
4. **Data Extraction**: Structured JSON output with confidence levels
5. **Form Population**: Automatic field filling with extracted data

### File Structure

```
/Users/natelad/Desktop/ampAI/rag/
├── vision_app.py              # Main Flask application
├── templates/
│   └── vision_form.html       # Web interface template
├── static/
│   └── liamai.png            # App icon/logo
├── vision_requirements.txt    # Python dependencies
├── setup_vision.py           # Setup automation script
├── run_vision.py             # Startup script
└── VISION_README.md          # This documentation
```

## Troubleshooting

### Camera Not Working
- Ensure HTTPS or localhost (camera requires secure context)
- Grant camera permissions when prompted
- Try refreshing the page

### Analysis Fails
- Ensure OpenAI API key is correctly set
- Check image quality and lighting
- Try taking the photo closer to the label

### Google Vision Not Working
- Verify Google Cloud credentials are correct
- Ensure Vision API is enabled in your project
- Check service account permissions

### Port Already in Use
- Change the port in `run_vision.py` or set `PORT` environment variable
- Kill any existing Flask processes

## Development

### Running in Debug Mode
```bash
FLASK_DEBUG=True python3 vision_app.py
```

### Testing Vision API
Visit `/health` endpoint to check API connectivity.

### Adding New Fields
1. Update the HTML form in `vision_form.html`
2. Modify the system prompt in `vision_app.py`
3. Update form population logic in JavaScript

## Security Notes

- API keys are loaded from environment variables
- Images are processed temporarily and not stored permanently
- Analysis results are stored in session (consider database for production)
- Camera access requires user permission

## Future Enhancements

- [ ] Batch processing of multiple labels
- [ ] Export functionality (PDF, CSV)
- [ ] Database integration for persistent storage
- [ ] Advanced image preprocessing
- [ ] Multi-language support
- [ ] Integration with existing electrical safety systems

## License

This project is part of the AmpAI electrical safety assistant suite.
