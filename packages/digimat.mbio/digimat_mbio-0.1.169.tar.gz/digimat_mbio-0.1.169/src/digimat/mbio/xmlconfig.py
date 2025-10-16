#!/bin/python

import xml.etree.ElementTree as ET

import base64


class XMLConfig(object):
    # xml is supposed to be already lowerized
    def __init__(self, xml: ET):
        self._xml=xml

    @property
    def tag(self):
        return self._xml.tag

    def isConfig(self, name):
        if self.tag==name.lower():
            return True
        return False

    def getAttribute(self, name, default=None):
        try:
            data=self._xml.get(name.lower(), default)
            if data[:5]=='(b16)':
                data=data[5:].upper()
                return base64.b16decode(data).decode()
            return data
        except:
            pass
        return default

    def get(self, name, default=None):
        return self.getAttribute(name, default)

    def text(self):
        try:
            return self._xml.text.strip()
        except:
            pass

    def __getkey__(self, key):
        return self.get(key)

    def hasAttribute(self, name):
        if self.getAttribute(name) is not None:
            return True
        return False

    def hasChild(self, name):
        if self.child(name):
            return True
        return False

    def getBool(self, name, default=None):
        try:
            value=self.getAttribute(name, default).lower()
            if value=='1' or value=='yes' or value=='true':
                return True
            return False
        except:
            pass
        return default

    def match(self, name, value):
        try:
            if self.get(name)==value.lower():
                return True
        except:
            pass
        return False

    def getInt(self, name, default=None, vmin=None, vmax=None):
        try:
            value=int(self.getAttribute(name, default))
            if vmin is not None:
                value=max(value, int(vmin))
            if vmax is not None:
                value=min(value, int(vmax))
            return value
        except:
            pass
        return default

    def getFloat(self, name, default=None, vmin=None, vmax=None):
        try:
            value=float(self.getAttribute(name, default))
            if vmin is not None:
                value=max(value, float(vmin))
            if vmax is not None:
                value=min(value, float(vmax))
            return value
        except:
            pass
        return default

    def getB16Str(self, name, default=None):
        try:
            # base64.b16encode(datastr.encode())
            data=self.get(name, default).upper().encode()
            return base64.b16decode(data).decode()
        except:
            pass
        return default

    def children(self, name='*'):
        children=[]
        items=self._xml.findall(name.lower())
        if items:
            for item in items:
                children.append(XMLConfig(item))
        return children

    def child(self, name):
        item=self._xml.find(name.lower())
        if item is not None:
            return XMLConfig(item)

    def tostring(self):
        return ET.tostring(self._xml, encoding='utf8')

    def dump(self):
        print(self.tostring())


if __name__ == "__main__":
    pass
