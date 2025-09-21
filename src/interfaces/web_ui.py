# This is the main application file for the anonymization project.
# It handles the routing for the different web pages and the core logic
# for the anonymization process using LangGraph workflow.

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv

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

# Try to import LangGraph workflow, fallback to basic pipeline if not available
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    #from graph import anonymize_text
    USE_LANGGRAPH = False  # Temporarily disable LangGraph until we fix the hanging issue
    print("⚠️ LangGraph temporarily disabled, using basic pipeline")
except ImportError:
    USE_LANGGRAPH = False
    print("⚠️ LangGraph not available, using basic pipeline")

# Always import the basic pipeline as fallback
from agent.executor import AnonymizerPipeline

# Route for the landing page (index.html)
@app.route('/')
def index():
    """
    Renders the main landing page of the application.
    """
    return render_template('index.html')

# Route for the loading screen (loading.html)
@app.route('/loading')
def loading():
    """
    Renders the loading screen to show that processing is in progress.
    """
    return render_template('loading.html')

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
        
        # Process the file with custom entity types
        result = doc_processor.process_file_with_entities(file_path, file_type, entity_types)
        
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
        
        # Anonymize with custom entity types
        result = pipeline.anonymize(input_text, entity_types)
        
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
    This route handles the POST request for anonymizing data using LangGraph workflow.
    It can handle either text from the textarea or a file upload.
    """
    try:
        # Check if the request contains text data
        if 'text' in request.form and request.form['text'].strip():
            input_text = request.form['text'].strip()
            detector_type = request.form.get('detector', 'spacy')  # Default to spaCy
            
            print(f"Received text for anonymization: {input_text[:50]}...")
            print(f"Using detector: {detector_type}")
            
            # Process with LangGraph or fallback pipeline
            if USE_LANGGRAPH:
                # Use LangGraph workflow
                print(f"🚀 Running LangGraph workflow...")
                #result = anonymize_text(input_text, detector_type=detector_type)
                print(f"📊 LangGraph result: {result}")
                
                # Store results in session for result page
                session['anonymization_result'] = {
                    'success': result.get('success', False),
                    'original_text': result.get('original_text', input_text),
                    'anonymized_text': result.get('anonymized_text', ''),
                    'statistics': result.get('statistics', {}),
                    'replacement_mapping': result.get('replacement_mapping', {}),
                    'error_message': result.get('error_message'),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'workflow_type': 'LangGraph'
                }
                print(f"💾 Session data: {session['anonymization_result']}")
            else:
                # Use basic pipeline as fallback
                pipeline = AnonymizerPipeline(detector=detector_type)
                result = pipeline.anonymize(input_text)
                
                # Calculate statistics
                entities_found = len(result['replacement_mapping'])
                entities_anonymized = len(result['replacement_mapping'])
                
                session['anonymization_result'] = {
                    'success': True,
                    'original_text': input_text,
                    'anonymized_text': result['anonymized_text'],
                    'replacement_mapping': result['replacement_mapping'],
                    'entity_info': result.get('entity_info', {}),
                    'statistics': {
                        'detector_used': detector_type,
                        'entities_found': entities_found,
                        'entities_anonymized': entities_anonymized,
                        'processing_time': '0.5'  # Placeholder for now
                    },
                    'error_message': None,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'workflow_type': 'Basic Pipeline'
                }
                print(f"💾 Session data: {session['anonymization_result']}")
            
            # Redirect to result page
            return redirect(url_for('result'))

        # Check if the request contains a file
        elif 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                print(f"Received file for anonymization: {file.filename}")
                
                # Get file info
                detector_type = request.form.get('detector', 'spacy')
                file_extension = file.filename.split('.')[-1].lower()
                
                # Create pipeline
                pipeline = AnonymizerPipeline(detector=detector_type)
                
                # Check if this is a document that needs special processing
                if file_extension in ['pdf', 'docx', 'txt']:
                    # Save uploaded file temporarily FIRST (before reading it)
                    temp_dir = tempfile.gettempdir()
                    temp_input_path = os.path.join(temp_dir, f"input_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                    file.save(temp_input_path)
                    
                    try:
                        # Use DocumentProcessor to create anonymized document
                        doc_processor = DocumentProcessor(pipeline)
                        result = doc_processor.process_file(temp_input_path, file_extension)
                        
                        if result['success']:
                            # Store file path for download
                            session['anonymized_file_path'] = result['output_path']
                            session['anonymized_file_type'] = result.get('file_type', file_extension)
                            
                            # Get replacement details for display
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
                        # Clean up temporary input file
                        if os.path.exists(temp_input_path):
                            os.remove(temp_input_path)
                
                else:
                    # For other file types, use the old text-based approach
                    # Extract text from file using the file processor
                    file_content, error_message = extract_text_from_file(file, file.filename)
                    
                    if error_message:
                        # File processing failed
                        session['anonymization_result'] = {
                            'success': False,
                            'error_message': error_message,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'source_file': file.filename
                        }
                        return redirect(url_for('result'))
                    
                    # Continue with text-based processing for non-document files
                    if USE_LANGGRAPH:
                        #result = anonymize_text(file_content, detector_type=detector_type)
                        session['anonymization_result'] = {
                            'success': result.get('success', False),
                            'original_text': result.get('original_text', file_content),
                            'anonymized_text': result.get('anonymized_text', ''),
                            'statistics': result.get('statistics', {}),
                            'replacement_mapping': result.get('replacement_mapping', {}),
                            'error_message': result.get('error_message'),
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'workflow_type': 'LangGraph',
                            'source_file': file.filename
                        }
                    else:
                        # Use basic pipeline
                        result = pipeline.anonymize(file_content)
                        
                        # Calculate statistics
                        entities_found = len(result['replacement_mapping'])
                        entities_anonymized = len(result['replacement_mapping'])
                        
                        session['anonymization_result'] = {
                            'success': True,
                            'original_text': file_content,
                            'anonymized_text': result['anonymized_text'],
                            'statistics': {
                                'detector_used': detector_type,
                                'entities_found': entities_found,
                                'entities_anonymized': entities_anonymized,
                                'processing_time': '0.8'
                            },
                            'replacement_mapping': result['replacement_mapping'],
                            'entity_info': result['entity_info'],
                            'error_message': None,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'workflow_type': 'Basic Pipeline',
                            'source_file': file.filename
                        }
                
                return redirect(url_for('result'))
            
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
