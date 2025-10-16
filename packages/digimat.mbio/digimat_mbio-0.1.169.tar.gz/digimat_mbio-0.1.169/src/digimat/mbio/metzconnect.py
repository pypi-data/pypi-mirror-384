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


class MBIODeviceMetzConnect(MBIODevice):
    pass


class MBIODeviceMetzConnectMRDO4(MBIODeviceMetzConnect):
    NBCHANNEL=4

    def onInit(self):
        self.config.set('watchdog', 60)
        self.OVR=self.valueDigital('override')
        self.DO=[]

        for channel in range(self.NBCHANNEL):
            value=self.valueDigital('do%d' % channel, writable=True, commissionable=True)
            self.DO.append(value)
            value.config.set('invert', False)
            value.config.set('default', None)

    def onLoad(self, xml: XMLConfig):
        self.config.xmlUpdateInt(xml, 'watchdog', vmin=0)

        for channel in range(self.NBCHANNEL):
            value=self.DO[channel]

            item=xml.child('do%d' % channel)
            if item:
                if not item.getBool('enable', True):
                    value.disable()
                value.config.xmlUpdateBool(item, 'invert')
                value.config.xmlUpdateBool(item, 'default')

    def poweron(self):
        self.writeRegistersIfChanged(66, self.config.watchdog*100)
        data=0x0
        for channel in range(self.NBCHANNEL):
            value=self.DO[channel]
            state=value.config.default
            if value.config.invert:
                state=not state
            if state:
                data |= (0x1 << channel)
        self.writeRegistersIfChanged(1, data)
        return True

    def poweroff(self):
        return True

    def refresh(self):
        count=self.NBCHANNEL
        r=self.readCoils(0, 2*count)
        if r:
            override=False
            for channel in range(count):
                self.microsleep()
                value=self.DO[channel]

                state=bool(r[channel])
                if value.config.invert:
                    state=not state
                value.updateValue(state)

                state=r[count+channel]
                value.setOverride(state)
                if state:
                    override=True

            self.OVR.updateValue(override)
        return 2.0

    def sync(self):
        for channel in range(self.NBCHANNEL):
            self.microsleep()
            value=self.DO[channel]
            if not value.isEnabled():
                continue
            if value.isPendingSync():
                self.signalRefresh(0.1)
                state=value.toReachValue
                if value.config.invert:
                    state=not state
                if self.writeCoils(channel, state):
                    value.clearSync()

    def off(self):
        for channel in range(self.NBCHANNEL):
            self.DO[channel].off()

    def on(self):
        for channel in range(self.NBCHANNEL):
            self.DO[channel].on()

    def toggle(self):
        for channel in range(self.NBCHANNEL):
            self.DO[channel].toggle()


class MBIODeviceMetzConnectMRDI10(MBIODeviceMetzConnect):
    NBCHANNEL=10

    def onInit(self):
        self.DI=[]
        for channel in range(self.NBCHANNEL):
            value=self.valueDigital('di%d' % channel, commissionable=True)
            self.DI.append(value)
            value.config.set('invert', False)

    def onLoad(self, xml: XMLConfig):
        for channel in range(self.NBCHANNEL):
            value=self.DI[channel]
            item=xml.child('di%d' % channel)
            if item:
                if not item.getBool('enable', True):
                    value.disable()
                value.config.xmlUpdateBool(item, 'invert')

    def poweron(self):
        return True

    def poweroff(self):
        return True

    def refresh(self):
        r=self.readDiscreteInputs(0, self.NBCHANNEL)
        if r:
            for channel in range(self.NBCHANNEL):
                self.microsleep()
                value=self.DI[channel]

                state=bool(r[channel])
                if value.config.invert:
                    state=not state

                value.updateValue(state)

        return 1.0


class MBIODeviceMetzConnectMRDI4(MBIODeviceMetzConnectMRDI10):
    NBCHANNEL=4


