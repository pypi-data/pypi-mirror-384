# Biblioteca de Integração Imobiliária

Este projeto contém classes para integração com uma API imobiliária e suporte a operações auxiliares, como autenticação e upload de documentos no **Amazon S3**.  

O nome dos metodos são os mesmos nomes dos endpoints da API, então se precisar saber mais sobre o enpoint [clique aqui](http://credreal.imobiliar.com.br:5001/webservice/Imobiliar2).
Tem algumas funções que possuem o paramêtro body, elas são do tipo dict, para construir esse body se baseie no campo "Body" do endpoint. 

## Estrutura das Classes

### `ImobPost` (arquivo: `exec.py`)
Classe base responsável por enviar requisições **HTTP POST** para a API.  
- **Atributos**:
  - `_url`: URL base da API.  
- **Métodos**:
  - `post(data)`: envia uma requisição POST com payload em JSON. Retorna uma tupla `(erro, resposta)`.

---

### `ImobAuth` (arquivo: `auth.py`)
Classe de autenticação, herda de `ImobPost`.  
- **Atributos**:
  - `_user`: usuário da API.  
  - `_password`: senha da API.  
  - `token`: token de sessão retornado pelo login.  
- **Métodos**:
  - `login(imob_id)`: autentica na API, retornando o token de sessão.  
  - `logout()`: encerra a sessão autenticada.  

---

### `ClientS3` (arquivo: `s3_client.py`)
Cliente para upload de arquivos no **Amazon S3**.  
- **Atributos**:
  - `_s3`: instância do cliente boto3 configurado.  
- **Métodos**:
  - `login(access_key, secret_key)`: autentica no S3 com credenciais da AWS.  
  - `upload_file(bucket, filepath)`: envia um arquivo PDF para o bucket informado.  

---

### `Condominio` (arquivo: `condominos.py`)
Classe para operações relacionadas a condomínios. Herda de `ImobPost`.  
- **Atributos**:
  - `_token`: token de sessão.  
- **Métodos**:
  - `CONDOM_CONDOMINIO_CONSULTAR(cod_condominio)`: consulta informações de um condomínio específico.  
  - `CONDOM_CONDOMINIO_PESQUISAR(cnpj, qtd_linhas)`: pesquisa condomínios por CNPJ.  

---

### `ContaPagar` (arquivo: `contas_pagar.py`)
Classe para operações de contas a pagar. Herda de `ImobPost`.  
- **Atributos**:
  - `_token`: token de sessão.  
- **Métodos**:
  - `CTAPAG_LANCAMENTO_ADICIONAR_IMAGEM(lancto, url_doc)`: adiciona uma imagem a um lançamento.  
  - `CTAPAG_CONDOMINIO_INCLUIR(body)`: cria um novo lançamento de contas a pagar.  
  - `CTAPAG_CODBARRAS_CONSULTAR(cod_barras)`: consulta informações a partir de um código de barras.  
  - `CTAPAG_LANCAMENTO_EXCLUIR(lancto, excluir_prvisao)`: exclui um lançamento.  
  - `CTAPAG_LANCAMENTO_PESQUISAR(body)`: pesquisa lançamentos com base em critérios definidos.  
  - `CTAPAG_LANCAMENTO_CONSULTAR(lancto)`: consulta detalhes de um lançamento específico.  

---

## Pacote (`__init__.py`)
O pacote exporta as seguintes classes para uso externo:  
- `ImobAuth`  
- `ImobPost`  
- `ClientS3`  
- `ContaPagar`  
- `Condominio`  

---

## Exemplo de Uso

```python
from imoblib import ImobAuth, ContaPagar

# Autenticação
auth = ImobAuth(url="https://api.exemplo.com", user="usuario", password="senha")
error, message = auth.login(imob_id="123")

if not error:
    conta = ContaPagar(url="https://api.exemplo.com", token=auth.token)
    error, lancamentos = conta.CTAPAG_LANCAMENTO_PESQUISAR({"CodCondominio": "001"})
    print(lancamentos)
```
