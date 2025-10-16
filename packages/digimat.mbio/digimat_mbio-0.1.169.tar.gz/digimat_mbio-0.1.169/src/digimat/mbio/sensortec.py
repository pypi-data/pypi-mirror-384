#!/bin/python

from __future__ import annotations

from .device import MBIODevice
# from prettytable import PrettyTable



# from pymodbus.constants import Endian

from .xmlconfig import XMLConfig


class MBIODeviceSensortecELD(MBIODevice):
    def onInit(self):
        self._vendor='Sensortec'
        self._model='EL-D'
        self.setPingInputRegister(39)
        self.t=self.value('t', unit='C', commissionable=True)
        self.hr=self.value('hr', unit='%', resolution=1)
        self.dewp=self.value('dewp', unit='C')

        self.config.set('icons', False)
        self.config.set('occupancy', False)
        self.config.set('fan', False)
        self.config.set('setpoint', False)
        self.config.set('temperature', False)
        self.config.set('toffset', 0)
        self.config.set('hygrometry', False)
        self.config.set('iaq', False)
        self.config.set('co2', False)
        self.config.set('cov', False)
        self.config.set('iaq', False)
        self.config.set('dark', False)

    def probe(self):
        self.logger.debug('Probing device address %d' % self.address)
        data={}
        r=self.readInputRegisters(39, 1)
        if r:
            v={0x20: 'EL-D-MB', 0x21: 'EL-D-TH-MB', 0x22: 'EL-D-THC-MB', 0x23: 'EL-D-THCV-MB'}
            data['model']=v.get(r[0], '?')

        r=self.readInputRegisters(15, 4)
        if r:
            data['version']='%d.%d' % ((r[0] >> 8), (r[0] & 0xff))
            data['serial']='%d' % (r[1]+(r[2] << 16))
            data['type']='%d' % (r[3])

        return data

    def onLoad(self, xml: XMLConfig):
        self.config.dark=xml.match('theme', 'dark')
        self.config.brightness=xml.getInt('brightness', 100, vmin=0, vmax=100)
        self.config.backlight=xml.getInt('backlight', 15, vmin=5, vmax=15)
        self.config.standby=xml.getInt('standby', 60, vmin=1, vmax=60)
        self.config.proximity=xml.getInt('proximity', 100, vmin=0, vmax=100)

        item=xml.child('hygrometry')
        if item:
            self.config.hygrometry=True
            self.config.set('hrhidden', item.getBool('hidden', False))

        item=xml.child('temperature')
        if item:
            self.config.temperature=True
            self.config.update('toffset',  item.getFloat('offset', 0, vmin=-3.0, vmax=3.0))
            self.config.set('thidden', item.getBool('hidden', False))

        item=xml.child('co2')
        if item:
            self.config.co2=True
            self.config.iaq=True
            self.config.set('co2warning',  item.getInt('warning', 800))
            self.config.set('co2alarm', item.getInt('alarm', 1200))
            self.config.set('co2hidden', item.getBool('hidden', False))
            self.co2=self.value('co2', unit='ppm', resolution=10)

        item=xml.child('cov')
        if item:
            self.config.cov=True
            self.config.iaq=True
            self.config.set('covwarning',  item.getInt('warning', 100))
            self.config.set('covalarm', item.getInt('alarm', 300))
            self.config.set('covhidden', item.getBool('hidden', False))
            self.cov=self.value('cov', unit='ppb', resolution=10)
            self.ecov=self.value('ecov', unit='ppm', resolution=10)

        if self.config.iaq:
            self.iaqwarning=self.valueDigital('iaqwarning')
            self.iaqalarm=self.valueDigital('iaqalarm')
            self.iaq=self.value('iaq', unit='', resolution=1)

        item=xml.child('Setpoint')
        if item:
            self.config.setpoint=True
            self.config.set('spmodeabsolute', not item.getBool('relative', False))
            self.config.set('spzero', item.getFloat('zero', 22.0))
            self.config.set('sprange', item.getFloat('range', 3.0))
            self.config.set('spstep', item.getFloat('step', 0.5, vmin=0.1, vmax=1.0))
            self.config.set('sphidden', item.getBool('hidden', False))
            self.spT=self.value('spt', unit='C', writable=True, commissionable=True)
            self.spTX=self.value('sptx', unit='C')

        item=xml.child('Fan')
        if item:
            self.config.fan=True
            self.config.set('fanstages', item.getInt('stages', 3, vmin=0, vmax=3))
            self.fanAuto=self.valueDigital('fanauto', writable=True)
            self.fanSpeed=self.value('fanspeed', unit='', writable=True, commissionable=True)

        if xml.child('Icons'):
            self.config.icons=True
            self.cooling=self.valueDigital('cooling', writable=True, default=False)
            self.heating=self.valueDigital('heating', writable=True, default=False)

        if xml.child('Occupancy'):
            self.config.occupancy=True
            self.occ=self.valueDigital('occ', writable=True, default=False)

    def poweron(self):
        # Communication
        self.writeRegistersIfChanged(11, [19200, 0])

        if self.config.dark:
            self.writeRegistersIfChanged(21, 2)
        else:
            self.writeRegistersIfChanged(21, 1)

        self.writeRegistersIfChanged(22, self.config.brightness)
        self.writeRegistersIfChanged(23, self.config.backlight)
        self.writeRegistersIfChanged(24, self.config.standby)
        self.writeRegistersIfChanged(38, int(self.config.proximity/10.0))

        v=0
        if self.config.setpoint and not self.config.sphidden:
            v |= (0x1)
        if self.config.fan:
            v |= (0x1 << 1)
        if self.config.occupancy:
            v |= (0x1 << 2)
        if self.config.temperature and not self.config.thidden:
            v |= (0x1 << 3)
        if self.config.hygrometry and not self.config.hrhidden:
            v |= (0x1 << 4)
        if self.config.icons:
            v |= (0x1 << 5)
        if self.config.iaq and (not self.config.co2hidden or not self.config.covhidden):
            v |= (0x1 << 6)
        self.writeRegistersIfChanged(20, v)

        self.writeRegistersIfChanged(14, self.config.toffset*100)

        if (self.config.co2 and not self.config.co2hidden) and (self.config.cov and not self.config.covhidden):
            self.writeRegistersIfChanged(32, 3)
        elif self.config.co2 and not self.config.co2hidden:
            self.writeRegistersIfChanged(32, 2)
        elif self.config.cov and not self.config.covhidden:
            self.writeRegistersIfChanged(32, 1)
        else:
            self.writeRegistersIfChanged(32, 0)

        if self.config.co2:
            self.writeRegistersIfChanged(35, self.config.co2warning)
            self.writeRegistersIfChanged(36, self.config.co2alarm)

        if self.config.cov:
            self.writeRegistersIfChanged(33, self.config.covwarning)
            self.writeRegistersIfChanged(34, self.config.covalarm)

        if self.config.iaq:
            # TODO: should be writeCoilsIfChanged
            self.writeCoils(507, 0)

        # iaq histeresis (ppm/ppb)
        self.writeRegistersIfChanged(37, 100)

        if self.config.setpoint:
            self.writeRegistersIfChanged(26, int(self.config.spstep*100.0))
            if self.config.spmodeabsolute:
                self.writeRegistersIfChanged(25, 0)
                self.writeRegistersIfChanged(27, int((self.config.spzero-self.config.sprange)*100.0))
                self.writeRegistersIfChanged(28, int((self.config.spzero+self.config.sprange)*100.0))
            else:
                self.writeRegistersIfChanged(25, 1)
                encoder=self.encoder()
                v=-int(self.config.sprange*100.0)
                encoder.int16(v)
                encoder.writeRegistersIfChanged(29)
                encoder=self.encoder()
                v=int(self.config.sprange*100.0)
                encoder.int16(v)
                encoder.writeRegistersIfChanged(30)

        # Fan
        if self.config.fan:
            if self.config.fanstages==0:
                self.writeRegistersIfChanged(31, 0x0102)
            elif self.config.fanstages==1:
                self.writeRegistersIfChanged(31, 0x0104)
            elif self.config.fanstages==2:
                self.writeRegistersIfChanged(31, 0x0108)
            else:
                self.writeRegistersIfChanged(31, 0x0110)
        else:
            self.writeRegistersIfChanged(31, 0x0110)

        return True

    def poweroff(self):
        return True

    def refresh(self):
        r=self.readInputRegisters(0, 8)
        if r:
            decoder=self.decoderFromRegisters(r)
            self.t.updateValue(decoder.word()/100.0)
            self.hr.updateValue(decoder.word()/100.0)
            self.dewp.updateValue(self.calcDEWP(self.t.value, self.hr.value))
            vsp=decoder.int16()/100.0
            if self.config.setpoint:
                self.spT.updateValue(vsp)
                if self.config.spmodeabsolute:
                    v=self.spT.value-self.config.spzero
                    self.spTX.updateValue(v)
                else:
                    v=self.config.spzero+self.spT.value
                    self.spTX.updateValue(v)

            vco2=decoder.word()
            status=decoder.word()
            vcov=decoder.word()
            vecov=decoder.word()
            viaq=decoder.word()
            if self.config.co2:
                self.co2.updateValue(vco2)
            if self.config.cov:
                self.cov.updateValue(vcov)
                self.ecov.updateValue(vecov)
            if self.config.iaq:
                self.iaq.updateValue(viaq)
                self.iaqwarning.updateValue(status & (0x1 << 5))
                self.iaqalarm.updateValue(status & (0x1 << 6))
            if self.config.occupancy:
                self.occ.updateValue(status & (0x1 << 1))
            if self.config.fan:
                self.fanAuto.updateValue(status & (0x1 << 8))
                speed=0
                if status & (0x1 << 10):
                    speed=1
                elif status & (0x1 << 11):
                    speed=2
                elif status & (0x1 << 12):
                    speed=3
                self.fanSpeed.updateValue(speed)
            if self.config.icons:
                self.heating.updateValue(status & (0x1 << 14))
                self.cooling.updateValue(status & (0x1 << 15))

        return 5.0

    def sync(self):
        if self.config.setpoint:
            value=self.spT
            if value.isPendingSync():
                if self.config.spmodeabsolute:
                    if self.writeRegisters(2, int(value.toReachValue*100)):
                        value.clearSync()
                else:
                    encoder=self.encoder()
                    encoder.int16(int(value.toReachValue*100))
                    if encoder.writeRegisters(2):
                        value.clearSync()

        if self.config.occupancy:
            value=self.occ
            if value.isPendingSync():
                if self.writeCoils(501, value.toReachValue):
                    value.clearSync()

        if self.config.fan:
            value=self.fanAuto
            if value.isPendingSync():
                if self.writeCoils(508, value.toReachValue):
                    value.clearSync()

            value=self.fanSpeed
            if value.isPendingSync():
                if value.toReachValue==0:
                    if self.writeCoils(509, 1):
                        value.clearSync()
                elif value.toReachValue==1:
                    if self.writeCoils(510, 1):
                        value.clearSync()
                elif value.toReachValue==2:
                    if self.writeCoils(511, 1):
                        value.clearSync()
                elif value.toReachValue==3:
                    if self.writeCoils(512, 1):
                        value.clearSync()

        if self.config.icons:
            value=self.heating
            if value.isPendingSync():
                if self.writeCoils(514, value.toReachValue):
                    value.clearSyncAndUpdateValue()
            value=self.cooling
            if value.isPendingSync():
                if self.writeCoils(515, value.toReachValue):
                    value.clearSyncAndUpdateValue()

    def reboot(self):
        if self.writeRegisters(99, 1):
            return True
        return False


