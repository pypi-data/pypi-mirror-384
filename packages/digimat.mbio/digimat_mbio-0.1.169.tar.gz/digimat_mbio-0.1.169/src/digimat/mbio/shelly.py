#!/bin/python

from .task import MBIOTask
from .xmlconfig import XMLConfig

from .netscan import MBIONetworkScanner
import requests


# Should use https://shelly-api-docs.shelly.cloud/gen2/General/RPCChannels
# https://shelly-api-docs.shelly.cloud/gen2/General/ComponentConcept
# https://shelly-api-docs.shelly.cloud/gen2/ComponentsAndServices/Shelly
# Sys.GetConfig
# Shelly.GetConfig
# Shelly.ListMethods
# Shelly.GetDeviceInfo
# Shelly.GetComponents
# Switch.GetConfig?id=0
# Switch.GetStatus?id=0
# Switch.Toggle?id=0
# Switch.Set?id=0&on=true


class ShellyDevice(object):
    def __init__(self, ip, logger):
        self._ip=ip
        self._logger=logger
        self._methods=None
        self.onInit()

    def onInit(self):
        pass

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self._ip)

    @property
    def logger(self):
        return self._logger

    def url(self, command):
        return 'http://%s/rpc/%s' % (self._ip, command)

    def doGET(self, command, params=None):
        try:
            url=self.url(command)
            proxies = { 'http': '', 'https': '' }
            self.logger.debug('shelly:%s(%s)' % (url, params))
            r=requests.get(url, params=params, timeout=3.0, verify=False, proxies=proxies)
            if r and r.ok:
                data=r.json()
                if data:
                    return data
                return True
        except:
            # self.logger.exception('doGET(%s:%s)' % (url, params))
            pass

    def call(self, name, params=None):
        return self.doGET(name, params)

    def getSystemStatus(self):
        return self.call('Sys.GetStatus')

    def getSystemConfig(self):
        return self.call('Sys.GetConfig')

    def reboot(self):
        return self.call('Shelly.Reboot')

    @property
    def firmware(self):
        try:
            return self.getSystemConfig()['device']['fw_id']
        except:
            pass

    @property
    def components(self):
        try:
            return self.call('Shelly.GetComponents')
        except:
            pass

    def upgrade(self, beta=False, url=None):
        stage='stable'
        if beta:
            stage='beta'
        params={'stage': stage}
        if url:
            params['url']=url
        return self.call('Shelly.Update', params)

    def getMAC(self):
        try:
            return self.getSystemConfig()['device']['mac'].lower()
        except:
            pass

    def ping(self):
        if self.getMAC():
            return True
        return False

    def methods(self, search=None):
        methods=self._methods
        if not methods:
            try:
                data=self.doGET('Shelly.ListMethods')
                methods=data['methods']
                if methods:
                    self._methods=methods
            except:
                pass
        if methods:
            if search:
                search=search.lower()
                return [item for item in methods if search in item.lower()]
            return methods


class ShellyDeviceSwitch(ShellyDevice):
    def getConfig(self, sid=0):
        params={'id': sid}
        return self.call('Switch.GetConfig', params)

    def getState(self, sid=0):
        try:
            params={'id': sid}
            data=self.call('Switch.GetStatus', params)
            if data['output']:
                return True
            return False
        except:
            pass

    def set(self, sid, state):
        try:
            if state:
                state='true'
            else:
                state='false'

            params={'id': sid, 'on': state}
            if self.call('Switch.Set', params):
                return True
        except:
            pass
        return False

    def on(self, sid=0):
        return self.set(sid, True)

    def off(self, sid=0):
        return self.set(sid, False)

    def toggle(self, sid=0):
        params={'id': sid}
        if self.call('Switch.Toggle', params):
            return True
        return False

class ShellyDeviceInput(ShellyDevice):
    def getConfig(self, sid=0):
        params={'id': sid}
        return self.call('Input.GetConfig', params)

    def getState(self, sid=0):
        try:
            params={'id': sid}
            data=self.call('Input.GetStatus', params)
            if data['state']:
                return True
            return False
        except:
            pass


