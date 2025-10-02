from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file, flash
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import threading
import uuid
import tempfile
from typing import Dict, Tuple

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.file_processor import extract_text_from_file
from utils.document_processor import DocumentProcessor
from agent.executor import AnonymizerPipeline
from agent.tools.detectors.spacy_detector import SpacyDetector
from agent.tools.detectors.llm_detector import LLMDetector

# Load environment variables
load_dotenv()

# Configure Flask
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
static_dir = os.path.join(os.path.dirname(__file__), 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

# Persistent detector instances for reuse across requests
persistent_spacy_detector = SpacyDetector()
persistent_llm_detector = LLMDetector()

# Global task tracking for background processing
background_tasks = {}


# ==================== CORE ROUTES ====================

@app.route('/')
def index():
    """Render main landing page."""
    return render_template('index.html')


@app.route('/entity-selection')
def entity_selection():
    """Render entity selection page for custom anonymization."""
    return render_template('entity_selection.html')


@app.route('/result')
def result():
    """Render results page with anonymization output."""
    task_id = session.get('task_id')
    
    if not task_id or task_id not in background_tasks:
        return redirect(url_for('index'))
    
    task = background_tasks[task_id]
    result_data = task.get('result', {})
    
    if not result_data or not result_data.get('success', False):
        return redirect(url_for('index'))
    
    # Store result in session
    session['anonymization_result'] = result_data
    
    # Store file path for download if applicable
    if result_data.get('has_file_download') and result_data.get('output_path'):
        session['anonymized_file_path'] = result_data['output_path']
    
    # Format changes for template
    replacement_mapping = result_data.get('replacement_mapping', {})
    entity_info = result_data.get('entity_info', {})
    changes = [
        {
            'type': entity_info.get(original, 'UNKNOWN'),
            'original': original,
            'replacement': replacement
        }
        for original, replacement in replacement_mapping.items()
    ]
    
    return render_template(
        'result.html',
        result=result_data,
        stats=result_data.get('statistics', {}),
        original_text=result_data.get('original_text', ''),
        anonymized_text=result_data.get('anonymized_text', ''),
        success=result_data.get('success', False),
        error_message=result_data.get('error_message'),
        replacement_mapping=replacement_mapping,
        changes=changes,
        workflow_type=result_data.get('workflow_type', 'Unknown')
    )


@app.route('/waiting')
def waiting():
    """Render waiting page with progress animation."""
    task_id = session.get('task_id')
    if not task_id or task_id not in background_tasks:
        return redirect(url_for('index'))
    
    return render_template('waiting.html', task_id=task_id)


# ==================== API ENDPOINTS ====================

@app.route('/task_status/<task_id>')
def task_status(task_id):
    """Get task status and progress for polling."""
    if task_id not in background_tasks:
        return jsonify({'status': 'not_found'}), 404
    
    task = background_tasks[task_id]
    elapsed = (datetime.now() - task['start_time']).total_seconds()
    
    response = {
        'status': task['status'],
        'progress': task.get('progress', 0),
        'elapsed_time': elapsed,
        'type': task.get('type', 'unknown'),
        'detected_language': task.get('detected_language'),
        'will_use_llm': task.get('will_use_llm', False),
        'auto_switched_to_llm': task.get('auto_switched_to_llm', False)
    }
    
    # Include error details if task failed
    if task['status'] == 'error' and 'result' in task:
        result = task['result']
        response['error_message'] = result.get('error_message', 'Unknown error')
        response['error_details'] = result.get('error', 'No details available')
    
    app.logger.info(f"Task {task_id} status: {task['status']}, progress: {task.get('progress', 0)}")
    
    return jsonify(response)


@app.route('/download')
def download_file():
    """Download anonymized document file."""
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


# ==================== ANONYMIZATION ROUTES ====================

@app.route('/anonymize', methods=['POST'])
def anonymize():
    """Handle standard anonymization for text or files."""
    detector_type = request.form.get('detector', 'spacy')
    
    # Check for text input
    input_text = request.form.get('text', '').strip()
    if input_text:
        return _start_text_task(input_text, detector_type, 'text')
    
    # Check for file upload
    elif 'file' in request.files and request.files['file'].filename:
        return _start_file_task(request.files['file'], detector_type, 'file')
    
    else:
        flash('Please provide text or upload a file to anonymize.', 'error')
        return redirect(url_for('index'))


@app.route('/custom-anonymize', methods=['POST'])
def custom_anonymize():
    """Handle custom anonymization with selected entity types."""
    try:
        entity_types = request.form.getlist('entity_types')
        detection_method = request.form.get('detection_method', 'spacy')
        
        app.logger.info(f"Custom anonymization - Entities: {entity_types}, Method: {detection_method}")
        
        # Check for text input
        if 'text' in request.form and request.form['text'].strip():
            input_text = request.form['text'].strip()
            return _start_text_task(input_text, detection_method, 'custom_text', entity_types)
        
        # Check for file upload
        elif 'file' in request.files and request.files['file'].filename:
            return _start_file_task(request.files['file'], detection_method, 'custom_file', entity_types)
        
        else:
            return jsonify({'success': False, 'error': 'No text or file provided'})
    
    except Exception as e:
        app.logger.error(f"Error in custom anonymization: {e}")
        return jsonify({'success': False, 'error': f'An error occurred: {str(e)}'})


# ==================== HELPER FUNCTIONS ====================

def _start_text_task(input_text: str, detector_type: str, task_type: str, entity_types=None) -> str:
    """Start background task for text anonymization."""
    task_id = str(uuid.uuid4())
    background_tasks[task_id] = {
        'status': 'queued',
        'progress': 0,
        'start_time': datetime.now(),
        'type': task_type,
    }
    
    # Choose appropriate worker function
    if entity_types:
        worker = run_custom_anonymization_task
        args = (task_id, input_text, entity_types, detector_type, 'text')
    else:
        worker = run_anonymization_task
        args = (task_id, input_text, detector_type, 'text')
    
    thread = threading.Thread(target=worker, args=args)
    thread.start()
    
    session['task_id'] = task_id
    return redirect(url_for('waiting'))


def _start_file_task(file, detector_type: str, task_type: str, entity_types=None):
    """Start background task for file anonymization."""
    filename = file.filename
    
    # Validate file type
    allowed_extensions = ['txt', 'docx', 'pdf']
    file_extension = filename.split('.')[-1].lower() if '.' in filename else ''
    
    if file_extension not in allowed_extensions:
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload TXT, DOCX, or PDF files.'})
        else:
            flash('Invalid file type. Please upload TXT, DOCX, or PDF files.', 'error')
            return redirect(url_for('index'))
    
    # Save uploaded file temporarily
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, filename)
    
    try:
        file.save(temp_file_path)
        
        task_id = str(uuid.uuid4())
        background_tasks[task_id] = {
            'status': 'queued',
            'progress': 0,
            'start_time': datetime.now(),
            'type': task_type,
        }
        
        # Choose appropriate worker function
        if entity_types:
            worker = run_custom_anonymization_task
            args = (task_id, (temp_file_path, filename), entity_types, detector_type, 'file')
        else:
            worker = run_anonymization_task
            args = (task_id, (temp_file_path, filename), detector_type, 'file')
        
        thread = threading.Thread(target=worker, args=args)
        thread.start()
        
        session['task_id'] = task_id
        return redirect(url_for('waiting'))
    
    except Exception as e:
        app.logger.error(f"File upload error: {e}")
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': False, 'error': 'Error processing uploaded file.'})
        else:
            flash('Error processing uploaded file.', 'error')
            return redirect(url_for('index'))