class MBIODeviceMetzConnectMRAI8(MBIODeviceMetzConnect):
    NBCHANNEL=8

    def getFormatFromType(self, value):
        stype=value.config.type
        types=['pt100', 'pt500', 'pt1000',
            'ni1000-tk5000', 'ni1000-tk6180',
            'balco500',
            'kty81-110', 'kty81-210',
            'ntc-1k8', 'ntc-5k', 'ntc-10k', 'ntc-20k',
            'lm235',
            'ntc-10k-carel']
        try:
            index=types.index(stype.lower())
            value.unit='C'
            return 0x80 | (index << 1) | 0x0
        except:
            pass

        try:
            types=['ohm', '10v']
            index=types.index(stype.lower())
            if index==0:
                value.unit='ohm'
                return (0x2 << 5) | 0x0
            if index==1:
                value.unit='V'
                if value.config.get('unit'):
                    value.unit=value.config.unit
                return (0x0 << 5) | 0x0
        except:
            pass

        self.logger.warning('%s:unknown AI format %s' % (self.key, stype))

        # PT1000
        value.unit='C'
        return 0x80 | (2 << 1) | 0x0

    def onInit(self):
        self.AI=[]
        for channel in range(self.NBCHANNEL):
            value=self.value('ai%d' % channel, commissionable=True)
            value.config.set('type', 'pt1000')
            value.config.set('resolution', 0.1)
            value.config.set('offset', 0)
            self.AI.append(value)

    def onLoad(self, xml: XMLConfig):
        for channel in range(self.NBCHANNEL):
            value=self.AI[channel]
            item=xml.child('ai%d' % channel)
            if item:
                if not item.getBool('enable', True):
                    value.disable()
                value.config.xmlUpdate(item, 'type')
                value.config.xmlUpdateFloat(item, 'resolution', vmin=0)
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

    def poweron(self):
        for channel in range(self.NBCHANNEL):
            value=self.AI[channel]
            # offset
            self.writeRegistersIfChanged(0+channel, 0)
            self.writeRegistersIfChanged(0+channel+1, 0)

            data=self.getFormatFromType(value)
            self.writeRegistersIfChanged(16+channel, data)
        return True

    def poweroff(self):
        return True

    def refresh(self):
        r=self.readInputRegisters(0, self.NBCHANNEL*2)
        if r:
            decoder=self.decoderFromRegisters(r)
            for channel in range(self.NBCHANNEL):
                self.microsleep()
                value=self.AI[channel]
                data=decoder.float32()
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
        return 5.0


