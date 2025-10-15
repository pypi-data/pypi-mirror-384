#=================================================================
# Author: Garrett York
# Date: 2023/11/29
# Description: Class for Zoho Billings API (formerly Zoho Subscriptions)
#=================================================================

from .base_api_wrapper import BaseAPIWrapper
from datetime import datetime

class ZohoBillingAPI(BaseAPIWrapper):

    VALID_SUBSCRIPTION_FILTERS = {
        'All', 'ACTIVE', 'LIVE', 'FUTURE', 'TRIAL', 'PAST_DUE', 'UNPAID', 
        'NON_RENEWING', 'CANCELLED_FROM_DUNNING', 'CANCELLED', 'EXPIRED', 
        'TRIAL_EXPIRED', 'CANCELLED_LAST_MONTH', 'CANCELLED_THIS_MONTH'
        }

    VALID_CUSTOMER_STATUS_FILTERS = {
        'All', 'Active', 'Inactive', 'Gapps', 'Crm', 'NonSubscribers', 'PortalEnabled', 'PortalDisabled'
    }

    VALID_INVOICE_FILTERS = {
        'All', 'Sent', 'Draft', 'OverDue', 'Paid', 'PartiallyPaid', 'Void', 'Unpaid'
    }

    # Referenced these from the Status column in the UI
    VALID_CREDIT_NOTE_STATUS_FILTERS = {
        'All', 'Open', 'Void', 'Closed'
    }

    #-----------------------------------------------------------------
    # Method - Constructor
    #-----------------------------------------------------------------

    def __init__(self, client_id, client_secret, refresh_token, organization_id, api_iteration_limit=50, auth_url="https://accounts.zoho.com", base_url="https://www.zohoapis.com/subscriptions/v1/", redirect_uri="www.zohoapis.com/subscriptions"):
        super().__init__(base_url)
        self.auth_url = auth_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.organization_id = organization_id
        self.redirect_uri = redirect_uri
        self.api_iteration_limit = api_iteration_limit # Number of times to call an API endpoint in a single function 
        self.time_of_last_refresh = None # Set in _refresh_access_token()
        self.access_token = None # Set in _refresh_access_token()
        self._refresh_access_token()

    #-----------------------------------------------------------------
    # Method - Refresh Access Token
    #-----------------------------------------------------------------

    def _refresh_access_token(self):

        """
        Refreshes the OAuth access token using the refresh token.
        
        :return: True if the access token was successfully refreshed, False otherwise.
        """

        self.logger.debug("Entering _refresh_access_token()")
        self.time_of_last_refresh = datetime.now()

        path = "/oauth/v2/token" # a / at the end of the path will break things

        data = {
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'refresh_token'
        }
        headers = {}

        response = self.post(path=path, headers=headers, data=data, is_auth=True)
        response = response.json() if response is not None else None

        #valide if response is successful, if it was return true, if not return false
        if response is None:
            self.logger.error("Failed to refresh access token - response is None")
            return False
        else:
            #if access token exists, return true
            if "access_token" in response:
                self.access_token = response["access_token"]
                self.logger.info("Access token refreshed")
                return True
            else:
                self.logger.error("Failed to refresh access token - access token does not exist in response")
                return False
    
    #-----------------------------------------------------------------
    # Method - Check Last Time Access Token Was Refreshed
    #-----------------------------------------------------------------
    
    def check_if_access_token_needs_refreshed(self):
        """
        Checks if the access token needs to be refreshed.
        return: True if the access token needs to be refreshed, False otherwise.
        """
        self.logger.info("Entering check_last_refresh()")

        time_since_last_refresh = datetime.now() - self.time_of_last_refresh

        if time_since_last_refresh.seconds > 3600:
            self.logger.info("Exiting check_last_refresh() - Token needs to be refreshed")
            return True
        else:
            self.logger.info("Exiting check_last_refresh() - Token does not need to be refreshed")
            return False
    
    #-----------------------------------------------------------------
    # Method - Get Headers
    #-----------------------------------------------------------------

    def _get_headers(self):
        self.logger.info("Entering _get_headers()")
        if self.check_if_access_token_needs_refreshed():
            if not self._refresh_access_token():
                return None

        headers = {
            'X-com-zoho-subscriptions-organizationid': self.organization_id,
            'Authorization': f'Zoho-oauthtoken {self.access_token}'
        }

        self.logger.info(f'Headers have been set!')
        self.logger.info("Exiting _get_headers()")
        return headers
    
    #-----------------------------------------------------------------
    # Method - Fetch Data
    #-----------------------------------------------------------------
    
    def _fetch_data(self, endpoint, initial_params, data_key, page=1):
        self.logger.info(f'Entering _fetch_data() for endpoint {endpoint}')
        all_data_list = []
        iteration = 0
        params = initial_params
        headers = self._get_headers()

        while True:
            iteration += 1
            if iteration > self.api_iteration_limit:
                self.logger.warning(f"Pagination limit of {self.api_iteration_limit} reached for {endpoint}")
                break
            # if page is none, then we are fetching a single object, so don't include page in the params
            if page is None:
                self.logger.info(f"Fetching data from {endpoint} for a single object")
            else:
                self.logger.info(f"Fetching data from {endpoint} for page {page}")
                params["page"] = page
            response = self.get(endpoint, params=params, headers=headers)
            response = response.json() if response is not None else None

            if response is None:
                self.logger.error(f"Error fetching data from {endpoint} for page {page}. The response is None.")
                break

            if data_key in response:
                if isinstance(response[data_key], list):
                    data_count = len(response[data_key])
                    all_data_list.extend(response[data_key])
                    self.logger.info(f"Retrieved {data_count} {data_key} from page {page}")
                    if "page_context" in response:
                        if response["page_context"]["has_more_page"]:
                            page += 1
                        else:
                            self.logger.info(f"No more pages to fetch from {endpoint}")
                            break
                    else:
                        self.logger.error(f"No 'page_context' key found in the response for page {page}")
                        break
                elif isinstance(response[data_key], dict):
                    all_data_list.append(response[data_key])
                    self.logger.info(f"Retrieved 1 {data_key} from page {page}")
                    break
                else:
                    self.logger.error(f"Unexpected data type for {data_key} in response")
                    break               
            else:
                self.logger.error(f"No '{data_key}' key found in the response for page {page}")
                break

        self.logger.info(f"Exiting _fetch_data() with total {len(all_data_list)} {data_key} fetched")
        return all_data_list

    #-----------------------------------------------------------------
    # Method - Get Subscriptions
    #-----------------------------------------------------------------
    
    def get_subscriptions(self, subscription_id=None, customer_id=None, filter_by=None, page=1):
        """
        Fetches subscriptions from Zoho Billing API based on the specified status and optional filters.

        :param subscription_id: Optional subscription ID to fetch a specific subscription.
        :param customer_id: Optional customer ID to filter subscriptions for a specific customer.
        :param filter_by: Optional subscription status to filter by.
        :param page: Optional page number to fetch.
        :return: A list of all subscriptions meeting the criteria.
        """
        self.logger.debug("Entering get_subscriptions()")
        params = {}
        endpoint = "subscriptions"
        data_key = endpoint

        if subscription_id:
            endpoint += f"/{subscription_id}"
            data_key = "subscription"
        else:
            if filter_by:
                if not self._validate_subscription_filter(filter_by):
                    self.logger.error("Invalid subscription status filter provided.")
                    return None

            params = {
                "filter_by": f"SubscriptionStatus.{filter_by}" if filter_by else None,
                "customer_id": customer_id
                }

            params = self._prepare_params(params)

        all_subscriptions = self._fetch_data(endpoint, params, data_key, page=page)

        self.logger.info(f"Exiting get_subscriptions() with total {len(all_subscriptions)} subscriptions fetched")
        return all_subscriptions
    

    def get_plans(self, plan_code=None, active_plans_only=False, page=1):
        """
        Fetches subscription plans from Zoho Billing API.

        :param plan_code: Optional plan code to fetch a specific plan.
        :param page: Optional page number to fetch.
        :param active_plans_only: Optional filter to only return active plans. Includes all plans by default.
        :return: A list of all subscription plans meeting the criteria.
        """
        self.logger.debug("Entering get_plans()")
        params = {}
        endpoint = "plans"
        data_key = endpoint

        if plan_code:
            endpoint += f"/{plan_code}"
            data_key = "plan"
        else:
            params = self._prepare_params(params)
            if active_plans_only:
                params['status'] = 'active'

        self.logger.debug(f"Fetching plans with endpoint: {endpoint} and params: {params}")
        
        # Check and refresh the access token if needed
        headers = self._get_headers()
        if not headers:
            self.logger.error("Failed to fetch plans - unable to set headers")
            return None

        all_plans = self._fetch_data(endpoint, params, data_key, page=page)

        self.logger.info(f"Exiting get_plans() with total {len(all_plans)} plans fetched")
        return all_plans

    
    #-----------------------------------------------------------------
    # Method - Get Customers
    #-----------------------------------------------------------------
    
    def get_customers(self, customer_id=None, customer_name=None, email=None, phone=None, filter_by=None, page=1, sort_by=None, sort_order=None):
        """
        Fetches customers from Zoho Billing API based on the specified criteria.

        :param customer_id: Optional customer ID to fetch a specific customer.
        :param customer_name: Optional customer name to fetch a specific customer.
        :param email: Optional customer email to fetch a specific customer.
        :param phone: Optional customer phone to fetch a specific customer.
        :param filter_by: Optional string to filter customers by, e.g., 'Status.Active' for active customers.
        :param page: Optional page number to fetch.
        :param sort_by: Optional column to sort by (e.g., 'updated_time').
        :param sort_order: Optional sort order ('A' for ascending, 'D' for descending).
        :return: A list of customers or a single customer object meeting the criteria, or None if not found.
        """
        self.logger.debug(f"Entering get_customers()")

        params = {}
        endpoint = "customers"
        data_key = endpoint

        if customer_id:
            endpoint += f"/{customer_id}"
            data_key = "customer"
        else:
            if filter_by:
                if self._validate_customer_status_filter(filter_by):
                    filter_by = "Status." + filter_by
                else:
                    self.logger.error("Invalid customer status filter provided.")
                    return None  
            params = {
                "display_name_contains": customer_name,
                "email": email,
                "phone": phone,
                "filter_by": filter_by,
                "sort_column": sort_by,
                "sort_order": sort_order
            }

            params = self._prepare_params(params)

        all_customers = self._fetch_data(endpoint, params, data_key, page=page)

        self.logger.info(f"Exiting get_customers() with total {len(all_customers)} customers fetched")

        return all_customers
    

    #-----------------------------------------------------------------
    # Method - Update Customer
    #-----------------------------------------------------------------

    def update_customer(self, customer_id, first_name=None, last_name=None, display_name=None, email=None, phone=None, crm_profile_url=None):
        """
        Updates a customer record in Zoho Subscriptions with standard fields and a custom field.

        :param customer_id: The ID of the customer to update.
        :param first_name: The first name of the customer. 
        :param last_name: The last name of the customer. 
        :param display_name: The display name of the customer.
        :param email: The email of the customer.
        :param phone: The phone number of the customer.
        :param crm_profile_url: The URL to be updated in the custom field. This corresponds to the 'cf_crm_profile_url' custom field in Zoho.
        :return: The updated customer data on success, None otherwise.
        """
        self.logger.debug(f"Entering update_customer() for customer_id: {customer_id}")

        update_payload = {}
        if first_name:
            update_payload["first_name"] = first_name
        if last_name:
            update_payload["last_name"] = last_name
        if display_name:
            update_payload["display_name"] = display_name
        if email:
            update_payload["email"] = email
        if phone:
            update_payload["phone"] = phone

        # Handle the custom field if provided
        if crm_profile_url:
            update_payload["custom_fields"] = [
                {
                    "customfield_id": "2840008000037414894",  # The specific custom field ID for cf_crm_profile_url
                    "value": crm_profile_url
                }
            ]

        headers = self._get_headers()
        if not headers:
            self.logger.error("Failed to update customer - unable to set headers")
            return None

        endpoint = f"customers/{customer_id}"
        
        response = self.put(path=endpoint, json=update_payload, headers=headers)

        if response is None:
            error_msg = f"Failed to update customer: {customer_id}. No response received. Check to ensure your inputs are valid."
            self.logger.error(error_msg)
            raise Exception(error_msg)

        elif response.status_code == 200:
            self.logger.info(f"Customer updated successfully: {customer_id}")
            response_json = response.json()
            return response_json
        else:
            error_msg = (f"Failed to update customer: {customer_id}. Status Code: {response.status_code}. "
                        "Check that inputs are correct and that the account has the necessary permissions and scope.")
            self.logger.error(error_msg)
            raise Exception(error_msg)
        
    #-----------------------------------------------------------------
    # Method - Get Invoices
    #-----------------------------------------------------------------
        
    def get_invoices(self, invoice_id=None, customer_id=None, subscription_id=None, filter_by=None, page=1, sort_by=None, sort_order=None):
        """
        Fetches invoices from Zoho Billing API based on specified criteria.

        :param customer_id: Optional customer ID to filter invoices for a specific customer.
        :param subscription_id: Optional subscription ID to filter invoices for a specific subscription.
        :param filter_by: Optional invoice status to filter by.
        :param invoice_id: Optional invoice ID to fetch a specific invoice.
        :param page: Optional page number to fetch.
        :param sort_by: Optional column to sort by (e.g., 'date', 'invoice_number', 'total').
        :param sort_order: Optional sort order ('A' for ascending, 'D' for descending).
        :return: A list of invoices, a single invoice object, or None if not found.
        """
        self.logger.info("Entering get_invoices()")
        params = {}
        endpoint = "invoices"
        data_key = endpoint

        # If a specific invoice ID is provided, adjust the endpoint
        if invoice_id:
            endpoint += f"/{invoice_id}"
            page = None
            data_key = "invoice"
        else:
            if filter_by:
                if self._validate_invoice_filter(filter_by):
                    filter_by = "Status." + filter_by
                else:
                    self.logger.error("Invalid invoice status filter provided.")
                    return None
            
            params = {
                "customer_id": customer_id,
                "subscription_id": subscription_id,
                "filter_by": filter_by,
                "sort_column": sort_by,
                "sort_order": sort_order
            }
            params = self._prepare_params(params)

        all_invoices = self._fetch_data(endpoint, params, data_key, page=page)

        self.logger.info(f"Exiting get_invoices() with total {len(all_invoices)} invoices fetched")
        return all_invoices
    
    #-----------------------------------------------------------------
    # Method - Get Credit Notes
    #-----------------------------------------------------------------
    
    def get_credit_notes(self, credit_note_id=None, customer_id=None, customer_name=None, filter_by=None, page=1, sort_by=None, sort_order=None):
        """
        Fetches credit notes from Zoho Billing API based on the specified filter or credit note ID.

        :param credit_note_id: Optional credit note ID to fetch a specific credit note.
        :param customer_id: Optional customer ID to filter credit notes for a specific customer.
        :param customer_name: Optional customer name to fetch a specific credit note.
        :param filter_by: Optional string to filter credit notes by, e.g., 'Status.Active' for active credit notes.
        :param page: Optional page number to fetch.
        :param sort_by: Optional column to sort by (e.g., 'last_modified_time').
        :param sort_order: Optional sort order ('A' for ascending, 'D' for descending).
        :return: A list of credit notes or a single credit note object meeting the criteria, or None if not found.
        """
        self.logger.info(f"Entering get_credit_notes()")

        params = {}
        endpoint = "creditnotes"
        data_key = endpoint

        if credit_note_id:
            endpoint += f"/{credit_note_id}"
            data_key = "creditnote"
        else:
            if filter_by:
                if self._validate_credit_note_status_filter(filter_by):
                    filter_by = "Status." + filter_by
                else:
                    self.logger.error("Invalid credit note status filter provided.")
                    return None  
            params = {
                "customer_id": customer_id,
                "customer_name_contains": customer_name,
                "filter_by": filter_by,
                "sort_column": sort_by,
                "sort_order": sort_order
                }

            params = self._prepare_params(params)

        all_credit_notes = self._fetch_data(endpoint, params, data_key, page=page)

        self.logger.info(f"Exiting get_credit_notes() with total {len(all_credit_notes)} credit notes fetched")
        return all_credit_notes

    #-----------------------------------------------------------------
    # Method - Validate Filter
    #-----------------------------------------------------------------

    def _validate_filter(self, filter_value, valid_filters):
        self.logger.info("Entering filter validation")

        if filter_value in valid_filters:
            self.logger.info("Filter value is valid.")
            return True
        else:
            self.logger.error(f"Invalid filter value: {filter_value}")
            return False
        
    #-----------------------------------------------------------------
    # Method - Validate Subscription Filter
    #-----------------------------------------------------------------

    def _validate_subscription_filter(self, filter_value):
        return self._validate_filter(filter_value, self.VALID_SUBSCRIPTION_FILTERS)

    def _validate_customer_status_filter(self, filter_value):
        return self._validate_filter(filter_value, self.VALID_CUSTOMER_STATUS_FILTERS)

    def _validate_invoice_filter(self, filter_value):
        return self._validate_filter(filter_value, self.VALID_INVOICE_FILTERS)
    
    def _validate_credit_note_status_filter(self, filter_value):
        return self._validate_filter(filter_value, self.VALID_CREDIT_NOTE_STATUS_FILTERS)

    #-----------------------------------------------------------------
    # Methods - Get filters
    #-----------------------------------------------------------------

    def get_subscription_filters(self):
        return self.VALID_SUBSCRIPTION_FILTERS
    
    def get_customer_status_filters(self):
        return self.VALID_CUSTOMER_STATUS_FILTERS
    
    def get_invoice_filters(self):
        return self.VALID_INVOICE_FILTERS
    
    def get_credit_note_status_filters(self):
        return self.VALID_CREDIT_NOTE_STATUS_FILTERS


    #-----------------------------------------------------------------
    # Methods - API Pagination Control
    #-----------------------------------------------------------------

    def set_api_iteration_limit(self, limit):
        """
        Set the API iteration limit.

        :param limit: The new iteration limit. Must be a positive integer.
        :raises ValueError: If the limit is not a positive integer.
        """
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("API iteration limit must be a positive integer.")
        
        self.api_iteration_limit = limit
        self.logger.debug(f"API iteration limit set to {limit}")