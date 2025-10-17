from ..exec import ImobPost

class Condominio(ImobPost):
    def __init__(self, url:str, token:str):
        super().__init__(url)
        self._token = token
        
    def CONDOM_CONDOMINIO_CONSULTAR(self, cod_condominio:str)  -> tuple[bool, dict | str]:
        data = {
            "Header":{
                "SessionId":self._token,
                "Action":"CONDOM_CONDOMINIO_CONSULTAR"
            },
            "Body":{
                "CodCondominio":cod_condominio
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
        
    def CONDOM_CONDOMINIO_PESQUISAR(self, cnpj:str, qtd_linhas:int)  -> tuple[bool, dict | str]:
        data = {
            "Header":{
                "SessionId":self._token,
                "Action":"CONDOM_CONDOMINIO_PESQUISAR"
            },
            "Body":{
                "Texto":cnpj,
                "OrdenarPor":"C",
                "PesquisarPor":"C",
                "IncluiInativos":"N",
                "QtdeLinhas":qtd_linhas,
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
        return False, response["Body"]["Condominios"]
        