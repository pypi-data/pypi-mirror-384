#!/bin/python

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .value import MBIOValue

from .task import MBIOTask
from .xmlconfig import XMLConfig
from .xknxclient import XKNXClient


class MBIOTaskKnx(MBIOTask):
    def initName(self):
        return 'knx'

    @property
    def client(self):
        return self._client

    def onInit(self):
        self._client=None
        self._data={}

        self.config.set('refreshperiod', 10)
        self._timeoutRefresh=0
        self.valueDigital('comerr', default=False)

    def addGroup(self, name, address, dtype, timeout, writable=False):
        if name and name not in self._data and address:
            data={}
            data['address']=address
            data['knx']=self._client._values.add(address, timeout=timeout)
            if dtype in ('bool'):
                value=self.valueDigital('%s_state' % name, writable=writable, commissionable=True)
            elif dtype in ('byte', 'int', 'number', 'float'):
                value=self.value('%s_value' % name, writable=writable, commissionable=True)
            data['state']=value

            self.logger.debug("KNX: mapping knx %s group %s to value %s", dtype, address, value.name)
            self._data[name]=data
            return value

    def onLoad(self, xml: XMLConfig):
        self.config.update('refreshperiod', xml.getInt('refresh'))
        self.config.set('host', xml.get('host'))
        if not self.config.host:
            self.config.update('host', self.pickleRead('host'))

        self._client=XKNXClient(host=self.config.host,
                logger=self.logger,
                timeoutRefresh=self.config.refreshperiod)

        items=xml.children('group')
        if items:
            for item in items:
                # deny name duplication
                name=item.get('name')
                address=item.get('address')
                dtype=item.get('type')
                timeout=item.getFloat('timeout')
                writable=item.getBool('writable')
                self.addGroup(name, address, dtype, timeout, writable)

    def waitForConnection(self, timeout=2.0):
        if self.client and self.config.host:
            self.client.start()
            timeout=self.timeout(timeout)
            while not self.isTimeout(timeout):
                if self.client.isConnected():
                    self.logger.info('KNX: connected to router %s' % self.config.host)
                    return True
                self.sleep(0.1)

        self.logger.error('KNX: unable to connect to router %s' % self.config.host)
        return False

    def poweron(self):
        if self.waitForConnection(3.0):
            self.client.refreshValues()
        return True

    def poweroff(self):
        self.client.stop()
        return True

    def run(self):
        delay=5.0

        if not self.client.isConnected():
            self.values.comerr.updateValue(True)
            for data in self._data.values():
                value=data['state']
                value.setError(True)
        else:
            self.values.comerr.updateValue(False)
            for data in self._data.values():
                knxvalue=data['knx']
                knxvalue.refreshIfTimeout()

                if knxvalue.age()>180:
                    value.setError(True)
                else:
                    value=data['state']
                    value.updateValue(knxvalue.data)
                    value.setError(False)
                    if value.isPendingSync():
                        knxvalue.write(value.toReachValue)
                        value.clearSync()
                        delay=1.0

        return delay

    def discover(self, stopOnFound=False):
        return self.client.discover(self.getMBIO().interface, stopOnFound=stopOnFound)


if __name__ == "__main__":
    pass
