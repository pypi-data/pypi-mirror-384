#!/bin/python

from prettytable import PrettyTable


class MBIOConfig(object):
    def __init__(self):
        self._data={}
        # self._updated=False

    # Force return None if called with an unknown attribute (config name)
    def __getattr__(self, name):
        try:
            return getattr(self, name)
        except:
            pass
        return None

    def get(self, name, default=None):
        try:
            return self._data[name.lower()]
        except:
            pass
        return default

    # def updated(self, reset=True):
        # if self._updated:
            # if reset:
                # self._updated=False
                # return True
        # return False

    def set(self, name, value=None):
        if name is not None:
            # create the object's variable attribute
            setattr(self, name, value)
            self._data[name.lower()]=value

    def update(self, name, value):
        if value is not None and name in self._data:
            self.set(name, value)

    def xmlUpdate(self, xml, name):
        data=xml.get(name)
        self.update(name, data)

    def xmlUpdateBool(self, xml, name):
        data=xml.getBool(name)
        self.update(name, data)

    def xmlUpdateFloat(self, xml, name, vmin=None, vmax=None):
        data=xml.getFloat(name, vmin=vmin, vmax=vmax)
        self.update(name, data)

    def xmlUpdateInt(self, xml, name, vmin=None, vmax=None):
        data=xml.getInt(name, vmin=vmin, vmax=vmax)
        self.update(name, data)

    def __getkey__(self, key):
        return self.get(key)

    def getBool(self, name, default=None):
        try:
            value=self.get(name)
            if type(value) is bool:
                return value
            if type(value) is int:
                return bool(value)
            if value.lower() in ['1', 'yes', 'true']:
                return True
            if value.lower() in ['0', 'no', 'false']:
                return False
        except:
            pass
        return default

    def contains(self, name, data):
        try:
            value=self.get(name)
            if data.lower() in value:
                return True
        except:
            return False

    def bool(self, name, default=None):
        return self.getBool(name, default)

    def getInt(self, name, default=None, vmin=None, vmax=None):
        try:
            value=int(self.get(name))
            if vmin is not None:
                value=max(value, int(vmin))
            if vmax is not None:
                value=min(value, int(vmax))
            return value
        except:
            pass
        return default

    def int(self, name, default=None):
        return self.getInt(name, default)

    def getFloat(self, name, default=None, vmin=None, vmax=None):
        try:
            value=float(self.get(name))
            if vmin is not None:
                value=max(value, int(vmin))
            if vmax is not None:
                value=min(value, int(vmax))
            return value
        except:
            pass
        return default

    def float(self, name, default=None):
        return self.getFloat(name, default)

    def count(self):
        return len(self._data)

    def __len__(self):
        return self.count()

    def all(self):
        return self._data

    def __iter__(self):
        return iter(self.all())

    def dump(self):
        t=PrettyTable()
        t.field_names=['Config', 'Value']
        t.align='l'

        for data in self._data:
            v=None
            try:
                v=getattr(self, data)
            except:
                pass
            t.add_row([data, v])

        print(t.get_string())

    def __repr__(self):
        return '%s(%d items)' % (self.__class__.__name__, self.count())


if __name__=='__main__':
    pass
