#!/bin/python

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .value import MBIOValue

from .task import MBIOTask
from .xmlconfig import XMLConfig


import requests

from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# https://www.sensorpush.com/gateway-cloud-api
# https://dashboard.sensorpush.com/


class MBIOTaskSensorPush(MBIOTask):
    def initName(self):
        return 'spush'

    def onInit(self):
        self.config.set('refreshperiod', 60)
        self._token=None
        self._timeoutToken=0
        self._timeoutRefresh=0
        self._retry=3
        self.valueDigital('comerr', default=False)
        self._cache={'gateways': None, 'sensors': None}
        self._data=[]
        self._sensors=[]

    def onLoad(self, xml: XMLConfig):
        self.config.set('email', xml.get('email'))
        self.config.set('password', xml.get('password'))
        self.config.update('refreshperiod', xml.getInt('refresh'))
        self._data=[]
        for item in xml.children('sensor'):
            sid=item.get('id')
            if sid:
                for v in item.children('value'):
                    name=v.get('name')
                    dataname=v.get('source')
                    if name and dataname:
                        unit=v.get('unit')
                        resolution=v.getFloat('resolution', 0.1)
                        default=v.getFloat('default')
                        value=self.value(name, unit=unit, default=default, resolution=resolution)
                        item={'name': name, 'sid': sid, 'dataname': dataname, 'value': value}
                        self._data.append(item)
                        if sid not in self._sensors:
                            self._sensors.append(sid)

    @property
    def token(self):
        return self._token

    def url(self, path='/'):
        url='https://api.sensorpush.com/api/v1'
        return '%s/%s' % (url, path)

    def POST(self, path, data=None):
        try:
            url=self.url(path)
            headers={}
            proxies = { 'http': '', 'https': '' }
            if self._token:
                headers={'Authorization': self._token}
            if data is None:
                data={}

            #sself.logger.debug('%s(%s)' % (url, data))
            self.logger.debug('%s' % (url))
            r=requests.post(url,
                            headers=headers, json=data,
                            verify=False, timeout=5.0, proxies=proxies)
            if r and r.ok:
                # self.logger.warning(r.text)
                data=r.json()
                # self.logger.debug(data)
                return data
            self.logger.error(r.text)
        except:
            self.logger.exception('post')

    def auth(self, force=False):
        if self._token and not self.isTimeout(self._timeoutToken):
            return self._token

        if not self.isTimeout(self._timeoutToken) and not force:
            return

        self._token=None
        self._timeoutToken=self.timeout(15)

        try:
            data={'email': self.config.email, 'password': self.config.password}
            r=self.POST('oauth/authorize', data)
            if r:
                key=r['authorization']
                if key:
                    data={'authorization': key}
                r=self.POST('oauth/accesstoken', data)
                if r:
                    self._token=r['accesstoken']
                    self._timeoutToken=self.timeout(60*45)
                    return self._token
        except:
            self.logger.exception('auth')

    def deauth(self):
        self._token=None

    def cache(self, name):
        try:
            return self._cache[name]
        except:
            pass

    def cacheUpdate(self, name, data):
        try:
            if name and data:
                self._cache[name]=data
        except:
            pass
        return self.cache(name)

    def retrieveGateways(self, refresh=False):
        cache='gateways'
        data=self.cache(cache)
        if refresh or not data:
            data={'active': True, 'format': 'json'}
            r=self.POST('devices/gateways', data)
            return self.cacheUpdate(cache, r)
        return data

    def gateways(self, refresh=False):
        gateways=[]
        try:
            for gateway in self.retrieveGateways(refresh).values():
                gateways.append(gateway['id'])
        except:
            pass
        return gateways

    def retrieveSensors(self, refresh=False):
        cache='sensors'
        data=self.cache(cache)
        if refresh or not data:
            data={'active': True, 'format': 'json'}
            r=self.POST('devices/sensors', data)
            return self.cacheUpdate(cache, r)
        return data

    def sensors(self, refresh=False):
        sensors=[]
        try:
            for sensor in self.retrieveSensors(refresh).keys():
                sensors.append(sensor)
        except:
            pass
        return sensors

    def sensorType(self, sid):
        try:
            return self.retrieveSensors()[sid]['type'].lower()
        except:
            pass

    def f2c(self, value):
        try:
            value=float(value)
            return (value-32.0)*5.0/9.0
        except:
            pass

    def retrieveValues(self, sensors=None):
        if not sensors:
            sensors=self.sensors()
        if sensors:
            data={'active': True, 'bulk': False, 'format': 'json',
                'limit': 1, 'sensors': sensors}
            r=self.POST('samples', data)
            try:
                result={}
                for sensor in sensors:
                    try:
                        state=r['sensors'][sensor][0]
                        result[sensor]=state
                    except:
                        pass
                return result
            except:
                pass

    def poweron(self):
        self.auth()
        self.retrieveGateways()
        self.retrieveSensors()
        return True

    def poweroff(self):
        self.deauth()
        return True

    def run(self):
        if not self.auth():
            return 5.0

        if self.isTimeout(self._timeoutRefresh):
            self._timeoutRefresh=self.timeout(self.config.refreshperiod)
            error=False

            dataread=self.retrieveValues(self._sensors)
            try:
                for item in self._data:
                    value=item['value']
                    try:
                        sid=item['sid']
                        stype=self.sensorType(sid)
                        sensordata=dataread[sid]
                        dataname=item['dataname']
                        svalue=float(sensordata[dataname])

                        if dataname=='temperature':
                            svalue=self.f2c(svalue)

                        value.updateValue(svalue)
                        value.setError(False)
                    except:
                        value.setError(True)
                        error=True
            except:
                self.logger.exception('spush')
                error=True

            if not error:
                self._timeoutRefresh=self.timeout(self.config.refreshperiod)
                self._retry=3
                self.values.comerr.updateValue(False)
            else:
                self._timeoutRefresh=self.timeout(60)
                if self._retry>0:
                    self._retry-=1
                    if self._retry==0:
                        self.values.comerr.updateValue(True)

        return 5.0


if __name__ == "__main__":
    pass
