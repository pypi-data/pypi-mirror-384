import os
from selenium.webdriver import Chrome
from Adlib.logins import getCredenciais
from Adlib.funcoes import mensagemTelegram, esperarElemento
from Adlib.virtaus import selectOption
from Adlib.apiConferirRg import enviarDocumentos
from Adlib.apiValid import obterToken, coletarAnalysisId, verificarFraude
from Adlib.utils import tokenBotAnaliseDocs, chatIdAnalise
import time
from Adlib.api import postSolicitacao, putStatusSolicitacao, EnumStatusSolicitacao

loginValid, senhaValid = getCredenciais(714)


def processarDocumentos(pastaDestino, virtaus, solicitacaoVirtaus, tokenTelegram, chatIdTelegram, cpfParceiro, id):
    try:
        status_code, resposta_api, documentos_true = enviarDocumentos(pastaDestino)
        documentos_true = documentos_true[:2]  # só 2 documentos True
        print(f"Documentos com resposta True: {documentos_true}")
        print(f"{status_code}")
        print(f"{resposta_api}")

        if not documentos_true:
            print("Não haviam Documentos/Documentos inválidos ❌")
            return acaoFalha(
                virtaus,
                tokenTelegram,
                chatIdTelegram,
                solicitacaoVirtaus,
                motivo="Não haviam Documentos/Documentos inválidos ❌",
                id=id
            )

        listaDocumentosTrue = [os.path.join(pastaDestino, f) for f in documentos_true]
        token = obterToken(loginValid, senhaValid)

        if not token:
            print("Token inválido ❌")
            return acaoFalha(
                virtaus,
                tokenTelegram,
                chatIdTelegram,
                solicitacaoVirtaus,
                motivo="Token inválido ❌",
                id=id
            )

        analisysID = coletarAnalysisId(token, cpfParceiro, listaDocumentosTrue)
        print("Analise iniciada, ID:", analisysID)

        if not analisysID:
            print("Análise ID inválido ❌")
            return acaoFalha(
                virtaus,
                tokenTelegram,
                chatIdTelegram,
                solicitacaoVirtaus,
                motivo="Falha ao coletar analysisID ❌",
                id=id
            )

        validarDocumento = verificarFraude(token, analisysID, 350, 40)
        print("Análise de fraude concluída:", validarDocumento, '📝')

        if validarDocumento is True:
            print("Score maior que 80 ✅")
            return acaoSucesso(
                virtaus,
                tokenTelegram,
                chatIdTelegram,
                solicitacaoVirtaus,
                mensagem="Movimentado para: Aguardando Videochamada ✅",
                id=id
            )
        else:
            return acaoFalha(
                virtaus,
                tokenTelegram,
                chatIdTelegram,
                solicitacaoVirtaus,
                motivo=f"Score {validarDocumento} menor que 80 ❌",
                id=id
            )

    except Exception as e:
        print("Erro em processarDocumentos:", e)
        return acaoFalha(
            virtaus,
            tokenTelegram,
            chatIdTelegram,
            solicitacaoVirtaus,
            motivo=f"Erro ao baixar/processar documentos ❌: {e}",
            id=id
        )


def limparPastaDestino(pastaDestino):
    for arquivo in os.listdir(pastaDestino):
        caminho_arquivo = os.path.join(pastaDestino, arquivo)
        try:
            os.remove(caminho_arquivo)
            print(f'Arquivo {arquivo} apagado 🗑️')
        except Exception as e:
            print(f'Erro ao apagar o arquivo {arquivo}: {e}')


def acaoSucesso(virtaus, tokenTelegram, chatIdTelegram, solicitacao, mensagem, id):
    try:
        print("Análise concluída 📝")
        finalizarSolicitacao(virtaus, id)
        mensagemTelegram(
            tokenTelegram,
            chatIdTelegram,
            f"Análise de Documentos <b>C6</b> Solicitação: {solicitacao}\n {mensagem}"
        )
    except Exception as e:
        print(f"Erro ao finalizar solicitação com sucesso: {e}")


def acaoFalha(virtaus, tokenTelegram, chatIdTelegram, solicitacao, motivo, id):
    try:
        finalizarSolicitacao(virtaus, id, status='Aguardando analise')
        mensagemTelegram(
            tokenTelegram,
            chatIdTelegram,
            f"Análise de Documentos <b>C6</b> Solicitação: {solicitacao}\n"
            f"Movimentado para: Aguardando Análise 🔍\n {motivo}"
        )
    except Exception as e:
        print(f"Erro ao finalizar solicitação com falha: {e}")


def finalizarSolicitacao(virtaus: Chrome, id: int, status: str = 'Aguardando Videochamada'):
    print("Finalizando solicitação...")
    try:
        virtaus.switch_to.default_content()
        iframe = esperarElemento(virtaus, '//*[@id="workflowView-cardViewer"]')
        virtaus.switch_to.frame(iframe)

        try:
            esperarElemento(virtaus,'/html/body/div[1]/form/div/div[1]/div[4]/div[2]/div/div/div[3]/span/div/button',
                tempoEspera=3,
                debug=False
            ).click()
            selectCheckBox = esperarElemento(virtaus,'//*[@id="abaDadosGerais"]/div[4]/div[2]/div/div/div[3]/span/div/ul/li[2]/a/label/input',
                tempoEspera=3,
                debug=False
            )
            if not selectCheckBox.is_selected():
                selectCheckBox.click()
        except Exception:
            pass

        time.sleep(5)

        virtaus.switch_to.default_content()
        esperarElemento(virtaus, '//*[@id="send-process-button"]').click()

        selectOption(virtaus, '//*[@id="nextActivity"]', status)
        esperarElemento(virtaus, '//*[@id="moviment-button"]').click()

        putStatusSolicitacao(id, EnumStatusSolicitacao.CONCLUIDO)

    except Exception as e:
        print(f"Erro ao localizar elemento: {e}")
