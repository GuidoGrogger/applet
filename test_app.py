import unittest
from unittest.mock import patch, MagicMock
import json
import os
import shutil
from io import BytesIO
import uuid

from app.main import app

class AppletTestCase(unittest.TestCase):
    def setUp(self):
        # Set up the Flask test client
        self.app = app.test_client()
        self.app.testing = True

        # Set up a temporary directory for UPLOAD_DIR
        self.test_dir = 'test_applets'
        app.config['UPLOAD_DIR'] = self.test_dir
        os.makedirs(self.test_dir, exist_ok=True)


    def tearDown(self):
        # Remove the test directory and prompts after tests
        shutil.rmtree(self.test_dir)

    def test_home(self):
        """
        Test that the home page loads correctly and returns a 200 status code.
        """
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)  # Check for HTML content

    def test_show_applet_not_found(self):
        """
        Test that requesting a non-existent applet returns a 404 error.
        """
        response = self.app.get('/applet/00000000-0000-0000-0000-000000000000')
        self.assertEqual(response.status_code, 404)
        response_data = response.get_json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Applet not found')

    @patch('app.main.transcribe_audio')  # Patching where transcribe_audio is used in main.py
    @patch('app.main.generate_html_from_prompt')  # Patching where generate_html_from_prompt is used in main.py
    def test_upload_audio(self, mock_generate_html_from_prompt, mock_transcribe_audio):
        """
        Test uploading audio to create a new applet.
        Mocks the transcribe_audio and generate_html_from_prompt functions to avoid external API calls.
        """
        # Set up the mocks to return dummy data
        mock_transcribe_audio.return_value = 'This is a test transcription.'
        mock_generate_html_from_prompt.return_value = ('<html><body>Test HTML</body></html>', '{}')

        # Create a dummy audio file in memory
        audio_content = b'test audio content'
        data = {
            'audio': (BytesIO(audio_content), 'test_audio.webm', 'audio/webm')
        }

        # Send POST request to /applet to upload audio
        response = self.app.post('/applet', data=data, content_type='multipart/form-data')

        # Assert that the response is successful and contains the expected data
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertIn('uuid', response_data)
        self.assertIn('message', response_data)
        self.assertEqual(response_data['message'], 'Audio file uploaded and processed successfully')

        # Check that the applet directory was created in the filesystem
        applet_uuid = response_data['uuid']
        applet_dir = os.path.join(self.test_dir, applet_uuid)
        self.assertTrue(os.path.exists(applet_dir))

    @patch('app.main.transcribe_audio')  # Patching where transcribe_audio is used in main.py
    @patch('app.main.generate_html_from_prompt')  # Patching where generate_html_from_prompt is used in main.py
    def test_change_applet(self, mock_generate_html_from_prompt, mock_transcribe_audio):
        """
        Test changing an existing applet by uploading new audio.
        Mocks external API calls to avoid making actual requests.
        """
        # Set up the mocks to return dummy data for the change
        mock_transcribe_audio.return_value = 'This is a change transcription.'
        mock_generate_html_from_prompt.return_value = ('<html><body>Modified HTML</body></html>', '{}')

        # First, create an applet to modify
        audio_content = b'test audio content'
        data = {
            'audio': (BytesIO(audio_content), 'test_audio.webm', 'audio/webm')
        }

        # Create the applet
        response = self.app.post('/applet', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        applet_uuid = response_data['uuid']

        # Now, upload new audio to change the applet
        change_audio_content = b'test change audio content'
        data = {
            'audio': (BytesIO(change_audio_content), 'test_change_audio.webm', 'audio/webm')
        }

        response = self.app.post(f'/applet/{applet_uuid}', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertIn('message', response_data)
        self.assertEqual(response_data['message'], 'Applet changed successfully')
        self.assertEqual(response_data['uuid'], applet_uuid)

    def test_update_applet_storage(self):
        """
        Test updating the applet storage with new data.
        """
        # Create an applet directory directly
        applet_uuid = str(uuid.uuid4())
        applet_dir = os.path.join(self.test_dir, applet_uuid)
        os.makedirs(applet_dir, exist_ok=True)

        # Send PUT request to update storage with JSON data
        storage_data = {'key': 'value'}
        response = self.app.put(f'/applet/{applet_uuid}/storage', json=storage_data)
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertEqual(response_data['message'], 'Storage updated successfully')

        # Verify that the storage.json file was created and contains the correct data
        storage_file_path = os.path.join(applet_dir, 'storage.json')
        self.assertTrue(os.path.exists(storage_file_path))
        with open(storage_file_path, 'r') as f:
            saved_storage_data = json.load(f)
        self.assertEqual(saved_storage_data, storage_data)

    def test_get_applet_storage(self):
        """
        Test retrieving the applet storage data.
        """
        # Create an applet and storage file with sample data
        applet_uuid = str(uuid.uuid4())
        applet_dir = os.path.join(self.test_dir, applet_uuid)
        os.makedirs(applet_dir, exist_ok=True)

        storage_data = {'key': 'value'}
        storage_file_path = os.path.join(applet_dir, 'storage.json')
        with open(storage_file_path, 'w') as f:
            json.dump(storage_data, f)

        # Send GET request to retrieve the storage data
        response = self.app.get(f'/applet/{applet_uuid}/storage')
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertEqual(response_data, storage_data)

    def test_get_applet_storage_invalid_json(self):
        """
        Test retrieving the applet storage data when there is invalid JSON.
        """
        # Create an applet and storage file with sample data
        applet_uuid = str(uuid.uuid4())
        applet_dir = os.path.join(self.test_dir, applet_uuid)
        os.makedirs(applet_dir, exist_ok=True)

        storage_file_path = os.path.join(applet_dir, 'storage.json')
        with open(storage_file_path, 'w') as f:
            f.write('INVALID Json Data')

        # Send GET request to retrieve the storage data
        response = self.app.get(f'/applet/{applet_uuid}/storage')
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertEqual(response_data, {})        

    def test_delete_applet_storage(self):
        """
        Test deleting (emptying) the applet storage.
        """
        # Create an applet and storage file with sample data
        applet_uuid = str(uuid.uuid4())
        applet_dir = os.path.join(self.test_dir, applet_uuid)
        os.makedirs(applet_dir, exist_ok=True)

        storage_data = {'key': 'value'}
        storage_file_path = os.path.join(applet_dir, 'storage.json')
        with open(storage_file_path, 'w') as f:
            json.dump(storage_data, f)

        # Send DELETE request to empty the storage
        response = self.app.delete(f'/applet/{applet_uuid}/storage')
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertEqual(response_data['message'], 'Storage emptied successfully')

        # Verify that the storage.json file is now empty
        with open(storage_file_path, 'r') as f:
            emptied_storage_data = json.load(f)
        self.assertEqual(emptied_storage_data, {})

    def test_show_applet_html(self):
        """
        Test retrieving the applet HTML content.
        """
        # Create an applet directory and an index.html file
        applet_uuid = str(uuid.uuid4())
        applet_dir = os.path.join(self.test_dir, applet_uuid)
        os.makedirs(applet_dir, exist_ok=True)

        index_file_path = os.path.join(applet_dir, 'index.html')
        with open(index_file_path, 'w') as f:
            f.write('<html><body>Applet HTML</body></html>')

        # Send GET request to retrieve the HTML content
        response = self.app.get(f'/applet/{applet_uuid}/html')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Applet HTML', response.data)

    def test_show_applet_html_not_found(self):
        """
        Test retrieving applet HTML when the index.html file does not exist.
        Should return a 404 error.
        """
        applet_uuid = str(uuid.uuid4())
        # Do not create index.html
        applet_dir = os.path.join(self.test_dir, applet_uuid)
        os.makedirs(applet_dir, exist_ok=True)

        response = self.app.get(f'/applet/{applet_uuid}/html')
        self.assertEqual(response.status_code, 404)
        response_data = response.get_json()
        self.assertEqual(response_data['error'], 'HTML file not found')

    def test_invalid_audio_file_type(self):
        """
        Test uploading an audio file with an invalid file type.
        Should return a 400 error.
        """
        audio_content = b'test audio content'
        data = {
            'audio': (BytesIO(audio_content), 'test_audio.txt', 'text/plain')  # Invalid content type
        }

        response = self.app.post('/applet', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        response_data = response.get_json()
        self.assertEqual(response_data['error'], 'Invalid audio file type')

    def test_missing_audio_file(self):
        """
        Test uploading without providing an audio file.
        Should return a 400 error.
        """
        data = {}
        response = self.app.post('/applet', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        response_data = response.get_json()
        self.assertEqual(response_data['error'], 'No audio file provided')

    def test_update_storage_invalid_json(self):
        """
        Test updating the applet storage with invalid JSON data.
        Should return a 400 error.
        """
        # Create an applet directory
        applet_uuid = str(uuid.uuid4())
        applet_dir = os.path.join(self.test_dir, applet_uuid)
        os.makedirs(applet_dir, exist_ok=True)

        # Send PUT request with invalid JSON
        response = self.app.put(f'/applet/{applet_uuid}/storage', data='Invalid JSON', content_type='application/json')
        self.assertEqual(response.status_code, 400)
        response_data = response.get_json()
        self.assertEqual(response_data['error'], 'Invalid JSON')

    def test_get_storage_not_found(self):
        """
        Test retrieving storage when the storage file does not exist.
        Should return an empty JSON object.
        """
        applet_uuid = str(uuid.uuid4())
        applet_dir = os.path.join(self.test_dir, applet_uuid)
        os.makedirs(applet_dir, exist_ok=True)

        response = self.app.get(f'/applet/{applet_uuid}/storage')
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertEqual(response_data, {})  # Should return empty JSON

    def test_delete_storage_not_found(self):
        """
        Test deleting storage when the storage file does not exist.
        Should return a 404 error.
        """
        applet_uuid = str(uuid.uuid4())
        applet_dir = os.path.join(self.test_dir, applet_uuid)
        # Do not create storage.json

        response = self.app.delete(f'/applet/{applet_uuid}/storage')
        self.assertEqual(response.status_code, 404)
        response_data = response.get_json()
        self.assertEqual(response_data['error'], 'Storage file not found')

    @patch('app.ai_manager.transcribe_audio')
    @patch('app.ai_manager.generate_html_from_prompt')
    def test_change_applet_not_found(self, mock_generate_html_from_prompt, mock_transcribe_audio):
        """
        Test changing an applet that does not exist.
        Should return a 404 error.
        """
        # Set up the mocks
        mock_transcribe_audio.return_value = 'This is a test transcription.'
        mock_generate_html_from_prompt.return_value = ('<html><body>Test HTML</body></html>', '{}')

        audio_content = b'test audio content'
        data = {
            'audio': (BytesIO(audio_content), 'test_audio.webm', 'audio/webm')
        }

        # Use a random UUID that does not correspond to any applet
        applet_uuid = str(uuid.uuid4())
        response = self.app.post(f'/applet/{applet_uuid}', data=data, content_type='multipart/form-data')

        self.assertEqual(response.status_code, 404)
        response_data = response.get_json()
        self.assertEqual(response_data['error'], 'Applet not found')

    def test_update_storage_too_large(self):
        """
        Test updating the applet storage with data that exceeds the size limit.
        Should return a 400 error.
        """
        # Create an applet directory
        applet_uuid = str(uuid.uuid4())
        applet_dir = os.path.join(self.test_dir, applet_uuid)
        os.makedirs(applet_dir, exist_ok=True)

        # Generate storage data larger than 10 MB
        storage_data = {'key': 'a' * (10 * 1024 * 1024 + 1)}
        response = self.app.put(f'/applet/{applet_uuid}/storage', json=storage_data)
        self.assertEqual(response.status_code, 400)
        response_data = response.get_json()
        self.assertEqual(response_data['error'], 'Storage data too large')

if __name__ == '__main__':
    unittest.main()
