# This is the main application file for the anonymization project.
# It handles the routing for the different web pages and the core logic
# for the anonymization process using the pipeline architecture.

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
import threading
import uuid
import time

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.file_processor import extract_text_from_file
from utils.document_processor import DocumentProcessor
from agent.executor import AnonymizerPipeline
import tempfile

# Load environment variables (including PYTHONDONTWRITEBYTECODE=1)
load_dotenv()

# Configure Flask with correct template and static folders
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
static_dir = os.path.join(os.path.dirname(__file__), 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = 'your-secret-key-change-in-production'  # For session management

# Import the anonymization pipeline
from agent.executor import AnonymizerPipeline

# Global task tracking for background processing
background_tasks = {}

def run_anonymization_task(task_id, input_data, detector_type, data_type):
    """Run anonymization in background thread"""
    global background_tasks
    
    try:
        background_tasks[task_id]['status'] = 'processing'
        background_tasks[task_id]['progress'] = 10
        
        # Always use the detector selected by the user
        pipeline = AnonymizerPipeline(detector=detector_type)
        if data_type == 'text':
            # Process text (LLM allowed for short text)
            background_tasks[task_id]['progress'] = 30
            result = pipeline.anonymize(input_data)
            
            # Calculate statistics
            entities_found = len(result['replacement_mapping'])
            
            # Store result
            background_tasks[task_id].update({
                'status': 'completed',
                'progress': 100,
                'result': {
                    'success': True,
                    'original_text': input_data,
                    'anonymized_text': result['anonymized_text'],
                    'replacement_mapping': result['replacement_mapping'],
                    'entity_info': result.get('entity_info', {}),
                    'statistics': {
                        'detector_used': detector_type,
                        'entities_found': entities_found,
                        'entities_anonymized': entities_found,
                        'processing_time': '30.0' if detector_type == 'llm' else '2.0'
                    },
                    'error_message': None,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'workflow_type': 'Background Pipeline'
                }
            })
            
        else:  # file processing
            background_tasks[task_id]['progress'] = 20
            
            # input_data is the file path for file processing
            file_path, filename = input_data
            file_extension = filename.split('.')[-1].lower()
            if file_extension in ['pdf', 'docx', 'txt']:
                background_tasks[task_id]['progress'] = 50
                # Use DocumentProcessor
                doc_processor = DocumentProcessor(pipeline)
                result = doc_processor.process_file(file_path, file_extension)
                
                if result['success']:
                    replacement_mapping = result.get('replacement_mapping', {})
                    entity_info = {}
                    
                    if hasattr(pipeline.replacer, 'get_replacements_with_types'):
                        replacement_details = pipeline.replacer.get_replacements_with_types()
                        for original, replacement, entity_type in replacement_details:
                            entity_info[original] = entity_type
                    
                    background_tasks[task_id].update({
                        'status': 'completed',
                        'progress': 100,
                        'result': {
                            'success': True,
                            'original_text': result['original_text'],
                            'anonymized_text': result['anonymized_text'],
                            'statistics': {
                                'detector_used': detector_type,
                                'entities_found': len(replacement_mapping),
                                'entities_anonymized': len(replacement_mapping),
                                'processing_time': '30.0' if detector_type == 'llm' else '3.0'
                            },
                            'replacement_mapping': replacement_mapping,
                            'entity_info': entity_info,
                            'error_message': None,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'workflow_type': 'Document Processing',
                            'source_file': filename,
                            'output_file': os.path.basename(result['output_path']),
                            'has_file_download': True,
                            'message': result.get('message', 'Document processed successfully'),
                            'output_path': result['output_path']
                        }
                    })
                else:
                    background_tasks[task_id].update({
                        'status': 'error',
                        'progress': 0,
                        'result': {
                            'success': False,
                            'error_message': result.get('error', 'Document processing failed'),
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'source_file': filename
                        }
                    })
            
    except Exception as e:
        print(f"Background task error: {str(e)}")
        background_tasks[task_id].update({
            'status': 'error',
            'progress': 0,
            'result': {
                'success': False,
                'error_message': f'Processing failed: {str(e)}',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })

# Route for the landing page (index.html)
@app.route('/')
def index():
    """
    Renders the main landing page of the application.
    """
    return render_template('index.html')


@app.route('/task_status/<task_id>')
def task_status(task_id):
    """
    API endpoint to check task status and progress.
    Returns JSON with current task state.
    """
    if task_id not in background_tasks:
        return jsonify({'status': 'not_found'}), 404
    
    task = background_tasks[task_id]
    
    # Calculate elapsed time
    elapsed = (datetime.now() - task['start_time']).total_seconds()
    
    return jsonify({
        'status': task['status'],
        'progress': task.get('progress', 0),
        'elapsed_time': elapsed,
        'type': task.get('type', 'unknown')
    })

# Route for the results page (result.html)
@app.route('/result')
def result():
    """
    Renders the results page to display the anonymized text.
    Gets data from session that was stored during the anonymization process.
    """
    # Get results from session
    result_data = session.get('anonymization_result', {})
    
    if not result_data:
        # No results available, redirect to index
        return redirect(url_for('index'))
    
    # Format replacement mapping for template
    changes = []
    replacement_mapping = result_data.get('replacement_mapping', {})
    entity_info = result_data.get('entity_info', {})
    
    for original, replacement in replacement_mapping.items():
        entity_type = entity_info.get(original, 'UNKNOWN')
        changes.append({
            'type': entity_type,
            'original': original,
            'replacement': replacement
        })
    
    return render_template('result.html', 
                         result=result_data,
                         stats=result_data.get('statistics', {}),
                         original_text=result_data.get('original_text', ''),
                         anonymized_text=result_data.get('anonymized_text', ''),
                         success=result_data.get('success', False),
                         error_message=result_data.get('error_message'),
                         replacement_mapping=replacement_mapping,
                         changes=changes,  # Add the formatted changes
                         workflow_type=result_data.get('workflow_type', 'Unknown'))

# Route for the entity selection page
@app.route('/entity-selection')
def entity_selection():
    """
    Renders the entity selection page where users can choose which types
    of entities to detect and anonymize.
    """
    return render_template('entity_selection.html')

# Route to handle custom anonymization with selected entities
@app.route('/custom-anonymize', methods=['POST'])
def custom_anonymize():
    """
    This route handles the POST request for anonymizing data with custom entity selection.
    It can handle either text from the textarea or a file upload.
    """
    try:
        # Get selected entity types
        entity_types = request.form.getlist('entity_types')
        detection_method = request.form.get('detection_method', 'llm')
        
        print(f"Custom anonymization with entity types: {entity_types}")
        print(f"Using detection method: {detection_method}")
        
        # Check if text was provided
        if 'text' in request.form and request.form['text'].strip():
            input_text = request.form['text'].strip()
            return handle_custom_text_input(input_text, entity_types, detection_method)
        
        # Check if file was uploaded
        elif 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            return handle_custom_file_upload(file, entity_types, detection_method)
        
        else:
            return jsonify({'success': False, 'error': 'No text or file provided'})
            
    except Exception as e:
        print(f"❌ Error in custom anonymization: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'An error occurred during custom anonymization: {str(e)}'
        })

def handle_custom_file_upload(file, entity_types, detection_method):
    """Handle file upload with custom entity selection"""
    try:
        # Save uploaded file temporarily
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)
        file.save(file_path)
        
        print(f"Custom processing file: {file.filename}")
        print(f"Entity types: {entity_types}")
        print(f"Detection method: {detection_method}")
        
        # Determine file type
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension == '.txt':
            file_type = 'txt'
        elif file_extension == '.pdf':
            file_type = 'pdf'
        elif file_extension in ['.docx', '.doc']:
            file_type = 'docx'
        else:
            return jsonify({'success': False, 'error': 'Unsupported file type'})
        
        # Create pipeline with selected detection method
        pipeline = AnonymizerPipeline(detector=detection_method)
        
        # Create document processor
        doc_processor = DocumentProcessor(pipeline)
        
        # Process the file with custom entity types (with timeout handling)
        try:
            print(f"🚀 Starting {detection_method.upper()} processing for file: {file.filename}")
            result = doc_processor.process_file_with_entities(file_path, file_type, entity_types)
            print(f"✅ {detection_method.upper()} processing completed successfully")
        except Exception as e:
            print(f"❌ Error during {detection_method.upper()} processing: {e}")
            return jsonify({
                'success': False, 
                'error': f'Processing failed with {detection_method.upper()}. Try SpaCy instead or contact support.',
                'details': str(e)
            })
        
        if result['success']:
            # Store results in session with proper download support
            session['anonymization_result'] = {
                'success': True,
                'original_text': result['original_text'],
                'anonymized_text': result['anonymized_text'],
                'replacement_mapping': result['replacement_mapping'],
                'entity_info': result.get('entity_info', {}),
                'statistics': {
                    'entities_found': len(result['replacement_mapping']),
                    'entities_anonymized': len(result['replacement_mapping']),
                    'entity_types_found': len(set(result.get('entity_info', {}).values())),
                    'selected_entity_types': entity_types,
                    'detection_method': detection_method,
                    'processing_time': '0.2'
                },
                'output_file': os.path.basename(result.get('output_path', '')),
                'original_file': file.filename,
                'file_type': file_type,
                'has_file_download': True,
                'workflow_type': f'Custom ({detection_method.upper()})'
            }
            
            # Store the file path in session for download route
            session['anonymized_file_path'] = result.get('output_path', '')
            
            # Clean up temp file
            try:
                os.remove(file_path)
                os.rmdir(temp_dir)
            except:
                pass  # Ignore cleanup errors
                
            return redirect(url_for('result'))
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error occurred')
            })
            
    except Exception as e:
        print(f"❌ Error processing custom file: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Error processing file: {str(e)}'
        })

