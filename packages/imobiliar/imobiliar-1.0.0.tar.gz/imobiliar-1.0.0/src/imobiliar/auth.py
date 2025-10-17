from .exec import ImobPost
class ImobAuth(ImobPost):
    def __init__(self, url: str, user: str, password: str):
        super().__init__(url)
        self._user = user
        self._password = password
        self.token = None
    
    def login(self, imob_id:str) -> tuple[bool, dict | str]:
        data = {
            'Header':{
            'Action':"LOGIN"
            },
            'Body':{
                'IMOB_ID':imob_id,
                'USER_ID':self._user,
                'USER_PASS':self._password
            },
        }
        error, response = self.post(data=data)
        if error:
            message = None
            try:
                message = response["Body"]["Erros"]
            except:
                message = response
            return error, message
        self.token = response["Header"]["SessionId"]
        return False, "Login feito com sucesso"
    
    def logout(self) -> dict|str:
        data = {
            'Header':{
            'SessionId':self.token,
            'Action':"LOGOUT"
            },
            'Body':{
            },
        }
        response = self.post(data=data)
        return response