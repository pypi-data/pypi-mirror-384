from .main import Xurl
from ...tools.logger import Logger

class APIService:
    def __init__(self, base_url: str = None,
                 args: dict = None):
        self.base_url = base_url
        self.args = args

    def processRequest(self):
        """
        Get the response from the args dictionary.
        Returns:
            str: The response if available, otherwise None.
        """
        base_url = self.base_url
        xurl_json = self.args.get("json")
        xurl_auth = self.args.get("auth")
        if xurl_auth is None:
            xurl_auth = self.args.get("ntlm_auth")
        xurl_headers = self.args.get("headers")
        xurl_method = self.args.get("method", "GET")
        xurl_verify_ssl = self.args.get("verify_ssl", False)
        # print("************** [xursparks.services.http.api_service.processRequest] START **************")
        # print(f'base_url: {base_url}')
        # print(f'xurl_json: {xurl_json}')
        # print(f'xurl_auth: {xurl_auth}')
        # print(f'xurl_method: {xurl_method}')
        # print(f'xurl_verify_ssl: {xurl_verify_ssl}')
        # print(f'xurl_headers: {xurl_headers}')
        # print("************** [xursparks.services.http.api_service.processRequest] END **************")
        xurl = Xurl(
            url=base_url,
            headers=xurl_headers,
            json=xurl_json,
            auth=xurl_auth,
            verify_ssl=xurl_verify_ssl,
        )
        print(f'xurl[processRequest]: {str(xurl)}')
        if xurl_method.upper() == "POST":
            response = xurl.post()
        else:
            response = xurl.get()
        Logger().log(f'xurl[processRequest]: {response}', level='debug')
        return response