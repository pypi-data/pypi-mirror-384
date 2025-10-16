#!/bin/python

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .mbio import MBIOGateway

from .device import MBIODevice
# from prettytable import PrettyTable

from .xmlconfig import XMLConfig


class MBIODeviceBelimo(MBIODevice):
    def __init__(self, gateway: MBIOGateway, address, xml: XMLConfig = None):
        super().__init__(gateway, address, xml=xml)
        self._serialNumber=None

    def familySuffix(self):
        if self._serialNumber:
            return (self._serialNumber >> 8) & 0xff

    def familyCode(self):
        if self._serialNumber:
            return self._serialNumber & 0xff

    def deviceCategory(self):
        if self._serialNumber:
            return self.familySuffix() & 0xf

    def builtinModule(self):
        if self._serialNumber:
            return (self.familySuffix() >> 8) & 0xf

    def probe(self):
        self.logger.debug('Probing BELIMO device address %d' % self.address)
        r=self.readInputRegisters(100, 4)
        if r:
            self._serialNumber=(r[0] << 32) + (r[1] << 16) + r[2]
            data={'version': str(r[3]/100.0),
                  'model': self.familyCode(),
                  'category': self.deviceCategory(),
                  'module': self.builtinModule()}
            return data


class MBIODeviceBelimoActuator(MBIODeviceBelimo):
    def onInit(self):
        self._vendor='Belimo'
        self._model='Actuator'
        self.setPingInputRegister(0)
        self.config.set('min', 0)
        self.config.set('max', 100)
        self.config.set('source', 'bus')
        self.config.set('default', None)
        self.config.set('type', 0)

    def onLoad(self, xml: XMLConfig):
        self.config.update('min', xml.getInt('min'))
        self.config.update('max', xml.getInt('max'))

        self.value('pos', unit='%', resolution=1)

        item=xml.child('sp')
        if item:
            self.config.update('source', item.get('source'))

        if self.config.source=='ai':
            value=self.value('sp', unit='%', resolution=0.1, commissionable=True)
            value.setRange(0, 100)
        else:
            self.config.update('default', item.get('default'))
            value=self.value('sp', unit='%', writable=True, resolution=0.1, commissionable=True)
            value.setRange(0, 100)

        item=xml.child('sensor')
        if item:
            self.config.set('sensor', item.get('type'))
            if self.config.sensor=='10v':
                self.config.set('x0', 0)
                self.config.set('x1', 10)
                resolution=xml.getFloat('resolution', 0.1)
                unit=xml.get('unit', '%')

                self.config.update('x0', xml.getFloat('x0'))
                self.config.update('x1', xml.getFloat('x1', vmin=self.config.x0))
                self.value('sensor', unit=unit, resolution=resolution, commissionable=True)
            elif self.config.sensor in ['pt1000', 'ni1000', 'ohm', 'ohm-20k']:
                resolution=xml.getFloat('resolution', 0.1)
                self.value('sensor', unit='C', resolution=resolution, commissionable=True)
            elif self.config.sensor in ['di']:
                self.valueDigital('sensor', commissionable=True)

    def poweron(self):
        r=self.readHoldingRegisters(3)
        if r:
            # 0=Unknown, 1=air/water, 2=VAV/EPIV, 3=FireDamper, 4=Energy Valve, 5=V6V EPIV
            self.config.type=r[0]

        # !!! DIFFER BY MODELS 108
        # fail position
        if self.config.default in ['closed', 'close', '0']:
            self.writeRegistersIfChanged(108, 1)
        if self.config.default in ['open', '100', '1']:
            self.writeRegistersIfChanged(108, 2)
        else:
            self.writeRegistersIfChanged(108, 0)

        if self.config.source=='ai':
            self.writeRegistersIfChanged(118, 0)
        else:
            self.writeRegistersIfChanged(118, 1)

        self.writeRegistersIfChanged(105, self.config.min*100.0)
        self.writeRegistersIfChanged(106, self.config.max*100.0)

        # self.writeRegistersIfChanged(108, self.config.default/100.0)

        # Reset override
        self.writeRegistersIfChanged(1, 0)

        # !!! DIFFER BY MODELS 107
        data={'none': 0, '10v': 1, 'di': 4, 'pt1000': 5, 'ni1000': 6, 'ohm': 2, 'ohm-20k': 3}
        self.writeRegistersIfChanged(107, data.get(self.config.source, 0))

        return True

    def poweronsave(self):
        # send reset if config changed
        # !!! DIFFER BY MODELS 2
        self.writeHoldingRegisters(2, 2)

    def poweroff(self):
        return True

    def refresh(self):
        delay=5

        r=self.readInputRegisters(0, 5)
        if r:
            # actual value
            self.values.pos.updateValue(r[4]/100.0)

            # sp
            if self.config.source=='bus':
                self.values.sp.updateValue(r[0]/100.0)
            else:
                r=self.readInputRegisters(12, 1)
                if r:
                    self.values.sp.updateValue(r[0]/100.0)

        # service information
        r=self.readInputRegisters(104, 1)
        if r:
            data=r[0]
            # !!! DIFFER BY MODELS 104 bits
            self.values.pos.setOverride(data & 0x200)

        # sensor
        if self.config.sensor:
            # !!! DIFFER BY MODELS 8
            r=self.readInputRegisters(8, 1)
            if r:
                v=r[0]/100.0
                try:
                    dx=(self.config.x1-self.config.x0)
                    v=self.config.x0+v*dx
                except:
                    pass
                self.values.sensor.updateValue(v)

        return delay

    def sync(self):
        value=self.values.sp
        if value.isPendingSync():
            if self.writeRegisters(0, int(value.toReachValue*100.0)):
                value.clearSync()


