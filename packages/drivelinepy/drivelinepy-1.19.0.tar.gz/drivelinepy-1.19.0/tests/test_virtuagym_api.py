import unittest
from unittest.mock import patch, MagicMock
from drivelinepy.virtuagym_api import VirtuagymAPI
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

class TestVirtuagymAPI(unittest.TestCase):

    def setUp(self):
        self.api_key = os.getenv("DRIVELINEPY_VIRTUAGYM_API_KEY")
        self.club_secret = os.getenv("DRIVELINEPY_VIRTUAGYM_CLUB_SECRET")
        self.club_id = os.getenv("DRIVELINEPY_VIRTUAGYM_WASHINGTON_CLUB_ID")
        
        if not all([self.api_key, self.club_secret, self.club_id]):
            raise ValueError("Virtuagym API credentials or club ID not set in environment variables")
        
        self.virtuagym_api = VirtuagymAPI(api_key=self.api_key, club_secret=self.club_secret)
        self.test_member_id = "27119834"  # garrett york id
        self.expected_email = "garrett@drivelinebaseball.com"

    @patch('drivelinepy.virtuagym_api.BaseAPIWrapper.get')
    def test_get_single_club_member_email(self, mock_get):
        logging.info("Virtuagym API - Testing get_club_members for single member email...")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": [
                {
                    "member_id": 27119834,
                    "email": self.expected_email,
                    # Other fields omitted for brevity
                }
            ],
            "status": {
                "results_remaining": 0
            }
        }
        mock_get.return_value = mock_response

        # Call the method to get a single club member
        member = self.virtuagym_api.get_club_members(self.club_id, club_member_id=self.test_member_id)

        # Assertions
        self.assertIsInstance(member, list, "Result should be a list")
        self.assertEqual(len(member), 1, "Result should contain exactly one member")
        self.assertEqual(member[0]['email'], self.expected_email, "Email should match the expected value")

        # Verify that the API was called with the correct parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn(f"club/{self.club_id}/member/{self.test_member_id}", args[0], 
                      "API call should include correct club_id and member_id")

if __name__ == '__main__':
    unittest.main()