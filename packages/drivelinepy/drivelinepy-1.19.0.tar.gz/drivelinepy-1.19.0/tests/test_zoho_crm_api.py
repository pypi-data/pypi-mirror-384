import unittest
from unittest.mock import patch, MagicMock
from drivelinepy.zoho_crm_api import ZohoCrmAPI
from dotenv import load_dotenv
import logging
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

class TestZohoCrmAPI(unittest.TestCase):

    def setUp(self):
        print("Zoho CRM API - Setting up class for testing...")
        self.client_id = os.getenv("DRIVELINEPY_ZOHO_CLIENT_ID")
        self.client_secret = os.getenv("DRIVELINEPY_ZOHO_CLIENT_SECRET")
        self.refresh_token = os.getenv("DRIVELINEPY_ZOHO_REFRESH_TOKEN")
        self.organization_id = os.getenv("DRIVELINEPY_ZOHO_ORGANIZATION_ID")

        if not all([self.client_id, self.client_secret, self.refresh_token, self.organization_id]):
            raise ValueError("Zoho CRM API credentials not set in environment variables")

        self.zoho = ZohoCrmAPI(
            client_id=self.client_id,
            client_secret=self.client_secret,
            refresh_token=self.refresh_token,
            organization_id=self.organization_id
        )

    @patch('drivelinepy.zoho_crm_api.ZohoCrmAPI._fetch_data')
    def test_get_specific_contact_email(self, mock_fetch_data):
        print("Zoho CRM API - Testing get_customer_records for email confirmation...")
        
        expected_email = "garrett@drivelinebaseball.com"
        
        # Prepare mock data
        mock_contact = [{
            "Email": expected_email,
        }]
        mock_fetch_data.return_value = mock_contact

        # Call the method
        contact = self.zoho.get_customer_records(module="Contacts", email=expected_email)

        # Assertions for the returned data
        self.assertIsInstance(contact, list)
        self.assertEqual(len(contact), 1)
        self.assertEqual(contact[0]["Email"], expected_email)

        # Verify that the method was called correctly
        mock_fetch_data.assert_called_once()
        
        # Inspect the call arguments
        args, kwargs = mock_fetch_data.call_args
        
        # Assert the correct endpoint and search criteria
        self.assertEqual(args[0], "Contacts/search")
        self.assertIn("initial_params", kwargs)
        self.assertIn("criteria", kwargs["initial_params"])
        self.assertEqual(kwargs["initial_params"]["criteria"], f"(Email:equals:{expected_email})")

if __name__ == '__main__':
    unittest.main()