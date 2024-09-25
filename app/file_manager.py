import os
from datetime import datetime
import json

INITIAL_PROMPT_TEMPLATE_PATH = "prompts/initial_app.prompt"
CHANGE_PROMPT_TEMPLATE_PATH = "prompts/change_app.prompt"


def save_local_storage(local_storage_content, applet_dir):
    storage_file_path = os.path.join(applet_dir, 'storage.json')
    with open(storage_file_path, 'w') as f:
        f.write(local_storage_content)  # Save the local storage content as a string


def save_html_files(html_content, applet_dir):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    index_file_path = os.path.join(applet_dir, 'index.html')
    index_timestamp_file_path = os.path.join(applet_dir, f'index-{timestamp}.html')

    with open(index_file_path, 'w') as file:
        file.write(html_content)

    with open(index_timestamp_file_path, 'w') as file:
        file.write(html_content)

    return index_file_path, index_timestamp_file_path


def save_transcription(transcription_text, file_path):
    transcription_file_path = file_path.replace(".webm", ".prompt")
    with open(transcription_file_path, "w") as text_file:
        text_file.write(transcription_text)
    return transcription_file_path


def load_and_format_initial_prompt(transcription_text):
    with open(INITIAL_PROMPT_TEMPLATE_PATH, "r") as template_file:
        prompt_template = template_file.read()
    formatted_prompt = prompt_template.replace("{description}", transcription_text)
    return formatted_prompt


def load_and_format_change_prompt(transcription_text, current_html, current_local_storage):
    with open(CHANGE_PROMPT_TEMPLATE_PATH, "r") as template_file:
        prompt_template = template_file.read()
    formatted_prompt = prompt_template.replace("{description}", transcription_text)
    formatted_prompt = formatted_prompt.replace("{current_html}", current_html)
    formatted_prompt = formatted_prompt.replace("{current_local_storage}", json.dumps(current_local_storage))  # Ensure it's a string
    return formatted_prompt
