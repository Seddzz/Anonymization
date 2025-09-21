# Setup Guide

## Installation and Setup

### Prerequisites
- Python 3.8+
- pip package manager
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/anonymization.git
cd anonymization
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r docker/requirements.txt
```

### 4. Environment Configuration
Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

Edit `.env` with your API keys:
```
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 5. Initialize Data Directories
```bash
mkdir -p src/data/raw
mkdir -p src/data/processed
mkdir -p src/data/vectorstore
mkdir -p logs
mkdir -p temp
mkdir -p output
```

### 6. Run Tests
```bash
python -m pytest tests/
```

### 7. Start the Application

#### Web Interface
```bash
python -m src.interfaces.web_ui
```
Access at: http://localhost:5000

#### CLI Interface
```bash
python -m src.interfaces.cli --help
```

#### API Server
```bash
python -m src.interfaces.api
```

### 8. Docker Setup (Optional)
```bash
cd docker
docker-compose up -d
```

## Configuration

### Agent Configuration
Edit `src/configs/agent_config.yaml`:
```yaml
agent:
  default_detector: "spacy"
  default_replacer: "faker"
  memory_enabled: true
  
models:
  llm_provider: "openai"
  llm_model: "gpt-3.5-turbo"
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
```

### Logging
Logs are written to `logs/app.log` by default.
Configure log level in `.env`:
```
LOG_LEVEL=INFO
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure PYTHONPATH includes src directory
   - Check virtual environment activation

2. **API Key Issues**
   - Verify `.env` file configuration
   - Check API key validity

3. **Memory Issues**
   - Increase MAX_FILE_SIZE in `.env`
   - Clear vector store cache

### Getting Help
- Check logs in `logs/` directory
- Run with debug mode: `FLASK_DEBUG=True`
- Submit issues on GitHub