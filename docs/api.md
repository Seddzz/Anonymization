# API Documentation

## Anonymization API

### Overview
The Anonymization API provides endpoints for anonymizing sensitive information in text and documents using AI-powered detection and replacement techniques.

### Base URL
```
http://localhost:5000
```

### Endpoints

#### 1. Anonymize Text
**POST** `/api/anonymize/text`

Anonymize plain text input.

**Request Body:**
```json
{
    "text": "string",
    "detector": "spacy|llm", 
    "entity_types": ["PERSON", "ORG", "GPE"]
}
```

**Response:**
```json
{
    "success": true,
    "original_text": "string",
    "anonymized_text": "string",
    "entities_found": 5,
    "replacement_mapping": {},
    "processing_time": 0.5
}
```

#### 2. Anonymize Document
**POST** `/api/anonymize/document`

Anonymize uploaded documents (PDF, DOCX, TXT).

**Request:**
- Content-Type: `multipart/form-data`
- File: document file
- detector: detection method
- entity_types: optional entity types filter

**Response:**
```json
{
    "success": true,
    "download_url": "/api/download/{file_id}",
    "entities_found": 10,
    "processing_time": 2.1
}
```

#### 3. Download Anonymized File
**GET** `/api/download/{file_id}`

Download processed document.

**Response:**
- Content-Type: `application/octet-stream`
- File download

### Error Responses
```json
{
    "success": false,
    "error": "Error message",
    "code": 400
}
```

### Status Codes
- 200: Success
- 400: Bad Request
- 500: Internal Server Error