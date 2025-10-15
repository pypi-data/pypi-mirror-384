import time
import logging
import requests
from datetime import datetime
from Adlib.funcoes import getCredenciais 

usernameValid, passwordValid = getCredenciais(714)

BASE_URL = "https://services.flexdoc-apis.com.br/services/api"
 
 
def obterToken(username: str, password: str) -> str:
    """
    Obtém o token de autenticação usando as credenciais fornecidas.
 
    :param username: Nome de usuário
    :param password: Senha
    :return: Token de acesso ou None em caso de erro
    """
    auth_url = f"{BASE_URL}/v1/authentication"
    auth_payload = {"username": username, "password": password}
    auth_headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
 
    response = requests.post(auth_url, json=auth_payload, headers=auth_headers)
 
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Erro ao obter token: {response.status_code} - {response.text}")
        return None
 

def coletarAnalysisId(token: str, cpf: str, images: list, institution: str = "Ad Promotora", id_lote: str = "", parent_id: str = ""):
    """
    Envia documentos para análise de fraude e retorna o resultado da API.

    :param token: JWT para autenticação.
    :param cpf: CPF do cliente (string).
    :param images: Lista de caminhos de arquivos de imagem.
    :param institution: Nome da instituição. Default = 'Ad Promotora'.
    :param id_lote: ID do lote, se houver.
    :param parent_id: ParentId, se houver.
    :return: JSON com a resposta da API.
    """

    url = f"{BASE_URL}/adpromo/v1/fraud/analysis"

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # multipart precisa repetir o campo "images" -> usar lista de tuplas
    files = [
        ("idLote", (None, id_lote)),
        ("institution", (None, institution)),
        ("cpf", (None, cpf)),
    ]

    for image in images:
        try:
            files.append(("images", (image.split("/")[-1], open(image, "rb"), "image/jpeg")))
        except FileNotFoundError:
            logging.error(f"Arquivo não encontrado: {image}")
            raise

    files.append(("parentId", (None, parent_id)))

    while True:
        try:
            response = requests.post(url, headers=headers, files=files, timeout=60)
            response.raise_for_status()
            logging.info(f"Análise de fraude concluída para CPF {cpf}.")
            return response.json().get("analysisId")
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro na análise de fraude para CPF {cpf}: {e}")
            raise


def verificarFraude(token: str, analysisId: str, timeout: int = 300, intervalo: int = 40) -> bool:
    
    """
    Verifica o status da análise de fraude usando o analysisId.
    Espera até o status ser DONE (ou estourar o timeout).
    Retorna True se score >= 80, senão False.
    """

    url = f"{BASE_URL}/adpromo/v1/fraud/analysis/{analysisId}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    inicio = time.time()

    while True:
        if time.time() - inicio > timeout:
            logging.error("Timeout esperando status DONE")
            return False

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao verificar análise de fraude: {e}")
            return False

        status = data.get("status")
        logging.info(f"Status da análise {analysisId}: {status}")

        if status == "DONE":
            
            analyses = data.get("analysis", [])
            for a in analyses:
                score_result = a.get("scoreResult", {})
                score = score_result.get("score")
                try:
                    if score is not None and int(score) >= 80:
                        return True
                except (ValueError, TypeError):
                    logging.warning(f"Score inválido: {score}")
                    return False
            return False  # se não achou nenhum score >= 80
        if status == "REJECTED":
            logging.error(f"Análise {analysisId} falhou.")
            return False
        
        time.sleep(intervalo)


def main(): 
    token = obterToken(usernameValid, passwordValid)
    analysisId = coletarAnalysisId(token, "12345678909", ["RG Frente.jpg", "RG Verso.jpg"])
    verificarFraude(token, analysisId)
 
 
if __name__ == "__main__":
    main()
 