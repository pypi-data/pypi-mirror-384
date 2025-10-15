from lxml import etree

encoding='unicode'

class Key:
    """
       Classe da utilizzare per rappresentare la definizione di una chiave di una classe di business.
       """

    def __init__(self):
        self.name = None
        self.type = None
        self.reference = None
        self.default_value = None

    @staticmethod
    def from_xml(xml: 'str'):
        """
        Restituisce un oggetto Key effettuando il parsing di un xml.
        :param xml: str  Rappresentazione xml della chiave.
        :rtype: Restituisce un oggetto di tipo Key che rappresenta l'xml fornito in input
        """
        return Key.from_element_tree(etree.fromstring(xml))

    def to_xml(self):
        """
        Esporta la chiave in formato xml.
        :rtype: xml
        """
        return etree.tostring(self.to_element_tree(), encoding=encoding)

    def to_element_tree(self):
        """
        Esporta la chiave in formato elementTree.
        :rtype: Element
        """
        key = etree.Element('key')
        etree.SubElement(key, 'name', {}).text = self.name
        etree.SubElement(key, 'type', {}).text = self.type
        if self.reference is not None:
            etree.SubElement(key, 'reference', {}).text = self.reference
        if self.default_value is not None:
            etree.SubElement(key, 'defaultValue', {}).text = self.default_value

        return key

    @staticmethod
    def from_element_tree(root):
        """
        Restituisce un oggetto Key effettuando il parsing di un xml.
        :param root:
        :rtype: Restituisce un oggetto di tipo Key che rappresenta l'xml fornito in input
        """
        key = Key()
        for child in root:
            if child.tag == 'name':
                key.name = child.text
            elif child.tag == 'type':
                key.type = child.text
            elif child.tag == 'reference':
                key.reference = child.text
            elif child.tag == 'defaultValue':
                key.default_value = child.text

        return key


class Xslt:
    """
       Classe da utilizzare per rappresentare la definizione di una xslt di una classe di business.
       """

    def __init__(self):
        self.name = None
        self.description = None
        self.value = None

    @staticmethod
    def from_xml(xml: 'str'):
        """
        Restituisce un oggetto Xslt effettuando il parsing di un xml.
        :param xml: str  Rappresentazione xml del Xslt.
        :rtype: Restituisce un oggetto di tipo Xslt che rappresenta l'xml fornito in input
        """
        return Xslt.from_element_tree(etree.fromstring(xml))

    def to_xml(self):
        """
        Esporta l'xslt in formato xml.
        :rtype: xml
        """
        return etree.tostring(self.to_element_tree(), encoding=encoding)

    def to_element_tree(self):
        """
        Esporta l'xslt' in formato elementTree.
        :rtype: Element
        """
        xslt = etree.Element('xslt')
        etree.SubElement(xslt, 'name', {}).text = self.name
        if self.description is not None: etree.SubElement(xslt, 'description', {}).text = self.description
        etree.SubElement(xslt, 'value', {}).text = etree.fromstring(self.value)

        return xslt

    @staticmethod
    def from_element_tree(root):
        """
        Restituisce un oggetto Xslt effettuando il parsing di un xml.
        :param root:
        :rtype: Restituisce un oggetto di tipo Xslt che rappresenta l'xml fornito in input
        """
        xslt = Xslt()
        for child in root:
            if child.tag == 'name':
                xslt.name = child.text
            elif child.tag == 'description':
                xslt.description = child.text
            elif child.tag == 'value':
                xslt.value = etree.tostring(child[0], encoding=encoding) if len(child)>0 else None

        return xslt


