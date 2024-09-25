import os
import re
import logging
from groq import Groq

# Configure logging
logger = logging.getLogger(__name__)

# Configure the Groq API client
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)


def generate_html_from_prompt(prompt):
    logger.info(f"Sending prompt to Groq API: {prompt}")

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=2170,
            top_p=1,
            stream=True,
            stop=None,
        )

        full_content = ""
        for chunk in completion:
            full_content += chunk.choices[0].delta.content or ""

        logger.info(f"Received response from Groq API: {full_content}") 

        html_content = extract_content(full_content, "HTML") or ""  # Ensure empty if no HTML
        local_storage_content = extract_content(full_content, "LOCAL_STORAGE") or ""  # Ensure empty if no LOCAL_STORAGE
        
        return html_content, local_storage_content
    except Exception as e:
        logger.error(f"Error generating HTML from prompt: {e}")
        raise


def extract_content(full_content, marker):
    match = re.search(fr"##BEGIN_{marker}##(.*?)##END_{marker}##", full_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        logger.warning(f"No {marker.lower()} content found in the response")
        return ""


def transcribe_audio(file_path):
    try:
        with open(file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(file_path, file.read()),
                model="whisper-large-v3",
                response_format="verbose_json",
            )
            return transcription.text
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        raise