class MBIOTaskShelly(MBIOTask):
    def initName(self):
        return 'shelly'

    def onInit(self):
        requests.packages.urllib3.disable_warnings()
        self.config.set('refreshperiod', 15)
        self._switches={}
        self._inputs={}
        self._devices=[]
        self._timeoutRefresh=0
        self.valueDigital('comerr', default=False)

    def addDevice(self, device):
        self._devices[device]

    def onLoad(self, xml: XMLConfig):
        self.config.update('refreshperiod', xml.getInt('refresh'))

        items=xml.children('switch')
        if items:
            for item in items:
                name=item.get('name')
                ip=item.get('ip')
                cid=item.getInt('id', 0)
                invert=item.getBool('invert', False)
                if name and not self._switches.get(name):
                    data={}
                    value=self.valueDigital('%s_state' % name, writable=True, commissionable=True)
                    data['state']=value
                    value.config.set('ip', ip)
                    value.config.set('cid', cid)
                    value.config.set('invert', invert)
                    value.config.set('device', self.switch(ip))
                    self._switches[name.lower()]=data

        items=xml.children('input')
        if items:
            for item in items:
                name=item.get('name')
                ip=item.get('ip')
                cid=item.getInt('id', 0)
                invert=item.getBool('invert', False)
                if name and not self._switches.get(name):
                    data={}
                    value=self.valueDigital('%s_state' % name, commissionable=True)
                    data['state']=value
                    value.config.set('ip', ip)
                    value.config.set('cid', cid)
                    value.config.set('invert', invert)
                    value.config.set('device', self.input(ip))
                    # data['t']=self.value('%s_t' % name, unit='C', resolution=0.1)
                    self._inputs[name.lower()]=data

    def poweron(self):
        return True

    def poweroff(self):
        return True

    def run(self):
        for name in self._switches.keys():
            value=self._switches[name]['state']
            if value.isPendingSync():
                self.microsleep()
                try:
                    device=value.config.device
                    cid=value.config.cid
                    if device.set(cid, value.toReachValue):
                        value.clearSync()
                        self._timeoutRefresh=0
                except:
                    pass
                value.clearSyncAndUpdateValue()

        if self.config.refreshperiod>0 and self.isTimeout(self._timeoutRefresh):
            self._timeoutRefresh=self.timeout(self.config.refreshperiod)
            error=False
            for name in self._switches.keys():
                self.microsleep()
                dev=self._switches[name]
                try:
                    value=dev['state']
                    device=value.config.device
                    cid=value.config.cid
                    v=device.getState(cid)
                    if v is not None:
                        if value.config.invert:
                            v=not v
                        value.updateValue(v)
                        value.setError(False)
                        continue
                    else:
                        error=True
                except:
                    pass

                dev['state'].setError(True)
                # dev['t'].setError(True)
                error=True

            for name in self._inputs.keys():
                self.microsleep()
                dev=self._inputs[name]
                try:
                    value=dev['state']
                    device=value.config.device
                    cid=value.config.cid
                    v=device.getState(cid)
                    if v is not None:
                        if value.config.invert:
                            v=not v
                        value.updateValue(v)
                        value.setError(False)
                        continue
                    else:
                        error=True
                except:
                    pass

                dev['state'].setError(True)
                # dev['t'].setError(True)
                error=True

            self.values.comerr.updateValue(error)

        return 5.0

    def scanner(self, network=None):
        network=network or self.getMBIO().network
        s=ShellyScanner(self, network)
        return s.scan()

    def device(self, ip):
        device=ShellyDevice(ip, self.logger)
        self._devices.append(device)
        return device

    def switch(self, ip):
        device=ShellyDeviceSwitch(ip, self.logger)
        self._devices.append(device)
        return device

    def input(self, ip):
        device=ShellyDeviceInput(ip, self.logger)
        self._devices.append(device)
        return device

    def upgrade(self):
        for device in self._devices:
            device.upgrade()

    def reboot(self):
        for device in self._devices:
            device.reboot()


class ShellyScanner(MBIONetworkScanner):
    def probe(self, host):
        try:
            url='http://%s/rpc/Sys.GetConfig' % (host)
            proxies = { 'http': '', 'https': '' }
            r=requests.get(url, timeout=1.0, proxies=proxies)
            if r and r.ok:
                data=r.json()
                return data['device']['mac']
        except:
            pass


if __name__ == "__main__":
    pass
