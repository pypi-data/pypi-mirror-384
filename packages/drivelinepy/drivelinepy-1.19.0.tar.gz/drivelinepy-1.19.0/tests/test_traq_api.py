import unittest
from unittest.mock import patch, MagicMock
from drivelinepy.traq_api import TRAQAPI
import os
from dotenv import load_dotenv
import logging
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

class TestTRAQAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("TRAQ API - Setting up class for testing...")
        cls.client_id = os.getenv("DRIVELINEPY_TRAQ_CLIENT_ID")
        cls.client_secret = os.getenv("DRIVELINEPY_TRAQ_CLIENT_SECRET")
        if not cls.client_id or not cls.client_secret:
            raise ValueError("TRAQ API credentials not set in environment variables")
        cls.traq_api = TRAQAPI(cls.client_id, cls.client_secret)
        cls.VALID_TRAQ_ID = 6183
        cls.VALID_EMAIL = "garrettyork03@gmail.com"
        cls.mock_response = {"data": [
            {'id': 6183, 'email': 'garrettyork03@gmail.com'}
        ]}

    #-----------------------------------------------------------------
    # Test - Get users by TRAQ ID
    #----------------------------------------------------------------

    @patch('drivelinepy.traq_api.BaseAPIWrapper.get')
    def test_get_users_by_traq_id(self, mock_get):
        print("TRAQ API - Testing get_users by TRAQ ID...")
        mock_get.return_value.json.return_value = self.mock_response
        response = self.traq_api.get_users(traq_id=self.VALID_TRAQ_ID)
        
        self.assertIsInstance(response, list)
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['id'], self.VALID_TRAQ_ID)
        self.assertEqual(response[0]['email'], 'garrettyork03@gmail.com')

    #-----------------------------------------------------------------
    # Test - Get users by email
    #-----------------------------------------------------------------

    @patch('drivelinepy.traq_api.BaseAPIWrapper.get')
    def test_get_users_by_email(self, mock_get):
        print("TRAQ API - Testing get_users by email...")
        mock_get.return_value.json.return_value = self.mock_response
        response = self.traq_api.get_users(email=self.VALID_EMAIL)

        self.assertIsInstance(response, list)
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['id'], self.VALID_TRAQ_ID)
        self.assertEqual(response[0]['email'], 'garrettyork03@gmail.com')

    #-----------------------------------------------------------------
    # Test - Post Media
    #-----------------------------------------------------------------

    @patch('drivelinepy.traq_api.BaseAPIWrapper.post')
    @patch('builtins.open', create=True)
    @patch('os.path.getsize')
    @patch('os.path.exists')
    @patch('os.path.isfile')
    @patch('os.path.basename')
    @patch('os.path.splitext')
    def test_post_media_success(self, mock_splitext, mock_basename, mock_isfile, mock_exists, mock_getsize, mock_open, mock_post):
        print("TRAQ API - Testing post_media success...")

        # Setup mocks
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_getsize.return_value = 1024 * 1024 * 5  # 5 MB file
        mock_basename.return_value = 'test.png'
        mock_splitext.return_value = ('test', '.png')
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True, 'message': 'Media uploaded successfully'}
        mock_post.return_value = mock_response

        # Test the method
        result = self.traq_api.post_media(
            user_id=self.VALID_TRAQ_ID,  # 6183 (Garrett York)
            tab_id=231,
            name='test',
            file_path='/path/to/test.png'
        )

        # Assertions
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        mock_post.assert_called_once()

    @patch('os.path.exists')
    def test_post_media_file_not_found(self, mock_exists):
        print("TRAQ API - Testing post_media with file not found...")
        mock_exists.return_value = False

        with self.assertRaises(FileNotFoundError):
            self.traq_api.post_media(
                user_id=self.VALID_TRAQ_ID,  # 6183 (Garrett York)
                tab_id=231,
                name='test',
                file_path='/nonexistent/file.png'
            )

    def test_post_media_invalid_user_id(self):
        print("TRAQ API - Testing post_media with invalid user_id...")

        with self.assertRaises(ValueError) as context:
            self.traq_api.post_media(
                user_id='invalid',  # Invalid type
                tab_id=231,
                name='test',
                file_path='/path/to/test.png'
            )

        self.assertIn("Invalid TRAQ ID", str(context.exception))

    def test_post_media_invalid_tab_id(self):
        print("TRAQ API - Testing post_media with invalid tab_id...")

        with self.assertRaises(ValueError) as context:
            self.traq_api.post_media(
                user_id=self.VALID_TRAQ_ID,  # 6183 (Garrett York)
                tab_id='invalid_tab',  # Invalid tab_id (not 'miscellaneous' or int)
                name='test',
                file_path='/path/to/test.png'
            )

        self.assertIn("Invalid tab_id", str(context.exception))

    def test_post_media_empty_name(self):
        print("TRAQ API - Testing post_media with empty name...")

        with self.assertRaises(ValueError) as context:
            self.traq_api.post_media(
                user_id=self.VALID_TRAQ_ID,  # 6183 (Garrett York)
                tab_id=231,
                name='',  # Empty name
                file_path='/path/to/test.png'
            )

        self.assertIn("Invalid name", str(context.exception))

    @patch('drivelinepy.traq_api.BaseAPIWrapper.post')
    @patch('builtins.open', create=True)
    @patch('os.path.getsize')
    @patch('os.path.exists')
    @patch('os.path.isfile')
    @patch('os.path.basename')
    @patch('os.path.splitext')
    def test_post_media_api_failure(self, mock_splitext, mock_basename, mock_isfile, mock_exists, mock_getsize, mock_open, mock_post):
        print("TRAQ API - Testing post_media API failure...")

        # Setup mocks
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_getsize.return_value = 1024 * 1024 * 5  # 5 MB file
        mock_basename.return_value = 'test.png'
        mock_splitext.return_value = ('test', '.png')
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Mock failed API response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': 'Bad request'}
        mock_response.text = 'Bad request'
        mock_post.return_value = mock_response

        # Test the method
        with self.assertRaises(Exception) as context:
            self.traq_api.post_media(
                user_id=self.VALID_TRAQ_ID,  # 6183 (Garrett York)
                tab_id=231,
                name='test',
                file_path='/path/to/test.png'
            )

        self.assertIn("Failed to upload media", str(context.exception))

    @patch('os.path.getsize')
    @patch('os.path.exists')
    @patch('os.path.isfile')
    def test_post_media_max_file_size_exceeded(self, mock_isfile, mock_exists, mock_getsize):
        print("TRAQ API - Testing post_media with file size exceeding limit...")
        # Setup mocks
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_getsize.return_value = 1024 * 1024 * 150  # 150 MB file (exceeds 100 MB limit)

        # Test with max_file_size_mb parameter
        with self.assertRaises(ValueError) as context:
            self.traq_api.post_media(
                user_id=self.VALID_TRAQ_ID,
                tab_id=231,
                name='large_file',
                file_path='/path/to/large_file.mp4',
                max_file_size_mb=100  # Set 100 MB limit
            )

        self.assertIn("exceeds maximum allowed size", str(context.exception))
        self.assertIn("150", str(context.exception))  # Should mention actual file size
        self.assertIn("100", str(context.exception))  # Should mention limit

    @patch('drivelinepy.traq_api.BaseAPIWrapper.post')
    @patch('builtins.open', create=True)
    @patch('os.path.getsize')
    @patch('os.path.exists')
    @patch('os.path.isfile')
    @patch('os.path.basename')
    @patch('os.path.splitext')
    def test_post_media_with_size_limit_success(self, mock_splitext, mock_basename, mock_isfile, mock_exists, mock_getsize, mock_open, mock_post):
        print("TRAQ API - Testing post_media with file size within limit...")
        # Setup mocks
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_getsize.return_value = 1024 * 1024 * 50  # 50 MB file (within 100 MB limit)
        mock_basename.return_value = 'test_video.mp4'
        mock_splitext.return_value = ('test_video', '.mp4')
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True, 'message': 'Media uploaded successfully'}
        mock_post.return_value = mock_response

        # Test with max_file_size_mb parameter
        result = self.traq_api.post_media(
            user_id=self.VALID_TRAQ_ID,
            tab_id=231,
            name='test_video',
            file_path='/path/to/test_video.mp4',
            max_file_size_mb=100  # Set 100 MB limit
        )

        # Assertions
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        mock_post.assert_called_once()

if __name__ == '__main__':
    unittest.main()