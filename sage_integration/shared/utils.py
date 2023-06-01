# importation des modules nécessaires
from zeep import Client
from zeep.wsse.username import UsernameToken
from zeep.transports import Transport
from requests import Session
import frappe

def get_x3_articles():
    # déclaration des variables
    wsdl = 'http://dc7-web.marsavco.com:8124/soap-wsdl/syracuse/collaboration/syracuse/CAdxWebServiceXmlCC?wsdl'
    username = 'kossivi'
    password = 'A2ggrb012345-'

    # initialisation du client SOAP
    #session = Session()
    #session.auth = UsernameToken(username, password)
    #transport = Transport(session=session)
    client = Client(wsdl=wsdl)

    # Ajout des en-têtes SOAP
    headers = {
        'poolAlias': 'LIVE',
        'codeLang': 'ENG',
        'codeUser': 'kossivi', 
        'password': 'A2ggrb012345-',
    }
    client.set_default_soapheaders(headers)

    # appel du service web ZITMLIST pour récupérer les articles non synchronisés
    article_list = []
    try:
        result = client.service['ZPAYMLIST']( {'ZCODE': 'DM000011','ZDATE1': '20230101','ZDATE2': '20231231','ZSTAT': '0','ZTYPE': 'R'})
        for article in result[0]:
            article_list.append({'code': article.BPR, 'description': article.BPANAM})
    except Exception as e:
        frappe.log_error(e)

    # affichage des résultats
    for article in article_list:
        print(str(article))

    return article_list