import time
from selenium.webdriver import Chrome
from Adlib.api import putStatusSolicitacao, EnumStatusSolicitacao, EnumStatus, putTicketBlip, putHoraFinalFunction
from Adlib.funcoes import moveToElement, esperarElemento, mensagemTelegram

def ficarOnline(blip: Chrome):
    try:
        ficarOnline = blip.find_element('id' , 'set-online-btn')
        ficarOnline.click()
        time.sleep(5)
        logging.info("🟢 Ficou online")
    except:
        print("ja esta online")
        time.sleep(5)


def transferiTicket(blip, tag, obsErro, ticket, fila):
    try:
        print("Iniciando transferência 🔁")

        transferir = blip.find_elements('xpath', '//*[@id="transfer-ticket-button"]')[0]
        transferir.click()
        time.sleep(3)

        selecionarFila = blip.find_element('xpath', '//*[@id="transfer-attendance"]/div[1]/div/div[2]/div[1]/bds-autocomplete')
        selecionarFila.click()                    
        time.sleep(3)    
        selecionarFila.send_keys(tag)              
        time.sleep(3)

        shadow_host = blip.find_element('css selector', '#transfer-attendance > div.transfer-modal-content.w-100 > div > div.select-field > div:nth-child(1) > bds-autocomplete')
        time.sleep(3)

        shadow_root = blip.execute_script("return arguments[0].shadowRoot", shadow_host)
        time.sleep(3)

        elemento_desejado = shadow_root.find_element('css selector', f'div.select__options.select__options--position-bottom.select__options--open > bds-select-option:nth-child({fila})')
        elemento_desejado.click()
        time.sleep(3)

        confirmarTransferencia = blip.find_element('xpath', '//*[@id="confirm-transfer-btn"]')
        confirmarTransferencia.click()

        putTicketBlip(EnumStatusSolicitacao.TRANSFERIDO, obsErro, ticket)
        putHoraFinalFunction(ticket)
        print("Ticket transferido 🔁")
    except Exception as e:
        print(f"❌ Erro na transferência: {e}")


def finalizarTicket(blip, token, chatId, mensagem, tipo = 'CONSULTA DE PROPOSTA',):
    esperarElemento(blip, '//*[@id="close-ticket-button"]').click()

    shadow_host = blip.find_element('css selector', '#close-attendance > div.modal-content-container > div.select-tag-container.w-70.body.bp-fs-6 > div > bds-select-chips')
    time.sleep(0.5)

    shadow_root = blip.execute_script("return arguments[0].shadowRoot", shadow_host)
    time.sleep(0.5)
    
    inputFinalizar = shadow_host
    inputFinalizar.click() 
    time.sleep(0.5)

    opcoes = blip.find_elements("xpath", "//*[local-name()='bds-select-option']")

    for opt in opcoes:
        label = opt.get_attribute("aria-label")
        if label and label.strip() == f"{tipo}":
            blip.execute_script("arguments[0].scrollIntoView({ block: 'center' });", opt)
            time.sleep(0.5)
            
            moveToElement(blip, f'//*[@aria-label="{tipo}"]', click=True)
            botaoFinalizarTicket = blip.find_element('xpath', '//bds-button[@id="confirm-close-btn" and contains(text(), "Finalizar ticket")]')
            botaoFinalizarTicket.click()
            mensagemTelegram(token, chatId, mensagem)
            print(mensagemTelegram)
            break