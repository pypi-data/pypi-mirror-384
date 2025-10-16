#!/bin/python

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .value import MBIOValue

from .task import MBIOTask
from .xmlconfig import XMLConfig


# During the onInit() phase, the task pre-declares inputs
# During the onLoad() phase, a ref (mbio-value, constant) is looked for each predeclared value
# A mbio-value is declared for each input which is still unlinked after the load phase

class VIO(object):
    def __init__(self):
        pass


class VBlock(object):
    def __init__(self):
        pass


class MBIOTaskVPLC(MBIOTask):
    def initName(self):
        name=self.__class__.__name__.lower().removeprefix('mbiotask')
        return '%s%d' % (name, self._parent.tasks.countByType(self.__class__))

    def declareAnalogInput(self, name, unit, resolution=0.1, default=None):
        if name:
            name=name.lower()
            if name not in self._inputs:
                i={'name': name, 'type': 'analog', 'value': None, 'unit': None, 'resolution': resolution, 'default': default}
                self._inputs[name]=i

    def declareDigitalInput(self, name, default=None):
        if name:
            name=name.lower()
            if name not in self._inputs:
                i={'name': name, 'type': 'digital', 'value': None, 'default': default}
                self._inputs[name]=i

    def declareInputs(self):
        # to be overriden
        pass

    def declareAnalogOutput(self, name, unit, resolution=0.1, default=None):
        if name:
            name=name.lower()
            if name not in self._outputs:
                self._outputs[name]=self.value('o_%s' % name, unit=unit, resolution=resolution, default=default)

    def declareDigitalOutput(self, name, default=None):
        if name:
            name=name.lower()
            if name not in self._outputs:
                self._outputs[name]=self.valueDigital('o_%s' % name, default=default)

    def declareOutputs(self):
        # to be overriden
        pass

    def onInit(self):
        self._inputs={}
        self._outputs={}
        self.declareInputs()
        self.declareOutputs()

    def input(self, name):
        try:
            return self._inputs[name]
        except:
            pass

    def output(self, name):
        try:
            return self._outputs[name]
        except:
            pass

    def str2value(self, data):
        if data is None:
            return None
        data=data.strip().lower()
        if data in ['1', 'true', 'on', 'yes']:
            return 1
        if data in ['0', 'false', 'off', 'no']:
            return 0
        try:
            return float(data)
        except:
            pass
        return 0

    def getInputValue(self, name, default=None):
        value=self.input(name)
        if value is not None:
            try:
                return value.value
            except:
                return value
        return default

    def onLoadInputs(self, xml: XMLConfig):
        inputs=xml.children('input')
        if inputs:
            for i in inputs:
                name=i.get('name')
                # check if input is available
                if self.input(name) is not None:
                    # 1. check if value is a ref to an existing mbio value
                    value=self.getMBIO().value(i.get('source'))
                    if value is not None:
                        self._inputs[name]=value
                        continue

                    # 2. value is a constant
                    value=self.str2value(i.get('value'))
                    if value is not None:
                        self._inputs[name]=value
                        continue

        # declare mbio values for still unlinked inputs
        for i in self._inputs.values():
            try:
                name=i['name']
                if i['type']=='analog':
                    value=self.value('i_%s' % name, unit=i['unit'], resolution=i['resolution'], default=i['default'], writable=True)
                    self._inputs[name]=value
                    continue
                if i['type']=='digital':
                    value=self.valueDigital('i_%s' % name, default=i['default'], writable=True)
                    self._inputs[name]=value
                    continue
            except:
                pass

    def onLoadOutputs(self, xml: XMLConfig):
        outputs=xml.children('output')
        if outputs:
            for o in outputs:
                name=o.get('name')
                # check if output is available
                if self.output(name) is not None:
                    # TODO:
                    pass

    def configure(self, xml: XMLConfig):
        pass

    def onLoad(self, xml: XMLConfig):
        self.onLoadInputs(xml)
        self.onLoadOutputs(xml)
        self.configure(xml)

    def poweron(self):
        return True

    def poweroff(self):
        return True

    def run(self):
        return 5.0


class MBIOTaskVPLCTest(MBIOTaskVPLC):
    def declareInputs(self):
        self.declareAnalogInput('t', 'C')
        self.declareAnalogInput('spt', 'C')
        self.declareDigitalInput('heat')
        self.declareDigitalInput('cool')

    def declareOutputs(self):
        self.declareAnalogOutput('vheat', '%')
        self.declareAnalogOutput('vcool', '%')

    def configure(self, xml: XMLConfig):
        pass

    def poweron(self):
        return True

    def poweroff(self):
        return True

    def run(self):
        self.values.o_vheat.updateValue(self.getInputValue('spt'))
        return 1.0


if __name__ == "__main__":
    pass