class Component:
    """
       Classe da utilizzare per rappresentare la definizione di un componente di una classe di business.
       """

    def __init__(self):
        self.name = None
        self.description = None
        self.clazz = None
        self.xmlSchema = None
        self.xmlSchemaScope = None
        self.extractQuery = None
        self.updateQueryReplace = None
        self.updateQueryAppend = None
        self.updateQueryFirst = None
        self.updateQueryAfter = None
        self.updateQueryBefore = None

    @staticmethod
    def from_xml(xml: 'str'):
        """
        Restituisce un oggetto Component effettuando il parsing di un xml.
        :param xml: str  Rappresentazione xml del componente
        :rtype: Restituisce un oggetto di tipo Component che rappresenta l'xml fornito in input
        """
        return Component.from_element_tree(etree.fromstring(xml))

    def to_xml(self):
        """
        Esporta il componenente in formato xml.
        :rtype: xml
        """
        return etree.tostring(self.to_element_tree(), encoding=encoding)

    def to_element_tree(self):
        """
        Esporta il componente in formato elementTree.
        :rtype: Element
        """
        component = etree.Element('component')
        etree.SubElement(component, 'name', {}).text = self.name
        if self.description is not None: etree.SubElement(component, 'description', {}).text = self.description
        if self.clazz is not None: etree.SubElement(component, 'clazz', {}).text = self.clazz
        if self.xmlSchema is not None: etree.SubElement(component, 'xmlSchema', {
            'scope': self.xmlSchemaScope if self.xmlSchema is not None else 'inherit'}).text = self.xmlSchema
        if self.extractQuery is not None: etree.SubElement(component, 'extractQuery', {}).text = self.extractQuery
        if self.updateQueryReplace is not None: etree.SubElement(component, 'updateQueryReplace',
                                                              {}).text = self.updateQueryReplace
        if self.updateQueryAppend is not None: etree.SubElement(component, 'updateQueryAppend',
                                                             {}).text = self.updateQueryAppend
        if self.updateQueryFirst is not None: etree.SubElement(component, 'updateQueryFirst',
                                                            {}).text = self.updateQueryFirst
        if self.updateQueryAfter is not None: etree.SubElement(component, 'updateQueryAfter',
                                                            {}).text = self.updateQueryAfter
        if self.updateQueryBefore is not None: etree.SubElement(component, 'updateQueryBefore',
                                                             {}).text = self.updateQueryBefore
        return component

    @staticmethod
    def from_element_tree(root):
        """
        Restituisce un oggetto Component effettuando il parsing di un xml.
        :param root:
        :rtype: Restituisce un oggetto di tipo Component che rappresenta l'xml fornito in input
        """
        component = Component()
        for child in root:
            if child.tag == 'name':
                component.name = child.text
            elif child.tag == 'description':
                component.description = child.text
            elif child.tag == 'clazz':
                component.clazz = child.text
            elif child.tag == 'xmlSchema':
                component.xmlSchema = etree.tostring(child[0], encoding=encoding) if len(child)>0 else None
                if 'scope' in child.attrib.keys():
                    component.scope = child.attrib['scope']
            elif child.tag == 'extractQuery':
                component.extractQuery = child.text
            elif child.tag == 'updateQueryReplace':
                component.updateQueryReplace = child.text
            elif child.tag == 'updateQueryAppend':
                component.updateQueryAppend = child.text
            elif child.tag == 'updateQueryFirst':
                component.updateQueryFirst = child.text
            elif child.tag == 'updateQueryAfter':
                component.updateQueryAfter = child.text
            elif child.tag == 'updateQueryBefore':
                component.updateQueryBefore = child.text
        return component


class Schematron:
    """
       Classe da utilizzare per rappresentare uno schematron.
       """

    def __init__(self):
        self.name = None
        self.description = None
        self.script = None
        self.scope = None
        self.ext = None

    @staticmethod
    def from_xml(xml: 'str'):
        """
        Restituisce un oggetto Schematron effettuando il parsing di un xml.
        :param xml: str  Rappresentazione xml dello Schematron.
        :rtype: Restituisce un oggetto di tipo Schematron che rappresenta l'xml fornito in input
        """
        return Schematron.from_element_tree(etree.fromstring(xml))

    def to_xml(self):
        """
        Esporta lo schematron in formato xml.
        :rtype: xml
        """

        return etree.tostring(self.to_element_tree(), encoding=encoding)

    def to_element_tree(self):
        """
        Esporta lo schematron in formato elementTree.
        :rtype: Element
        """
        key = etree.Element('schematron')
        etree.SubElement(key, 'name', {}).text = self.name
        if self.description is not None: etree.SubElement(key, 'description', {}).text = self.description
        etree.SubElement(key, 'script', {}).text = self.script
        if self.scope is not None:
            etree.SubElement(key, 'scope', {}).text = self.scope
        if self.ext is not None:
            etree.SubElement(key, 'ext', {}).text = self.ext

        return key

    @staticmethod
    def from_element_tree(root):
        """
        Restituisce un oggetto Schematron effettuando il parsing di un xml.
        :param root:
        :rtype: Restituisce un oggetto di tipo Schematron che rappresenta l'xml fornito in input
        """
        schematron = Schematron()
        for child in root:
            if child.tag == 'name':
                schematron.name = child.text
            elif child.tag == 'description':
                schematron.description = child.text
            elif child.tag == 'script':
                schematron.script = etree.tostring(child[0], encoding=encoding) if len(child)>0 else None
                if 'scope' in child.attrib.keys():
                    schematron.scope = child.attrib['scope']
            elif child.tag == 'ext':
                schematron.ext = child.text
        return schematron


