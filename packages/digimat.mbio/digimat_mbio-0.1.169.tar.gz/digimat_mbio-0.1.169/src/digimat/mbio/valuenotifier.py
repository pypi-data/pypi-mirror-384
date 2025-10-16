#!/bin/python

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .mbio import MBIO

# import time
import queue

from prettytable import PrettyTable


class QueueUnique(object):
    def __init__(self):
        self._set=set()
        self._queue=queue.Queue()

    def put(self, item):
        if item is not None and item not in self._set:
            self._set.add(item)
            self._queue.put(item)
            return True
        return False

    def get(self, wait=None):
        try:
            if wait:
                item=self._queue.get(True, wait)
            else:
                item=self._queue.get(False)

            if item is not None:
                self._set.remove(item)
                return item
        except:
            pass

    def count(self):
        return len(self._set)

    def reset(self):
        try:
            while self.get(False):
                pass
        except:
            pass
        self._set=set()

    def __len__(self):
        return self.count()

    def __iter__(self):
        return iter(self._set)


class MBIOValueNotifier(object):
    def __init__(self, mbio: MBIO):
        self._queue=QueueUnique()
        mbio.registerValueNotifier(self)

    def put(self, value):
        self._queue.put(value)

    def get(self, wait=None):
        return self._queue.get(wait)

    def reset(self):
        self._queue.reset()

    def count(self):
        return self._queue.count()

    def __radd__(self, value):
        self.put(value)

    def __len__(self):
        return self.count()

    def __iter__(self):
        return iter(self._queue)

    def dump(self):
        if self.count()>0:
            t=PrettyTable()
            t.field_names=['Values']
            t.align='l'
            for value in self._queue:
                t.add_row([value])

            print(t)


if __name__=='__main__':
    pass
