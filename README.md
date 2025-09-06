# 🔐 Anonymize Me - Document Anonymization Tool

A powerful, privacy-first tool for anonymizing sensitive information in documents and text. Runs entirely on your local machine - your data never leaves your computer.

## ✨ Features

- 🛡️ **Complete Privacy** - All processing happens locally
- 🚀 **AI-Powered Detection** - Smart PII detection using spaCy NLP
- 📄 **Multi-Format Support** - Text, PDF, and DOCX files
- ⚡ **Fast & Reliable** - Instant anonymization with realistic replacements
- 🎨 **Modern UI** - Clean, responsive web interface
- 🔒 **Zero Data Retention** - Nothing is stored or transmitted

## 📋 Requirements

- **Python 3.8+** (Python 3.10+ recommended)
- **4GB RAM minimum** (for spaCy models)
- **Windows, macOS, or Linux**

## � Quick Installation

### Option 1: Simple Setup (Recommended)

1. **Download or Clone** this repository:
   ```bash
   git clone https://github.com/9ada19/PFE2.git
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

## 🛠️ Troubleshooting

### Common Issues:

**"Module not found" errors:**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

**Port already in use:**
```bash
# Try a different port
python app.py --port 5001
```

**Permission errors on Windows:**
```bash
# Run as administrator or check antivirus settings
```

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

## � Privacy & Security

- **Local Processing Only** - No data sent to external servers
- **No Data Storage** - Nothing is saved after processing
- **Open Source** - Full transparency of all operations
- **No Telemetry** - No usage tracking or analytics

## 🎯 Roadmap

- [ ] LangGraph integration for advanced workflows
- [ ] Additional file format support (Excel, CSV)
- [ ] Batch processing capabilities
- [ ] Custom entity types
- [ ] API mode for integration

## 🤝 Contributing

Found a bug or want to contribute? 

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

MIT License - Feel free to use, modify, and distribute.

## 👨‍� Author

Built with ❤️ by [seddz](https://github.com/Seddzz)

---

**⚠️ Important:** This tool is designed for legitimate privacy protection. Always ensure you have permission to anonymize documents and comply with relevant data protection laws.
