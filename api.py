import requests
import json

class Api():
    def __init__(self):
        self.api_endpoint = "http://diamonds.etimo.se/api/"
        self.data = {}
        
    def set_data(self, data):
        self.data = data
        
    def _req(self, api, protocol):
        headers = {
            "Content-Type": "application/json"
        }
        if(protocol == "POST"):
            return requests.post(url = self.api_endpoint + api, headers = headers, data =json.dumps(self.data), timeout=2, verify=False)
        return requests.get(self.api_endpoint+api, timeout=2, verify=False)
