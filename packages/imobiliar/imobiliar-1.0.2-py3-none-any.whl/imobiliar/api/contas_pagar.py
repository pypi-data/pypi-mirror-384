from ..exec import ImobPost

class ContaPagar(ImobPost):
    def __init__(self, url:str, token:str):
        super().__init__(url)
        self._token = token
        
    def CTAPAG_LANCAMENTO_ADICIONAR_IMAGEM(self, lancto: int, url_doc: str) -> tuple[bool, dict | str]:
        data = {
            'Header':{
                'SessionId':self._token,
                'Action':"CTAPAG_LANCAMENTO_ADICIONAR_IMAGEM"
            },
            'Body':{
                'NumeroLancto':lancto,
                'UrlImagem':url_doc
            },
        }       
        error, response = self.post(data, data=data)
        
        if error:
            message = None
            try:
                message = response["Body"]["Erros"]
            except:
                message = response
            return error, message
        return False, response["Body"]["NumeroLancto"]
    
    def CTAPAG_CONDOMINIO_INCLUIR(self, body:dict) -> tuple[bool, dict | str]:
        data = {
            'Header':{
                'SessionId':self._token,
                'Action':"CTAPAG_CONDOMINIO_INCLUIR"
            },
            'Body': body,
        }     
        error, response = self.post(data, data=data)
        
        if error:
            message = None
            try:
                message = response["Body"]["Erros"]
            except:
                message = response
            return error, message
        return False, response["Body"]["NumeroLancto"]
    
    def CTAPAG_CODBARRAS_CONSULTAR(self, cod_barras: str) -> tuple[bool, dict | str]:
        data = {
            "Header":{
                "SessionId":self._token,
                "Action":"CTAPAG_CODBARRAS_CONSULTAR"
            },
            "Body":{
                "CodigoBarras":cod_barras
            }
        }
        error, response = self.post(data, data=data)
        
        if error:
            message = None
            try:
                message = response["Body"]["Erros"]
            except:
                message = response
            return error, message
        return False, response["Body"]

    def CTAPAG_LANCAMENTO_EXCLUIR(self, lancto:int, excluir_prvisao:str = "N")  -> tuple[bool, dict | str]:
        data = {
            "Header":{
                "SessionId":self._token,
                "Action":"CTAPAG_LANCAMENTO_EXCLUIR"
            },
            "Body":{
                "NumeroLancto":lancto,
                "ExcluirPrevisao":excluir_prvisao
            }
        }
        error, response = self.post(data, data=data)
        
        if error:
            message = None
            try:
                message = response["Body"]["Erros"]
            except:
                message = response
            return error, message
        return False, response["Body"]["NumeroLancto"]

    def CTAPAG_LANCAMENTO_PESQUISAR(self, body: dict) -> tuple[bool, dict | str]:
        
        data = {
            "Header":{
                "SessionId":self._token,
                "Action":"CTAPAG_LANCAMENTO_PESQUISAR"
            },
            "Body":body
        }
        error, response = self.post(data, data=data)
        
        if error:
            message = None
            try:
                message = response["Body"]["Erros"]
            except:
                message = response
            return error, message
        return False, response["Body"]["Lancamentos"]
    

    def CTAPAG_LANCAMENTO_CONSULTAR(self, lancto: str) -> tuple[bool, dict | str]:
        
        data = {
            "Header":{
                "SessionId":self._token,
                "Action":"CTAPAG_LANCAMENTO_CONSULTAR"
            },
            "Body": {
                "NumeroLancto": lancto
            }
        }
        error, response = self.post(data, data=data)
        
        if error:
            message = None
            try:
                message = response["Body"]["Erros"]
            except:
                message = response
            return error, message
        return False, response["Body"]