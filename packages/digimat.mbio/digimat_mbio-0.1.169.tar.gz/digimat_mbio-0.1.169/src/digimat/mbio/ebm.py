#!/bin/python

from .device import MBIODevice
from .xmlconfig import XMLConfig

from pymodbus.constants import Endian


class MBIODeviceEBM(MBIODevice):
    def onInit(self):
        self._vendor='EBM'
        self._model='BASE'

        # must return FAN address
        self.setPingHoldingRegister(0xd100)

        self.config.set('enablesource', 'bus')
        self.config.set('speedsource', 'bus')
        self.config.set('controlmode', 'speed')
        self.config.set('maxrpm', 0)
        self.config.set('minspeed', 5.0)
        self.config.set('maxspeed', 100.0)
        self.config.set('ramp')
        self.config.set('ramp0')
        self.config.set('ramp1')
        self.config.set('io1type', 'di')
        self.config.set('io2type', 'ai')
        self.config.set('io3type', 'ao')
        self.config.set('watchdogsource')
        self.config.set('vref', 0)
        self.config.set('iref', 0)
        self.config.set('vout')

        self.value('speed', unit='%')

        self.value('rpm', unit='t/min', resolution=1.0)
        self.value('status', unit=35)
        self.value('warning', unit=35)
        self.value('t1', unit='C')
        self.value('t2', unit='C')
        self.value('t3', unit='C')
        self.valueDigital('clockwise')
        self.value('dci', 'A', resolution=0.2)
        self.value('pow', 'W', resolution=1.0)
        self.value('ene', 'kWh', resolution=0.001)
        self.value('hcnt', unit='h')

        self._timeoutRefreshSlow=0

    def sendWarmReset(self):
        """Reset motor (ack ERROR + reload CONFIG) without communication break"""
        return self.writeRegisters(0xd000, 1)

    def sendColdreset(self):
        """Reset motor (ack ERROR + reload CONFIG) with communication break"""
        return self.writeRegisters(0xd000, 8)

    def onLoad(self, xml: XMLConfig):
        item=xml.child('enable')
        if item:
            self.config.update('enablesource', item.get('source'))
            if self.config.enablesource=='bus':
                self.valueDigital('enable', writable=True)
            else:
                self.valueDigital('enable')

        subitem=xml.child('io1')
        if subitem:
            self.config.update('io1type', subitem.get('type'))

        subitem=xml.child('io2')
        if subitem:
            self.config.update('io2type', subitem.get('type'))

        subitem=xml.child('io3')
        if subitem:
            self.config.update('io3type', subitem.get('type'))

        subitem=xml.child('vout')
        if subitem:
            self.config.update('vout', subitem.getFloat('value', vmin=3.3,  vmax=24.0))

        item=xml.child('speed')
        if item:
            self.config.update('minspeed', item.getFloat('min', vmin=5.0, vmax=50.0))
            self.config.update('maxspeed', item.getFloat('max', vmin=self.config.minspeed, vmax=100.0))
            self.config.update('speedsource', item.get('source'))
            self.config.update('controlmode', item.get('control'))
            self.config.update('ramp', item.getInt('ramp', vmin=0))
            self.config.update('ramp0', item.getInt('ramp0', vmin=0))
            self.config.update('ramp1', item.getInt('ramp1', vmin=0))

            if self.config.controlmode=='sensor':
                # sensor mode
                self.value('ai1', '%', resolution=0.1, commissionable=True)
                self.value('ai2', '%', resolution=0.1, commissionable=True)
                self.value('sp', unit='%', resolution=0.1)
            else:
                # speed mode
                if self.config.speedsource=='bus':
                    value=self.value('sp', unit='%', writable=True, resolution=1, commissionable=True)
                    value.setRange(0, 100)
                else:
                    self.value('ai1', '%', resolution=0.1, commissionable=True)
                    self.value('ai2', '%', resolution=0.1, commissionable=True)
                    self.value('sp', unit='%', resolution=0.1)

            self.config.set('x0', 1)
            self.config.set('y0', 0)
            self.config.set('x1', 10)
            self.config.set('y1', 100)

            subitem=item.child('input')
            if subitem:
                self.config.update('x0', subitem.getFloat('x0', vmin=0, vmax=10))
                self.config.update('x1', subitem.getFloat('x1', vmin=self.config.x0, vmax=10))
                self.config.update('y0', subitem.getFloat('y0', vmin=0, vmax=100))
                self.config.update('y1', subitem.getFloat('y1', vmin=self.config.y0, vmax=100))

            subitem=item.child('watchdog')
            if subitem:
                self.config.set('watchdogsource', subitem.get('source'))
                self.config.set('watchdogsp', subitem.getInt('sp', 0, vmin=0))
                if self.config.watchdogsource=='bus':
                    self.config.set('watchdogdelay', subitem.getInt('delay', 60, vmin=0))
                else:
                    self.config.set('watchdoglevel', subitem.getInt('min', 0, vmin=0))

    def poweron(self):
        # paramerter set 0
        self.writeRegistersIfChanged(0xd105, 0)

        # reload vref, iref
        r=self.readHoldingRegisters(0xd1a0, 2)
        if r:
            self.config.vref=r[0]*20.0/1000.0  # V
            self.config.iref=r[1]*2/1000.0     # A

        # VOUT (fixed power output 3.3..24.0V)
        if self.config.vout is not None:
            v=int((self.config.vout-3.3)/20.7*65536)
            self.writeRegistersIfChanged(0xd16e, v)

        # enable source
        # v6+
        data={'none': 0, 'bus': 1, 'di1-off': 2, 'di2-off': 3, 'di3-off': 4, 'di3': 4, 'di1-on': 5, 'di1': 5, 'di2-on': 6, 'di2': 6}
        self.writeRegistersIfChanged(0xd16a, data.get(self.config.enablesource, 0))

        # speed source
        self.writeRegistersIfChanged(0xd16c, 0)

        # control mode
        data={'speed': 0, 'sensor': 1}
        self.writeRegistersIfChanged(0xd106, data.get(self.config.controlmode, 0))

        # stop enable
        self.writeRegistersIfChanged(0xd112, 1)

        # max/min speed
        v=self.config.maxspeed
        if v is not None:
            self.writeRegistersIfChanged(0xd10e, int(v/100.0*255.0))

        v=self.config.minspeed
        if v is not None:
            self.writeRegistersIfChanged(0xd110, int(v/100.0*255.0))

        r=self.readHoldingRegisters(0xd119, 1)
        if r:
            self.config.update('maxrpm', r[0])

        ramp=self.config.ramp1 or self.config.ramp
        if ramp is not None:
            self.writeRegistersIfChanged(0xd11f, int(float(ramp)/2.5))
        ramp=self.config.ramp0 or self.config.ramp
        if ramp is not None:
            self.writeRegistersIfChanged(0xd120, int(float(ramp)/2.5))

        # input
        if self.config.speedsource != 'bus':
            self.writeRegistersIfChanged(0xd12a, int(self.config.x0/10.0*65535.0))
            self.writeRegistersIfChanged(0xd12c, int(self.config.x1/10.0*65535.0))
            if self.config.controlmode=='speed':
                self.writeRegistersIfChanged(0xd12b, int(self.config.y0/100.0*64000.0))
                self.writeRegistersIfChanged(0xd12d, int(self.config.y1/100.0*64000.0))
            elif self.config.controlmode=='sensor':
                self.writeRegistersIfChanged(0xd12b, int(self.config.y0/100.0*65535.0))
                self.writeRegistersIfChanged(0xd12d, int(self.config.y1/100.0*65535.0))
            elif self.config.controlmode=='openloop':
                self.writeRegistersIfChanged(0xd12b, int(self.config.y0/100.0*65535.0))
                self.writeRegistersIfChanged(0xd12d, int(self.config.y1/100.0*65535.0))

        # output speed monitoring 0-10V
        # self.writeRegistersIfChanged(0xd130, 0)
        self.writeRegistersIfChanged(0xd140, 0)
        self.writeRegistersIfChanged(0xd141, 0)
        self.writeRegistersIfChanged(0xd142, 65535)
        self.writeRegistersIfChanged(0xd143, 65535)

        # speed source
        data={'bus': 1, 'ai1': 0, 'ai2': 2}
        self.writeRegistersIfChanged(0xd101, data.get(self.config.speedsource, 1))

        if self.config.controlmode=='sensor':
            data={'ai1': 0, 'ai2': 1, 'max': 2, 'min': 3, 'mean': 4}
            self.writeRegistersIfChanged(0xd147, data.get(self.config.speedsource, 0))

        # shedding
        self.writeRegistersIfChanged(0xd150, 0)

        # IO1
        data={'di': 0, 'ai': 2}
        self.writeRegistersIfChanged(0xd158, data.get(self.config.io1type, 0))

        # IO2
        data={'di': 0, 'ai': 2}
        self.writeRegistersIfChanged(0xd159, data.get(self.config.io2type, 2))

        # IO3
        data={'di': 0, 'di0': 1, 'di!': 1, 'ao': 3}
        self.writeRegistersIfChanged(0xd15a, data.get(self.config.io3type, 3))

        # watchdog
        if self.config.watchdogsource:
            data={'bus': 1, 'ai1': 2, 'ai2': 2}
            self.writeRegistersIfChanged(0xd15c, data.get(self.config.watchdogsource, 0))
            if self.config.watchdogsource=='bus':
                self.writeRegistersIfChanged(0xd15e,
                    int(self.config.getInt('watchdogdelay', default=15, vmin=10)/100.0))
            elif self.config.watchdogsource in ['ai1', 'ai2']:
                self.writeRegistersIfChanged(0xd15f,
                    self.config.getFloat('watchdoglevel', default=0, vmin=0)/10.0*65535.0)

            v=self.config.getInt('value', default=0, vmin=0, vmax=100)
            if self.config.controlmode=='speed':
                self.writeRegistersIfChanged(0xd15d, int(v/100.0*64000.0))
            else:
                self.writeRegistersIfChanged(0xd15d, int(v/100.0*65535.0))

            # keep rotation direction
            self.writeRegistersIfChanged(0xd15b, 2)
        else:
            self.writeRegistersIfChanged(0xd15c, 0)

        if self.config.controlmode=='sensor':
            # Sensor caracteristics
            encoder=self.encoder(Endian.LITTLE)
            encoder.float32(0)
            encoder.float32(100)
            encoder.writeRegistersIfChanged(0xd160)

        return True

    def poweronsave(self):
        self.sendWarmReset()

    def poweroff(self):
        value=self.values.enable
        if value is not None and value.isWritable():
            value.off()
        value=self.values.sp
        if value is not None and value.isWritable():
            value.set(0)

        self.sync()
        return True

    def refresh(self):
        if self.config.maxrpm is not None:
            r=self.readInputRegisters(0xd010, 1)
            if r:
                try:
                    self.values.rpm.updateValue(r[0]/64000.0*self.config.maxrpm)
                except:
                    pass

        # Max 9 registers with firwmare <6
        r=self.readInputRegisters(0xd011, 9)
        if r:
            self.values.status.updateValue(r[0])
            self.values.warning.updateValue(r[1])
            # self.values.dcv.updateValue(r[2]/255.0*self.config.vref)
            self.values.dci.updateValue(r[3]/255.0*self.config.iref)
            self.values.t1.updateValue(r[4])
            self.values.t2.updateValue(r[5])
            self.values.t3.updateValue(r[6])
            self.values.clockwise.updateValue(r[7])
            self.values.speed.updateValue(r[8]/64000.0*100.0)

        r=self.readInputRegisters(0xd01a, 3)
        if r:
            value=self.values.sp
            if value is not None and not value.isWritable():
                if self.config.controlmode=='speed':
                    value.updateValue(r[1]/64000.0*100.0)
                else:
                    value.updateValue(r[1]/65535*100.0)
            value=self.values.enable
            if value is not None and not value.isWritable():
                value.updateValue(r[2])

        if self.values.ai1 is not None or self.values.ai2 is not None:
            r=self.readInputRegisters(0xd023, 2)
            if r:
                if self.values.ai1 is not None:
                    self.values.ai1.updateValue(r[0]/65535.0*100.0)
                if self.values.ai2 is not None:
                    self.values.ai2.updateValue(r[1]/65535.0*100.0)

        if self.isTimeout(self._timeoutRefreshSlow):
            r=self.readInputRegisters(0xd029, 2)
            if r:
                decoder=self.decoderFromRegisters(r[0:])
                self.values.ene.updateValue(decoder.dword())

            r=self.readInputRegisters(0xd021, 1)
            if r:
                v=r[0]/65535.0*self.config.vref*self.config.iref
                self.values.pow.updateValue(v)

            # r=self.readInputRegisters(0xd027, 1)
            # if r:
                # v=r[0]
                # self.values.pow.updateValue(v)

            r=self.readHoldingRegisters(0xd009, 1)
            if r:
                self.values.hcnt.updateValue(r[0])

            self._timeoutRefreshSlow=self.timeout(10)

        return 3.0

    def sync(self):
        value=self.values.enable
        if value is not None and value.isWritable() and value.isPendingSync():
            if self.writeRegisters(0xd00f, value.toReachValue):
                value.clearSyncAndUpdateValue()

        value=self.values.sp
        if value is not None and value.isWritable() and value.isPendingSync():
            vref=65535.0
            if self.config.controlmode=='speed':
                vref=64000.0
            if self.writeRegisters(0xd001, int(value.toReachValue/100.0*vref)):
                value.clearSyncAndUpdateValue()


if __name__ == "__main__":
    pass