def handle_custom_text_input(input_text, entity_types, detection_method):
    """Handle text input with custom entity selection"""
    try:
        print(f"Custom processing text: {input_text[:100]}...")
        print(f"Entity types: {entity_types}")
        print(f"Detection method: {detection_method}")
        
        # Create pipeline with selected detection method
        pipeline = AnonymizerPipeline(detector=detection_method)
        
        # Anonymize with custom entity types (with timeout handling)
        try:
            print(f"🚀 Starting {detection_method.upper()} processing for text input")
            result = pipeline.anonymize(input_text, entity_types)
            print(f"✅ {detection_method.upper()} processing completed successfully")
        except Exception as e:
            print(f"❌ Error during {detection_method.upper()} processing: {e}")
            return jsonify({
                'success': False, 
                'error': f'Processing failed with {detection_method.upper()}. Try SpaCy instead or contact support.',
                'details': str(e)
            })
        
        if result.get('success', True):  # Assume success if not explicitly set
            # Store results in session
            session['anonymization_result'] = {
                'success': True,
                'original_text': input_text,
                'anonymized_text': result['anonymized_text'],
                'replacement_mapping': result['replacement_mapping'],
                'entity_info': result.get('entity_info', {}),
                'statistics': {
                    'entities_found': len(result['replacement_mapping']),
                    'entities_anonymized': len(result['replacement_mapping']),
                    'entity_types_found': len(set(result.get('entity_info', {}).values())),
                    'selected_entity_types': entity_types,
                    'detection_method': detection_method,
                    'processing_time': '0.1'
                },
                'workflow_type': f'Custom Text ({detection_method.upper()})'
            }
            
            return redirect(url_for('result'))
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error occurred')
            })
            
    except Exception as e:
        print(f"❌ Error processing custom text: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Error processing text: {str(e)}'
        })

