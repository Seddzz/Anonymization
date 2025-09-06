# Document Anonymization Tool

A powerful, privacy-first tool for anonymizing sensitive information in documents and text. Runs entirely on your local machine - your data never leaves your computer.

## ✨ Features

- 🛡️ **Complete Privacy** - All processing happens locally
- 🚀 **AI-Powered Detection** - Smart PII detection using spaCy NLP
- 📄 **Multi-Format Support** - Text, PDF, and DOCX files
- ⚡ **Fast & Reliable** - Instant anonymization with realistic replacements
- 🔒 **Zero Data Retention** - Nothing is stored or transmitted

## 📋 Requirements

- **Python 3.8+** (Python 3.10+ recommended)
- **4GB RAM minimum** (for spaCy models)
- **Windows, macOS, or Linux**

## � Quick Installation

### Option 1: Simple Setup (Recommended)

1. **Download or Clone** this repository:
   ```bash
   git clone https://github.com/Seddzz/Anonymization.git
   cd anonymization
   ```

2. **Create Virtual Environment:**
   ```bash
   python -m venv .venv
   ```

3. **Activate Virtual Environment:**
   
   **Windows:**
   ```bash
   .venv\Scripts\activate
   ```
   
   **macOS/Linux:**
   ```bash
   source .venv/bin/activate
   ```

4. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Download spaCy Model:**
   ```bash
   python -m spacy download en_core_web_sm
   ```

6. **Run the Application:**
   ```bash
   python app.py
   ```

7. **Open Your Browser:**
   Navigate to `http://127.0.0.1:5000`

## � Usage

1. **Text Anonymization:**
   - Paste or type text in the input area
   - Click "Anonymize Text"
   - View results with detailed replacement mapping

2. **File Anonymization:**
   - Drag & drop or select files (.txt, .pdf, .docx)
   - Click "Anonymize File"  
   - Download the anonymized version

3. **Supported Entities:**
   - � Names (Person, Organization)
   - 📧 Email addresses
   - 🏢 Organizations & Companies
   - 📅 Dates and ages
   - 📍 Locations


## 📁 Project Structure

```
anonymization/
├── app.py                    # Main Flask application
├── pipeline.py               # Anonymization pipeline
├── requirements.txt          # Dependencies
├── detectors/               # Detection engines
├── replacers/               # Data replacement
├── utils/                   # File processing
├── templates/               # Web interface
└── static/                  # Assets & styling
```

## 🎯 Next

- [ ] LangGraph integration for advanced workflows
- [ ] Additional file format support (Excel, CSV)