class MBIODeviceMetzConnectMRAO4(MBIODeviceMetzConnect):
    NBCHANNEL=4

    def onInit(self):
        self.config.set('watchdog', 60)
        self.OVR=self.valueDigital('override')
        self.AO=[]
        for channel in range(4):
            value=self.value('ao%d' % channel, unit='%', resolution=1, writable=True, commissionable=True)
            value.setRange(0, 100)
            value.config.set('default', None)
            value.config.set('invert', False)
            value.config.set('lrange', 0)
            value.config.set('hrange', 100)
            value.config.set('resolution', 1.0)
            value.config.set('min', 0.0)
            value.config.set('max', 100.0)
            self.AO.append(value)

    def onLoad(self, xml: XMLConfig):
        self.config.xmlUpdateInt(xml, 'watchdog', vmin=0)

        for channel in range(self.NBCHANNEL):
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

    def raw2state(self, value, raw):
        if raw is not None:
            state=raw/0x7fff*100.0
            lrange=value.config.lrange
            hrange=value.config.hrange
            if lrange>0 or hrange<100:
                state=max(lrange, state)
                state=min(hrange, state)
                state=(state-lrange)/(hrange-lrange)*100
            if value.config.invert:
                state=100.0-state
            return state

    def state2raw(self, value, state):
        if state is not None:
            lrange=value.config.lrange
            hrange=value.config.hrange
            state=min(state, value.config.max)
            state=max(state, value.config.min)
            if value.config.invert:
                state=100.0-state
            if lrange>0 or hrange<100:
                raw=0x7fff/100.0*(lrange+(hrange-lrange)*state/100.0)
            else:
                raw=state/100.0*0x7fff
            return int(raw)

    def poweron(self):
        self.writeRegistersIfChanged(66, self.config.watchdog*100)
        for channel in range(self.NBCHANNEL):
            value=self.AO[channel]
            state=value.config.default
            self.writeRegistersIfChanged(self.NBCHANNEL+channel,
                self.state2raw(value, state))
        return True

    def poweroff(self):
        return True

    def refresh(self):
        count=self.NBCHANNEL
        r=self.readHoldingRegisters(0, count)
        if r:
            for channel in range(count):
                self.microsleep()
                value=self.AO[channel]
                state=self.raw2state(value, r[channel])
                value.updateValue(state)

        if self.model[-1].upper()=='P':
            # Have manual knobs
            r=self.readDiscreteInputs(0, count)
        else:
            # The device has no manual knobs
            r=[0]*count

        if r:
            override=False
            for channel in range(count):
                self.microsleep()
                value=self.AO[channel]

                state=r[channel]
                value.setOverride(state)
                if state:
                    override=True

            self.OVR.updateValue(override)
        return 5.0

    def sync(self):
        for channel in range(self.NBCHANNEL):
            self.microsleep()
            value=self.AO[channel]
            if not value.isEnabled():
                continue
            if value.isPendingSync():
                self.signalRefresh(1.0)
                raw=self.state2raw(value, value.toReachValue)
                if self.writeRegisters(channel, raw):
                    value.clearSync()

    def off(self):
        for channel in range(self.NBCHANNEL):
            self.AO[channel].set(0)

    def on(self):
        for channel in range(self.NBCHANNEL):
            self.AO[channel].set(100)

    def toggle(self):
        for channel in range(self.NBCHANNEL):
            if self.AO[channel].value:
                self.AO[channel].set(0)
            else:
                self.AO[channel].set(100)


