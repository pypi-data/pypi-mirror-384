import requests
import json

class Xurl:
    """
    A class to represent a cURL command.
    """
    def __init__(self, url: str,
                 headers: dict = None,
                 data: str = None,
                 params: dict = None,
                 json: dict = None,
                 auth: tuple = None,
                 ntlm_auth: object = None,
                 verify_ssl: bool = False):
        self.url = url
        self.headers = headers
        self.data = data
        self.params = params
        self.json = json
        self.auth = auth
        self.ntlm_auth = ntlm_auth  # Added to handle NTLM authentication   
        self.verify_ssl = verify_ssl  # Added to handle SSL verification

    #add code that will implement get and post methods using requests library
    def get(self):
        """
        Perform a GET request using the requests library.
        
        Returns:
            dict: JSON response with cookies
            
        Raises:
            requests.RequestException: If the request fails
        """
        try:
            # Build kwargs dictionary with only non-None values
            kwargs = {
                'url': self.url,
                'verify': self.verify_ssl
            }
            
            # Add optional parameters if they exist
            if self.headers:
                kwargs['headers'] = self.headers
            if self.params:
                kwargs['params'] = self.params
            if self.auth:
                kwargs['auth'] = self.auth
            if self.ntlm_auth:
                kwargs['auth'] = self.ntlm_auth

            # print all kwargs for debugging
            print(f"[xursparks.http.main][GET] Request parameters: {kwargs}")
            
            # Make the request with only non-None parameters
            response = requests.get(**kwargs)
            response.raise_for_status()
            
            # Get cookies from response
            cookies = response.cookies.get_dict()
            
            # Combine response JSON and cookies
            # Try to parse JSON, if fails return text response
            try:
                resp_data = response.json()
                resp_data['cookies'] = cookies
            except json.JSONDecodeError:
                resp_data = {
                    'text': response.text,
                    'cookies': cookies
                }
            # print(f"[xursparks.http.main][GET] Response data: {resp_data}")
            return resp_data
        except requests.RequestException as e:
            print(f"Request failed: {str(e)}")
            raise
    
    
    #add code that will implement post method using requests library
    def post(self):
        """
        Perform a POST request using requests library.
        
        Returns:
            dict: JSON response with cookies
            
        Raises:
            requests.RequestException: If the request fails
        """
        # print all kwargs for debugging
        print(f"[xursparks.http.main][POST] Request parameters: {kwargs}")
        try:
            # Build kwargs dictionary with only non-None values
            kwargs = {
                'url': self.url,
                'verify': self.verify_ssl
            }
            
            # Add optional parameters if they exist
            if self.headers:
                kwargs['headers'] = self.headers
            if self.params:
                kwargs['params'] = self.params
            if self.data:
                kwargs['data'] = self.data
            if self.json:
                kwargs['json'] = self.json
            if self.auth:
                kwargs['auth'] = self.auth
            
            # Make the request with only non-None parameters
            response = requests.post(**kwargs)
            response.raise_for_status()
            
            # Get cookies from response
            cookies = response.cookies.get_dict()
            
            # Combine response JSON and cookies
            try:
                resp_data = response.json()
                resp_data['cookies'] = cookies
            except json.JSONDecodeError:
                resp_data = {
                    'text': response.text,
                    'cookies': cookies
                }
            # print(f"[xursparks.http.main][POST] Response data: {resp_data}")
            return resp_data
        except requests.RequestException as e:
            print(f"Request failed: {str(e)}")
            raise

if __name__ == "__main__":
    pass