class Query:
    """
       Classe da utilizzare per rappresentare una class query o una alter query.
       """

    def __init__(self):
        self.name = None
        self.description = None
        self.body = None
        self.declaration = None
        self.mapImplicitParameter = {}

    @staticmethod
    def from_xml(xml: 'str'):
        """
        Restituisce un oggetto Query effettuando il parsing di un xml.
        :param xml: str  Rappresentazione xml della query.
        :rtype: Restituisce un oggetto di tipo Query che rappresenta l'xml fornito in input
        """
        return Query.from_element_tree(etree.fromstring(xml))

    def to_xml(self):
        """
        Esporta la query in formato xml.
        :rtype: xml
        """

        return etree.tostring(self.to_element_tree(), encoding=encoding)

    def to_element_tree(self):
        """
        Esporta la query in formato elementTree.
        :rtype: Element
        """
        query = etree.Element('query')
        etree.SubElement(query, 'name', {}).text = self.name
        if self.description is not None: etree.SubElement(query, 'description', {}).text = self.description
        if self.body is not None: etree.SubElement(query, 'body', {}).text = self.body
        if self.declaration is not None: etree.SubElement(query, 'declaration', {}).text = self.declaration
        if len(self.mapImplicitParameter.keys())>0 :
            implicit_parameter = etree.SubElement(query, 'implicitParameter', {})
            for ip in self.mapImplicitParameter:
                etree.SubElement(implicit_parameter, 'queryForPar', {"name": ip}).text = self.mapImplicitParameter[ip]
        return query

    @staticmethod
    def from_element_tree(root):
        """
        Restituisce un oggetto Query effettuando il parsing di un xml.
        :param root:
        :rtype: Restituisce un oggetto di tipo Query che rappresenta l'xml fornito in input
        """
        query = Query()
        for child in root:
            if child.tag == 'name':
                query.name = child.text
            elif child.tag == 'description':
                query.description = child.text
            elif child.tag == 'body':
                query.body = child.text
            elif child.tag == 'declaration':
                query.declaration = child.text
            elif child.tag == 'implicitParameter':
                for p in child:
                    query.mapImplicitParameter[p.attrib['name']] = p.text

        return query


class Validator:
    """
       Classe da utilizzare per rappresentare un validator.
       """

    def __init__(self):
        self.name = None
        self.description = None
        self.select = None
        self.function = None
        self.message = None
        self.language = "xquery"
        self.declaration = None
        # nella forma name=value   e    name.asSequence=true|false  (default true)
        self.globalVariable = {}

    @staticmethod
    def from_xml(xml: 'str'):
        """
        Restituisce un oggetto Validator effettuando il parsing di un xml.
        :param xml: str  Rappresentazione xml del validator.
        :rtype: Restituisce un oggetto di tipo Validator che rappresenta l'xml fornito in input
        """
        return Validator.from_element_tree(etree.fromstring(xml))

    def to_xml(self):
        """
        Esporta il validator in formato xml.
        :rtype: xml
        """
        return etree.tostring(self.to_element_tree(), encoding=encoding)

    def to_element_tree(self):
        """
        Esporta il validator in formato elementTree.
        :rtype: Element
        """
        validator = etree.Element('validator')
        etree.SubElement(validator, 'name', {}).text = self.name
        if self.description is not None: etree.SubElement(validator, 'description', {}).text = self.description
        if self.select is not None: etree.SubElement(validator, 'select', {}).text = self.select
        if self.function is not None: etree.SubElement(validator, 'function', {"language": self.language}).text = self.function
        if self.declaration is not None: etree.SubElement(validator, 'declaration', {}).text = self.declaration
        if self.message is not None: etree.SubElement(validator, 'message', {}).text = self.message

        for ip in self.globalVariable:
            if not (ip.endswith(".asSequence")):
                etree.SubElement(validator, 'global', {"name": ip, "isSequence": self.globalVariable[
                    f"{ip}.asSequence"] if f"{ip}.asSequence" in self.globalVariable else 'true'}).text = \
                    self.globalVariable[ip]
        return validator

    @staticmethod
    def from_element_tree(root):
        """
        Restituisce un oggetto Validator effettuando il parsing di un xml.
        :param root:
        :rtype: Restituisce un oggetto di tipo Validator che rappresenta l'xml fornito in input
        """
        validator = Validator()
        for child in root:
            if child.tag == 'name':
                validator.name = child.text
            elif child.tag == 'description':
                validator.description = child.text
            elif child.tag == 'select':
                validator.select = child.text
            elif child.tag == 'function':
                validator.function = child.text
                if 'language' in child.attrib:
                    validator.language = child.attrib['language']
            elif child.tag == 'message':
                validator.message = child.text
            elif child.tag == 'declaration':
                validator.declaration = child.text
            elif child.tag == 'language':
                validator.language = child.text
            elif child.tag == 'global':
                validator.globalVariable[child.attrib['name']] = child.text
                if 'isSequence' in child.attrib:
                    validator.globalVariable[f"{child.attrib['name']}.asSequence"] = child.attrib['isSequence']
        return validator