class MBIODeviceBelimoP22RTH(MBIODeviceBelimo):
    def onInit(self):
        self._vendor='Belimo'
        self._model='P-22RTH'
        self.setPingInputRegister(0)
        self.readonly=self.valueDigital('readonly', writable=True)
        self.t=self.value('t', unit='C', commissionable=True)
        self.hr=self.value('hr', unit='%', resolution=1)
        self.dewp=self.value('dewp', unit='C')
        self.co2=self.value('co2', unit='ppm', resolution=10)

        self.config.set('readonly', False)
        self.config.set('icons', False)
        self.config.set('fan', False)
        self.config.set('setpoint', False)
        self.config.set('temperature', False)
        self.config.set('toffset', 0)
        self.config.set('hygrometry', False)
        self.config.set('iaq', False)
        self.config.set('iaqled', False)
        self.config.set('dark', False)
        self.config.set('onoff', False)
        self.config.set('boost', False)

    def onLoad(self, xml: XMLConfig):
        self.config.dark=xml.match('theme', 'dark')
        self.config.update('readonly', xml.getBool('readonly'))

        item=xml.child('hygrometry')
        if item:
            self.config.hygrometry=True
            self.config.set('hrhidden', item.getBool('hidden', False))

        item=xml.child('temperature')
        if item:
            self.config.temperature=True
            self.config.update('toffset',  item.getFloat('offset'))
            self.config.set('thidden', item.getBool('hidden', False))

        item=xml.child('iaq')
        if item:
            self.config.iaq=True
            self.config.iaqled=item.getBool('led', True)
            self.config.set('iaqwarning',  item.getInt('warning', 800))
            self.config.set('iaqalarm', item.getInt('alarm', 1200))
            self.co2alarm=self.valueDigital('co2alarm')
            self.config.set('iaqhidden', item.getBool('hidden', False))

        if xml.child('Icons'):
            self.config.icons=True
            self.cooling=self.valueDigital('cooling', writable=True)
            self.heating=self.valueDigital('heating', writable=True)

        item=xml.child('Fan')
        if item:
            self.config.fan=True
            self.config.set('fanstages', item.getInt('stages', 3, vmin=3, vmax=4))
            self.fanAuto=self.valueDigital('fanauto', writable=True)
            self.fanSpeed=self.value('fanspeed', unit='', writable=True, commissionable=True)

        item=xml.child('Setpoint')
        if item:
            self.config.setpoint=True
            self.config.set('spmodeabsolute', not item.getBool('relative', False))
            self.config.set('spzero', item.getFloat('zero', 22.0))
            self.config.set('sprange', item.getFloat('range', 3.0))
            self.spT=self.value('spt', unit='C', writable=True, commissionable=True)
            self.spTX=self.value('sptx', unit='C')
            self.config.set('sphidden', item.getBool('hidden', False))

        item=xml.child('onoff')
        if item:
            self.config.onoff=True
            self.onoff=self.valueDigital('onoff', writable=True)

        item=xml.child('boost')
        if item:
            self.config.boost=True
            self.config.set('boostdelay', item.getInt('delay', 60, vmin=1, vmax=60))

    def poweron(self):
        # Comfort Mode forced if no ON/ON, ECO or BOOST buttons
        if not self.config.onoff and not self.config.boost:
            self.writeRegistersIfChanged(30, 1)

        if self.config.dark:
            self.writeRegistersIfChanged(130, 1)
        else:
            self.writeRegistersIfChanged(130, 0)

        readonly=self.readonly.isOn()
        if self.config.readonly:
            readonly=True
        self.writeRegistersIfChanged(33, not readonly)

        self.writeRegistersIfChanged(132, 1)
        self.writeRegistersIfChanged(141, 0)

        # small values on the left
        if self.config.setpoint and not self.config.sphidden:
            self.writeRegistersIfChanged(131, self.config.temperature and not self.config.thidden)
        else:
            # if setpoint not activated, disable small temperature and enable big temperature
            self.writeRegistersIfChanged(131, 0)

        self.writeRegistersIfChanged(132, self.config.hygrometry and not self.config.hrhidden)
        self.writeRegistersIfChanged(133, self.config.iaq and not self.config.iaqhidden)
        if self.config.iaq:
            self.writeRegistersIfChanged(115, self.config.iaqwarning)
            self.writeRegistersIfChanged(116, self.config.iaqalarm)
            if self.config.iaqled:
                self.writeRegistersIfChanged(117, 1)
                self.writeRegistersIfChanged(135, 2)
            else:
                self.writeRegistersIfChanged(117, 0)
                self.writeRegistersIfChanged(135, 0)
        else:
            self.writeRegistersIfChanged(117, 0)
            self.writeRegistersIfChanged(135, 0)

        if self.config.setpoint:
            self.writeRegistersIfChanged(147, int(self.config.sprange*2.0))

            if self.config.spmodeabsolute:
                self.writeRegistersIfChanged(146, int(self.config.spzero)*100)
                self.writeRegistersIfChanged(145, 0)
            else:
                self.writeRegistersIfChanged(145, 1)

            self.writeRegistersIfChanged(137, 2)
        else:
            if self.config.temperature and not self.config.thidden:
                self.writeRegistersIfChanged(137, 1)
            else:
                self.writeRegistersIfChanged(137, 0)

        # HeatCool Icons
        self.writeRegistersIfChanged(32, 0)
        self.writeRegistersIfChanged(134, self.config.icons)

        # Fan
        self.writeRegistersIfChanged(139, 1)
        if self.config.fan:
            self.writeRegistersIfChanged(138, 1)
            self.writeRegistersIfChanged(148, self.config.fanstages)
            self.writeRegistersIfChanged(31, 1)
            self.writeRegistersIfChanged(149, 1)
        else:
            self.writeRegistersIfChanged(138, 0)
            self.writeRegistersIfChanged(148, 2)

        # OnOff button
        if self.config.onoff:
            self.writeRegistersIfChanged(141, 2)
        else:
            self.writeRegistersIfChanged(141, 0)

        # Boost button
        if self.config.boost:
            self.writeRegistersIfChanged(140, 1)
            self.writeRegistersIfChanged(142, self.config.boostdelay*60)
        else:
            self.writeRegistersIfChanged(140, 0)
            self.writeRegistersIfChanged(142, 3600)

        # Offsets
        encoder=self.encoder()
        v=int(self.config.toffset*100.0)
        encoder.int(v)
        encoder.writeRegistersIfChanged(110)


        return True

    def poweroff(self):
        self.writeRegistersIfChanged(33, 0)
        return True

    def refresh(self):
        r=self.readInputRegisters(0, 5)
        if r:
            decoder=self.decoderFromRegisters(r)
            # self.t.updateValue(r[0]/100)
            # self.hr.updateValue(r[2]/100)
            # self.co2.updateValue(r[3])
            # self.dewp.updateValue(r[4]/100)
            self.t.updateValue(decoder.word()/100)
            decoder.word()
            self.hr.updateValue(decoder.word()/100)
            self.co2.updateValue(decoder.word())
            # self.dewp.updateValue(decoder.int()/100)
            self.dewp.updateValue(self.calcDEWP(self.t.value, self.hr.value))

        if self.config.iaq:
            r=self.readHoldingRegisters(6, 1)
            if r:
                self.co2alarm.updateValue(r[0]>=3)

        r=self.readInputRegisters(21, 2)
        if r:
            if self.config.setpoint:
                if self.config.spmodeabsolute:
                    self.spT.updateValue(r[0]/100)
                    v=self.spT.value-self.config.spzero
                    self.spTX.updateValue(v)

            if self.config.fan:
                # retrieve fan speed in %
                v=r[1]/100
                speed=round(self.config.fanstages*v/100)
                self.fanSpeed.updateValue(speed)
                r=self.readInputRegisters(30, 2)
                if r:
                    fanauto=True
                    # opmode: 0=off, 1=comfort, 2=eco, 3=boost
                    if r[0]!=1:
                        fanauto=False
                    # 0=manual fan, 1=auto fan
                    if r[1]==0:
                        fanauto=False
                    self.fanAuto.updateValue(fanauto)

        if self.config.setpoint:
            if not self.config.spmodeabsolute:
                r=self.readInputRegisters(36, 1)
                if r:
                    decoder=self.decoderFromRegisters(r)
                    v=decoder.int()/100
                    self.spT.updateValue(v)
                    v=self.config.spzero+self.spT.value
                    self.spTX.updateValue(v)

        r=self.readInputRegisters(33, 1)
        if r:
            self.readonly.updateValue(not r[0])

        # Operation mode (0:OFF, 1:ON/NORMAL, 2:ECO, 3:BOOST)
        if self.config.onoff:
            r=self.readInputRegisters(30, 1)
            if r:
                # OFF if 0, ON else
                self.onoff.updateValue(r[0]>0)

        return 5.0

    def sync(self):
        value=self.readonly
        if value.isPendingSync():
            if self.writeRegisters(33, not value.toReachValue):
                value.clearSyncAndUpdateValue()

        if self.config.setpoint:
            value=self.spT
            if value.isPendingSync():
                if self.config.spmodeabsolute:
                    if self.writeRegisters(21, int(value.toReachValue*100)):
                        value.clearSync()
                else:
                    encoder=self.encoder()
                    encoder.int(int(value.toReachValue*100))
                    if encoder.writeRegisters(36):
                        value.clearSync()

        if self.config.fan:
            value=self.fanAuto
            if value.isPendingSync():
                if self.writeRegisters(31, value.toReachValue):
                    value.clearSync()
            value=self.fanSpeed
            if value.isPendingSync():
                speed=int((100.0/self.config.fanstages)*value.toReachValue)
                if self.writeRegisters(22, int(speed*100)):
                    value.clearSync()

        if self.config.icons:
            if self.heating.isPendingSync() or self.cooling.isPendingSync():
                if self.heating.toReachValue:
                    self.writeRegisters(32, 1)
                elif self.cooling.toReachValue:
                    self.writeRegisters(32, 2)
                else:
                    self.writeRegisters(32, 0)

                self.heating.clearSyncAndUpdateValue()
                self.cooling.clearSyncAndUpdateValue()

        if self.config.onoff:
            if self.onoff.isPendingSync():
                value=self.onoff
                mode=0
                if value.toReachValue:
                    mode=1
                if self.writeRegisters(30, mode):
                    value.clearSyncAndUpdateValue()

if __name__ == "__main__":
    pass
