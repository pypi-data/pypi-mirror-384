# =================================================================
# Author: Garrett York
# Date: 2023/12/21
# Description: Class for Zoho Billings API (formerly Zoho Subscriptions)
# =================================================================

from .base_api_wrapper import BaseAPIWrapper
from datetime import datetime


class ZohoCrmAPI(BaseAPIWrapper):
    SUPPORTED_MODULES = ["Contacts", "Leads"]

    # Contact id included return by default for mass users -- fields below we can modify as needed
    # pulling a single user via /Contacts/<contact_id> will return all fields
    DEFAULT_CONTACTS_MODULE_FIELDS = [
        "Email",
        "First_Name",
        "Last_Name",
        "TRAQ_Profile_URL",
        "Subscriptions_Customer_Profile"
    ]

    # -----------------------------------------------------------------
    # Method - Constructor
    # -----------------------------------------------------------------

    def __init__(self, client_id, client_secret, refresh_token, organization_id, api_iteration_limit=50,
                 auth_url="https://accounts.zoho.com", base_url="https://www.zohoapis.com/crm/v2/",
                 redirect_uri="www.zohoapis.com/crm"):
        super().__init__(base_url)
        self.auth_url = auth_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.organization_id = organization_id
        self.redirect_uri = redirect_uri
        self.api_iteration_limit = api_iteration_limit  # Number of times to call an API endpoint in a single function
        self.time_of_last_refresh = None  # Set in _refresh_access_token()
        self.access_token = None  # Set in _refresh_access_token()
        self._refresh_access_token()

    # -----------------------------------------------------------------
    # Method - Refresh Access Token
    # -----------------------------------------------------------------

    def _refresh_access_token(self):

        """
        Refreshes the OAuth access token using the refresh token.
        
        :return: True if the access token was successfully refreshed, False otherwise.
        """

        self.logger.debug("Entering _refresh_access_token()")
        self.time_of_last_refresh = datetime.now()

        path = "/oauth/v2/token"  # a / at the end of the path will break things

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

        # validate if response is successful, if it was return true, if not return false
        if response is None:
            self.logger.error("Failed to refresh access token - response is None")
            return False
        else:
            # if access token exists, return true
            if "access_token" in response:
                self.access_token = response["access_token"]
                self.logger.info("Access token refreshed")
                self.logger.debug("Exiting _refresh_access_token()")
                return True
            else:
                self.logger.error("Failed to refresh access token - access token does not exist in response")
                return False

    # -----------------------------------------------------------------
    # Method - Check Last Time Access Token Was Refreshed
    # -----------------------------------------------------------------

    def check_if_access_token_needs_refreshed(self):
        """
        Checks if the access token needs to be refreshed.
        return: True if the access token needs to be refreshed, False otherwise.
        """
        self.logger.debug("Entering check_last_refresh()")

        time_since_last_refresh = datetime.now() - self.time_of_last_refresh

        exit_message = "Exiting check_last_refresh()"
        if time_since_last_refresh.seconds > 3600:
            self.logger.debug(exit_message)
            self.logger.info("Token needs to be refreshed")
            return True
        else:
            self.logger.debug(exit_message)
            self.logger.info("Token does not need to be refreshed")
            return False

    # -----------------------------------------------------------------
    # Method - Get Headers
    # -----------------------------------------------------------------

    def _get_headers(self):
        self.logger.debug("Entering _get_headers()")
        if self.check_if_access_token_needs_refreshed():
            if not self._refresh_access_token():
                return None

        headers = {
            'X-com-zoho-subscriptions-organizationid': self.organization_id,
            'Authorization': f'Zoho-oauthtoken {self.access_token}'
        }

        self.logger.info('Headers have been set!')
        self.logger.debug("Exiting _get_headers()")
        return headers

    # -----------------------------------------------------------------
    # Method - Fetch Data
    # -----------------------------------------------------------------

    def _fetch_data(self, endpoint, initial_params, data_key, page=1):
        """
        Fetches data from Zoho CRM API and handles various API response edge cases.
        
        This method handles several Zoho API edge cases:
        - Empty responses from attachment endpoints (normal, not an error)
        - Single record fetches that don't include pagination info
        - Different response formats for list vs single object responses
        - Proper handling of pagination for multi-page responses
        
        :param endpoint: API endpoint to fetch data from
        :param initial_params: Initial query parameters 
        :param data_key: The key in the response JSON that contains the data
        :param page: The page number to start fetching from (default: 1)
        :return: List of fetched records
        """
        self.logger.info(f'Entering _fetch_data() for endpoint {endpoint}')
        all_data_list = []
        iteration = 0
        params = initial_params
        headers = self._get_headers()
        
        # Flag special endpoints that have unique behavior
        is_attachments_endpoint = "/Attachments" in endpoint
        # Single record fetches (endpoints with an ID) don't have pagination info
        is_single_record_fetch = "/" in endpoint and not is_attachments_endpoint and page == 1

        while True:
            # API iteration limit prevents infinite loops if pagination is misconfigured
            iteration += 1
            if iteration > self.api_iteration_limit:
                self.logger.warning(f"Pagination limit of {self.api_iteration_limit} reached for {endpoint}")
                break
                
            # Handle pagination parameter
            if page is None:
                self.logger.info(f"Fetching data from {endpoint} for a single object")
            else:
                self.logger.info(f"Fetching data from {endpoint} for page {page}")
                params["page"] = page
                
            # Make the API request
            response = self.get(endpoint, params=params, headers=headers)
            
            # Check if response exists before attempting to process it
            if response is None:
                self.logger.error(f"Error fetching data from {endpoint} for page {page}. The response is None.")
                break
                
            # Parse response content, handling empty or invalid JSON responses
            try:
                if response.text.strip():
                    response_json = response.json()
                else:
                    # Empty response handling - attachments endpoint returns empty if no attachments exist
                    if is_attachments_endpoint:
                        # For attachments endpoint, empty response means no attachments - not an error
                        self.logger.info(f"No attachments found for {endpoint}")
                        break
                    else:
                        self.logger.warning(f"Empty response received from {endpoint} for page {page}")
                    response_json = None
            except Exception as e:
                # Log detailed error information for debugging
                self.logger.error(f"Error parsing JSON from {endpoint} response: {str(e)}")
                self.logger.error(f"Response status code: {response.status_code}, Content: {response.text}")
                break

            # Verify the response contains valid data
            if response_json is None:
                # Don't log as error for attachments endpoint (empty is normal)
                if not is_attachments_endpoint:
                    self.logger.error(f"No valid JSON data in response from {endpoint} for page {page}")
                break

            # Process the data if the expected data key exists
            if data_key in response_json:
                # Handle list responses (multiple records)
                if isinstance(response_json[data_key], list):
                    data_count = len(response_json[data_key])
                    all_data_list.extend(response_json[data_key])
                    self.logger.info(f"Retrieved {data_count} {data_key} from page {page}")
                    
                    # Check for pagination info - only present in list/search endpoints
                    if "info" in response_json:
                        # If there are more pages, increment page counter
                        if response_json["info"]["more_records"] == True:
                            page += 1
                        else:
                            self.logger.info(f"No more pages to fetch from {endpoint}")
                            break
                    else:
                        # Single record fetches don't have "info" key - not an error
                        if is_single_record_fetch:
                            self.logger.debug(f"No 'info' key found in response for single record fetch - this is normal")
                            break
                        else:
                            # Missing "info" key in list response is an error
                            self.logger.error(f"No 'info' key found in the response for page {page}")
                            break
                            
                # Handle single record responses (returns a dict for the record)
                elif isinstance(response_json[data_key], dict):
                    all_data_list.append(response_json[data_key])
                    self.logger.info(f"Retrieved 1 {data_key} from page {page}")
                    break
                else:
                    # Unexpected data type in response
                    self.logger.error(f"Unexpected data type for {data_key} in response")
                    break
            else:
                # The expected data key is missing from response
                self.logger.error(f"No '{data_key}' key found in the response for page {page}")
                break

        self.logger.info(f"Exiting _fetch_data() with total {len(all_data_list)} {data_key} fetched")
        return all_data_list

    # -----------------------------------------------------------------
    # Method - Get Customer Records
    # -----------------------------------------------------------------

    def get_customer_records(self, module, customer_id=None, first_name=None, last_name=None, email=None,
                             converted_leads=None, attachments=None, page=1):
        """
        Fetches customer records from the Zoho CRM API based on the specified criteria.
        :param module: The module to fetch records from.
        :param customer_id: The ID of the customer to fetch.
        :param first_name: The first name of the customer to fetch.
        :param last_name: The last name of the customer to fetch.
        :param email: The email of the customer to fetch.
        :param page: The page number to fetch.
        :param converted_leads: If True, fetch converted leads only.
        :param attachments: If True, fetch attachments.

        """
        self.logger.debug("Entering get_customer_records()")

        # check if module in supported modules
        if module in self.SUPPORTED_MODULES:
            endpoint = module
        else:
            self.logger.error("Invalid module provided.")
            return None

        params = {}
        data_key = "data"

        if customer_id:
            # Fetch a specific customer by ID
            endpoint += f"/{customer_id}"
            # If attachments are requested, add the parameter to the endpoint
            if attachments:
                endpoint += "/Attachments"
        else:
            # Search for customers based on provided criteria or fetch all if no criteria
            criteria_list = []
            if first_name:
                criteria_list.append(f"(First_Name:equals:{first_name})")
            if last_name:
                criteria_list.append(f"(Last_Name:equals:{last_name})")
            if email:
                criteria_list.append(f"(Email:equals:{email})")

            if criteria_list:
                # If search criteria are provided, use the search endpoint
                endpoint += "/search"
                params['criteria'] = 'AND'.join(criteria_list)
            # If no search criteria and no customer_id, it will fetch all records
            # Use the default fields if specific fields are not provided
            params['fields'] = ','.join(self.DEFAULT_CONTACTS_MODULE_FIELDS)

        # If leads module and converted_leads is true add paramater "converted" to the params set to true
        if module == "Leads" and converted_leads:
            params['converted'] = "true"  # has to be a string for the API, tried python bool and it didn't work

        all_records = self._fetch_data(endpoint, initial_params=params, data_key=data_key, page=page)

        self.logger.info(f"Exiting get_customer_records() with total {len(all_records)} records fetched")
        return all_records

    # -----------------------------------------------------------------
    # Method - Update CRM Record
    # -----------------------------------------------------------------

    def update_customer_record(self, module, customer_id, subscriptions_customer_profile=None, traq_profile_url=None):
        """
        Updates a customer record from the Zoho CRM API based on the specified criteria. Currently allows for only Bridge URL updates.

        :param module: The module to update the customer record in. Currently only supports "Contacts" for Bridge URLs.
        :param customer_id: The ID of the customer to update.
        :param subscriptions_customer_profile: The URL of the customer's Billings Profile, corresponds to Subscriptions_Customer_Profile field.
        :param traq_profile_url: The Traq Profile URL of the customer, corresponds to TRAQ_Profile_URL field.
        :return: The updated customer data on success, None otherwise.
        """

        self.logger.debug(f"Entering update_customer_record() for module {module}, record ID {customer_id}")

        if not self.check_if_module_is_supported(module):
            supported_modules = ', '.join(self.SUPPORTED_MODULES)
            self.logger.error(f"Module '{module}' is not supported. Supported modules are: {supported_modules}.")
            return None

        headers = self._get_headers()
        if headers is None:
            self.logger.error("Failed to obtain authorization headers.")
            return None

        # Prepare the update payload with only the fields that are provided
        update_payload = {"data": [{"id": customer_id}]}
        if subscriptions_customer_profile:
            update_payload["data"][0]["Subscriptions_Customer_Profile"] = subscriptions_customer_profile
        if traq_profile_url:
            update_payload["data"][0]["TRAQ_Profile_URL"] = traq_profile_url

        endpoint = f"{module}"  # Use the module parameter to target the correct API endpoint
        response = self.put(endpoint, json=update_payload, headers=headers)

        if response is None:
            error_message = f"Failed to update customer in module '{module}' with ID {customer_id}. No response received. Check to ensure your inputs are valid."
            self.logger.error(error_message)
            raise Exception(error_message)

        elif response.status_code == 200:
            self.logger.info(f"Customer in module '{module}' with ID {customer_id} updated successfully.")
            response_json = response.json()
            return response_json
        else:
            error_message = (f"Failed to update customer in module '{module}' with ID {customer_id}. "
                         f"Status Code: {response.status_code}, Response: {response.text}")
            self.logger.error(error_message)
            raise Exception(error_message)

    # -----------------------------------------------------------------
    # Method - Get Deals
    # -----------------------------------------------------------------

    def get_deals(self, deal_id=None, page=1):
        """
        Fetches deal records from the Zoho CRM API based on the specified criteria.
        :param deal_id: The ID of the deal to fetch.
        :param page: The page number to fetch.
        """
        self.logger.debug("Entering get_deals()")

        endpoint = "Deals"
        params = {}
        data_key = "data"

        if deal_id:
            try:
                deal_id = int(deal_id)
            except:
                self.logger.error("Invalid deal_id provided.")
                return None
            endpoint += f"/{deal_id}"

        all_deals = self._fetch_data(endpoint, initial_params=params, data_key=data_key, page=page)

        self.logger.debug(f"Exiting get_deals() with total {len(all_deals)} deals fetched")
        return all_deals

    # -----------------------------------------------------------------
    # Method - Get Supported Modules
    # -----------------------------------------------------------------

    def get_supported_modules(self):
        return self.SUPPORTED_MODULES

    def check_if_module_is_supported(self, module, ):
        if module in self.SUPPORTED_MODULES:
            return True
        else:
            return False

    # -----------------------------------------------------------------
    # Method - Query the CRM Database
    # -----------------------------------------------------------------
    
    def coql_query(self, select_query, limit=2000):
        """
        Executes a COQL query to fetch records from Zoho CRM (10,000 row maximum)

        :param select_query: The base COQL select query as a string (without LIMIT and OFFSET).
        :param limit: The number of records to fetch per query (1 to 200 = 1 API credit, 201-1000 = 2 API credits, 1001-2000 = 3 API credits).

        :return: List of fetched records, up to 10,000 rows maximum.

        :additional info: https://www.zoho.com/crm/developer/docs/api/v6/COQL-Overview.html
        """
        
        self.logger.debug(f"Entering execute_coql_query() with query: {select_query}")
        original_base_url = self.base_url  # Save the original base_url to revert it after the COQL query
        self.base_url = "https://www.zohoapis.com/crm/v6/"  # Change base_url to v6 for COQL query as it only exists in v6 API
        endpoint = "coql"
        headers = self._get_headers()
        if headers is None:
            self.logger.error("Failed to get headers, cannot execute COQL query.")
            return None

        # Raise ValueError if the query contains "LIMIT" or "OFFSET", as these are added based on the limit parameter
        if "limit " in select_query.lower() or "offset " in select_query.lower():
            error_message = "Your query should not contain LIMIT or OFFSET. Enter the limit as a parameter."
            self.logger.error(error_message)
            raise ValueError(error_message)

        params = {
            "select_query": select_query
        }

        all_records = []
        offset = 0

        while True:
            paginated_query = f"{select_query} LIMIT {limit} OFFSET {offset}"
            self.logger.info(f"Fetching data from COQL query: OFFSET {offset}")

            params = {
                "select_query": paginated_query
            }

            response = self.post(endpoint, json=params, headers=headers)
            if response is None:
                self.logger.error("Response is None. Check to make sure your query is correct.")
                break

            elif response.status_code == 204:  # no data in response

                self.logger.error("No data found in response.")
                break
            elif response.status_code != 200:
                self.logger.error(f"Error executing COQL query: {response.status_code} - {response.text}")
                break
                
            data = response.json()
            if "data" in data:
                all_records.extend(data["data"])
                if len(data["data"]) < limit:
                    # If fewer records are returned than the limit, we have fetched all records
                    break
                offset += limit
                if offset + limit > 10000:
                    self.logger.error("Your query exceeds the 10,000 row limit.")
                    raise ValueError("Query exceeds the 10,000 row limit")
            else:
                self.logger.error(f"No data found in response: {data}")
                break

        self.base_url = original_base_url # Revert the base_url back to the original after the COQL query
        self.logger.info(f"Exiting execute_coql_query() with total {len(all_records)} records fetched")
        return all_records