class MBIODeviceSensortecEL(MBIODevice):
    def onInit(self):
        self._vendor='Sensortec'
        self._model='EL'
        self.setPingInputRegister(20)
        self.t=self.value('t', unit='C', commissionable=True)

        self.config.set('temperature', False)
        self.config.set('toffset', 0)
        self.config.set('hygrometry', False)
        self.config.set('iaq', False)
        self.config.set('co2', False)
        self.config.set('cov', False)

    def probe(self):
        self.logger.debug('Probing device address %d' % self.address)
        data={}
        r=self.readInputRegisters(16, 6)
        if r:
            data['version']='%d.%d' % ((r[0] >> 8), (r[0] & 0xff))
            data['serial']='%d' % (r[1]+(r[2] << 16))
            data['type']='%d' % (r[4])
            model='EL-'
            caps=r[5]
            if caps & (0x1<<0):
                model+='T'
            if caps & (0x1<<1):
                model+='H'
            if caps & (0x1<<2):
                model+='C'
            if caps & (0x1<<3):
                model+='V'
            data['model']=model

        return data

    def onLoad(self, xml: XMLConfig):
        item=xml.child('temperature')
        if item:
            self.config.temperature=True
            self.config.update('toffset',  item.getFloat('offset', 0, vmin=-2.0, vmax=2.0))

        item=xml.child('hygrometry')
        if item:
            self.config.hygrometry=True
            self.hr=self.value('hr', unit='%', resolution=1)
            self.dewp=self.value('dewp', unit='C')

        item=xml.child('co2')
        if item:
            self.config.co2=True
            self.config.iaq=True
            self.config.set('co2warning',  item.getInt('warning', 800))
            self.config.set('co2alarm', item.getInt('alarm', 1200))
            self.co2=self.value('co2', unit='ppm', resolution=10)

        item=xml.child('cov')
        if item:
            self.config.cov=True
            self.config.iaq=True
            self.config.set('covwarning',  item.getInt('warning', 100))
            self.config.set('covalarm', item.getInt('alarm', 300))
            self.cov=self.value('cov', unit='ppb', resolution=10)
            self.ecov=self.value('ecov', unit='ppm', resolution=10)

        if self.config.iaq:
            self.iaqwarning=self.valueDigital('iaqwarning')
            self.iaqalarm=self.valueDigital('iaqalarm')
            self.iaq=self.value('iaq', unit='', resolution=1)

    def poweron(self):
        # Communication
        self.writeRegistersIfChanged(11, [19200, 0])

        self.writeRegistersIfChanged(13, self.config.toffset*100)

        if self.config.co2:
            self.writeRegistersIfChanged(24, self.config.co2warning)
            self.writeRegistersIfChanged(25, self.config.co2alarm)

        if self.config.cov:
            self.writeRegistersIfChanged(22, self.config.covwarning)
            self.writeRegistersIfChanged(23, self.config.covalarm)

        if self.config.iaq:
            # iaq histeresis ppm/ppq
            self.writeRegistersIfChanged(26, 50)

        return True

    def poweroff(self):
        return True

    def refresh(self):
        r=self.readInputRegisters(0, 8)
        if r:
            decoder=self.decoderFromRegisters(r)
            self.t.updateValue(decoder.word()/100.0+self.config.toffset)
            vhr=decoder.word()/100.0
            if self.config.hygrometry:
                self.hr.updateValue(vhr)
                self.dewp.updateValue(self.calcDEWP(self.t.value, self.hr.value))

            vsp=decoder.int16()/100.0
            vco2=decoder.word()
            status=decoder.word()
            vcov=decoder.word()
            vecov=decoder.word()
            viaq=decoder.word()
            if self.config.co2:
                self.co2.updateValue(vco2)
            if self.config.cov:
                self.cov.updateValue(vcov)
                self.ecov.updateValue(vecov)
            if self.config.iaq:
                self.iaq.updateValue(viaq)
                self.iaqwarning.updateValue(status & (0x1 << 9))
                self.iaqalarm.updateValue(status & (0x1 << 10))

        return 5.0

    def sync(self):
        pass

    def reboot(self):
        if self.writeRegisters(19, 1):
            return True
        return False
    pass


if __name__ == "__main__":
    pass
