#!/bin/python

from .task import MBIOTask
from .xmlconfig import XMLConfig

from .netscan import MBIONetworkScanner
import requests


# API: https://api.mystrom.ch/#a141a894-925c-4e8b-bcaf-68c3a67fa98d
class MBIOTaskMyStromSwitch(MBIOTask):
    def initName(self):
        return 'mystrom'

    def onInit(self):
        self.config.set('refreshperiod', 15)
        self._switches={}
        self._timeoutRefresh=0
        self.valueDigital('comerr', default=False)

    def onLoad(self, xml: XMLConfig):
        self.config.update('refreshperiod', xml.getInt('refresh'))

        items=xml.children('switch')
        if items:
            for item in items:
                name=item.get('name')
                ip=item.get('ip')
                model=item.get('model')
                if name and not self._switches.get(name):
                    data={}
                    data['state']=self.valueDigital('%s_state' % name, writable=True, commissionable=True)
                    data['state'].config.set('ip', ip)
                    data['state'].config.set('model', model)

                    if model=='zero':
                        pass
                    else:
                        # data['ene']=self.value('%s_ene' % name, unit='kWh', resolution=0.1)
                        data['pow']=self.value('%s_pow' % name, unit='W', resolution=0.1)
                        data['t']=self.value('%s_t' % name, unit='C', resolution=0.1)

                    self._switches[name.lower()]=data

    def poweron(self):
        return True

    def poweroff(self):
        return True

    def url(self, ip, command):
        return 'http://%s/%s' % (ip, command)

    def decodeValueState(self, value, data, datakey):
        if value is not None and data:
            try:
                v=data[datakey]
                if v is not None:
                    v=int(v)
                    value.updateValue(v)
                    value.setError(False)
                    return
            except:
                pass

            value.setError(True)

    def decodeValueFloat(self, value, data, datakey, factor=1.0):
        if value is not None and data:
            try:
                v=data[datakey]
                if v is not None:
                    v=float(v)*factor
                    value.updateValue(v)
                    value.setError(False)
                    return
            except:
                # self.logger.exception('%s/%s' % (data, datakey))
                pass

            value.setError(True)

    def run(self):
        for name in self._switches.keys():
            value=self._switches[name]['state']
            if value.isPendingSync():
                self.microsleep()
                try:
                    ip=value.config.ip
                    url=self.url(ip, 'relay')
                    state=bool(value.toReachValue)
                    url=url + '?state=%d' % int(state)
                    proxies = { 'http': '', 'https': '' }
                    self.logger.debug('mystrom(%s)->%s' % (value.key, url))
                    r=requests.get(url, timeout=3.0, proxies=proxies)
                    if r and r.ok:
                        value.clearSync()
                        self._timeoutRefresh=0
                    else:
                        self.logger.error('mystrom(%s)->%s' % (value.key, url))
                except:
                    pass
                value.clearSyncAndUpdateValue()

        if self.config.refreshperiod>0 and self.isTimeout(self._timeoutRefresh):
            self._timeoutRefresh=self.timeout(self.config.refreshperiod)
            error=False
            for name in self._switches.keys():
                self.microsleep()
                dev=self._switches[name]
                model=dev['state'].config.model
                try:
                    ip=dev['state'].config.ip
                    url=self.url(ip, 'report')
                    # self.logger.debug('mystrom(%s)->%s' % (dev['state'].key, url))
                    proxies = { 'http': '', 'https': '' }
                    r=requests.get(url, timeout=3.0, proxies=proxies)
                    if r and r.ok:
                        data=r.json()
                        # self.logger.debug(data)
                        self.decodeValueState(dev['state'], data, 'relay')
                        # self.decodeValueFloat(dev['ene'], data, 'energy_since_boot', 1.0/3600000.0)

                        if model=='zero':
                            pass
                        else:
                            self.decodeValueFloat(dev['pow'], data, 'power')
                            self.decodeValueFloat(dev['t'], data, 'temperature')
                        continue
                    else:
                        self.logger.error('mystrom(%s)->%s' % (dev['state'].key, url))
                        error=True
                except:
                    pass

                dev['state'].setError(True)
                # dev['ene'].setError(True)
                if model=='zero':
                    pass
                else:
                    dev['pow'].setError(True)
                    dev['t'].setError(True)
                error=True

            self.values.comerr.updateValue(error)

        return 5.0

    def scanner(self, network=None):
        network=network or self.getMBIO().network
        s=MyStromScanner(self, network)
        return s.scan()


class MyStromScanner(MBIONetworkScanner):
    def probe(self, host):
        try:
            url='http://%s/report' % (host)
            proxies = { 'http': '', 'https': '' }
            r=requests.get(url, timeout=1.0, proxies=proxies)
            if r and r.ok:
                data=r.json()
                return data['boot_id']
        except:
            pass


if __name__ == "__main__":
    pass
