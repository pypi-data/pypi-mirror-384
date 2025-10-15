import unittest
from unittest.mock import patch
from drivelinepy.zoho_billing_api import ZohoBillingAPI
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

class TestZohoBillingAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up the test environment once for all test methods."""
        print("Zoho Billing API - Setting up class for testing...")
        cls.client_id = os.getenv("DRIVELINEPY_ZOHO_CLIENT_ID")
        cls.client_secret = os.getenv("DRIVELINEPY_ZOHO_CLIENT_SECRET")
        cls.refresh_token = os.getenv("DRIVELINEPY_ZOHO_REFRESH_TOKEN")
        cls.organization_id = os.getenv("DRIVELINEPY_ZOHO_ORGANIZATION_ID")

        if not all([cls.client_id, cls.client_secret, cls.refresh_token, cls.organization_id]):
            raise ValueError("Zoho Billing API credentials not set in environment variables")

        cls.zoho_billing_api = ZohoBillingAPI(
            client_id=cls.client_id,
            client_secret=cls.client_secret,
            refresh_token=cls.refresh_token,
            organization_id=cls.organization_id
        )

    @patch('drivelinepy.zoho_billing_api.ZohoBillingAPI._fetch_data')
    def test_get_customer_by_email(self, mock_fetch_data):
        """Test getting a customer by email address."""
        print("Zoho Billing API - Testing get_customers for email confirmation...")
        
        test_email = "garrett@drivelinebaseball.com"
        expected_customer_data = {"email": test_email}
        
        # Mock the API response
        mock_fetch_data.return_value = [expected_customer_data]

        # Call the method being tested
        result = self.zoho_billing_api.get_customers(email=test_email)

        # Assertions
        self.assertEqual(len(result), 1, "Result should contain exactly one customer")
        self.assertEqual(result[0]["email"], test_email, "Returned email should match the test email")

        # Verify that _fetch_data was called with the correct parameters
        mock_fetch_data.assert_called_once_with(
            'customers',
            {'email': test_email},
            'customers',
            page=1
        )

if __name__ == '__main__':
    unittest.main()