def _detect_language_from_text(text: str) -> str:
    """Detect language from text."""
    detector = SpacyDetector()
    return detector._detect_language(text)


def _select_pipeline(detector_type: str, detected_language: str) -> Tuple[AnonymizerPipeline, str]:
    """
    Select appropriate pipeline based on detector type and language.
    
    Returns: (pipeline, actual_detector_used)
    """
    # Auto-switch to LLM for Arabic
    if detected_language == 'ar' or detector_type == 'llm':
        return AnonymizerPipeline(detector=persistent_llm_detector), 'llm'
    elif detector_type == 'spacy':
        return AnonymizerPipeline(detector=persistent_spacy_detector), detector_type
    else:
        return AnonymizerPipeline(detector='spacy'), 'spacy'


def infer_entity_type(text: str, entity_types: list) -> str:
    """Infer entity type based on text content and available entity types."""
    import re
    
    # Email pattern
    if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', text) and 'EMAIL' in entity_types:
        return 'EMAIL'
    
    # Phone pattern
    if re.match(r'^[\+]?[1-9]?[0-9]{7,15}$', re.sub(r'[\s\-\(\)]', '', text)) and 'PHONE' in entity_types:
        return 'PHONE'
    
    # Age pattern
    if re.match(r'^\d{1,3}\s*(years?|yrs?|y\.o\.|years old)$', text.lower()) and 'AGE' in entity_types:
        return 'AGE'
    
    # Organization indicators
    org_indicators = ['corp', 'inc', 'ltd', 'llc', 'company', 'corporation', 'university', 'college']
    if any(indicator in text.lower() for indicator in org_indicators) and 'ORGANIZATION' in entity_types:
        return 'ORGANIZATION'
    
    # Default to PERSON if available, otherwise first available type
    if 'PERSON' in entity_types:
        return 'PERSON'
    elif entity_types:
        return entity_types[0]
    else:
        return 'ENTITY'