class Updater:
    """
       Classe da utilizzare per rappresentare un updater.
       """

    def __init__(self):
        self.name = None
        self.description = None
        self.select = None
        self.selectAsSequence = True
        self.function = None
        self.message = None
        self.apply = None
        self.default = None
        self.language = "xquery"
        self.declaration = None
        # nella forma name=value   e    name.asSequence=true|false  (default true)
        self.globalVariable = {}

    @staticmethod
    def from_xml(xml: 'str'):
        """
        Restituisce un oggetto Updater effettuando il parsing di un xml.
        :param xml: str  Rappresentazione xml del updater.
        :rtype: Restituisce un oggetto di tipo Updater che rappresenta l'xml fornito in input
        """
        return Updater.from_element_tree(etree.fromstring(xml))

    def to_xml(self):
        """
        Esporta l'updater in formato xml.
        :rtype: xml
        """
        return etree.tostring(self.to_element_tree(), encoding=encoding)

    def to_element_tree(self):
        """
        Esporta l'updater in formato elementTree.
        :rtype: Element
        """
        updater = etree.Element('updater')
        etree.SubElement(updater, 'name', {}).text = self.name
        if self.description is not None: etree.SubElement(updater, 'description', {}).text = self.description
        if self.select is not None: etree.SubElement(updater, 'select', {"isSequence": str(self.selectAsSequence)}).text = self.select
        if self.function is not None: etree.SubElement(updater, 'function', {"language": self.language}).text = self.function
        if self.apply is not None: etree.SubElement(updater, 'apply', {}).text = self.apply
        if self.default is not None: etree.SubElement(updater, 'default', {}).text = self.default
        if self.declaration is not None: etree.SubElement(updater, 'declaration', {}).text = self.declaration
        if self.message is not None:  etree.SubElement(updater, 'message', {}).text = self.message

        for ip in self.globalVariable:
            if not (ip.endswith(".asSequence")):
                etree.SubElement(updater, 'global', {"name": ip, "isSequence": self.globalVariable[
                    f"{ip}.asSequence"] if f"{ip}.asSequence" in self.globalVariable else 'true'}).text = \
                self.globalVariable[ip]
        return updater

    @staticmethod
    def from_element_tree(root):
        """
        Restituisce un oggetto Updater effettuando il parsing di un xml.
        :param root:
        :rtype: Restituisce un oggetto di tipo Updater che rappresenta l'xml fornito in input
        """
        updater = Updater()
        for child in root:
            if child.tag == 'name':
                updater.name = child.text
            elif child.tag == 'description':
                updater.description = child.text
            elif child.tag == 'select':
                updater.select = child.text
                if 'isSequence' in child.attrib:
                    updater.selectAsSequence = child.attrib['isSequence']
            elif child.tag == 'function':
                updater.function = child.text
                if 'language' in child.attrib:
                    updater.language = child.attrib['language']
            elif child.tag == 'message':
                updater.message = child.text
            elif child.tag == 'apply':
                updater.apply = child.text
            elif child.tag == 'default':
                updater.default = child.text
            elif child.tag == 'declaration':
                updater.declaration = child.text
            elif child.tag == 'global':
                updater.globalVariable[child.attrib['name']] = child.text
                if 'isSequence' in child.attrib:
                    updater.globalVariable[f"{child.attrib['name']}.asSequence"] = child.attrib['isSequence']
        return updater
