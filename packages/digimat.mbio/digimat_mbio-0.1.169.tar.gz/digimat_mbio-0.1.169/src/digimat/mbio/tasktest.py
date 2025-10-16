#!/bin/python

from .task import MBIOTask
from .xmlconfig import XMLConfig

# import requests
# import io
# import csv


class MBIOTaskPulsar(MBIOTask):
    def onInit(self):
        self._timeout=0
        self._period=1
        self._outputs=[]

    def onLoad(self, xml: XMLConfig):
        mbio=self.getMBIO()
        self._period=xml.getFloat('period', 1)
        items=xml.children('output')
        if items:
            for item in items:
                value=mbio[item.get('key')]
                if value and value.isWritable():
                    self._outputs.append(value)

    def poweron(self):
        self._timeout=self.timeout(self._period)
        return True

    def poweroff(self):
        return True

    def run(self):
        if self._outputs:
            if self.isTimeout(self._timeout):
                self._timeout=self.timeout(self._period)
                for value in self._outputs:
                    value.toggle()
            return min(5.0, self.timeToTimeout(self._timeout))


class MBIOTaskCopier(MBIOTask):
    def onInit(self):
        self._outputs=[]

    def onLoad(self, xml: XMLConfig):
        mbio=self.getMBIO()
        self._source=mbio.value(xml.get('source'))
        items=xml.children('output')
        if items:
            for item in items:
                value=mbio[item.get('key')]
                if value and value.isWritable():
                    self._outputs.append(value)

    def poweron(self):
        return True

    def poweroff(self):
        return True

    def run(self):
        if self._source and self._outputs:
            for value in self._outputs:
                value.set(self._source.value)
            return 1


if __name__ == "__main__":
    pass
