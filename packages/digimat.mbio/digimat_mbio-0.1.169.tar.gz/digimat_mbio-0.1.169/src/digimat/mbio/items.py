#!/bin/python

from prettytable import PrettyTable


class Items(object):
    def __init__(self, logger):
        self._items=[]
        self._logger=logger
        self._itemIndex={}

    @property
    def logger(self):
        return self._logger

    def count(self):
        return len(self._items)

    def isEmpty(self):
        return self.count()==0

    def all(self):
        return self._items

    def __len__(self):
        return self.count()

    def __iter__(self):
        return iter(self.all())

    def __getitem__(self, key):
        if key is not None:
            try:
                return self._items[key]
            except:
                pass
        return None

    def item(self, key):
        return self[key]

    def add(self, item):
        index=len(self._items)
        self._items.append(item)
        self._itemIndex[item]=index
        return item

    def index(self, item):
        try:
            return self._itemIndex[item]
        except:
            pass

    def __repr__(self):
        return '%s(%d items)' % (self.__class__.__name__, self.count())

    def dump(self):
        if self._items:
            t=PrettyTable()
            t.field_names=['#', 'Content']
            t.align='l'
            for n in range(self.count()):
                item=self._items[n]
                t.add_row([self.index(item), str(item)])
        print(t.get_string())


if __name__ == "__main__":
    pass
