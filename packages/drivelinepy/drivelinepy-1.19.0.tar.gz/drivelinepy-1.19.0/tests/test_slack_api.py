import unittest
from unittest.mock import patch, MagicMock, mock_open, call
from drivelinepy.slack_api import SlackAPI
import json
import os

class TestSlackAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("Slack API - Setting up class for testing...")
        cls.test_token = "test-slack-token"
        cls.slack_api = SlackAPI(cls.test_token)
        cls.test_channel = "C01AL24207R"
        cls.test_file_path = "/tmp/test_file.txt"

    #-----------------------------------------------------------------
    # Test - Upload file with new implementation (no base_url mutation)
    #-----------------------------------------------------------------

    @patch('drivelinepy.slack_api.mimetypes.guess_type')
    @patch('drivelinepy.slack_api.os.path.getsize')
    @patch('drivelinepy.slack_api.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data=b'test file content')
    def test_upload_file_simplified(self, mock_file, mock_exists, mock_getsize, mock_mime):
        print("Slack API - Testing simplified upload_file with direct post...")

        # Setup mocks
        mock_exists.return_value = True
        mock_getsize.return_value = 100
        mock_mime.return_value = ('text/plain', None)

        # Mock responses for the three API calls
        mock_get_url_response = MagicMock()
        mock_get_url_response.status_code = 200
        mock_get_url_response.json.return_value = {
            'ok': True,
            'upload_url': 'https://files.slack.com/upload/v1/abc123',
            'file_id': 'F1234567890'
        }

        mock_upload_response = MagicMock()
        mock_upload_response.status_code = 200

        mock_complete_response = MagicMock()
        mock_complete_response.status_code = 200
        mock_complete_response.json.return_value = {
            'ok': True,
            'files': [{'id': 'F1234567890', 'name': 'test_file.txt'}]
        }

        # Setup the mock to return different responses for different calls
        self.slack_api.post = MagicMock(side_effect=[
            mock_get_url_response,
            mock_upload_response,  # Now the upload is called on self
            mock_complete_response
        ])

        # Store original base_url
        original_base_url = self.slack_api.base_url

        # Call the method
        response = self.slack_api.upload_file(
            channel=self.test_channel,
            file_absolute_path=self.test_file_path,
            text="Test message"
        )

        # Verify base_url was not changed
        self.assertEqual(self.slack_api.base_url, original_base_url)

        # Verify the upload was called with correct headers
        upload_call = self.slack_api.post.call_args_list[1]  # Second call is the upload
        self.assertEqual(upload_call[0][0], 'https://files.slack.com/upload/v1/abc123')
        self.assertIn('headers', upload_call[1])
        self.assertEqual(upload_call[1]['headers']['Content-Type'], 'text/plain')
        self.assertEqual(upload_call[1]['headers']['Content-Length'], '100')

        # Verify response transformation
        self.assertIn('file', response)
        self.assertEqual(response['file']['id'], 'F1234567890')

    #-----------------------------------------------------------------
    # Test - Response structure validation for backwards compatibility
    #-----------------------------------------------------------------

    @patch('drivelinepy.slack_api.mimetypes.guess_type')
    @patch('drivelinepy.slack_api.os.path.getsize')
    @patch('drivelinepy.slack_api.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data=b'test file content')
    def test_response_structure_validation(self, mock_file, mock_exists, mock_getsize, mock_mime):
        print("Slack API - Testing response structure validation...")

        # Setup mocks
        mock_exists.return_value = True
        mock_getsize.return_value = 100
        mock_mime.return_value = ('text/plain', None)

        mock_upload_response = MagicMock()
        mock_upload_response.status_code = 200

        # Test cases for different response structures
        test_cases = [
            # Valid list with files
            {
                'response': {'ok': True, 'files': [{'id': 'F123', 'name': 'test.txt'}]},
                'should_have_file': True,
                'description': 'Valid files list'
            },
            # Empty files list
            {
                'response': {'ok': True, 'files': []},
                'should_have_file': False,
                'description': 'Empty files list'
            },
            # Files is not a list (string)
            {
                'response': {'ok': True, 'files': 'not-a-list'},
                'should_have_file': False,
                'description': 'Files is a string'
            },
            # Files is None
            {
                'response': {'ok': True, 'files': None},
                'should_have_file': False,
                'description': 'Files is None'
            },
            # No files key
            {
                'response': {'ok': True},
                'should_have_file': False,
                'description': 'No files key'
            }
        ]

        for test_case in test_cases:
            with self.subTest(test_case['description']):
                # Setup mock responses
                mock_get_url_response = MagicMock()
                mock_get_url_response.status_code = 200
                mock_get_url_response.json.return_value = {
                    'ok': True,
                    'upload_url': 'https://files.slack.com/upload/v1/abc123',
                    'file_id': 'F1234567890'
                }

                mock_complete_response = MagicMock()
                mock_complete_response.status_code = 200
                mock_complete_response.json.return_value = test_case['response']

                self.slack_api.post = MagicMock(side_effect=[
                    mock_get_url_response,
                    mock_upload_response,
                    mock_complete_response
                ])

                # Call the method
                response = self.slack_api.upload_file(
                    channel=self.test_channel,
                    file_absolute_path=self.test_file_path
                )

                # Check if backwards compatibility 'file' key was added correctly
                if test_case['should_have_file']:
                    self.assertIn('file', response)
                    self.assertEqual(response['file'], test_case['response']['files'][0])
                else:
                    self.assertNotIn('file', response)

    #-----------------------------------------------------------------
    # Test - Missing upload_url/file_id validation
    #-----------------------------------------------------------------

    @patch('drivelinepy.slack_api.os.path.getsize')
    @patch('drivelinepy.slack_api.os.path.exists')
    def test_missing_upload_url_file_id(self, mock_exists, mock_getsize):
        print("Slack API - Testing validation for missing upload_url/file_id...")

        # Setup mocks
        mock_exists.return_value = True
        mock_getsize.return_value = 100

        # Test missing upload_url
        mock_response_missing_url = MagicMock()
        mock_response_missing_url.status_code = 200
        mock_response_missing_url.json.return_value = {
            'ok': True,
            'file_id': 'F1234567890'
            # upload_url is missing
        }

        self.slack_api.post = MagicMock(return_value=mock_response_missing_url)

        with self.assertRaises(Exception) as context:
            self.slack_api.upload_file(
                channel=self.test_channel,
                file_absolute_path=self.test_file_path
            )

        self.assertIn("Missing required fields in upload URL response", str(context.exception))

        # Test missing file_id
        mock_response_missing_id = MagicMock()
        mock_response_missing_id.status_code = 200
        mock_response_missing_id.json.return_value = {
            'ok': True,
            'upload_url': 'https://files.slack.com/upload/v1/abc123'
            # file_id is missing
        }

        self.slack_api.post = MagicMock(return_value=mock_response_missing_id)

        with self.assertRaises(Exception) as context:
            self.slack_api.upload_file(
                channel=self.test_channel,
                file_absolute_path=self.test_file_path
            )

        self.assertIn("Missing required fields in upload URL response", str(context.exception))

    #-----------------------------------------------------------------
    # Test - Error handling during file upload
    #-----------------------------------------------------------------

    @patch('drivelinepy.slack_api.mimetypes.guess_type')
    @patch('drivelinepy.slack_api.os.path.getsize')
    @patch('drivelinepy.slack_api.os.path.exists')
    @patch('builtins.open', side_effect=FileNotFoundError("File not found"))
    def test_file_upload_error_handling(self, mock_file, mock_exists, mock_getsize, mock_mime):
        print("Slack API - Testing error handling during file upload...")

        # Setup mocks
        mock_exists.return_value = True
        mock_getsize.return_value = 100
        mock_mime.return_value = ('text/plain', None)

        # Mock get URL response
        mock_get_url_response = MagicMock()
        mock_get_url_response.status_code = 200
        mock_get_url_response.json.return_value = {
            'ok': True,
            'upload_url': 'https://files.slack.com/upload/v1/abc123',
            'file_id': 'F1234567890'
        }

        self.slack_api.post = MagicMock(return_value=mock_get_url_response)

        # Store original base_url
        original_base_url = self.slack_api.base_url

        # Call should raise FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            self.slack_api.upload_file(
                channel=self.test_channel,
                file_absolute_path=self.test_file_path
            )

        # Verify base_url was not changed even after exception
        self.assertEqual(self.slack_api.base_url, original_base_url)

    #-----------------------------------------------------------------
    # Test - Post message functionality
    #-----------------------------------------------------------------

    def test_post_message_success(self):
        print("Slack API - Testing post_message success...")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ok': True,
            'channel': self.test_channel,
            'ts': '1234567890.123456'
        }

        # Mock the post method directly on the instance
        self.slack_api.post = MagicMock(return_value=mock_response)

        response = self.slack_api.post_message(
            channel=self.test_channel,
            text="Test message"
        )

        self.assertTrue(response['ok'])
        self.assertIn('ts', response)  # Check timestamp is present

        # Verify the post method was called with correct parameters
        self.slack_api.post.assert_called_once()

    def test_post_message_empty_text(self):
        print("Slack API - Testing post_message with empty text...")

        with self.assertRaises(ValueError) as context:
            self.slack_api.post_message(
                channel=self.test_channel,
                text=""
            )

        self.assertIn("Text cannot be None or an empty string", str(context.exception))

if __name__ == '__main__':
    unittest.main()