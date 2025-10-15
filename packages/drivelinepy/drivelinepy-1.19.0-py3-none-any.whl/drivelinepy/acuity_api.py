from .base_api_wrapper import BaseAPIWrapper
import base64

class AcuityAPI(BaseAPIWrapper):
    """
    Wrapper for the Acuity Scheduling API.
    Documentation: https://developers.acuityscheduling.com/reference/
    """

    
    #---------------------------------------------------------------------------
    # Constructor
    #---------------------------------------------------------------------------

    def __init__(self, user_id, api_key):
        """
        Initialize the Acuity API wrapper.
        
        :param user_id: Acuity User ID
        :param api_key: Acuity API Key
        """
        super().__init__(base_url="https://acuityscheduling.com/api/v1/")
        
        # Create basic auth header using user_id and api_key
        auth_string = f"{user_id}:{api_key}"
        auth_bytes = auth_string.encode('ascii')
        base64_auth = base64.b64encode(auth_bytes).decode('ascii')
        self.headers = {
            'Authorization': f'Basic {base64_auth}',
            'Content-Type': 'application/json'
        }

    #---------------------------------------------------------------------------
    # Method - Get Appointments
    #---------------------------------------------------------------------------

    def get_appointments(self, max=100, min_date=None, max_date=None, calendar_id=None, 
                        appointment_type_id=None, canceled=False, first_name=None, 
                        last_name=None, email=None, phone=None, field_id=None, 
                        exclude_forms=False, direction="DESC", additional_params=None):
        """
        Get list of appointments.
        
        :param max: Maximum number of results (default: 100)
        :param min_date: Only get appointments this date and after (YYYY-MM-DD)
        :param max_date: Only get appointments this date and before (YYYY-MM-DD)
        :param calendar_id: Show only appointments on calendar with specified ID
        :param appointment_type_id: Show only appointments of this type
        :param canceled: Get canceled appointments (default: False)
        :param first_name: Filter appointments for client first name
        :param last_name: Filter appointments for client last name
        :param email: Filter appointments for client email address
        :param phone: Filter appointments for client phone
        :param field_id: Filter appointments matching a particular custom intake form field
        :param exclude_forms: Don't include intake forms in response (default: False)
        :param direction: Sort direction, ASC or DESC (default: DESC)
        :param additional_params: Optional dictionary of additional query parameters
        :return: JSON response with appointments data
        """
        params = {
            'max': max,
            'minDate': min_date,
            'maxDate': max_date,
            'calendarID': calendar_id,
            'appointmentTypeID': appointment_type_id,
            'canceled': canceled,
            'firstName': first_name,
            'lastName': last_name,
            'email': email,
            'phone': phone,
            'field:id': field_id,
            'excludeForms': exclude_forms,
            'direction': direction
        }
        
        response = self.get(
            path="appointments",
            headers=self.headers,
            params=self._prepare_params(params, additional_params)
        )
        return response.json() if response else None

    #---------------------------------------------------------------------------
    # Method - Get Appointment
    #---------------------------------------------------------------------------

    def get_appointment(self, appointment_id, past_form_answers=False):
        """
        Get a specific appointment by ID.
        
        :param appointment_id: ID of the appointment
        :param past_form_answers: Include previous answers given to the intake forms (default: False)
        :return: JSON response with appointment data
        """
        params = {
            'pastFormAnswers': past_form_answers
        }
        
        response = self.get(
            path=f"appointments/{appointment_id}",
            headers=self.headers,
            params=params
        )
        return response.json() if response else None
    
    #---------------------------------------------------------------------------
    # Method - Get Calendars
    #---------------------------------------------------------------------------

    def get_calendars(self):
        """
        Get list of calendars.
        
        :return: JSON response with calendars data
        """
        response = self.get(
            path="calendars",
            headers=self.headers
        )
        return response.json() if response else None

    #---------------------------------------------------------------------------
    # Method - Get Clients
    #---------------------------------------------------------------------------

    def get_clients(self, search: str = None):
        """
        Get list of clients.
        
        :param search: Filter client list by first name, last name, phone number, email, etc
        :return: JSON response with clients data
        """
        params = {
            'search': search
        }
        
        response = self.get(
            path="clients",
            headers=self.headers,
            params=self._prepare_params(params)
        )
        return response.json() if response else None

    #---------------------------------------------------------------------------
    # Method - Create Client
    #---------------------------------------------------------------------------

    def create_client(self, first_name: str, last_name: str, email: str = None, 
                     phone: str = None, notes: str = None, additional_params: dict = None):
        """
        Create a new client.
        
        :param first_name: Client's first name
        :param last_name: Client's last name
        :param email: Client's email address (optional)
        :param phone: Client's phone number (optional)
        :param notes: Additional notes about the client (optional)
        :param additional_params: Optional dictionary of additional parameters
        :return: JSON response with created client data
        """
        payload = {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "phone": phone,
            "notes": notes
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        # Add any additional parameters
        if additional_params:
            payload.update(additional_params)
            
        response = self.post(
            path="clients",
            headers=self.headers,
            json=payload
        )
        return response.json() if response else None


