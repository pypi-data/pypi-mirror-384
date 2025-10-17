import requests

class ImobPost:
    
    def __init__(self, url:str):
        self._url = url
    
    def post(self, data) -> tuple[bool, dict | str]:
        
        response = requests.post(self._url, json=data)
        if response.status_code != 200:
            return True, response
        response_json = response.json()
        return response_json["Header"]["Error"], response_json