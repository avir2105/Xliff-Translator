# XLIFF Translator

A web-based application for translating XLIFF (XML Localization Interchange File Format) files using Google's Gemini AI model. This tool helps streamline the localization process by automatically translating content while preserving the XLIFF structure.

## What is XLIFF?

XLIFF (XML Localization Interchange File Format) is an XML-based format created to standardize the way localizable data is passed between tools during a localization process. It's designed to:

- Store localizable data and carry it from one step to another in the localization process
- Separate localizable text from formatting
- Enable multiple tools to work on the localization process
- Store metadata about the localization process

Common use cases for XLIFF:
- Software localization
- Document translation
- Web content management
- Product documentation
- Marketing materials

## Features

- Drag-and-drop file upload interface
- Support for XLIFF 1.2 format
- Automatic translation using Google's Gemini AI model
- Preservation of XLIFF structure and metadata
- Batch processing of translation units
- Downloadable translated XLIFF files
- Progress indicators and status messages
- Error handling and validation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/xliff-translator.git
cd xliff-translator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Gemini API key:
   - Get an API key from Google AI Studio
   - Replace the API key in `main.py`

## Usage

1. Start the server:
```bash
uvicorn app:app --reload
```

2. Open your browser and navigate to `http://localhost:8000`

3. Upload an XLIFF file using either:
   - Drag and drop
   - File browser

4. Enter the target language code (e.g., 'fr' for French)

5. Click "Translate and Download"

## Project Structure

```
final_xlif/
├── app.py              # FastAPI application entry point
├── main.py            # Core translation logic
├── static/
│   ├── script.js      # Frontend JavaScript
│   └── styles.css     # CSS styles
├── templates/
│   └── index.html     # Main HTML template
└── temp_files/        # Temporary storage for uploads
```

## Technical Details

### Backend
- FastAPI for the web framework
- Google Gemini AI for translation
- lxml for XML processing
- Type hints and dataclasses for robust code structure

### Frontend
- Vanilla JavaScript for interactivity
- Modern CSS with flexbox/grid
- Font Awesome icons
- Responsive design

## XLIFF File Structure Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2">
  <file source-language="en" target-language="fr">
    <body>
      <trans-unit id="1">
        <source>Hello World</source>
        <target>Bonjour le monde</target>
      </trans-unit>
    </body>
  </file>
</xliff>
```

## Best Practices for XLIFF Translation

1. **Preserve Tags**: The translator maintains XML tags and placeholders
2. **Batch Processing**: Translations are processed in batches for efficiency
3. **Error Handling**: Robust error handling for API and file processing
4. **Validation**: Input validation for file format and language codes
5. **Memory Management**: Temporary files are cleaned up automatically

## Common XLIFF Use Cases

1. **Software Localization**
   - UI strings
   - Error messages
   - Help documentation

2. **Content Management**
   - Website content
   - Marketing materials
   - Product descriptions

3. **Documentation**
   - Technical manuals
   - User guides
   - API documentation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini AI for translation capabilities
- FastAPI for the web framework
- XLIFF 1.2 specification and community

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.
