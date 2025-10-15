from __future__ import annotations

from io import StringIO
from typing import Dict

import pandas as pd
from lxml import etree
from pandas import DataFrame

from .exception import TidyException

encoding = 'unicode'

class Document:
    """
    Classe che rappresenta un documento di una classe di business
    E' possibile:
      - recuperare l'intero xml
      - recuperare un singolo nodo sia in forma di stringa che DataFrame ove possibile
      - modificare il contenuto
      - ripubblicarre il contenuto
      - eliminare il documento

    Attributi
    ----------
    adapter : Adapter|None
        riferimento all'oggetto Adapter
    class_business :ClassBusiness|None
       riferimento all'oggetto ClassBusiness
    __root : etree._Element()
       root del documento xml
    name : str
       Nome della classe di business
    owner : str
       Utente che ha creato il documento
    lastUpdateOwner : str
       Utente che ha effettuato l'ultima modifica al documento
    group : str
       gruppo di appartenenza dell'owner
    nameApplication : str
       nome applicazione di appartenenza dell'owner
    creationDate : str
       data creazione dl documento
    lastUpdateDate : str
       data ultima modifica del documento
    note : str
       note aggiuntive aggiunte in fase di pubblicazione
    revision : int
       revisine del documento
    version : str
       numero versione della classe di business
    labelVersion : str
       label version della classe di business
    update : int
       numero di update della classe di business
    workspace : str
       workspacee di appartenenza dell'owner
    keys :Dict[str, str]= {}
       Dictionary contenente nome chiave e valore chiave
    metainf : etree._Element()|None
       Eventuali metainf associate al documento

    Methods
    -------
    from_xml(xml: str, is_wrapped: bool = False):Document
        Restituisce un Documento
    to_xml(self, with_reference: bool = False)->str
        Esporta il documento in xml
    from_element_tree(document:etree._Element(), is_wrapped: bool = False)->Document
        Restituisce un oggetto Document effettuando il parsing di un xml.
    get_doc(self)->etree._Element():
        Restituisce il documento.
    get(self, xpath: str = '', wrapped: bool = False) ->str:
        Restituisce il valore presente al xpath indicato.
    get_table(self, xpath: str = '') -> DataFrame:
         Restituisce il valore presente al xpath indicato come DataFrame.
    replace_value(self, xpath: str = '', new_value: str = '') ->Document:
        Sostituisce  il testo contenuto nell'elemento identificato da xpath con new_value
    replace_node(self, xpath: 'str' = '', xml_node: 'str|Element|DataFrame' = None, root_name: str = None,  row_name: str = 'row')->Document:
        Sostituisce gli elementi identificati dalla stringa xpath con il nuovo elemento xml_node.
    append(self, xpath: 'str' = '', xml_node: 'str|Element|DataFrame' = None, root_name: str = None,  row_name: str = 'row')->Document:
        Appende l'elemento xml_node come come ultimo nodo negli elementi identificati dalla stringa xpath.
    add_next(self, xpath: 'str' = '', xml_node: 'str|Element|DataFrame' = None, root_name: str = None, row_name: str = 'row')->Document:
        Aggiunge l'elemento xml_node come fratello successivo direttamente dopo gli elementi identificati dalla stringa xpath.
    add_previous(self, xpath: 'str' = '', xml_node: 'str|etree._Element|DataFrame' = None, root_name: str = None, row_name: str = 'row')->Document:
        Aggiunge l'elemento xml_node come fratello precedente direttamente prima degli elementi identificati dalla stringa xpath.
    delete(self, xpath: 'str' = ''   ) -> Document:
        Elimina gli elementi  identificati dalla stringa xpath.
    publish(self, is_revision: bool = True)->ServiceResponse:
        Pubblica il documento sul servet tidy4.
    delete(self, revision:int =0) -> ServiceResponse:
        Elimina il documento dal servet tidy4.        
    """
    def __init__(self):
        self.adapter: 'Adapter' | None = None
        self.class_business: 'ClassBusiness' | None = None
        self.__root: etree._Element |None = None
        self.name: str | None = None
        self.owner: str | None = None
        self.lastUpdateOwner: str | None = None
        self.group: str | None = None
        self.nameApplication: str | None = None
        self.creationDate: str | None = None
        self.lastUpdateDate: str | None = None
        self.note: str | None = None
        self.revision: int | None = None
        self.version: str | None = None
        self.labelVersion: str | None = None
        self.update: int | None = None
        self.workspace: str | None = None
        self.keys: Dict[str, str] | None = {}
        self.metainf = None

    @staticmethod
    def from_xml(xml: str, is_wrapped: bool = False) -> Document:
        """
        Restituisce un oggetto Document effettuando il parsing di un xml.
        :param xml: str  Rappresentazione xml del documento.
        :param is_wrapped: Se True considero il documento decorato con una sovrastruttura che comprende anche i references, le chiavi e le metainf
            Esempio
               <value>
                 <references>...</references>
                 <keys>...</keys>
                 <xmlValue>...</xmlValue>
                 <metainf>...</metainf>
               </value>
        :rtype: Restituisce un oggetto di tipo Document che rappresenta l'xml fornito in input
        """
        return Document.from_element_tree(etree.fromstring(xml), is_wrapped)

    def to_xml(self, with_reference: bool = False) -> str:
        """
        Esporta il documento in formato xml.
        :param with_reference: se True racchiude il documento in una sovrastruttura contenente i references, le chiavi e le metainf
        :rtype: xml
        """
        return etree.tostring(self.__to_element_tree(with_reference), encoding=encoding)

    def __to_element_tree(self, with_reference: bool = False) -> etree._Element:
        """
        Esporta il documento in formato etree._Element().
        :param with_reference: se True racchiude il documento in una sovrastruttura contenente i references, le chiavi e le metainf
        :rtype: Element
        """

        if with_reference:
            if self.class_business is None: raise TidyException("variabile class_business non impostata")
            value = etree.Element('value')
            references = etree.SubElement(value, 'references', {})
            if self.name is not None: etree.SubElement(references, 'name', {}).text = self.name
            if self.owner is not None: etree.SubElement(references, 'owner', {}).text = self.owner
            if self.lastUpdateOwner is not None: etree.SubElement(references, 'lastUpdateOwner',
                                                                  {}).text = self.lastUpdateOwner
            if self.group is not None: etree.SubElement(references, 'group', {}).text = self.group
            if self.nameApplication is not None: etree.SubElement(references, 'nameApplication',
                                                                  {}).text = self.nameApplication
            if self.creationDate is not None: etree.SubElement(references, 'creationDate', {}).text = self.creationDate
            if self.lastUpdateDate is not None: etree.SubElement(references, 'lastUpdateDate',
                                                                 {}).text = self.lastUpdateDate
            if self.note is not None: etree.SubElement(references, 'note', {}).text = self.note
            if self.revision is not None: etree.SubElement(references, 'revision', {}).text = str(self.revision)
            if self.version is not None: etree.SubElement(references, 'version', {}).text = self.version
            if self.labelVersion is not None: etree.SubElement(references, 'labelVersion', {}).text = self.labelVersion
            if self.update is not None: etree.SubElement(references, 'update', {}).text = str(self.update)
            if self.workspace is not None: etree.SubElement(references, 'workspace', {}).text = self.workspace
            keys = etree.SubElement(value, 'keys', {})
            for k in self.class_business.keys:
                etree.SubElement(keys, 'key', {'name': k.name}).text = str(self.keys[k.name])
            xmlValue = etree.SubElement(value, 'xmlValue', {})
            xmlValue.append(self.__root)
            if self.metainf is not None: etree.SubElement(value, 'metainf', {}).text = etree.tostring(self.metainf,
                                                                                                      encoding=encoding)

            return value
        else:
            return self.__root

    @staticmethod
    def from_element_tree(document: etree._Element, is_wrapped: bool = False) -> Document:
        """
        Restituisce un oggetto Document effettuando il parsing di un xml.
        :param document:
        :param is_wrapped: Se True considero il documento decorato con una sovrastruttura che comprende anche i references, le chiavi e le metainf
            Esempio
               <value>
                 <references>...</references>
                 <keys>...</keys>
                 <xmlValue>...</xmlValue>
                 <metainf>...</metainf>
               </value>
        :rtype: Restituisce un oggetto di tipo Document che rappresenta l'xml fornito in input
        """
        doc = Document()
        if is_wrapped:
            for child in document:
                if child.tag == 'references':
                    for r in child:
                        if r.tag == 'name':
                            doc.name = r.text
                        elif r.tag == 'lastUpdateOwner':
                            doc.lastUpdateOwner = r.text
                        elif r.tag == 'owner':
                            doc.owner = r.text
                        elif r.tag == 'group':
                            doc.group = r.text
                        elif r.tag == 'nameApplication':
                            doc.nameApplication = r.text
                        elif r.tag == 'update':
                            doc.update = int(r.text)
                        elif r.tag == 'creationDate':
                            doc.creationDate = r.text
                        elif r.tag == 'lastUpdateDate':
                            doc.lastUpdateDate = r.text
                        elif r.tag == 'note':
                            doc.note = r.text
                        elif r.tag == 'revision':
                            doc.revision = int(r.text)
                        elif r.tag == 'labelVersion':
                            doc.labelVersion = r.text
                        elif r.tag == 'update':
                            doc.update = r.text
                        elif r.tag == 'workspace':
                            doc.workspace = r.text
                elif child.tag == 'keys':
                    for k in child:
                        doc.keys[k.attrib['name']] = k.text
                elif child.tag == 'metainf':
                    doc.metainf = child
                elif child.tag == 'xmlValue':
                    doc.__root = child[0]
        else:
            doc.__root = document

        return doc

    def get_doc(self) -> etree._Element:
        """
        Restituisce il documento.
        E' possibile effettuare interrogazioni ed effettuare modifiche
        :rtype: lxml
        """
        return self.__root

    def get(self, xpath: str = '', wrapped: bool = False) -> str:
        """
        Restituisce il valore presente al xpath indicato.
        se l'xpath restituisce più elementi è restituita un'unica stringa con la concatenazione di tutti i risultati
        se l'xpath restituisce un solo elemento ed il parametr wrapped è False (valore di default) è restituito solo il testo dell'elemento
        :param xpath: xpath da eseguire
        :param wrapped: se True restituisce tutto il nodo xml
           Esempio:
              xpath=root/id
              se wrapped=True  restituisce   <id>1</id>
              se wrapped=False restituisce 1

        :rtype: str
        """
        p = self.__root.xpath(xpath)
        return p[0].text if not wrapped and len(p) == 1 and p[0].text is not None else ''.join(
            etree.tostring(child, encoding=encoding) for child in p)

    def get_table(self, xpath: str = '.') -> DataFrame:
        """
        Restituisce il valore presente al xpath indicato come DataFrame.
        se all'xpath non è presente una tabella è generata un eccezione
        E' restituito un dataFrame
        :param xpath: xpath da eseguire
        :rtype: str
        """
        try:
            xml=self.__root if xpath=='.' else self.get(xpath=xpath, wrapped=True)
            return pd.read_xml(StringIO(etree.tostring(xml, encoding="unicode")))
        except:
            raise TidyException('Impossibile recuperare una DataFrame')

    def replace_value(self, xpath: str = '', new_value: str = '') -> Document:
        """
        Sostituisce  il testo contenuto nell'elemento identificato da xpath con new_value
        :param xpath: xpath da eseguire per identificare gli elementi a cui sostituie il valore
        :param new_value: nuovo valore
        :rtype: Document restituisce il documento stesso
        """
        p = self.__root.xpath(xpath)
        if p is not None:
            for child in p: child.text = new_value

        return self

    def replace_node(self, xpath: str = '', xml_node: str | etree._Element | DataFrame = None, root_name: str = None,
                     row_name: str = 'row') -> Document:
        """
        Sostituisce gli elementi identificati dalla stringa xpath con il nuovo elemento xml_node.
        :param xpath: xpath da eseguire per determinare i nodi da sostituire
        :param xml_node:str|Element|DataFrame documento xml da aggiungere
        :param root_name:str se il nodo è un DataFrame indica il nome della root della tabella, il valore di default è recuperato come ultimo path di xPath
        :param row_name:str se il nodo è un DataFrame indica i nomi di ogni riga, il valore di default è row
        :rtype: Document restituisce il documento stesso
        """
        assert xpath is not None, "xPath deve essere valorizzato!"
        assert xml_node is not None, "xml_node deve essere valorizzato!"

        p = self.__root.xpath(xpath)
        if p is not None:
            node_to_add = xml_node
            if isinstance(node_to_add, str): node_to_add = etree.fromstring(node_to_add)
            if isinstance(node_to_add, DataFrame):
                rn = xpath.split('/')[-1] if root_name is None else root_name
                split=rn.split('/')
                prefix=None
                if len(split) >1:
                    rn=split[-1]
                    prefix=etree.Element(split[0])
                    sub=prefix
                    for path in split[1:-1]:
                        sub.append(etree.Element(path))
                        sub=sub[0]
                node_to_add = etree.fromstring(node_to_add.to_xml(  root_name=rn, row_name=row_name, index=False, xml_declaration=False))
                if prefix is not None:
                    sub.append(node_to_add)
                    node_to_add=prefix

            for child in p:
                child.getparent().replace(child, node_to_add)
        return self

    def append(self, xpath: str = '', xml_node: str | etree._Element | DataFrame = None, root_name: str = None,
               row_name: str = 'row') -> Document:
        """
        Appende l'elemento xml_node come come ultimo nodo negli elementi identificati dalla stringa xpath.
        :param xpath: xpath da eseguire per determinare i nodi a cui appenddere xml_node
        :param xml_node:str|Element|DataFrame documento xml da aggiungere
        :param root_name:str se il nodo è un DataFrame indica il nome della root della tabella, il valore di default è recuperato come ultimo path di xPath
        :param row_name:str se il nodo è un DataFrame indica i nomi di ogni riga, il valore di default è row
        :rtype: Document restituisce il documento stesso
        """
        assert xpath is not None, "xPath deve essere valorizzato!"
        assert xml_node is not None, "xml_node deve essere valorizzato!"

        p = self.__root.xpath(xpath)
        if p is not None:
            node_to_add = xml_node
            if isinstance(node_to_add, str): node_to_add = etree.fromstring(node_to_add)
            if isinstance(node_to_add, DataFrame):
                rn = xpath.split('/')[-1] if root_name is None else root_name
                split=rn.split('/')
                prefix=None
                if len(split) >1:
                    rn=split[-1]
                    prefix=etree.Element(split[0])
                    sub=prefix
                    for path in split[1:-1]:
                        sub.append(etree.Element(path))
                        sub=sub[0]
                node_to_add = etree.fromstring(node_to_add.to_xml(  root_name=rn, row_name=row_name, index=False, xml_declaration=False))
                if prefix is not None:
                    sub.append(node_to_add)
                    node_to_add=prefix

            for child in p:
                child.append(node_to_add)
        return self

    def add_next(self, xpath: 'str' = '', xml_node: 'str|etree._Element|DataFrame' = None, root_name: str = None,
                 row_name: str = 'row') -> Document:
        """
        Aggiunge l'elemento xml_node come fratello successivo direttamente dopo gli elementi identificati dalla stringa xpath.
        :param xpath: xpath da eseguire per determinare i nodi a cui far seguire xml_node
        :param xml_node:str|Element|DataFrame documento xml da aggiungere
        :param root_name:str se il nodo è un DataFrame indica il nome della root della tabella, il valore di default è recuperato come ultimo path di xPath
        :param row_name:str se il nodo è un DataFrame indica i nomi di ogni riga, il valore di default è row
        :rtype: Document restituisce il documento stesso
        """
        assert xpath is not None, "xPath deve essere valorizzato!"
        assert xml_node is not None, "xml_node deve essere valorizzato!"

        p = self.__root.xpath(xpath)
        if p is not None:
            node_to_add = xml_node
            if isinstance(node_to_add, str): node_to_add = etree.fromstring(node_to_add)
            if isinstance(node_to_add,  DataFrame):
                rn = xpath.split('/')[-1] if root_name is None else root_name
                split=rn.split('/')
                prefix=None
                if len(split) >1:
                    rn=split[-1]
                    prefix=etree.Element(split[0])
                    sub=prefix
                    for path in split[1:-1]:
                        sub.append(etree.Element(path))
                        sub=sub[0]
                node_to_add = etree.fromstring(node_to_add.to_xml(  root_name=rn, row_name=row_name, index=False, xml_declaration=False))
                if prefix is not None:
                    sub.append(node_to_add)
                    node_to_add=prefix

            for child in p:
                child.addnext( node_to_add)
        return self

    def add_previous(self, xpath: 'str' = '', xml_node: 'str|etree._Element|DataFrame' = None, root_name: str = None,
                     row_name: str = 'row') -> Document:
        """
        Aggiunge l'elemento xml_node come fratello precedente direttamente prima degli elementi identificati dalla stringa xpath.
        :param xpath: xpath da eseguire per determinare i nodi a cui far precedere xml_node
        :param xml_node:str|Element|DataFrame documento xml da aggiungere
        :param root_name:str se il nodo è un DataFrame indica il nome della root della tabella, il valore di default è recuperato come ultimo path di xPath
        :param row_name:str se il nodo è un DataFrame indica i nomi di ogni riga, il valore di default è row
        :rtype: Document restituisce il documento stesso
        """
        assert xpath is not None, "xPath deve essere valorizzato!"
        assert xml_node is not None, "xml_node deve essere valorizzato!"

        p = self.__root.xpath(xpath)
        if p is not None:
            node_to_add = xml_node
            if isinstance(node_to_add, str): node_to_add = etree.fromstring(node_to_add)
            if isinstance(node_to_add,  DataFrame):
                rn = xpath.split('/')[-1] if root_name is None else root_name
                split=rn.split('/')
                prefix=None
                if len(split) >1:
                    rn=split[-1]
                    prefix=etree.Element(split[0])
                    sub=prefix
                    for path in split[1:-1]:
                        sub.append(etree.Element(path))
                        sub=sub[0]
                node_to_add = etree.fromstring(node_to_add.to_xml(  root_name=rn, row_name=row_name, index=False, xml_declaration=False))
                if prefix is not None:
                    sub.append(node_to_add)
                    node_to_add=prefix

            for child in p:
                child.addprevious( node_to_add)
        return self

    def delete_node(self, xpath: 'str' = ''   ) -> Document:
        """
        Elimina gli elementi  identificati dalla stringa xpath.
        :param xpath: xpath da eseguire per determinare i nodi da eliminare
        :rtype: Document restituisce il documento stesso
        """
        assert xpath is not None, "xPath deve essere valorizzato!"

        p = self.__root.xpath(xpath)
        if p is not None:
            for child in p:
                child.getparent().remove(child)
        return self

    def publish(self, is_revision: bool = True, background: bool = False) -> 'ServiceResponse':
        """
        Pubblica il documento sul servet tidy4.
        :param is_revision: se True crea una revisione altrimenti un update
        :param background:bool: se True la pubblicazione è lanciata in background
        :rtype: ServiceResponse
        """

        if self.adapter is None: raise TidyException("Variabile adapter non impostata")
        _,sr=self.adapter.publish(name_class=self.name, action=1 if is_revision else 0, note='from python adapter',
                             docs=[self.to_xml(with_reference=True)],background=background)
        return sr

    def delete(self, revision:int =0) -> 'ServiceResponse':
        """
        Elimina il documento dal servet tidy4.
        :param revision: indica la revisione da eliminare
                         0 : elimina l'ultima revisione
                         -1: elimina tutte le revisioni
                         >0 elimina la revisione specifica
        :rtype: ServiceResponse
        """
        if self.adapter is None: raise TidyException("Variabile adapter non impostata")

        sr=self.adapter.delete_value(name_class=self.name, keys=self.keys,revision=revision)

        return sr

class Documents(list[Document]):
    def to_xml(self,root:str=''):
        open=f"<{root}>" if root!='' else ''
        close = f"</{root}>" if root != '' else ''
        return f"{open}{''.join(x.to_xml() for x in self)}{close}"

    def get_table(self) -> DataFrame:
        """
        Restituisce il valore presente al xpath indicato come DataFrame.
        se all'xpath non è presente una tabella è generata un eccezione
        E' restituito un dataFrame
        :param xpath: xpath da eseguire
        :rtype: str
        """
        try:
            xml=self.to_xml(root="r")
            return pd.read_xml(StringIO(xml))
        except:
            raise TidyException('Impossibile recuperare una DataFrame')