class MCConfigurator(object):
    def __init__(self, host, password):
        self._host=host
        self._password=password
        self._link=MBIOSocketString(self._host, 23)
        self._config={}
        self._updated=False
        self._buf=None
        self._auth=False
        self.reset()

    @property
    def config(self):
        return self._config or self

    def reset(self):
        self._buf=''

    def isConnected(self):
        if self._link.isConnected():
            return True

    def isAuthenticated(self):
        if self.isConnected() and self._auth:
            return True
        return False

    def auth(self):
        if self.isConnected():
            if self._auth:
                return True
            passwords=['1234']
            if self._password:
                passwords.insert(0, self._password)
            for password in passwords:
                if self.send(password):
                    self._auth=True
                    self.update()
                    return True
        return False

    def connect(self):
        if self.isConnected():
            return self.auth()
        self._auth=False
        if self._link.connect(timeout=3.0):
            return self.auth()

    def disconnect(self):
        self._link.disconnect()
        self._auth=False
        self.reset()

    def __del__(self):
        self.disconnect()
        self._link=None

    def read(self):
        if self.isConnected():
            data=self._link.read()
            if data:
                self._buf+=data
                return data

    def wait(self, data, timeout=3.0):
        t=time.time()+timeout
        while True:
            r=self.read()
            if r and data in self._buf:
                return self._buf
            if not self._auth and 'password:' in self._buf:
                break
            if not timeout:
                break
            time.sleep(0.01)
            if time.time()>=t:
                break

    def waitprompt(self, timeout=3.0):
        if self.wait('>', timeout):
            try:
                lines=[]
                buf=self._buf.replace('\r\n', '\n')
                for line in buf.split('\n'):
                    line=line.strip()
                    if not line or line=='>':
                        continue
                    lines.append(line)
                return lines
            except:
                pass

    def send(self, data, timeout=3.0):
        if self.isConnected():
            self.reset()
            if self._link.write(data+'\n'):
                return self.waitprompt(timeout)
        return False

    def updateInfo(self):
        if self.isConnected():
            data=self.send('inf')
            if data:
                try:
                    for line in data:
                        pos=line.find(':')
                        if pos>0:
                            key=line[:pos]
                            value=line[pos+1:]
                            key=key.strip().lower()
                            value=value.strip()
                            if key and value:
                                self._config[key]=value
                    return True
                except:
                    pass

    def updateConfig(self):
        if self.isConnected():
            data=self.send('cfg')
            if data:
                try:
                    for line in data:
                        pos=line.find(':')
                        if pos>0:
                            key=line[:pos]
                            value=line[pos+1:]
                            key=key.strip().lower()
                            value=value.strip()
                            if key and value:
                                if 'commands' not in key:
                                    self._config[key]=value
                    return True
                except:
                    pass

    def update(self):
        if self.updateInfo() and self.updateConfig():
            return self._config

    def __getitem__(self, key):
        try:
            return self._config[key.lower()]
        except:
            pass

    def check(self, key, value):
        try:
            if self._config[key.lower()]==value:
                return True
        except:
            pass
        return False

    def command(self, command, value):
        if self.isConnected():
            if command and value is not None:
                command=command.lower()
                value=str(value)
                if value and command in ['name', 'ip', 'mask', 'gateway',
                        'dhcp', 'mac', 'password', 'allowedip', 'allowedmask',
                        'mode', 'parity', 'baudrate', 'stopbits',
                        'timeout', 'terminator', 'idletimeout']:
                    if self.check(command, value):
                        return True
                    self._updated=True
                    self.send('%s %s' % (command, value))
                    if command=='password':
                        self.disconnect()
                    self.update()
                    return self.check(command, value)
        return False

    @property
    def name(self) -> type:
        return self['name']

    @name.setter
    def name(self, value: type):
        self.command('name', value)

    @property
    def password(self) -> type:
        return self['password']

    @password.setter
    def password(self, value: type):
        self.command('password', value)
        self.disconnect()
        self._password=value
        self.connect()

    @property
    def idletimeout(self) -> type:
        return int(self['idletimeout'])

    @idletimeout.setter
    def idletimeout(self, seconds: type):
        seconds=int(seconds)
        if seconds<1:
            seconds=100
        self.command('idletimeout', seconds)

    def setIP(self, ip, mask='255.255.255.0', gw=None):
        try:
            n=ipcalc.Network('%s/%s' % (ip, mask))
            result=self.command('ip', n.to_tuple()[0])
            result&=self.command('mask', str(n.netmask()))
            result&=self.command('dhcp', 0)
            if gw:
                try:
                    n=ipcalc.Network(gw)
                    result&=self.command('gateway', n.to_tuple()[0])
                except:
                    pass
            return result
        except:
            pass
        return False

    def setAllowedIP(self, network):
        try:
            n=ipcalc.Network(network)
            result=self.command('allowedip', n.to_tuple()[0])
            result&=self.command('allowedmask', str(n.netmask()))
            return result
        except:
            pass
        return False

    def setDHCP(self):
        return self.command('dhcp', 1)

    def netrestart(self):
        if self._updated:
            self.send('netstart')
            self._updated=False
            return True

    def setRS485(self, speed=19200, parity='E', stopbits=1, timeout=0.1, terminator=True):
        result=self.command('mode', 0)

        speed=int(speed)
        if speed not in [9600, 19200, 38400, 57600]:
            speed=19200

        result&=self.command('baudrate', speed)
        try:
            parity={'N': 0, 'E': 1, 'O': 2}.get(parity.upper())
            result&=self.command('parity', parity)
        except:
            pass

        if timeout<1:
            timeout=1
        result&=self.command('timeout', int(timeout*1000.0))

        result&=self.command('stopbits', stopbits)
        value=1
        if not terminator:
            value=0
        result&=self.command('terminator', value)
        return result

    def __repr__(self):
        return '%s(%s@%s/%s, fw=%s)' % (self.__class__.__name__, self['name'], self['mac'], self['ip'], self['firmware version'])

    def dump(self):
        t=PrettyTable()
        t.field_names=['Property', 'Value']
        t.align='l'

        for key in self._config:
            t.add_row([key, self._config[key]])

        print(t.get_string())


class MCScanner(MBIONetworkScanner):
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
            self.logger.warning('Reconfiguring MetzConnect Gateway %s...' % (gateway.MAC))
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
