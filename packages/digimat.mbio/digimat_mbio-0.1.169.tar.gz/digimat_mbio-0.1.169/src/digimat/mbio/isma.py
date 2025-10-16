#!/bin/python

from __future__ import annotations

from prettytable import PrettyTable
import time
import ipcalc

from .device import MBIODevice
from .xmlconfig import XMLConfig

from .netscan import MBIONetworkScanner
from .mbiosocket import MBIOSocketString

# from prettytable import PrettyTable


class MBIODeviceIsma(MBIODevice):
    NBCHANNELDI=0
    NBCHANNELDO=0
    NBCHANNELAI=0
    NBCHANNELAO=0

    @property
    def nbdi(self):
        return self.NBCHANNELDI

    @property
    def nbdo(self):
        return self.NBCHANNELDO

    @property
    def nbai(self):
        return self.NBCHANNELAI

    @property
    def nbao(self):
        return self.NBCHANNELAO

    def hasDI(self):
        return self.nbdi>0

    def hasDO(self):
        return self.nbdo>0

    def hasAI(self):
        return self.nbai>0

    def hasAO(self):
        return self.nbao>0

    def hasInputs(self):
        return self.hasDI() or self.hasAI()

    def hasOutputs(self):
        return self.hasDO() or self.hasAO()

    def isIP(self):
        try:
            mtype=self.moduleTypeStr() or self.__class__.__name__[-2:].upper()
            if mtype=="IP":
                return True
        except:
            pass
        return False

    def onInitDI(self):
        for channel in range(self.nbdi):
            value=self.valueDigital('di%d' % channel, commissionable=True)
            self.DI.append(value)
            value.config.set('invert', False)

    def onInitDO(self):
        for channel in range(self.nbdo):
            value=self.valueDigital('do%d' % channel, writable=True, commissionable=True)
            self.DO.append(value)
            value.config.set('invert', False)
            value.config.set('default', None)

    def onInitAI(self):
        for channel in range(self.nbai):
            value=self.value('ai%d' % channel, commissionable=True)
            self.AI.append(value)
            value.config.set('type', 'pt1000')
            value.config.set('resolution', 0.1)
            value.config.set('offset', 0)
            value.config.set('filter', 10)

    def onInitAO(self):
        for channel in range(self.nbao):
            value=self.value('ao%d' % channel, unit='%', resolution=1, writable=True, commissionable=True)
            value.setRange(0, 100)
            self.AO.append(value)
            value.config.set('default', None)
            value.config.set('invert', False)
            value.config.set('lrange', 0)
            value.config.set('hrange', 100)
            value.config.set('resolution', 1.0)
            value.config.set('min', 0.0)
            value.config.set('max', 100.0)

    def onInit(self):
        super().onInit()

        self._moduleType=None
        self._rebootRequested=False

        self._vendor='ISMA'
        self._model='N/A'

        self._timeoutRefreshSlow=0
        self._timeoutRefreshDI=0
        self._timeoutRefreshDO=0
        self._timeoutRefreshAI=0
        self._timeoutRefreshAO=0

        self._overrideDO=None
        self._overrideAO=None

        self.setPingInputRegister(0)

        self.DI=[]
        self.DO=[]
        self.AI=[]
        self.AO=[]

        if self.hasOutputs():
            self.config.set('watchdog', 60)
            self.OVR=self.valueDigital('override')

        if self.hasDI():
            self.onInitDI()
        if self.hasDO():
            self.onInitDO()
        if self.hasAI():
            self.onInitAI()
        if self.hasAO():
            self.onInitAO()

        self.config.set('resistor')

    def onLoadDI(self, xml: XMLConfig):
        for channel in range(self.nbdi):
            value=self.DI[channel]
            item=xml.child('di%d' % channel)
            if item:
                if not item.getBool('enable', True):
                    value.disable()
                value.config.xmlUpdateBool(item, 'invert')

    def onLoadDO(self, xml: XMLConfig):
        for channel in range(self.nbdo):
            value=self.DO[channel]
            item=xml.child('do%d' % channel)
            if item:
                if not item.getBool('enable', True):
                    value.disable()
                value.config.xmlUpdateBool(item, 'invert')
                value.config.xmlUpdateBool(item, 'default')

    def onLoadAI(self, xml: XMLConfig):
        for channel in range(self.nbai):
            value=self.AI[channel]
            item=xml.child('ai%d' % channel)
            if item:
                if not item.getBool('enable', True):
                    value.disable()
                value.config.xmlUpdate(item, 'type')
                value.config.xmlUpdateFloat(item, 'resolution', vmin=0)
                value.config.xmlUpdateInt(item, 'filter', vmin=0, vmax=60)
                value.config.xmlUpdateFloat(item, 'offset')
                if value.config.contains('type', '10v'):
                    value.config.set('unit', 'V')
                    value.config.xmlUpdate(item, 'unit')
                    if value.config.type=='2-10v':
                        value.config.set('x0', 2.0)
                    else:
                        value.config.set('x0', 0.0)
                    value.config.xmlUpdateFloat(item, 'x0', vmin=0)
                    value.config.set('x1', 10.0)
                    value.config.xmlUpdateFloat(item, 'x1', vmin=value.config.x0, vmax=10)
                    value.config.set('y0', 0.0)
                    value.config.xmlUpdateFloat(item, 'y0')
                    value.config.set('y1', 10.0)
                    value.config.xmlUpdateFloat(item, 'y1', vmin=value.config.y0)
                if value.config.contains('type', '100%'):
                    value.config.set('unit', '%')
                    value.config.xmlUpdate(item, 'unit')
                    if value.config.type=='20-100%':
                        value.config.set('x0', 2.0)
                    else:
                        value.config.set('x0', 0.0)
                    value.config.xmlUpdateFloat(item, 'x0', vmin=0)
                    value.config.set('x1', 10.0)
                    value.config.xmlUpdateFloat(item, 'x1', vmin=value.config.x0, vmax=10)
                    value.config.set('y0', 0.0)
                    value.config.xmlUpdateFloat(item, 'y0')
                    value.config.set('y1', 100.0)
                    value.config.xmlUpdateFloat(item, 'y1', vmin=value.config.y0)
            value.resolution=value.config.resolution

    def onLoadAO(self, xml: XMLConfig):
        for channel in range(self.nbao):
            value=self.AO[channel]
            item=xml.child('ao%d' % channel)
            if item:
                if not item.getBool('enable', True):
                    value.disable()

                value.config.xmlUpdateFloat(item, 'default')
                value.config.xmlUpdateBool(item, 'invert')
                value.config.xmlUpdateFloat(item, 'lrange', vmin=0, vmax=100)
                value.config.xmlUpdateFloat(item, 'hrange', vmin=value.config.lrange, vmax=100)
                value.config.xmlUpdateFloat(item, 'resolution', vmin=0)
                value.config.xmlUpdateFloat(item, 'min', vmin=0, vmax=100)
                value.config.xmlUpdateFloat(item, 'max', vmin=value.config.min, vmax=100)
            value.resolution=value.config.resolution
        pass

    def onLoad(self, xml: XMLConfig):
        self.config.xmlUpdateBool(xml, 'resistor')

        if self.hasOutputs():
            self.config.xmlUpdateInt(xml, 'watchdog', vmin=0)

        if self.hasDI():
            self.onLoadDI(xml)
        if self.hasDO():
            self.onLoadDO(xml)
        if self.hasAI():
            self.onLoadAI(xml)
        if self.hasAO():
            self.onLoadAO(xml)

    def reboot(self):
        self.writeRegisters(1, 511)
        self.reset()

    def reloadSettings(self):
        self.writeRegisters(1, 767)
        self.reset()

    def moduleType(self):
        if self._moduleType:
            return (self._moduleType) & 0xff

    def moduleTypeStr(self):
        try:
            mtype=self.moduleType()
            mtypes={0x51: "8I",
                0x5B: "8IIP",
                0x54: "8U",
                0x5E: "8UIP",
                0x53: "4I4OH",
                0x5D: "4I4OHIP",
                0x55: "4U4OH",
                0x5F: "4U4OHIP",
                0x56: "4U4AH",
                0x60: "4U4AHIP",
                0x52: "4OH",
                0x5C: "4OHIP",
                0x57: "4TOH",
                0x61: "4TOHIP",
                0x32: "MIX18",
                0x33: "MIX38",
                0x34: "MIX18IP",
                0x35: "MIX38IP"}
            return mtypes.get(mtype).upper()
        except:
            pass

    def moduleFirmwareVersion(self):
        if self._moduleType:
            return float((self._moduleType >> 8) & 0xff)/10.0

    def checkModuleType(self, mtype):
        try:
            if mtype.upper() in self.moduleTypeStr():
                return True
        except:
            pass

    def probe(self):
        mac=None
        hwversion=None

        self.logger.debug('Probing ISMA device address %d' % self.address)
        r=self.readInputRegisters(0, 1)
        if r:
            self._moduleType=r[0]
            r=self.readInputRegisters(129, 4)
            if r:
                hwversion=float(r[0])/10.0
                mac=(r[1]>>8) | ((r[1] & 0xff) << 8)
                mac <<= 16
                mac |=(r[2]>>8) | ((r[2] & 0xff) << 8)
                mac <<= 16
                mac |=(r[3]>>8) | ((r[3] & 0xff) << 8)
                mac=self.mbio.normalizeMAC(hex(mac)[2:])

        mtype=self.moduleType()
        mversion=self.moduleFirmwareVersion()
        if mtype is not None and mversion is not None:
            data={'model': mtype,
                   'version': mversion,
                   'hwversion': hwversion,
                   'mac': mac}
            self._mac=mac
            return data

    def poweronDI(self):
        pass

    def poweronDO(self):
        # set default value (watchdog value)
        data=0x0
        for channel in range(self.nbdo):
            value=self.DO[channel]
            state=value.config.default
            if value.config.invert:
                state=not state
            if state:
                data |= (0x1 << channel)

            # operation mode
            self.writeRegistersIfChanged(175+(channel*4), 0)

        self.writeRegistersIfChanged(142, data)
        return True

    def poweron(self):
        for channel in range(self.NBCHANNEL):
            value=self.AI[channel]
            # offset
            self.writeRegistersIfChanged(0+channel, 0)
            self.writeRegistersIfChanged(0+channel+1, 0)

            data=self.getFormatFromType(value)
            self.writeRegistersIfChanged(16+channel, data)
        return True

    def poweronAI(self):
        # resolution (0=12bits, 1=16bits -- for ni1000 and pt1000)
        self.writeRegistersIfChanged(166, 0xfff)
        for channel in range(self.nbai):
            value=self.AI[channel]

            # type
            data=16
            if value.config.type is not None:
                if value.config.type=='+pt1000':
                    data=16
                    value.unit='C'
                elif value.config.type=='+ni1000':
                    data=17
                    value.unit='C'
                elif value.config.type=='+ni1000-5k':
                    data=18
                    value.unit='C'
                elif '10v' in value.config.type:
                    value.unit='V'
                    # allow custom unit
                    if value.config.get('unit'):
                        value.unit=value.config.unit
                elif 'pot' in value.config.type:
                    data=16
                    value.unit='ohm'
                    value.config.set('r2t', 'r')
                    # allow custom unit
                    if value.config.get('unit'):
                        value.unit=value.config.unit
                elif value.config.type=='ohm':
                    data=16
                    value.unit='ohm'
                    value.config.set('r2t', 'r')
                elif value.config.type in ['pt1000', 'ni1000', 'ni1000-5k']:
                    # the conversion will be made by the mbio processor
                    # so, the ai channel is set to "ohm" mode
                    data=16
                    value.config.set('r2t', value.config.type)
                    value.unit='C'
                elif value.config.type=='din':
                    # Resistive measure
                    data=126
                    value.unit='%'
            else:
                # PT1000
                data=16
                value.config.set('r2t', value.config.type)
                value.unit='C'

            self.writeRegistersIfChanged(150+channel, data)

            # filter
            if value.config.filter:
                self.writeRegistersIfChanged(158+channel, int(value.config.filter))

    def poweronAO(self):
        self.writeRegistersIfChanged(143, 0)
        for channel in range(self.nbao):
            value=self.AO[channel]
            state=value.config.default
            if state is not None:
                self.writeRegistersIfChanged(144+channel, state*1000)
            # 10v mode
            self.writeRegistersIfChanged(167, 0)

    def poweron(self):
        self._rebootRequested=False
        self.resetConditionalWriteMark()

        # RS485 baud rat
        self.writeRegistersIfChanged(135, 1920)

        if (self.config.resistor is None and self.address==1) or self.config.getBool('resistor'):
            # RS485 stop bits + terminator
            self.writeRegistersIfChanged(136, 0x101)
        else:
            # RS485 stop bits
            self.writeRegistersIfChanged(136, 1)
        # RS485 data bits
        self.writeRegistersIfChanged(137, 8)
        # RS485 parity (0=None, 1=ODD, 2=EVEN)
        self.writeRegistersIfChanged(138, 2)
        # RS485 response delay
        self.writeRegistersIfChanged(139, 0)

        if self.checkConditionalWriteMark():
            self._rebootRequested=True

        if self.hasOutputs():
            if self.config.watchdog:
                self.writeRegistersIfChanged(140, self.config.watchdog)
            else:
                self.writeRegistersIfChanged(140, 0)
        else:
            self.writeRegistersIfChanged(140, 0)

        if self.hasDI():
            self.poweronDI()
        if self.hasDO():
            self.poweronDO()
        if self.hasAI():
            self.poweronAI()
        if self.hasAO():
            self.poweronAO()

        return True

    def poweronsave(self):
        # called if any conditional registers write were done during poweron()
        if self._rebootRequested:
            self.logger.debug('Device %s poweron COM settings have changed, reload settings!' % (self.key))
            self.reloadSettings()

    def isreadytorun(self):
        if self._rebootRequested:
            if self.ping():
                return True
            return False
        return True

    def poweroff(self):
        # to be overriden
        return True

    def powerlost(self):
        # to be overriden
        # TODO: not a good name
        return True

    def refreshDI(self):
        r=self.readInputRegisters(15, 1)
        if r:
            data=r[0]
            for channel in range(self.nbdi):
                self.microsleep()
                value=self.DI[channel]

                state=bool((data>>channel) & 0x1)
                if value.config.invert:
                    state=not state

                value.updateValue(state)

    def refreshDO(self):
        # current state
        r=self.readHoldingRegisters(17, 1)
        if r:
            states=r[0]
            # manual override
            r=self.readInputRegisters(14, 1)
            if r:
                override=False
                data=r[0]
                for channel in range(self.nbdo):
                    value=self.DO[channel]
                    state=bool((states>>channel) & 0x1)
                    manualstate=(data>>(channel*2)) & 0x3

                    # auto
                    if manualstate==0:
                        value.setOverride(False)
                    # manual OFF
                    elif manualstate==2:
                        override=True
                        state=0
                        value.setOverride(True)
                    # manual ON
                    elif manualstate==3:
                        override=True
                        state=1
                        value.setOverride(True)

                    if value.config.invert:
                        state=not state
                    value.updateValue(state)

                self._overrideDO=override

    def refreshAI(self):
        # AI as 0/1
        states=None
        r=self.readInputRegisters(16, 1)
        if r:
            states=r[0]

        for channel in range(self.nbai):
            value=self.AI[channel]

            data=None
            try:
                if value.config.r2t:
                    r=self.readInputRegisters(102+channel, 1)
                    if r:
                        data=r[0]/10

                        rmin=0
                        rmax=9999
                        if value.config.type in ['pt1000', 'ni1000', 'ni1000_tk5000']:
                            rmin=500
                            rmax=2000

                        if data<rmin or data>rmax:
                            data=999999
                        else:
                            data=self.r2t(value.config.r2t, data)
                elif value.config.type in ['+pt1000', '+pt100', '+ni1000', '+ni1000-5k']:
                    r=self.readInputRegisters(72+(channel*2), 1)
                    if r:
                        data=r[0]/10.0
                        if data<-50 or data>150:
                            data=999999
                elif '10v' in value.config.type:
                    r=self.readInputRegisters(70+(channel*2), 1)
                    if r:
                        data=r[0]/1000.0
                elif value.config.type=='din':
                    data=0
                    if states is not None and (states >> channel) & 0x1:
                        data=100
            except:
                self.logger.exception('x')
                pass

            if data is not None:
                if data<999999:
                    try:
                        dy=(value.config.y1-value.config.y0)
                        dx=(value.config.x1-value.config.x0)
                        data=value.config.y0+(data-value.config.x0)/dx*dy
                        if data<value.config.y0:
                            data=value.config.y0
                        if data>value.config.y1:
                            data=value.config.y1
                    except:
                        pass

                    value.updateValue(data+value.config.offset)
                    value.setError(False)
                else:
                    value.updateValue(0)
                    value.setError(True)

    def refreshAO(self):
        r=self.readHoldingRegisters(120, 6)
        if r:
            states=r
            # manual override
            r=self.readInputRegisters(14, 1)
            if r:
                override=False
                data=r[0]
                for channel in range(self.nbao):
                    self.microsleep()
                    value=self.AO[channel]
                    manualstate=(data>>(channel*2)) & 0x3
                    state=states[channel]/100.0

                    if channel>=4:
                        value.setOverride(False)
                    else:
                        # auto
                        if manualstate==0:
                            value.setOverride(False)
                        # manual
                        else:
                            override=True
                            value.setOverride(True)
                            r=self.readHoldingRegisters(124+channel, 1)
                            if r:
                                state=r[0]

                    if value.config.invert:
                        state=100.0-state
                    value.updateValue(state)

                self._overrideAO=override

    def refresh(self):
        if self.hasDI() and self.isTimeout(self._timeoutRefreshDI):
            self._timeoutRefreshDI=self.timeout(2.0)
            self.refreshDI()
            self.microsleep()

        if self.hasDO() and self.isTimeout(self._timeoutRefreshDO):
            self._timeoutRefreshDO=self.timeout(5.0)
            self.refreshDO()
            self.microsleep()

        if self.hasAI() and self.isTimeout(self._timeoutRefreshAI):
            self._timeoutRefreshAI=self.timeout(2.0)
            self.refreshAI()
            self.microsleep()

        if self.hasAO() and self.isTimeout(self._timeoutRefreshAO):
            self._timeoutRefreshAO=self.timeout(5.0)
            self.refreshAO()
            self.microsleep()

        if self.hasOutputs():
            state=False
            if self._overrideDO or self._overrideAO:
                state=True
            self.OVR.updateValue(state)

        if self.isTimeout(self._timeoutRefreshSlow):
            self._timeoutRefreshSlow=self.timeout(15)

        return 1.0

    def syncDO(self):
        synced=False
        for channel in range(self.nbdo):
            value=self.DO[channel]
            if not value.isEnabled():
                continue
            if value.isPendingSync():
                self.signalRefresh(0.1)
                state=value.toReachValue
                if value.config.invert:
                    state=not state
                if self.writeRegisterBitIfChanged(17, channel, state):
                    value.clearSync()
                    self._timeoutRefreshDO=0
                    synced=True

        return synced

    def syncAO(self):
        synced=False

        for channel in range(self.nbao):
            self.microsleep()
            value=self.AO[channel]
            if not value.isEnabled():
                continue
            if value.isPendingSync():
                self.signalRefresh(1.0)
                if self.writeRegisters(120+channel, int(value.toReachValue/10.0*1000.0)):
                    value.clearSync()

        return synced

    def sync(self):
        if self.hasDO():
            if self.syncDO():
                self._timeoutRefreshDO=0
                self.microsleep()

        if self.hasAO():
            if self.syncAO():
                self._timeoutRefreshAO=0
                self.microsleep()

        return True

    def off(self):
        if self.hasDO():
            for channel in range(self.nbdo):
                self.DO[channel].off()

        if self.hasAO():
            for channel in range(self.nbao):
                self.AO[channel].set(0)

    def on(self):
        if self.hasDO():
            for channel in range(self.nbdo):
                self.DO[channel].on()

        if self.hasAO():
            for channel in range(self.nbao):
                self.AO[channel].set(100)

    def toggle(self):
        if self.hasDO():
            for channel in range(self.nbdo):
                self.DO[channel].toggle()

        if self.hasAO():
            for channel in range(self.nbao):
                value=self.AO[channel]
                if value.value>50:
                    self.AO[channel].set(0)
                else:
                    self.AO[channel].set(100)


class MBIODeviceIsma4I4OH(MBIODeviceIsma):
    NBCHANNELDI=4
    NBCHANNELDO=4


class MBIODeviceIsma4I4OHIP(MBIODeviceIsma4I4OH):
    pass

class MBIODeviceIsma4U4AH(MBIODeviceIsma):
    NBCHANNELAI=4
    NBCHANNELAO=4

class MBIODeviceIsma4U4AHIP(MBIODeviceIsma4U4AH):
    pass


class IsmaScanner(MBIONetworkScanner):
    def probe(self, host):
        hostid=None
        c=MCConfigurator(host, None)
        if c.connect():
            hostid=self.mbio.normalizeMAC(c['mac'])
        c.disconnect()
        return hostid

    def configureHostFromGateway(self, host, gateway):
        c=MCConfigurator(host, gateway.password)
        if c.connect():
            self.logger.warning('Reconfiguring Isma Gateway %s...' % (gateway.MAC))
            c.setIP(gateway.host)
            c.name=gateway.name
            c.setRS485(19200, 'E', 1, 1.0, True)
            c.idletimeout=30
            c.password=gateway.password
            # will restart only if config was updated
            c.netrestart()
        c.disconnect()


if __name__ == "__main__":
    pass
