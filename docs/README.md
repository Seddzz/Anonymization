# SecureDoc - Document Anonymization Tool

SecureDoc is a powerful web application that automatically detects and anonymizes sensitive personal information in documents while preserving original formatting.

## 🚀 Features

- **Multi-Format Support**: Process TXT, DOCX, and PDF files
- **Smart Entity Detection**: Automatically identifies personal information using NLP
- **Format Preservation**: Maintains original document formatting, styles, and layout
- **Customizable Anonymization**: Select specific entity types to anonymize
- **Live Preview**: Real-time editing and preview of anonymization results
- **Arabic Language Support**: Full compatibility with Arabic text and entities

## 📋 Supported Entity Types

- **👤 Person Names** (Arabic and English)
- **📧 Email Addresses**
- **🏢 Organizations**
- **📱 Phone Numbers**
- **🎂 Ages**
- **📍 Locations** (Addresses, cities, countries)
- **📅 Dates**

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Step 1: Clone the Repository
```bash
git clone https://github.com/Seddzz/Anonymization.git
cd anonymization
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Required Dependencies
```txt
# Core Web Framework
Flask==3.1.0

# Text Processing & NLP
spacy==3.8.7

# Document Processing
python-docx==1.2.0

# PDF Processing
PyPDF2==3.0.1
pdfplumber==0.11.7
reportlab==4.2.5
PyMuPDF==1.24.10

# Fake Data Generation
Faker==37.6.0

# HTTP Client
httpx==0.28.1

# Environment Variables
python-dotenv==1.1.1
```

### Step 4: Download SpaCy Model
```bash
python -m spacy download en_core_web_sm
```

## 🎯 Quick Start

### Running the Application
```bash
cd src/interfaces
python web_ui.py
```

The application will be available at: `http://localhost:5000`

### Basic Usage

1. **Upload a Document**: Choose from TXT, DOCX, or PDF formats
2. **Select Detection Method**:
   - **SpaCy NLP**: Fast processing for English and French
   - **LLM**: Advanced AI detection for complex patterns
3. **Choose Entity Types**: Select which personal information to anonymize
4. **Process & Download**: Get your anonymized document with preserved formatting

### Advanced Features

- **Entity Selection Mode**: Customize which entity types to detect
- **Live Edit**: Adjust entity selection and reprocess without re-uploading
- **Side-by-Side Comparison**: View original vs. anonymized content
- **Detailed Mapping**: See exactly what was changed and how

## 📁 Project Structure

```
anonymization/
├── src/
│   ├── agent/
│   │   ├── tools/
│   │   │   ├── detectors/     # Entity detection modules
│   │   │   └── replacers/     # Data anonymization modules
│   │   └── executor.py        # Main processing pipeline
│   ├── interfaces/
│   │   ├── web_ui.py         # Flask web application
│   │   ├── templates/        # HTML templates
│   │   └── static/           # CSS, JS, assets
│   └── utils/
│       ├── document_processor.py  # Document handling
│       ├── file_processor.py     # File format processing
│       └── helpers.py            # Utility functions
└── requirements.txt
```

## 🔧 Configuration

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
LLM_API_KEY=your-llm-api-key-optional
```

## 🌐 Web Interface

The application provides a user-friendly web interface with:

- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Processing**: Background task processing with progress updates
- **File Management**: Secure temporary file handling
- **Download Options**: Multiple format support for output

## 🎨 Processing Capabilities

### Document Types
- **TXT Files**: Simple text processing with structure preservation
- **DOCX Files**: Full formatting preservation (styles, tables, images)
- **PDF Files**: Advanced layout preservation with PyMuPDF

### Language Support
- **English**: Full entity detection and anonymization
- **Arabic**: Complete support for Arabic text and names
- **Multi-language**: Mixed language document handling

## 🔒 Privacy & Security

- **Local Processing**: All processing happens on your local machine
- **Temporary Files**: Uploaded files are automatically cleaned up
- **No Data Storage**: No personal data is stored or transmitted
- **Open Source**: Full transparency with source code available

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