# Route to handle the anonymization process
@app.route('/anonymize', methods=['POST'])
def anonymize():
    """
    This route handles the POST request for anonymizing data.
    It starts background processing and redirects to loading page.
    """
    try:
        # Check if the request contains text data
        if 'text' in request.form and request.form['text'].strip():
            input_text = request.form['text'].strip()
            detector_type = request.form.get('detector', 'spacy')
            print(f"Received text for anonymization: {input_text[:50]}... | Detector: {detector_type}")
            pipeline = AnonymizerPipeline(detector=detector_type)
            result = pipeline.anonymize(input_text)
            entities_found = len(result['replacement_mapping'])
            session['anonymization_result'] = {
                'success': True,
                'original_text': input_text,
                'anonymized_text': result['anonymized_text'],
                'replacement_mapping': result['replacement_mapping'],
                'entity_info': result.get('entity_info', {}),
                'statistics': {
                    'detector_used': detector_type,
                    'entities_found': entities_found,
                    'entities_anonymized': entities_found,
                    'processing_time': '0.5'
                },
                'error_message': None,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'workflow_type': 'Basic Pipeline'
            }
            return redirect(url_for('result'))

        # Check if the request contains a file
        elif 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                detector_type = request.form.get('detector', 'spacy')
                file_extension = file.filename.split('.')[-1].lower()
                print(f"Received file for anonymization: {file.filename} | Detector: {detector_type}")
                temp_dir = tempfile.gettempdir()
                temp_input_path = os.path.join(temp_dir, f"input_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                file.save(temp_input_path)
                try:
                    pipeline = AnonymizerPipeline(detector=detector_type)
                    doc_processor = DocumentProcessor(pipeline)
                    result = doc_processor.process_file(temp_input_path, file_extension)
                    if result['success']:
                        session['anonymized_file_path'] = result['output_path']
                        session['anonymized_file_type'] = result.get('file_type', file_extension)
                        replacement_mapping = result.get('replacement_mapping', {})
                        entity_info = {}
                        if hasattr(pipeline.replacer, 'get_replacements_with_types'):
                            replacement_details = pipeline.replacer.get_replacements_with_types()
                            for original, replacement, entity_type in replacement_details:
                                entity_info[original] = entity_type
                        session['anonymization_result'] = {
                            'success': True,
                            'original_text': result['original_text'],
                            'anonymized_text': result['anonymized_text'],
                            'statistics': {
                                'detector_used': detector_type,
                                'entities_found': len(replacement_mapping),
                                'entities_anonymized': len(replacement_mapping),
                                'processing_time': '1.2'
                            },
                            'replacement_mapping': replacement_mapping,
                            'entity_info': entity_info,
                            'error_message': None,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'workflow_type': 'Document Processing',
                            'source_file': file.filename,
                            'output_file': os.path.basename(result['output_path']),
                            'file_type': result.get('file_type', file_extension),
                            'has_file_download': True,
                            'message': result.get('message', 'Document processed successfully')
                        }
                    else:
                        session['anonymization_result'] = {
                            'success': False,
                            'error_message': result.get('error', 'Document processing failed'),
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'source_file': file.filename
                        }
                finally:
                    if os.path.exists(temp_input_path):
                        os.remove(temp_input_path)
                return redirect(url_for('result'))
        
        # If no valid input, redirect back to index
        return redirect(url_for('index'))
        
    except Exception as e:
        print(f"Error in anonymize route: {str(e)}")
        return redirect(url_for('index'))
            
        # If no text or file was provided, redirect back to the index page.
        session['anonymization_result'] = {
            'success': False,
            'error_message': "No text or file provided for anonymization.",
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return redirect(url_for('result'))
        
    except Exception as e:
        print(f"Error in anonymization: {e}")
        session['anonymization_result'] = {
            'success': False,
            'error_message': f"An error occurred during anonymization: {str(e)}",
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return redirect(url_for('result'))

@app.route('/download')
def download_file():
    """
    Download the anonymized document file
    """
    file_path = session.get('anonymized_file_path')
    if file_path and os.path.exists(file_path):
        result_data = session.get('anonymization_result', {})
        output_filename = result_data.get('output_file', 'anonymized_document')
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype='application/octet-stream'
        )
    else:
        return redirect(url_for('result'))

if __name__ == '__main__':
    # Running the app in debug mode is useful for development.
    app.run(debug=True)
