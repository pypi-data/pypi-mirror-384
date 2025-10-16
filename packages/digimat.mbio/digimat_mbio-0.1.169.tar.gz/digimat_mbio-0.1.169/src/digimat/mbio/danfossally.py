#!/bin/python

from .task import MBIOTask
from .xmlconfig import XMLConfig


from digimat.danfossally import DanfossAlly


class MBIOTaskDanfossAlly(MBIOTask):
    def initName(self):
        return 'ally'

    def onInit(self):
        self._danfoss=DanfossAlly(logger=self.logger)
        self._devices={}
        self._sensors={}
        self._radiators={}
        self._icons={}

        self.config.set('refreshperiod', 60)
        self.config.set('key')
        self.config.set('secret')
        self._timeoutRefresh=0
        self.valueDigital('comerr', default=False)

    def auth(self, key, secret, reset=True):
        self.config.update('key', key)
        self.pickleWrite('key', self.config.key)
        self.config.update('secret', secret)
        self.pickleWrite('secret', self.config.secret)
        if reset:
            self.reset()

    def onLoad(self, xml: XMLConfig):
        self.config.update('refreshperiod', xml.getInt('refresh', vmin=60))

        self.config.update('key', self.pickleRead('key'))
        self.config.update('key', xml.get('key'))
        self.config.update('secret', self.pickleRead('secret'))
        self.config.update('secret', xml.get('secret'))
        self.auth(self.config.key, self.config.secret, False)

        items=xml.children('sensor')
        if items:
            for item in items:
                name=item.get('name')
                if name and not self._devices.get(name):
                    did=item.get('id') or name
                    data={'id': did}
                    data['t']=self.value('%s_t' % name, unit='C', resolution=0.1)
                    data['hr']=self.value('%s_hr' % name, unit='%', resolution=1)
                    data['bat']=self.value('%s_bat' % name, unit='%', resolution=1)
                    data['err']=self.valueDigital('%s_err' % name)
                    self._devices[name]=data
                    self._sensors[did]=data

        items=xml.children('radiator')
        if items:
            for item in items:
                name=item.get('name')
                if name and not self._devices.get(name):
                    did=item.get('id') or name
                    data={'id': did}
                    data['t']=self.value('%s_t' % name, unit='C', resolution=0.1)
                    data['sp']=self.value('%s_sp' % name, unit='C', resolution=0.1, writable=True)
                    data['bat']=self.value('%s_bat' % name, unit='%', resolution=1)
                    data['heat']=self.valueDigital('%s_heat' % name)
                    data['err']=self.valueDigital('%s_err' % name)
                    self._devices[name]=data
                    self._radiators[did]=data

        items=xml.children('icon2')
        if items:
            for item in items:
                name=item.get('name')
                if name and not self._devices.get(name):
                    did=item.get('id') or name
                    data={'id': did}
                    data['t']=self.value('%s_t' % name, unit='C', resolution=0.1)
                    data['sp']=self.value('%s_sp' % name, unit='C', resolution=0.1, writable=True)
                    data['bat']=self.value('%s_bat' % name, unit='%', resolution=1)
                    data['heat']=self.valueDigital('%s_heat' % name)
                    data['err']=self.valueDigital('%s_err' % name)
                    self._devices[name]=data
                    self._icons[did]=data

    def refresh(self):
        if self._danfoss.refresh(True):
            self._timeoutRefresh=self.timeout(self.config.refreshperiod)
            return True

        self._timeoutRefresh=self.timeout(15)
        return False

    def triggerRefresh(self):
        self._timeoutRefresh=self.timeout(1)

    def poweron(self):
        self._danfoss.auth(self.config.key, self.config.secret)
        return True

    def poweroff(self):
        return True

    def run(self):
        # sync
        for item in self._radiators.values():
            self.microsleep()
            value=item['sp']
            if value.isPendingSync():
                device=self._danfoss.radiator(item['id'])
                if device:
                    device.sp=value.toReachValue
                    value.clearSyncAndUpdateValue()
                    self.triggerRefresh()

        for item in self._icons.values():
            self.microsleep()
            value=item['sp']
            if value.isPendingSync():
                device=self._danfoss.icon2(item['id'])
                if device:
                    device.sp=value.toReachValue
                    value.clearSyncAndUpdateValue()
                    self.triggerRefresh()

        # refresh
        if self.isTimeout(self._timeoutRefresh):
            self.refresh()
            error=False

            for item in self._sensors.values():
                self.microsleep()
                device=self._danfoss.sensor(item['id'])
                if device and not device.isError():
                    item['t'].updateValidValue(device.t)
                    item['hr'].updateValidValue(device.hr)
                    item['bat'].updateValidValue(device.battery)
                    item['err'].updateValidValue(False)
                else:
                    item['t'].setError(True)
                    item['hr'].setError(True)
                    item['bat'].setError(True)
                    item['err'].updateValidValue(True)
                    error=True

            for item in self._radiators.values():
                self.microsleep()
                device=self._danfoss.radiator(item['id'])
                if device and not device.isError():
                    item['t'].updateValidValue(device.tref)
                    item['sp'].updateValidValue(device.sp)
                    item['bat'].updateValidValue(device.battery)
                    item['heat'].updateValidValue(device.isHeating())
                    item['err'].updateValidValue(False)
                else:
                    item['t'].setError(True)
                    item['sp'].setError(True)
                    item['bat'].setError(True)
                    item['heat'].setError(True)
                    item['err'].updateValidValue(True)
                    error=True

            for item in self._icons.values():
                self.microsleep()
                device=self._danfoss.icon2(item['id'])
                if device and not device.isError():
                    item['t'].updateValidValue(device.t)
                    item['sp'].updateValidValue(device.sp)
                    item['bat'].updateValidValue(device.battery)
                    item['heat'].updateValidValue(device.isHeating())
                    item['err'].updateValidValue(False)
                else:
                    item['t'].setError(True)
                    item['sp'].setError(True)
                    item['bat'].setError(True)
                    item['heat'].setError(True)
                    item['err'].updateValidValue(True)
                    error=True

            self.values.comerr.updateValue(error)

        return 5.0

    def table(self, key=None):
        self._danfoss.table(key)

    def buildConfig(self, key=None):
        devices=self._danfoss.devices()
        if devices:
            print("<Ally name='%s' refresh='%d' key='%s' secret='%s'>" % (self.name,
                    self.config.refreshperiod,
                    self.b16encode(self.config.key),
                    self.b16encode(self.config.secret)))

            for device in devices:
                if key and not device.isMatching(key):
                    continue

                dtype=device.type
                name='%s %s' % (device.type, device.name)
                if 'Radiator Thermostat' in dtype:
                    print("   <Radiator name='' id='%s' comment='%s' />" % (device.did, name))
                elif 'Room Sensor' in dtype:
                    print("   <Sensor name='' id='%s' comment='%s' />" % (device.did, name))
                elif 'Icon2 RT' in dtype:
                    print("   <Icon2 name='' id='%s' comment='%s' />" % (device.did, name))

            print('</Ally>')


if __name__ == "__main__":
    pass