def _build_result(success: bool, result: Dict, processing_time: float, 
                  actual_detector_used: str, workflow_type: str, 
                  filename: str = None) -> Dict:
    """Build standardized result dictionary."""
    if not success:
        return {
            'success': False,
            'error_message': result.get('error', 'Processing failed'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source_file': filename
        }
    
    replacement_mapping = result.get('replacement_mapping', {})
    entity_info = result.get('entity_info', {})
    
    # Extract text content for display - handle both text and file processing
    original_text = result.get('original_text', '')
    anonymized_text = result.get('anonymized_text', '')
    
    # For text processing, ensure we have the original text
    if not original_text and not filename:
        # If this is text processing and no original_text in result, 
        # we need to get it from the input
        original_text = result.get('input_text', '')
    
    # If no anonymized_text but we have original_text and replacements, generate it
    if not anonymized_text and original_text and replacement_mapping:
        anonymized_text = original_text
        for original, replacement in replacement_mapping.items():
            anonymized_text = anonymized_text.replace(original, replacement)
    
    result_dict = {
        'success': True,
        'original_text': original_text,
        'anonymized_text': anonymized_text,
        'replacement_mapping': replacement_mapping,
        'entity_info': entity_info,
        'statistics': {
            'detector_used': actual_detector_used,
            'entities_found': len(replacement_mapping),
            'entities_anonymized': len(replacement_mapping),
            'processing_time': round(processing_time, 1)
        },
        'error_message': None,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'workflow_type': workflow_type
    }
    
    # Add file-specific fields
    if filename:
        result_dict.update({
            'source_file': filename,
            'output_file': os.path.basename(result['output_path']) if result.get('output_path') else f"anonymized_{filename}",
            'has_file_download': True,
            'message': result.get('message', 'Document processed successfully'),
            'output_path': result.get('output_path', ''),
            'file_type': result.get('file_type', filename.split('.')[-1].lower())
        })
    
    return result_dict


# ==================== BACKGROUND WORKERS ====================

def run_anonymization_task(task_id: str, input_data, detector_type: str, data_type: str):
    """Run standard anonymization in background thread."""
    global background_tasks
    
    try:
        background_tasks[task_id]['status'] = 'processing'
        background_tasks[task_id]['progress'] = 10
        processing_start = datetime.now()
        
        # Detect language
        if data_type == 'text':
            detected_language = _detect_language_from_text(input_data)
            background_tasks[task_id]['detected_language'] = detected_language
        else:
            # Extract text from file to detect language
            file_path, filename = input_data
            try:
                with open(file_path, 'rb') as file_obj:
                    extracted_text, _ = extract_text_from_file(file_obj, filename)
                detected_language = _detect_language_from_text(extracted_text) if extracted_text else 'unknown'
            except:
                detected_language = 'unknown'
            background_tasks[task_id]['detected_language'] = detected_language
        
        # Update task metadata
        will_use_llm = detector_type == 'llm' or detected_language == 'ar'
        auto_switched_to_llm = detected_language == 'ar' and detector_type != 'llm'
        background_tasks[task_id]['will_use_llm'] = will_use_llm
        background_tasks[task_id]['auto_switched_to_llm'] = auto_switched_to_llm
        
        # Select pipeline
        pipeline, actual_detector_used = _select_pipeline(detector_type, detected_language)
        
        # Process based on data type
        if data_type == 'text':
            background_tasks[task_id]['progress'] = 30
            print(f"[DEBUG] Calling pipeline.anonymize with text: {input_data[:100]}...")
            result = pipeline.anonymize(input_data)
            print(f"[DEBUG] Pipeline returned: {result}")
            processing_time = (datetime.now() - processing_start).total_seconds()
            
            # Ensure original text is preserved for text processing
            if isinstance(result, dict) and result.get('success', False):
                if 'original_text' not in result:
                    result['original_text'] = input_data
                if 'input_text' not in result:
                    result['input_text'] = input_data
            
            result_dict = _build_result(
                result.get('success', False),
                result,
                processing_time,
                actual_detector_used,
                'Background Pipeline'
            )
            print(f"[DEBUG] Built result dict - original_text: {result_dict.get('original_text', 'MISSING')[:100] if result_dict.get('original_text') else 'MISSING'}")
        
        else:  # file processing
            file_path, filename = input_data
            file_extension = filename.split('.')[-1].lower()

            background_tasks[task_id]['progress'] = 30

            print(f"[DEBUG] Processing file: {filename}, extension: {file_extension}, path: {file_path}")

            # Auto-switch to LLM for Arabic files
            if detected_language == 'ar' and actual_detector_used != 'llm':
                pipeline = AnonymizerPipeline(detector=persistent_llm_detector)
                actual_detector_used = 'llm'
                background_tasks[task_id]['auto_switched_to_llm'] = True

            print(f"[DEBUG] Creating DocumentProcessor with pipeline: {pipeline}")
            doc_processor = DocumentProcessor(pipeline)
            background_tasks[task_id]['progress'] = 50

            print(f"[DEBUG] Calling process_file with {file_path}, {file_extension}")
            result = doc_processor.process_file(file_path, file_extension)
            print(f"[DEBUG] process_file returned: {result}")
            processing_time = (datetime.now() - processing_start).total_seconds()

            # Extract entity info - PRIORITIZE the result's entity_info over the replacer
            entity_info = result.get('entity_info', {})
            print(f"[DEBUG] Entity info from result: {entity_info}")
            # Only use replacer if result doesn't have entity_info
            if not entity_info and hasattr(doc_processor.pipeline.replacer, 'get_replacements_with_types'):
                replacement_details = doc_processor.pipeline.replacer.get_replacements_with_types()
                for original, replacement, entity_type in replacement_details:
                    entity_info[original] = entity_type
                print(f"[DEBUG] Entity info from replacer (fallback): {entity_info}")

            # If still no entity_info, infer from replacement mapping
            if not entity_info and 'replacement_mapping' in result:
                # Make sure the infer_entity_type function exists
                for original in result['replacement_mapping'].keys():
                    entity_info[original] = infer_entity_type(original, ['PERSON', 'EMAIL', 'PHONE', 'LOCATION', 'ORGANIZATION', 'AGE'])
                print(f"[DEBUG] Entity info using inference: {entity_info}")

            print(f"[DEBUG] Final entity info: {entity_info}")
            result['entity_info'] = entity_info
            result_dict = _build_result(
                result.get('success', False),
                result,
                processing_time,
                actual_detector_used,
                'Document Processing',
                filename
            )
        
        # Update task with result
        background_tasks[task_id].update({
            'status': 'completed' if result_dict['success'] else 'error',
            'progress': 100 if result_dict['success'] else 0,
            'result': result_dict
        })
    
    except Exception as e:
        app.logger.error(f"Background task error: {str(e)}")
        background_tasks[task_id].update({
            'status': 'error',
            'progress': 0,
            'result': {
                'success': False,
                'error_message': f'Processing failed: {str(e)}',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })


def run_custom_anonymization_task(task_id: str, input_data, entity_types: list, 
                                   detection_method: str, data_type: str = 'text'):
    """Run custom anonymization with selected entity types in background thread."""
    global background_tasks
    
    try:
        background_tasks[task_id]['status'] = 'processing'
        background_tasks[task_id]['progress'] = 10
        processing_start = datetime.now()
        
        # Debug entity types
        print(f"[DEBUG] Custom anonymization - Entity types selected: {entity_types}")
        print(f"[DEBUG] Data type: {data_type}, Detection method: {detection_method}")
        
        # Detect language
        if data_type == 'text':
            detected_language = _detect_language_from_text(input_data)
        else:
            file_path, filename = input_data
            try:
                with open(file_path, 'rb') as file_obj:
                    extracted_text, _ = extract_text_from_file(file_obj, filename)
                detected_language = _detect_language_from_text(extracted_text) if extracted_text else 'unknown'
            except:
                detected_language = 'unknown'
        
        background_tasks[task_id]['detected_language'] = detected_language
        background_tasks[task_id]['will_use_llm'] = detected_language == 'ar' or detection_method == 'llm'
        
        # Select pipeline
        pipeline, actual_detector_used = _select_pipeline(detection_method, detected_language)
        
        background_tasks[task_id]['progress'] = 30
        
        # Process based on data type
        if data_type == 'text':
            print(f"[DEBUG] Processing text with entity types: {entity_types}")
            result = pipeline.anonymize(input_data, entity_types)
            processing_time = (datetime.now() - processing_start).total_seconds()
            
            # Ensure original text is preserved
            if isinstance(result, dict) and result.get('success', False):
                if 'original_text' not in result:
                    result['original_text'] = input_data
            
            if result.get('success', False):
                result_dict = {
                    'success': True,
                    'original_text': result.get('original_text', input_data),
                    'anonymized_text': result['anonymized_text'],
                    'replacement_mapping': result['replacement_mapping'],
                    'entity_info': result.get('entity_info', {}),
                    'statistics': {
                        'entities_found': len(result.get('replacement_mapping', {})),
                        'entities_anonymized': len(result.get('replacement_mapping', {})),
                        'entity_types_found': len(set(result.get('entity_info', {}).values())),
                        'selected_entity_types': entity_types,
                        'detection_method': actual_detector_used,
                        'processing_time': round(processing_time, 1)
                    },
                    'workflow_type': f'Custom Text ({actual_detector_used.upper()})'
                }
            else:
                result_dict = {
                    'success': False,
                    'error_message': result.get('error', 'Processing failed')
                }
        
        else:  # file processing
            file_path, filename = input_data
            file_extension = filename.split('.')[-1].lower()
            
            print(f"[DEBUG] Processing file: {filename} with entity types: {entity_types}")
            
            # Auto-switch to LLM for Arabic files
            if detected_language == 'ar' and actual_detector_used != 'llm':
                pipeline = AnonymizerPipeline(detector=persistent_llm_detector)
                actual_detector_used = 'llm'
                background_tasks[task_id]['auto_switched_to_llm'] = True
            
            doc_processor = DocumentProcessor(pipeline)
            background_tasks[task_id]['progress'] = 50
            
            # Use process_file_with_entities and pass the entity_types
            print(f"[DEBUG] Calling process_file_with_entities with entity_types: {entity_types}")
            result = doc_processor.process_file_with_entities(file_path, file_extension, entity_types)
            processing_time = (datetime.now() - processing_start).total_seconds()
            
            print(f"[DEBUG] File processing result: {result.get('success')}, entities: {len(result.get('replacement_mapping', {}))}")
            
            if result.get('success', False):
                # Extract entity info - FIXED: Get proper entity types from result
                entity_info = result.get('entity_info', {})
                print(f"[DEBUG] Entity info from result: {entity_info}")
                
                # If entity_info is empty but we have replacement_mapping, try to get types from pipeline
                if not entity_info and hasattr(doc_processor.pipeline.replacer, 'get_replacements_with_types'):
                    replacement_details = doc_processor.pipeline.replacer.get_replacements_with_types()
                    for original, replacement, entity_type in replacement_details:
                        # Only include entities that match the selected types
                        if entity_type in entity_types:
                            entity_info[original] = entity_type
                        else:
                            print(f"[DEBUG] Filtered out entity type: {entity_type} (not in selected types)")
                
                replacement_mapping = result.get('replacement_mapping', {})
                
                # Filter replacement mapping to only include selected entity types
                filtered_replacement_mapping = {}
                filtered_entity_info = {}
                
                for original, replacement in replacement_mapping.items():
                    entity_type = entity_info.get(original)
                    # If entity_type is not found, try to infer it or use default
                    if not entity_type:
                        # Try to infer entity type based on content or use default
                        entity_type = infer_entity_type(original, entity_types)
                        print(f"[DEBUG] Inferred entity type for '{original}': {entity_type}")
                    
                    if entity_type in entity_types:
                        filtered_replacement_mapping[original] = replacement
                        filtered_entity_info[original] = entity_type
                    else:
                        print(f"[DEBUG] Filtered out replacement: {original} -> {replacement} (type: {entity_type})")
                
                print(f"[DEBUG] Original replacement mapping count: {len(replacement_mapping)}")
                print(f"[DEBUG] Filtered replacement mapping count: {len(filtered_replacement_mapping)}")
                print(f"[DEBUG] Final entity info: {filtered_entity_info}")
                
                result_dict = {
                    'success': True,
                    'original_text': result['original_text'],
                    'anonymized_text': result['anonymized_text'],
                    'replacement_mapping': filtered_replacement_mapping,
                    'entity_info': filtered_entity_info,
                    'statistics': {
                        'entities_found': len(filtered_replacement_mapping),
                        'entities_anonymized': len(filtered_replacement_mapping),
                        'entity_types_found': len(set(filtered_entity_info.values())),
                        'selected_entity_types': entity_types,
                        'detection_method': actual_detector_used,
                        'processing_time': round(processing_time, 1)
                    },
                    'workflow_type': f'Custom File ({actual_detector_used.upper()})',
                    'source_file': filename,
                    'output_file': os.path.basename(result['output_path']),
                    'has_file_download': True,
                    'output_path': result['output_path'],
                    'file_type': result.get('file_type', file_extension)
                }
            else:
                result_dict = {
                    'success': False,
                    'error_message': result.get('error', 'Processing failed')
                }
        
        # Update task with result
        background_tasks[task_id].update({
            'status': 'completed' if result_dict['success'] else 'error',
            'progress': 100 if result_dict['success'] else 0,
            'result': result_dict
        })
    
    except Exception as e:
        app.logger.error(f"Background custom task error: {str(e)}")
        import traceback
        traceback.print_exc()
        background_tasks[task_id].update({
            'status': 'error',
            'progress': 0,
            'result': {
                'success': False,
                'error_message': f'Processing failed: {str(e)}'
            }
        })


# Add margin to the bottom of the page
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.context_processor
def inject_margin():
    return {'margin_bottom': 'mb-6'}


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)