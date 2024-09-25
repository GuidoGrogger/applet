import os
import uuid
import logging
import json

from datetime import datetime
from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    send_file,
    json as flask_json,
)
from flask_talisman import Talisman
from werkzeug.utils import secure_filename


from app.ai_manager import generate_html_from_prompt, transcribe_audio
from app.file_manager import (
    load_and_format_initial_prompt,
    load_and_format_change_prompt,
    save_html_files,
    save_local_storage,
    save_transcription,
)


app = Flask(__name__)

# Configuration
app.config['UPLOAD_DIR'] = os.path.abspath(os.getenv('UPLOAD_DIR', 'applets'))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
os.makedirs(app.config['UPLOAD_DIR'], exist_ok=True)


# Security
talisman = Talisman(app, force_https=False, content_security_policy={
    'default-src': ["'self'"],
    'script-src': ["'self'", "'unsafe-inline'"],  # Allow inline scripts
    'style-src': ["'self'", 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/', "'unsafe-inline'"],  # Allow inline styles
    'font-src': ["'self'", 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/']
})

# Set up logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_applet_dir(applet_uuid):
    return os.path.join(app.config['UPLOAD_DIR'], str(applet_uuid))


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/applet/<uuid:applet_uuid>', methods=['GET'])
def show_applet(applet_uuid):
    applet_dir = get_applet_dir(applet_uuid)
    if not os.path.exists(applet_dir):
        return jsonify({"error": "Applet not found"}), 404

    prompts = []
    try:
        for file in sorted(os.listdir(applet_dir)):
            if file.endswith('.prompt'):
                with open(os.path.join(applet_dir, file), 'r') as f:
                    prompts.append(f.read())
    except Exception as e:
        logger.error(f"Error reading prompts from {applet_dir}: {e}")
        return jsonify({"error": "Internal server error"}), 500

    return render_template('applet.html', uuid=applet_uuid, prompts=prompts)


@app.route('/applet/<uuid:applet_uuid>/html', methods=['GET', 'HEAD'])
def show_applet_html(applet_uuid):
    applet_dir = get_applet_dir(applet_uuid)
    index_file_path = os.path.join(applet_dir, 'index.html')


    if not os.path.exists(index_file_path):
        return jsonify({"error": "HTML file not found"}), 404
    

    file_mtime = os.path.getmtime(index_file_path)
    last_modified = datetime.fromtimestamp(file_mtime).strftime('%a, %d %b %Y %H:%M:%S GMT')

    if request.method == 'HEAD':
        response = app.response_class(status=200)
    else:
        response = send_file(os.path.abspath(index_file_path))

    response.headers['Last-Modified'] = last_modified

    return response

@app.route('/applet/<uuid:applet_uuid>/storage', methods=['GET', 'HEAD'])
def get_applet_storage(applet_uuid):
    applet_dir = get_applet_dir(applet_uuid)
    storage_file_path = os.path.join(applet_dir, 'storage.json')

    if not os.path.exists(storage_file_path):
        if request.method == 'HEAD':
            return '', 200
        return jsonify({}), 200

    file_mtime = os.path.getmtime(storage_file_path)
    last_modified = datetime.fromtimestamp(file_mtime).strftime('%a, %d %b %Y %H:%M:%S GMT')

    try:
        with open(storage_file_path, 'r') as f:
            storage_data = flask_json.load(f)
    except json.JSONDecodeError as e:  
        logger.error(f"JSON decoding error: {e}")
        return jsonify({}), 200  
    except Exception as e:
        logger.error(f"Error reading storage: {e}")
        return jsonify({"error": "Failed to read storage"}), 500

    response = jsonify(storage_data)
    response.headers['Last-Modified'] = last_modified
    return response



@app.route('/applet', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']

    # Validate file type
    if audio_file.mimetype not in ['audio/webm', 'audio/ogg', 'audio/wav', 'audio/mpeg', 'audio/mp3']:
        return jsonify({"error": "Invalid audio file type"}), 400

    applet_uuid = str(uuid.uuid4())
    applet_dir = get_applet_dir(applet_uuid)
    os.makedirs(applet_dir, exist_ok=True)

    # Save the audio file securely
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    file_name = secure_filename(f"{timestamp}_initial_prompt.webm")
    file_path = os.path.join(applet_dir, file_name)
    audio_file.save(file_path)

    try:
        transcription_text = transcribe_audio(file_path)
        save_transcription(transcription_text, file_path)
        formatted_prompt = load_and_format_initial_prompt(transcription_text)
        html_content, local_storage_content = generate_html_from_prompt(formatted_prompt)
        index_file_path, index_timestamp_file_path = save_html_files(html_content, applet_dir)
        if local_storage_content:
            save_local_storage(local_storage_content, applet_dir)
        
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        return jsonify({"error": "Failed to process audio"}), 500

    return jsonify({
        "message": "Audio file uploaded and processed successfully",
        "uuid": applet_uuid,
        "file_name": file_name,
        "index_file": index_file_path,
        "index_timestamp_file": index_timestamp_file_path
    }), 200


@app.route('/applet/<uuid:applet_uuid>', methods=['POST'])
def change_applet(applet_uuid):
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    applet_dir = get_applet_dir(applet_uuid)
    if not os.path.exists(applet_dir):
        return jsonify({"error": "Applet not found"}), 404

    audio_file = request.files['audio']

    # Validate file type
    if audio_file.mimetype not in ['audio/webm', 'audio/ogg', 'audio/wav', 'audio/mpeg', 'audio/mp3']:
        return jsonify({"error": "Invalid audio file type"}), 400

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    file_name = secure_filename(f"{timestamp}_change_prompt.webm")
    file_path = os.path.join(applet_dir, file_name)
    audio_file.save(file_path)

    try:
        transcription_text = transcribe_audio(file_path)
        save_transcription(transcription_text, file_path)

        current_index_path = os.path.join(applet_dir, 'index.html')
        if not os.path.exists(current_index_path):
            return jsonify({"error": "Current index.html not found"}), 404

        with open(current_index_path, 'r') as f:
            current_html_content = f.read()

        # Load current local storage from disk
        storage_file_path = os.path.join(applet_dir, 'storage.json')
        current_local_storage = {}
        if os.path.exists(storage_file_path):
            with open(storage_file_path, 'r') as f:
                current_local_storage = flask_json.load(f)

        formatted_prompt = load_and_format_change_prompt(
            transcription_text, current_html_content, current_local_storage
        )
        html_content, local_storage_content = generate_html_from_prompt(formatted_prompt)

        if html_content:
            index_file_path, _ = save_html_files(html_content, applet_dir)

        if local_storage_content:
            save_local_storage(local_storage_content, applet_dir)
        
    except Exception as e:
        logger.error(f"Error changing applet: {e}")
        return jsonify({"error": "Failed to change applet"}), 500

    return jsonify({
        "message": "Applet changed successfully",
        "uuid": str(applet_uuid),
        "file_name": file_name
    }), 200


@app.route('/applet/<uuid:applet_uuid>/storage', methods=['PUT'])
def update_applet_storage(applet_uuid):
    applet_dir = get_applet_dir(applet_uuid)
    if not os.path.exists(applet_dir):
        return jsonify({"error": "Applet not found"}), 404

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    try:
        storage_data = request.get_json()  
    except Exception as e:  
        logger.error(f"JSON decoding error: {e}")
        return jsonify({"error": "Invalid JSON"}), 400

    # Optional: Validate storage_data size
    if len(json.dumps(storage_data)) > 10 * 1024 * 1024:  # 10 MB limit
        return jsonify({"error": "Storage data too large"}), 400

    storage_file_path = os.path.join(applet_dir, 'storage.json')
    logger.info(f"Updating storage at: {storage_file_path} with data: {storage_data}")  # Log storage path and data

    try:
        with open(storage_file_path, 'w') as f:
            flask_json.dump(storage_data, f)
    except Exception as e:
        logger.error(f"Error updating storage: {e}")
        return jsonify({"error": "Failed to update storage"}), 500

    logger.info("Storage updated successfully")  # Log successful update
    return jsonify({"message": "Storage updated successfully"}), 200



@app.route('/applet/<uuid:applet_uuid>/storage', methods=['DELETE'])
def delete_applet_storage(applet_uuid):
    applet_dir = get_applet_dir(applet_uuid)
    storage_file_path = os.path.join(applet_dir, 'storage.json')

    if not os.path.exists(storage_file_path):
        return jsonify({"error": "Storage file not found"}), 404

    try:
        with open(storage_file_path, 'w') as f:
            f.write('{}')
    except Exception as e:
        logger.error(f"Error deleting storage: {e}")
        return jsonify({"error": "Failed to empty storage"}), 500

    return jsonify({"message": "Storage emptied successfully"}), 200

