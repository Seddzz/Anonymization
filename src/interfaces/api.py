"""
REST API interface for the anonymization system.
"""

import sys
import os
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import tempfile
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent.executor import AnonymizerPipeline
from utils.document_processor import DocumentProcessor

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'anonymization-api',
        'version': '1.0.0'
    })


@app.route('/api/anonymize/text', methods=['POST'])
def anonymize_text():
    """Anonymize plain text input."""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'Text field is required'
            }), 400
        
        text = data['text']
        detector = data.get('detector', 'spacy')
        entity_types = data.get('entity_types')
        
        # Create pipeline
        pipeline = AnonymizerPipeline(detector=detector)
        
        # Process text
        result = pipeline.anonymize(text, entity_types)
        
        return jsonify({
            'success': True,
            'original_text': text,
            'anonymized_text': result['anonymized_text'],
            'entities_found': len(result['replacement_mapping']),
            'replacement_mapping': result['replacement_mapping'],
            'entity_info': result.get('entity_info', {}),
            'processing_time': 0.5  # Placeholder
        })
        
    except Exception as e:
        logger.error(f"Error in text anonymization: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/anonymize/document', methods=['POST'])
def anonymize_document():
    """Anonymize uploaded document."""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        detector = request.form.get('detector', 'spacy')
        entity_types = request.form.getlist('entity_types')
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)
        
        # Determine file type
        file_extension = os.path.splitext(filename)[1].lower()
        
        # Create pipeline and processor
        pipeline = AnonymizerPipeline(detector=detector)
        doc_processor = DocumentProcessor(pipeline)
        
        # Process document
        if entity_types:
            result = doc_processor.process_file_with_entities(file_path, file_extension[1:], entity_types)
        else:
            result = doc_processor.process_file(file_path, file_extension[1:])
        
        if result['success']:
            return jsonify({
                'success': True,
                'download_url': f"/api/download/{os.path.basename(result['output_path'])}",
                'entities_found': len(result.get('replacement_mapping', {})),
                'processing_time': 2.0  # Placeholder
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Processing failed')
            }), 500
        
    except Exception as e:
        logger.error(f"Error in document anonymization: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download anonymized file."""
    try:
        # In a real implementation, you'd store file paths securely
        # This is a simplified version
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, secure_filename(filename))
        
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)