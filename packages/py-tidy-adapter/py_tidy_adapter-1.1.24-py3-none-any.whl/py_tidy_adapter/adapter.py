import base64
import gzip
import os
import pickle
from datetime import datetime
from typing import Dict, List
from pandas import DataFrame
import requests
from lxml import etree
import pandas as pd
from .class_business import ClassBusiness
from .exception import TidyException
from io import StringIO
import json
# from tensorflow import keras

TF_MODEL = 'tfModel'


class ServiceResponse(object):
    code: str = None
    time: int = None
    message: str = None
    detailMessage: str = None
    xml = None


class Adapter:
    """
    Classe da utilizzare per interfacciarsi al server tidy
    E' obbligatorio fornire l'endpoint a cui connettersi
    E' possibile fornire un idSessione di default utilizzato in ogni successiva chiamata,
    in alternativa ad ogni metodo è possibile fornire un idSessione specifico.
    """

    def __init__(self, endpoint: str = None, default_id_session: str = None, tidy_api_key: str = None):
        """
                :param endpoint: str . Endpoint del server Tidy
                :param default_id_session: str=None  Id sessione utilizzata come default se non specificata nel singolo metodo
                """
        if endpoint is not None:
            self.endpoint = endpoint
            self.default_id_session = default_id_session
        elif tidy_api_key is not None:
            try:
                split = base64.b64decode(tidy_api_key).decode().split('|||')
                self.endpoint = split[0]
                self.default_id_session = split[1]
            except:
                raise TidyException('TIDY_API_KEY non valida')
        else:
            if os.path.isfile('.env'):
                api_key = None
                with open('.env') as file:
                    for line in file:
                        if line.strip().startswith("TIDY_API_KEY"):
                            line = line.strip()
                            api_key = line[line.index('=') + 1:].strip()
                if api_key is None:  raise TidyException('Variabile TIDY_API_KEY non trovata nel file .env')
                try:
                    split = base64.b64decode(api_key).decode().split('|||')
                    self.endpoint = split[0]
                    self.default_id_session = split[1]
                except:
                    raise TidyException('TIDY_API_KEY non valida')
            else:
                raise TidyException('File .env non trovato')

    def set_default_id_session(self, default_id_session: str = None):
        """    Imposta l'id sessione di default, sovrascrive l'eventuale valore fornito nel costruttore.
                :param default_id_session: str=None  Id sessione utilizzata come default se non specificata nel singolo metodo
        """

        self.default_id_session = default_id_session

    def getsystemconfiguration(self) -> 'ws, app, properties, ServiceResponse':
        """
        Esegue l'azione GetSystemConfiguration sul server Tidy, restituendo:
          - la lista degli workspace
          - la lista delle applicazioni
          - la lista delle proprietà di configurazione
          - la risposta del servizio

        Questo metodo NON richiede un ID di sessione.

        Returns:
            tuple: Quattro elementi:
                - list of str: lista degli workspace
                - list of str: lista delle applicazioni
                - list of dict: lista delle proprietà di configurazione (chiave/valore)
                - ServiceResponse: oggetto con la risposta del server
    """
        request = f"""
                <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:it="it.itchange.bcr.basvi">
                   <soapenv:Header/>
                   <soapenv:Body>
                      <it:GetSystemConfiguration>
                         <GetSystemConfigurationRequest />
                      </it:GetSystemConfiguration>
                   </soapenv:Body>
                </soapenv:Envelope>    
       """
        response = requests.post(self.endpoint, request)
        doc = Adapter.__to_element__(response.text)

        sr = ServiceResponse()
        for child in doc[0][0][0]:
            setattr(sr, child.tag, etree.tostring(child[0]) if len(child) > 0 else child.text)
        xml = Adapter.__to_element__(sr.xml)
        return ([el.text for el in xml.xpath('workspaces/workspace')]
                , [el.text for el in xml.xpath('applications/application')]
                , [{el.xpath('key')[0].text: el.xpath('value')[0].text} for el in xml.xpath('properties/entry')]
                , sr)

    def login(self, user: str, password: str, workspace: str, name_application: str, type: str = 'NORMAL',
              as_user: str = None) -> 'ServiceResponse,str':
        """
        Effettua la login al server Tidy.

        Args:
            user (str): Nome utente.
            password (str): Password dell'utente.
            workspace (str): Workspace per cui si effettua la login.
            name_application (str): Application per cui si effettua la login.
            type (str, optional): Tipo di login. Può essere: NORMAL, PERMANENT, ONE_SHOT. Default è 'NORMAL'.
            as_user (str, optional): Nome utente usato per la connessione "as user". Default è None.

        Returns:
            tuple:
                - ServiceResponse: con informazioni sull'esito della chiamata.
                - str: idSession ottenuto dalla risposta, se presente.

        """
        request = f"""
                <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:it="it.itchange.bcr.basvi">
                   <soapenv:Header/>
                   <soapenv:Body>
                      <it:Login>
                         <LoginRequest>
                            <user>{user}</user>
                            {f'<asUser>{as_user}</asUser>' if as_user is not None else ''}                            
                            <password>{password}</password>
                            <workspace>{workspace}</workspace>
                            <nameApplication>{name_application}</nameApplication>
                            <type>{type}</type>
                         </LoginRequest>
                      </it:Login>
                   </soapenv:Body>
                </soapenv:Envelope>    
        """
        response = requests.post(self.endpoint, request)
        doc = Adapter.__to_element__(response.text)

        sr = ServiceResponse()
        for child in doc[0][0][0]:
            setattr(sr, child.tag, etree.tostring(child[0]) if len(child) > 0 else child.text)
        if sr.code == '0' or sr.code == '-1': self.default_id_session = sr.xml
        return sr, sr.xml

    def logout(self, id_session: str = None, background: bool = False) -> 'str,ServiceResponse':
        """
        Effettua il logout della sessione.

        Args:
            id_session (str, optional): Id sessione per cui si effettua il logout. Se None, viene usata la sessione di default.
            background (bool, optional): Flag per specificare la modalità di esecuzione. Default è False.

        Raises:
            TidyException: Se id_session non è specificato e non esiste una sessione di default.

        Returns:
            tuple:
                - str: messaggio di esito del logout.
                - ServiceResponse: con informazioni aggiuntive sulla risposta.
        """
        if id_session is None and self.default_id_session is None: raise TidyException('Id Sessione non specificato')
        request = f"""
                <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:it="it.itchange.bcr.basvi">
                   <soapenv:Header/>
                   <soapenv:Body>
                      <it:Logout>
                         <LogoutRequest>
                            <idSession>{id_session if id_session is not None else self.default_id_session}</idSession>
                            <background>{background}</background>
                         </LogoutRequest>
                      </it:Logout>
                   </soapenv:Body>
                </soapenv:Envelope>    
        """
        response = requests.post(self.endpoint, request)
        doc = Adapter.__to_element__(response.text)

        sr = ServiceResponse()
        for child in doc[0][0][0]:
            setattr(sr, child.tag, etree.tostring(child[0]) if len(child) > 0 else child.text)
        return sr.message, sr

    def nameClasses(self, id_session: str = None, background: bool = False) -> 'str[] , ServiceResponse':
        """
        Restituisce il nome di tutte le classi.

        Args:
            id_session (str, optional): Id sessione per cui si effettua la chiamata. Se None, viene usata la sessione di default.
            background (bool, optional): Flag per specificare la modalità di esecuzione. Default è False.

        Raises:
            TidyException: Se id_session non è specificato e non esiste una sessione di default.

        Returns:
            tuple:
                - list of str: lista dei nomi delle classi.
                - ServiceResponse: informazioni aggiuntive sulla risposta.
        """
        if id_session is None and self.default_id_session is None: raise TidyException('Id Sessione non specificato')
        request = f"""
                 <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:it="it.itchange.bcr.basvi">
                   <soapenv:Header/>
                   <soapenv:Body>
                      <it:GetInfoLogin>
                         <GetInfoLoginRequest >
                            <idSession>{id_session if id_session is not None else self.default_id_session}</idSession>
                            <lastVersion>true</lastVersion>
                            <bsc>true</bsc>
                            <abstracts>true</abstracts>
                            <views>true</views>
                            <components>false</components>
                            <onlyName>true</onlyName>
                            <background>{background}</background>
                         </GetInfoLoginRequest>
                      </it:GetInfoLogin>
                   </soapenv:Body>
                </soapenv:Envelope>       
        """
        response = requests.post(self.endpoint, request)
        doc = Adapter.__to_element__(response.text)
        list = []
        sr = ServiceResponse()
        for child in doc[0][0][0]:
            if child.tag == 'xml':
                for c in child[0]:
                    list.append(c.text)

            setattr(sr, child.tag, "".join([str(etree.tostring(c)) for c in child]) if len(child) > 0 else child.text)

        return list, sr

    def get_class_business(self, id_session: str = None, name: str = '',
                           background: bool = False) -> 'ClassBusiness,ServiceResponse':
        """
        Restituisce la classe di business specificata.

        Args:
            id_session (str, optional): Id sessione per cui si effettua la chiamata. Se None, viene usata la sessione di default.
            name (str): Nome della classe di business da recuperare.
            background (bool, optional): Flag per specificare la modalità di esecuzione. Default è False.

        Raises:
            TidyException: Se id_session non è specificato e non esiste una sessione di default.

        Returns:
            tuple:
                - ClassBusiness: istanza della classe di business, o None in caso di errore.
                - ServiceResponse: oggetto con informazioni sull'esito della chiamata.
        """
        if id_session is None and self.default_id_session is None: raise TidyException('Id Sessione non specificato')
        request = f"""
                <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:it="it.itchange.bcr.basvi">
                   <soapenv:Header/>
                   <soapenv:Body>
                      <it:GetClassBusiness>
                         <GetClassBusinessRequest priority="?" id="?">
                            <idSession>{id_session if id_session is not None else self.default_id_session}</idSession>
                            <nameClassBusiness>{name}</nameClassBusiness>
                            <background>{background}</background>
                         </GetClassBusinessRequest>
                      </it:GetClassBusiness>
                   </soapenv:Body>
                </soapenv:Envelope>      
        """
        response = requests.post(self.endpoint, request)
        doc = Adapter.__to_element__(response.text)

        sr = ServiceResponse()
        for child in doc[0][0][0]:
            setattr(sr, child.tag, etree.tostring(child[0]) if len(child) > 0 else child.text)
        c = ClassBusiness.from_xml(sr.xml) if sr.code == '0' else None
        if c is not None: c.adapter = self
        return c, sr

    def query(self, id_session: str = None, query: str = '"no query" ', param_list=None,
              background: bool = False) -> 'str , ServiceResponse':
        """
        Esegue una query generica con eventuali parametri.

        Args:
            id_session (str, optional): Id sessione per cui si effettua la chiamata. Se None, viene usata la sessione di default.
            query (str): Query da eseguire.
            param_list (list, optional): Lista di parametri associati alla query. Default è None.
            background (bool, optional): Flag per specificare la modalità di esecuzione. Default è False.

        Raises:
            TidyException: Se id_session non è specificato e non esiste una sessione di default.
            TidyException: Se la query non termina con codice di successo ('0' o '-1').

        Returns:
            tuple:
                - list of str: lista di stringhe XML risultanti dalla query, o lista con xml singolo.
                - ServiceResponse: oggetto con informazioni sull'esito della chiamata.
        """
        if id_session is None and self.default_id_session is None: raise TidyException('Id Sessione non specificato')
        params = ''
        if param_list is not None:
            params = '<paramList>'
            params += "".join([f'<value>{p}</value>' for p in param_list])
            params += '</paramList>'

        request = f"""
                    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:it="it.itchange.bcr.basvi">
                       <soapenv:Header/>
                       <soapenv:Body>
                          <it:ExecuteGenericQuery>
                             <ExecuteGenericQueryRequest>
                                <idSession>{id_session if id_session is not None else self.default_id_session}</idSession>
                                <query>{query}</query>
                                {params}
                                <clean>true</clean>
                                <background>{background}</background>
                             </ExecuteGenericQueryRequest>
                          </it:ExecuteGenericQuery>
                       </soapenv:Body>
                    </soapenv:Envelope>  
                  """

        response = requests.post(self.endpoint, request)

        doc = Adapter.__to_element__(response.text)

        list = []
        sr = ServiceResponse()
        for child in doc[0][0][0]:
            if child.tag == 'xml':
                list = [str(etree.tostring(c).decode()) for c in child]
            setattr(sr, child.tag,
                    "".join(str(etree.tostring(c).decode()) for c in child) if len(child) > 0 else child.text)

        if sr.code == '0' or sr.code == '-1':
            return list, sr
        else:
            raise TidyException(sr)

    def alterQuery(self, id_session: str = None, name_class: str = None, version: str = '0',
                   keys: 'dict' = None, query: str = 'generic', param_list=None, action: str = '1',
                   background: bool = False) -> 'str , ServiceResponse':

        """
        Esegue una query di modifica su una classe di business.

        Args:
            id_session (str, optional): Id sessione, se None viene usata la sessione di default.
            name_class (str): Nome della classe di business.
            version (str): Versione della classe. Default è '0'.
            keys (dict): Dizionario con le chiavi identificative.
            query (str): Query da eseguire. Default è 'generic'.
            param_list (list, optional): Lista di parametri associati alla query. Default è None.
            action (str): Azione da eseguire: '1' per revisione, '2' per sovrascrittura. Default è '1'.
            background (bool, optional): Flag per specificare la modalità di esecuzione. Default è False.

        Raises:
            TidyException: Se id_session non è specificato e non esiste una sessione di default.

        Returns:
            tuple:
                - str: messaggio di risposta del server (eventuale errore o conferma).
                - ServiceResponse: oggetto con informazioni sull'esito della chiamata.
        """
        if param_list is None:
            param_list = []

        if id_session is None and self.default_id_session is None: raise TidyException('Id Sessione non specificato')
        request = '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:it ="it.itchange.bcr.basvi" >'
        request += '<soapenv:Body>'
        request += '<it:ExecuteClassAlterQuery>'
        request += '<ExecuteClassAlterQueryRequest>'
        request += '<idSession>{}</idSession>'.format(
            id_session if id_session is not None else self.default_id_session)
        request += '<selection>'
        request += '<selector>'
        request += '<nameClassBusiness>{}</nameClassBusiness>'.format(name_class)
        request += '<version>{}</version>'.format(version)
        request += '<keys>'
        for k, v in keys.items():
            request += '<key name="{}">{}</key>'.format(k, v)
        request += '</keys>'
        request += '</selector>'
        request += '<paramList>'
        for v in param_list:
            request += '<value>{}</value>'.format(v)
        request += '</paramList>'
        request += '</selection>'
        request += '<nameQuery>{}</nameQuery>'.format(query)
        request += '<action>{}</action>'.format(action)
        request += '<background>{}</background>'.format('true' if background else 'false')
        request += '</ExecuteClassAlterQueryRequest>'
        request += '</it:ExecuteClassAlterQuery>'
        request += '</soapenv:Body>'
        request += '</soapenv:Envelope>'
        response = requests.post(self.endpoint, request)
        doc = Adapter.__to_element__(response.text)

        sr = ServiceResponse()
        for child in doc[0][0][0]:
            setattr(sr, child.tag, etree.tostring(child[0]) if len(child) > 0 else child.text)

        return sr.message, sr

    def script(self, id_session: str = None, language: str = 'groovy',
               script: str = 'print("Compilare il parametro script o nameScript")'
               , nameScript: str = None, param_list: dict = None, root_df: str = None,
               background: bool = False) -> 'DataFrame, str , ServiceResponse':
        """
        Esegue uno script lato server sul sistema Tidy.

        L'utente può fornire direttamente il testo dello script da eseguire (parametro `script`)
        oppure il nome di uno script salvato lato server (`nameScript`). Se entrambi sono forniti,
        ha la precedenza il parametro `script`.

        Args:
            id_session (str, optional): ID della sessione Tidy. Se non specificato, viene utilizzata
                la sessione di default dell'istanza.
            language (str, optional): Linguaggio dello script (default: 'groovy').
            script (str, optional): Contenuto dello script da eseguire. Ha la precedenza su `nameScript`.
            nameScript (str, optional): Nome di uno script già presente nel server.
            root_df (str, optional): Nel caso il risultato si xml è possibile ottenere il risultato come DataFrame, questo parametro determina la root da cui ha inizio la conversione in dataframe; se lasciato a None utilizza tutto l'xml.
            param_list (dict, optional): Dizionario dei parametri da passare allo script (saranno visti
                come variabili nel contesto di esecuzione).
            background (bool, optional): Se True, l'esecuzione sarà in modalità asincrona.

        Returns:
            DataFrame: se possibile la conversione in dataFrame del xml
            Tuple[str or List[str], ServiceResponse]: La risposta XML del server (stringa o lista di stringhe XML)
            e un oggetto ServiceResponse contenente informazioni dettagliate sulla risposta.

        Raises:
            TidyException: Se non è specificato un ID di sessione valido o se la risposta contiene errori.
        """
        if id_session is None and self.default_id_session is None: raise TidyException('Id Sessione non specificato')

        request = f"""
                <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:it="it.itchange.bcr.basvi">
                   <soapenv:Header/>
                   <soapenv:Body>
                      <it:ExecuteScript>
                         <ExecuteScriptRequest >
                            <idSession>{id_session if id_session is not None else self.default_id_session}</idSession> 
                            <language>{language}</language>
                            <script>{script if nameScript is None else ''}</script>
                            <nameScript>{nameScript if nameScript is not None else ''}</nameScript>                             
                            <parameters>
                               {("".join([f'<parameter name="{k}">{v}</parameter>' for k, v in param_list.items()])) if param_list is not None else ''}
                            </parameters>
                            <background>{background}</background>
                         </ExecuteScriptRequest>
                      </it:ExecuteScript>
                   </soapenv:Body>
                </soapenv:Envelope> 
                  """

        response = requests.post(self.endpoint, request)
        doc = Adapter.__to_element__(response.text)

        list = []
        sr = ServiceResponse()
        root_for_df = None
        for child in doc[0][0][0]:
            if child.tag == 'xml':
                list = [str(etree.tostring(c).decode()) for c in child]
                root_for_df = child
                if root_df is not None:
                    while root_for_df.tag != root_df and len(root_for_df) > 0:
                        root_for_df = root_for_df[0]
            setattr(sr, child.tag,
                    "".join(str(etree.tostring(c).decode()) for c in child) if len(child) > 0 else child.text)

        if sr.code == '0' or sr.code == '-1':
            xml = [sr.xml] if len(child) == 0 else list
            try:
                df = pd.read_xml(StringIO(etree.tostring(root_for_df).decode()))
            except:
                df = None
            return {'df': df, 'xml': xml, 'sr': sr}
        else:
            raise TidyException(sr)

    def actionProgress(self, id_session: str = None, params: str = '', desc: str = '', progress: float = 0.0) :
        """
        aggiorna il progress della action identificata nei parametri.

        Args:
            id_session (str, optional): ID della sessione Tidy. Se non specificato, viene utilizzata
                la sessione di default dell'istanza.
            params (str, optional): Parametro fornito dal server tidy (json).
            desc (str, optional): Nuova descrizione della action.
            progress (float, optional): Percentuale dii avanzamento della action.

        Raises:
            TidyException: Se non è specificato un ID di sessione valido o se la risposta contiene errori.
        """
        if id_session is None and self.default_id_session is None: raise TidyException('Id Sessione non specificato')

        data = json.loads(params)
        idAction=data['idAction']

        script=f"tidy.actionProgress({idAction},{progress},'{desc}')"
        request = f"""
                <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:it="it.itchange.bcr.basvi">
                   <soapenv:Header/>
                   <soapenv:Body>
                      <it:ExecuteScript>
                         <ExecuteScriptRequest >
                            <idSession>{id_session if id_session is not None else self.default_id_session}</idSession> 
                            <language>groovy</language>
                            <script>{script}</script>
                            <nameScript></nameScript>                             
                            <parameters></parameters>
                            <background>false</background>
                         </ExecuteScriptRequest>
                      </it:ExecuteScript>
                   </soapenv:Body>
                </soapenv:Envelope> 
                  """

        response = requests.post(self.endpoint, request)


    def addAttachment(self, id_session: str = None, name_class: str = None, version: str = '0',
                      keys: Dict[str, str] = None, name_attach: str = 'att1', data: str = ' ',
                      background: bool = False) -> 'str , ServiceResponse':
        """
        Aggiunge un allegato a un documento esistente nel sistema Tidy.

        L'allegato è legato a una classe di business identificata da nome, versione e chiavi. I dati
        dell'allegato devono essere forniti in formato base64.

        Args:
            id_session (str, optional): ID della sessione Tidy. Se non specificato, viene utilizzata
                la sessione di default dell'istanza.
            name_class (str): Nome della classe di business su cui aggiungere l'allegato.
            version (str, optional): Versione della classe (default: '0').
            keys (Dict[str, str]): Chiavi identificative dell'entità (es. {'id': '123'}).
            name_attach (str, optional): Nome logico dell'allegato (default: 'att1').
            data (str, optional): Contenuto dell'allegato codificato in base64.
            background (bool, optional): Se True, l'esecuzione sarà in modalità asincrona.

        Returns:
            Tuple[str, ServiceResponse]: Messaggio di esito (stringa) e un oggetto ServiceResponse
            con i dettagli della risposta.

        Raises:
            TidyException: Se non è specificato un ID di sessione valido.
        """
        if id_session is None and self.default_id_session is None: raise TidyException('Id Sessione non specificato')
        request = '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:it = "it.itchange.bcr.basvi" > '
        request += '<soapenv:Body>'
        request += '<it:AddAttachments>'
        request += '<AddAttachmentsRequest>'
        request += '<idSession>{}</idSession>'.format(id_session if id_session is not None else self.default_id_session)
        request += '<attachments>'
        request += '<attachmentsDoc>'
        request += '<selector>'
        request += '<nameClassBusiness>{}</nameClassBusiness>'.format(name_class)
        request += '<version>{}</version>'.format(version)
        request += '<keys>'
        for k, v in keys.items():
            request += '<key name="{}">{}</key>'.format(k, v)
        request += '</keys>'
        request += '</selector>'
        request += '<items>'
        request += '<item>'
        request += '<name>{}</name>'.format(name_attach)
        request += '<data>{}</data>'.format(data)
        request += '</item>'
        request += '</items>'
        request += '</attachmentsDoc>'
        request += '</attachments>'
        request += '<background>{}</background>'.format('true' if background else 'false')
        request += '</AddAttachmentsRequest>'
        request += '</it:AddAttachments>'
        request += '</soapenv:Body>'
        request += '</soapenv:Envelope>'

        response = requests.post(self.endpoint, request)
        doc = Adapter.__to_element__(response.text)

        sr = ServiceResponse()
        for child in doc[0][0][0]:
            setattr(sr, child.tag, etree.tostring(child[0]) if len(child) > 0 else child.text)

        return sr.message, sr

    def publish(self, id_session: str = None, name_class: str = None, version: str = '0',
                component_update_type: str = None, action: 'int' = 1, note: str = None,
                docs: 'list' = None, background: bool = False) -> 'str , ServiceResponse':
        """
           Pubblica una lista di documenti associati a una classe di business specifica.

           È possibile specificare la modalità di pubblicazione, la modalità di aggiornamento e un'eventuale nota.

           :param id_session: str, opzionale. ID della sessione da utilizzare. Se None, viene usata la sessione predefinita.
           :param name_class: str. Nome della classe di business a cui appartengono i documenti da pubblicare.
           :param version: str, opzionale. Versione della classe; default '0' indica l'ultima versione disponibile.
           :param component_update_type: str, opzionale. Specifica la modalità di aggiornamento (es. completa o parziale).
           :param action: int, opzionale. Indica la modalità di pubblicazione:
                          0 = aggiornamento,
                          1 = revisione (default),
                          2 = pubblicazione solo se il documento non esiste.
           :param note: str, opzionale. Nota descrittiva associata all'operazione di pubblicazione.
           :param docs: list. Lista di stringhe XML rappresentanti i documenti da pubblicare.
           :param background: bool, opzionale. Se True, la pubblicazione viene eseguita in background e viene restituito l'id del task.

           :return: tuple(str, ServiceResponse)
                    - str: Messaggio di conferma o ID del task se in background.
                    - ServiceResponse: Oggetto contenente il dettaglio della risposta del server.
           :raises TidyException: Se l'ID di sessione non è specificato e non esiste una sessione predefinita.
           """
        if id_session is None and self.default_id_session is None: raise TidyException('Id Sessione non specificato')

        template = """

        """
        request = '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:it = ' \
                  '"it.itchange.bcr.basvi" > '
        request += '<soapenv:Body>'
        request += '<it:BulkLoad>'
        request += '<BulkLoadRequest>'
        request += '<idSession>{}</idSession>'.format(id_session if id_session is not None else self.default_id_session)
        request += '<nameClassBusiness>{}</nameClassBusiness>'.format(name_class)
        request += '<action>{}</action>'.format(action if action is not None else '1')
        request += '<componentUpdateType>{}</componentUpdateType>'.format(
            component_update_type if component_update_type is not None else '')
        request += '<note>{}</note>'.format(note if note is not None else '')
        request += f'<background>{background}</background>'
        request += '<values>'
        for v in docs:
            request += v
        request += '</values>'
        request += '</BulkLoadRequest>'
        request += '</it:BulkLoad>'
        request += '</soapenv:Body>'
        request += '</soapenv:Envelope>'

        headers = {"Content-Type": "application/xml", "Content-Encoding": "gzip"}
        response = requests.post(self.endpoint, data=gzip.compress(str.encode(request)), headers=headers)
        doc = Adapter.__to_element__(response.text)

        sr = ServiceResponse()
        for child in doc[0][0][0]:
            setattr(sr, child.tag, etree.tostring(child[0]) if len(child) > 0 else child.text)

        return sr.message if background == False else sr.idTask, sr

    def delete_value(self, id_session: str = None, name_class: str = None, keys=None, xpathfilter: str = '',
                     revision: int = 0) -> ServiceResponse:
        """
        Elimina uno o più documenti da una classe di business.

        La funzione consente di eliminare documenti specificati tramite chiavi, un filtro XPath opzionale e una revisione.
        È possibile eliminare un documento specifico, tutte le revisioni o solo l'ultima revisione.

        :param id_session: str, opzionale. ID della sessione da utilizzare. Se None, viene usata la sessione predefinita.
        :param name_class: str. Nome della classe di business da cui eliminare i documenti.
        :param keys: list[str] o dict[str, str], opzionale. Identificatori dei documenti da eliminare. Se vuoto o None, saranno eliminati tutti i documenti.
        :param xpathfilter: str, opzionale. Filtro XPath per una selezione più precisa dei documenti da eliminare.
        :param revision: int, opzionale. Specifica la revisione da eliminare:
                         0 = ultima revisione (default),
                         -1 = tutte le revisioni,
                         >0 = revisione specifica.

        :return: ServiceResponse. Oggetto contenente il risultato dell'operazione.
        :raises TidyException: Se l'ID di sessione non è specificato e non esiste una sessione predefinita.
        """
        if keys is None:
            keys = []
        if id_session is None and self.default_id_session is None: raise TidyException('Id Sessione non specificato')

        keys_filter = ''
        if keys is None or len(keys) == 0:
            keys_filter = '<key name="*"></key>'
        else:
            if isinstance(keys, List):
                for idx, k in enumerate(keys):
                    keys_filter += f'<key name="*{idx}">{k}</key>'
            else:
                for nk in keys.keys():
                    keys_filter += f'<key name="{nk}">{keys[nk]}</key>'
        request = f"""
             <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:it="it.itchange.bcr.basvi">
               <soapenv:Header/>
               <soapenv:Body>
                  <it:DeleteValue>
                     <DeleteValueRequest>
                        <idSession>{id_session if id_session is not None else self.default_id_session}</idSession>
                        <selector>
                           <nameClassBusiness>{name_class}</nameClassBusiness>
                           <keys> 
                              {keys_filter}
                           </keys>
                           <xPathFilter>{xpathfilter}</xPathFilter> 
                        </selector>
                        <revision>{revision}</revision> 
                        <background>false</background>
                     </DeleteValueRequest>
                  </it:DeleteValue>
               </soapenv:Body>
            </soapenv:Envelope>
        """

        headers = {"Content-Type": "application/xml", "Content-Encoding": "gzip"}
        response = requests.post(self.endpoint, data=gzip.compress(str.encode(request)), headers=headers)
        doc = Adapter.__to_element__(response.text)

        sr = ServiceResponse()
        for child in doc[0][0][0]:
            setattr(sr, child.tag, etree.tostring(child[0]) if len(child) > 0 else child.text)

        return sr

    def add_attachment(self, id_session: str = None, name_class: str = None, version: str = '0',
                       keys: 'dict' = None, name_att: str = None,
                       data_att: str | bytes = None) -> 'str , ServiceResponse':
        """
        Aggiunge un allegato a un documento esistente in una classe di business.

        L'allegato deve essere fornito come stringa codificata in Base64 (o bytes). Se l'allegato è troppo grande,
        viene suddiviso in più blocchi da 16.000 caratteri e inviato in più richieste.

        :param id_session: str, opzionale. ID della sessione da utilizzare. Se None, viene usata la sessione predefinita.
        :param name_class: str. Nome della classe di business contenente il documento.
        :param version: str, opzionale. Versione della classe; default '0' indica l'ultima versione disponibile.
        :param keys: dict. Chiavi che identificano univocamente il documento all'interno della classe.
        :param name_att: str. Nome dell’allegato da creare.
        :param data_att: str | bytes. Contenuto dell’allegato in Base64 (può essere anche bytes codificati).

        :return: tuple(str, ServiceResponse)
                 - str: Messaggio di esito.
                 - ServiceResponse: Oggetto contenente il dettaglio della risposta del server.
        :raises TidyException: Se l'ID di sessione non è specificato e non esiste una sessione predefinita.
        """
        if id_session is None and self.default_id_session is None: raise TidyException('Id Sessione non specificato')

        size, chunk_size = len(data_att), 16000
        chunks = [data_att[i:i + chunk_size] for i in range(0, size, chunk_size)]

        for index, chunk in enumerate(chunks):
            request = '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:it = ' \
                      '"it.itchange.bcr.basvi" > '
            request += '<soapenv:Body>'
            request += '<it:AddAttachments>'
            request += '<AddAttachmentsRequest>'
            request += '<idSession>{}</idSession>'.format(
                id_session if id_session is not None else self.default_id_session)
            request += '<attachments>'
            request += '<attachmentsDoc>'
            request += '<selector>'
            request += '<nameClassBusiness>{}</nameClassBusiness>'.format(name_class)
            request += '<version>{}</version>'.format(version)
            request += '<keys>'
            for k, v in keys.items():
                request += '<key name="{}">{}</key>'.format(k, v)
            request += '</keys>'
            request += '</selector>'
            request += '<items>'
            request += '<item>'
            request += f'<name>{name_att}{index}</name>'
            request += '<data>{}</data>'.format(chunk.decode('utf8') if isinstance(chunk, bytes) else chunk)
            request += '<documentRevision>0</documentRevision>'
            request += '</item>'
            request += '</items>'
            request += '</attachmentsDoc>'
            request += '</attachments>'
            request += '<background>false</background>'
            request += '</AddAttachmentsRequest>'
            request += '</it:AddAttachments>'
            request += '</soapenv:Body>'
            request += '</soapenv:Envelope>'
            response = requests.post(self.endpoint, request)
            doc = Adapter.__to_element__(response.text)

            sr = ServiceResponse()
            for child in doc[0][0][0]:
                setattr(sr, child.tag, etree.tostring(child[0]) if len(child) > 0 else child.text)

        return sr.message, sr

    def read_attachment(self, id_session: str = None, name_class: str = None, version: str = '0',
                        keys: 'dict' = None, name_att: str = None, revision: 'int' = 0) -> 'str , ServiceResponse':
        """
        Recupera un allegato da un documento esistente in una classe di business.

        Il contenuto dell’allegato viene restituito come stringa codificata in Base64. Se l'allegato è stato
        salvato in più blocchi, questi vengono riuniti automaticamente.

        :param id_session: str, opzionale. ID della sessione da utilizzare. Se None, viene usata la sessione predefinita.
        :param name_class: str. Nome della classe di business contenente il documento.
        :param version: str, opzionale. Versione della classe; default '0' indica l'ultima versione disponibile.
        :param keys: dict. Chiavi che identificano univocamente il documento all'interno della classe.
        :param name_att: str. Nome dell’allegato da leggere.
        :param revision: int, opzionale. Revisione del documento da cui leggere l’allegato; default = 0 (ultima revisione).

        :return: tuple(str, ServiceResponse)
                 - str: Contenuto dell’allegato in Base64.
                 - ServiceResponse: Oggetto contenente il dettaglio della risposta del server.
        :raises TidyException: Se l'ID di sessione non è specificato e non esiste una sessione predefinita.
        :raises ValueError: Se l’allegato non viene trovato.
        """
        if id_session is None and self.default_id_session is None: raise TidyException('Id Sessione non specificato')
        data = []

        read = True
        index = 0
        while read:
            request = '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:it = ' \
                      '"it.itchange.bcr.basvi" > '
            request += '<soapenv:Body>'
            request += '<it:GetAttachments>'
            request += '<GetAttachmentsRequest>'
            request += '<idSession>{}</idSession>'.format(
                id_session if id_session is not None else self.default_id_session)
            request += '<attachments>'
            request += '<attachmentsDoc>'
            request += '<selector>'
            request += '<nameClassBusiness>{}</nameClassBusiness>'.format(name_class)
            request += '<version>{}</version>'.format(version)
            request += '<keys>'
            for k, v in keys.items():
                request += '<key name="{}">{}</key>'.format(k, v)
            request += '</keys>'
            request += '</selector>'
            request += '<items>'
            request += '<item>'
            request += f'<name>{name_att}{index}</name>'
            request += '<documentRevision>{}</documentRevision>'.format(revision)
            request += '</item>'
            request += '</items>'
            request += '</attachmentsDoc>'
            request += '</attachments>'
            request += '<background>false</background>'
            request += '</GetAttachmentsRequest>'
            request += '</it:GetAttachments>'
            request += '</soapenv:Body>'
            request += '</soapenv:Envelope>'
            response = requests.post(self.endpoint, request)
            doc = Adapter.__to_element__(response.text)

            sr = ServiceResponse()
            for child in doc[0][0][0]:
                setattr(sr, child.tag, etree.tostring(child[0]) if len(child) > 0 else child.text)
            index = index + 1
            if sr.code == '0':
                try:
                    data.append(doc.xpath('//xml/attachments/attachment[1]/items/item[1]/data')[0].text)
                except Exception:
                    read = False
            else:
                raise ValueError('no attachment found:')

        return "".join(data), sr

    def event_trigger(self, id_session: str = None, name_event: str = 'event', message_event: str = '',
                      parameters: 'dict' = None) -> 'ServiceResponse':
        """
           Invia un evento di tipo BasviEvent al sistema.

           L’evento può contenere un nome, un messaggio descrittivo e un dizionario di parametri addizionali.
           Questo può essere utile per notificare il sistema di modifiche, stati o azioni specifiche durante l’esecuzione
           di un processo applicativo.

           :param id_session: str, opzionale. ID della sessione da utilizzare. Se None, viene usata la sessione predefinita.
           :param name_event: str, opzionale. Nome dell’evento da generare (default: 'event').
           :param message_event: str, opzionale. Messaggio associato all’evento.
           :param parameters: dict, opzionale. Parametri addizionali dell’evento nel formato chiave-valore.

           :return: ServiceResponse. Oggetto contenente il risultato dell’operazione.
           :raises TidyException: Se l’ID di sessione non è specificato e non esiste una sessione predefinita.
           """
        if id_session is None and self.default_id_session is None: raise TidyException('Id Sessione non specificato')
        request = '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:it = ' \
                  '"it.itchange.bcr.basvi" > '
        request += '<soapenv:Body>'
        request += '<it:EventTrigger>'
        request += '<EventTriggerRequest>'
        request += '<idSession>{}</idSession>'.format(id_session if id_session is not None else self.default_id_session)
        request += '<name>{}</name>'.format(name_event)
        request += '<message>{}</message>'.format(message_event)
        request += '<parameters>'
        if parameters is not None:
            for k, v in parameters.items():
                request += '<parameter name="{}">{}</parameter>'.format(k, v)
        request += '</parameters>'
        request += '<background>false</background>'
        request += "</EventTriggerRequest>"
        request += '</it:EventTrigger>'
        request += '</soapenv:Body>'
        request += '</soapenv:Envelope>'

        response = requests.post(self.endpoint, request.encode("utf-8"))
        doc = Adapter.__to_element__(response.text)

        sr = ServiceResponse()
        for child in doc[0][0][0]:
            setattr(sr, child.tag, etree.tostring(child[0]) if len(child) > 0 else child.text)

        return sr

    @staticmethod
    def __to_element__(xml):
        if isinstance(xml, etree._Element):
            doc = xml
        else:
            doc = etree.fromstring(xml)
        return doc

    @staticmethod
    def to_list(xml: 'str or etree._Element', col_name: str = '*') -> 'list':
        """
        Estrae una lista partendo dall'xml fornito in input
        Esempi: adapter.to_list('<a><b>1</b><b>2</b></a>','b') -> [1,2]
                adapter.to_list('<a><c><b>1</b><b>2</b></c></a>','c/b') -> [1,2]
        :param xml: str or etree._Element,
        :param col_name: str, nome del tag xml oppure espressione xpath da utilizzare per determinare come estrarre la lista
        :rtype:  list Lista d valori estratti dall'xml
        """

        list = []
        for child in Adapter.__to_element__(xml).xpath(col_name):
            list.append(child.text)
        return list

    @staticmethod
    def to_matrix(xml, row_name: str = None, col_name: str = '*') -> List:
        """
        Estrae una matrice partendo dall'xml fornito in input
        Esempi: adapter.to_matrix('<a><row>
                                      <b>1</b>
                                      <b>2</b>
                                    </row>
                                    <row>
                                       <b>3</b>
                                       <b>4</b>
                                    </row>
                                </a>','row','b') -> [[1,2]  ,[3,4]]
                adapter.to_matrix('<a><c>
                                    <row>
                                      <b1>1</b>
                                      <b2>2</b>
                                    </row>
                                    <row>
                                       <b1>3</b>
                                       <b2>4</b>
                                    </row>
                               </c> </a>','c/row','*') -> [[1,2]  ,[3,4]]
        :param xml: str or etree._Element,
        :param row_name: str, nome del tag xml oppure espressione xpath da utilizzare per determinare le righe della matrice
        :param col_name: str, nome del tag xml oppure espressione xpath da utilizzare per determinare le colonne della matrice
        :rtype:  matrix Matrice d valori estratti dall'xml
        """

        matrix = []
        for row in Adapter.__to_element__(xml).xpath(row_name):
            r = []
            for child in row.xpath(col_name):
                r.append(child.text)
            matrix.append(r)

        return matrix

    @staticmethod
    def to_matrix_number(xml, row_name: str = None, col_name: str = '*') -> List:
        """
        Estrae una matrice partendo dall'xml fornito in input
        Esempi: adapter.to_matrix('<a><row>
                                      <b>1</b>
                                      <b>2</b>
                                    </row>
                                    <row>
                                       <b>3</b>
                                       <b>4</b>
                                    </row>
                                </a>','row','b') -> [[1,2]  ,[3,4]]
                adapter.to_matrix('<a><c>
                                    <row>
                                      <b1>1</b>
                                      <b2>2</b>
                                    </row>
                                    <row>
                                       <b1>3</b>
                                       <b2>4</b>
                                    </row>
                               </c> </a>','c/row','*') -> [[1,2]  ,[3,4]]
        :param xml: str or etree._Element,
        :param row_name: str, nome del tag xml oppure espressione xpath da utilizzare per determinare le righe della matrice
        :param col_name: str, nome del tag xml oppure espressione xpath da utilizzare per determinare le colonne della matrice
        :rtype:  matrix Matrice d valori estratti dall'xml
        """

        matrix = []
        for row in Adapter.__to_element__(xml).xpath(row_name):
            r = []
            for child in row.xpath(col_name):
                r.append(float(child.text))
            matrix.append(r)

        return matrix

    @staticmethod
    def matrix_to_xml(matrix, root_name: str, row_name: str, col_name: str) -> str:
        """
         Ricostruisce un xml utilizzando la matrice fornita in input
         Esempio:
            adapter.matrix_to_xml([[1,2],[3,4],'root','row','col') ->
                                      <root>
                                         <row>
                                            <col>1</col>
                                            <col>2</col>
                                         </row>
                                         <row>
                                            <col>3</col>
                                            <col>4</col>
                                         </row>
                                      </root>
         :param matrix: matrix  ,
         :param root_name: str, root dell'xml
         :param row_name: str, nome dell'elemento separatore delle righe
         :param col_name: str, nome dell'elemento separatore delle colonne
         :rtype:  str xml rappresentante la matrice
        """

        # noinspection PyListCreation
        str_list = []
        str_list.append('<{}>'.format(root_name))
        for row in matrix:
            str_list.append('<{}>'.format(row_name))
            i = 0
            for col in row:
                nn = col_name if isinstance(col_name, str) else col_name[i]
                str_list.append('<{}>'.format(nn))
                str_list.append(str(col))
                str_list.append('</{}>'.format(nn))
                i += 1
            str_list.append('</{}>'.format(row_name))
        str_list.append('</{}>'.format(root_name))
        return ''.join(str_list)

    def save_model(self, id_session: str = None, name: str = None, model=None, model_type: str = '',
                   model_description: str = '') -> 'str':
        """
        Serializza il modello e lo salva sulla classe tfModel
        :param id_session: str Id sessione per cui si effettua il logout, se vale None è utilizzata la sessione di default
        :param name: Nome del modello
        :param model: Modello da serializzare
        :param model_type: Tipo del modello
        :param model_description: Descrizione del modello
        :return:  messaggio di risposta
        """

        str_list = []
        str_list.append('<value>')
        str_list.append('<keys>')
        str_list.append(f'<key name="name">{name}</key>')
        str_list.append('</keys>')
        str_list.append('<xmlValue>')
        str_list.append('<tfModel>')
        str_list.append(f'<name>{name}</name>')
        str_list.append(f'<modelDescription>{model_description}</modelDescription>')
        str_list.append('<revisionDetail></revisionDetail>')
        str_list.append(f'<type>{model_type}</type>')
        str_list.append('<summary></summary>')
        str_list.append('<json></json>')
        str_list.append('<metrics>')
        str_list.append('</metrics>')
        str_list.append('<parameters>')
        str_list.append('</parameters>')
        str_list.append('</tfModel>')
        str_list.append('</xmlValue>')
        str_list.append('</value>')

        value = ''.join(str_list)

        self.delete_value(id_session, TF_MODEL, [name])
        message, sr = self.publish(id_session, TF_MODEL, '0', None, 0, 'from python client', [value])
        if sr.code == '0':
            name_temp_file = f'{name}_{str(datetime.timestamp(datetime.now())).replace(".", "_")}.pkl'
            try:

                with open(name_temp_file, "wb") as file:
                    pickle.dump(model, file)

                with open(name_temp_file, "rb") as pkl:
                    encoded_string = base64.b64encode(pkl.read()).decode('utf-8')
                    message, sr1 = self.add_attachment(id_session, TF_MODEL, '0', {'name': name}, 'model_pickle',
                                                       encoded_string)
                    if sr1.code == '0':
                        return 'model saved correctly', sr1
                    else:
                        raise TidyException(sr1)
            finally:
                os.remove(name_temp_file)
        else:
            raise TidyException(sr)

    def read_model(self, id_session: str = None, name: str = None, revision: 'int' = 0) -> 'model':
        """
        Legge dalla classe di business tfModel un modello tensorflow con i relativi pesi, eventuali parametri aggiuntivi e metriche per la valutazione
        :param id_session: str Id sessione per cui si effettua il logout, se vale None è utilizzata la sessione di default
        :param name: Nome del modello
        :param revision: Revisione del modello. Il valore di default è 0 (ultima revisione)
        :return:  tensorflow model utilizzabile
        """

        data, sr = self.read_attachment(id_session, TF_MODEL, '0', {'name': name}, 'model_pickle', revision)
        if sr.code == '0':
            name_temp_file = f'temp_{str(datetime.timestamp(datetime.now())).replace(".", "_")}.pkl'
            try:
                with open(name_temp_file, "wb") as pkl:
                    pkl.write(base64.b64decode(bytearray(data, 'utf-8')))
                with open(name_temp_file, "rb") as pkl:
                    model = pickle.load(pkl)
            finally:
                os.remove(name_temp_file)
            # return model, params
            return model
        else:
            raise TidyException(sr)

    def save_tf_model(self, id_session: str, name, model, scope_metrics: dict = None, model_description: str = '',
                      revision_detail: str = '', parameters=None) -> 'str, ServiceResponse':
        """
        Salva sulla classe di business tfModel un modello tensorflow con i relativi pesi, eventuali parametri aggiuntivi e metriche per la valutazione
        Il modello tensorflow è salvato come attachment della classe
        :param id_session: str Id sessione per cui si effettua il logout, se vale None è utilizzata la sessione di default
        :param name: Nome del modello
        :param model: Modello tensorflow
        :param scope_metrics: Dictionary in cui si forniscono differenti set di input-output utilizzati per la validazione del modello.
                              Le metriche utilizzate sono quelle definite sul modello tensorflow
                              Esempio {'training': ([x_train], [y_train]), 'validation': ([x_val], [y_val])}
        :param model_description: Descrizione generale del modello
        :param revision_detail: Descrizione della revisione del modello
        :param parameters: Eventuali parametri aggiuntivi utilizzati per generare l'output e necessari nella fase di predict. Ad esempio i parametri utilizzati per normalizzare i dati di input
        :return:  message,ServiceResponse message:ServiceResponse.message; ServiceResponse
        """
        # noinspection PyListCreation

        if parameters is None:
            parameters = []
        str_list = []
        str_list.append('<value>')
        str_list.append('<keys>')
        str_list.append('<key name="name">{}</key>'.format(name))
        str_list.append('</keys>')
        str_list.append('<xmlValue>')
        str_list.append('<tfModel>')
        str_list.append('<name>{}</name>'.format(name))
        str_list.append('<modelDescription>{}</modelDescription>'.format(model_description))
        str_list.append('<revisionDetail>{}</revisionDetail>'.format(revision_detail))
        str_list.append('<type>{}</type>'.format(model.name))
        str_list.append('<summary><![CDATA[{}]]></summary>'.format(model.summary))
        str_list.append('<json><![CDATA[{}]]></json>'.format(model.to_json()))
        str_list.append('<metrics>')
        if scope_metrics is not None:
            for scope in scope_metrics:
                inp = scope_metrics.get(scope)
                metrics = model.evaluate(inp[0], inp[1], verbose=0)
                if not isinstance(metrics, list):
                    metrics = [metrics]
                for i in range(len(metrics)):
                    str_list.append('<metric>')
                    str_list.append('<scope>{}</scope>'.format(scope))
                    str_list.append('<type>{}</type>'.format(model.metrics_names[i]))
                    str_list.append('<value>{}</value>'.format(metrics[i]))
                    str_list.append('</metric>')
        str_list.append('</metrics>')
        str_list.append('<parameters>')
        for param in parameters:
            str_list.append('<par>')
            str_list.append('<key>{}</key>'.format(param['key']))
            str_list.append('<value>{}</value>'.format(param['value']))
            str_list.append('</par>')
        str_list.append('</parameters>')
        str_list.append('</tfModel>')
        str_list.append('</xmlValue>')
        str_list.append('</value>')

        value = ''.join(str_list)

        message, sr = self.publish(id_session, TF_MODEL, '0', None, 1, 'from python client', [value])
        if sr.code == '0':
            name_temp_file = 'temp_' + str(datetime.timestamp(datetime.now())).replace('.', '_') + '.h5'
            model.save(name_temp_file)
            try:
                with open(name_temp_file, "rb") as h5:
                    encoded_string = base64.b64encode(h5.read()).decode('utf-8')
                    message, sr1 = self.add_attachment(id_session, TF_MODEL, '0', {'name': name}, 'model_h5',
                                                       encoded_string)
                    if sr1.code == '0':
                        return 'model saved correctly', sr1
                    else:
                        raise TidyException(sr1)
            finally:
                os.remove(name_temp_file)
        else:
            raise TidyException(sr)

    def read_tf_model(self, id_session: str, name: str, revision: 'int' = 0) -> 'tensorflow model':
        data, sr = self.query(id_session, "!!{}('{}'):f($xml/parameters)!!".format(TF_MODEL, name))
        """
        Legge dalla classe di business tfModel un modello tensorflow con i relativi pesi, eventuali parametri aggiuntivi e metriche per la valutazione
        :param id_session: str Id sessione per cui si effettua il logout, se vale None è utilizzata la sessione di default
        :param name: Nome del modello
        :param revision: Revisione del modello. Il valore di default è 0 (ultima revisione)        
        :return:  tensorflow model utilizzabile
        """

        if sr.code == '0':
            if data is None: raise TidyException('Il modello [{}] non è stato addestrato.'.format(name))
            params = {}
            for child in Adapter.__to_element__(data):
                params[child.xpath('key')[0].text] = child.xpath('value')[0].text

            data, sr = self.read_attachment(id_session, TF_MODEL, '0', {'name': name}, 'model_h5', revision)
            if sr.code == '0':
                name_temp_file = 'temp_' + str(datetime.timestamp(datetime.now())).replace('.', '_') + '.h5'
                try:
                    with open(name_temp_file, "wb") as h5:
                        h5.write(base64.b64decode(bytearray(data, 'utf-8')))
                # model = keras.models.load_model(name_temp_file)
                finally:
                    os.remove(name_temp_file)
                # return model, params
                return params
            else:
                raise TidyException(sr)


""" 
adapter = Adapter('https://it-change.it/tidy/ml/?wsdl/N58dMzn82Mxbx8Mznsw2mmQa5xoMsycLoanc1Pixc4Froc', None)
_,l=adapter.login('federico', 'Gen2024!', 'mathmarket', 'excel')
a=adapter.query(query='count(!!messages!!)')
print(a)

list_classes,_=adapter.nameClasses()
for nc in list_classes:
    print(f"read {nc}...")
    c,sr=adapter.get_class_business(name=nc)
    print(f"ok {c.name if c is not None else 'no'}")
"""
"""
c, sr = adapter.get_class_business(name='Temperature')
for d in c.get_document([1]):
   df = d.get_table('temp')
   ini=d.get('nsim')
   print(ini)
   print(df)
   # df=df.rename(columns = {'data':'ggggg'})
   # d.replace_table('temp',df)
   d.keys['scenario'] = 5
   d.replace_value('scenario','5')
   print(d.to_xml(with_reference=True))

 """

