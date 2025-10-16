#!/bin/python

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .mbio import MBIOGateway


from packaging.version import Version
import re
import ipcalc
import requests

from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

from .netscan import MBIONetworkScanner
from .mbiosocket import MBIOSocketString

from .device import MBIODevice
from prettytable import PrettyTable
import pprint
import pathlib

from .xmlconfig import XMLConfig


class MBIODeviceDigimatSIO(MBIODevice):
    NBCHANNELDI=4
    NBCHANNELDO=4
    NBCHANNELAI=8
    NBCHANNELAO=4

    def buildKey(self, gateway, address):
        return '%s_io' % (gateway.key)

    def onInit(self):
        self._vendor='Digimat'
        self._model='SIO'
        self._timeoutRefreshSlow=0
        self._timeoutRefreshDI=0
        self._timeoutRefreshDO=0
        self._timeoutRefreshAI=0
        self._timeoutRefreshAO=0

        self.setPingInputRegister(98)

        self.config.set('watchdog', 60)
        self.config.set('boards', 1)
        self.config.set('extended', True)

        self.DI=[]
        self.DO=[]
        self.AI=[]
        self.AO=[]
        self.LEDR=[]
        self.LEDG=[]
        self.LEDB=[]
        self.BUZZER=None
        self.T=None
        self.UPTIME=None

    def AO_raw2state(self, value, raw):
        if raw is not None:
            state=raw/10000*100.0
            lrange=value.config.lrange
            hrange=value.config.hrange
            if lrange>0 or hrange<100:
                state=max(lrange, state)
                state=min(hrange, state)
                state=(state-lrange)/(hrange-lrange)*100
            if value.config.invert:
                state=100.0-state
            return state

    def AO_state2raw(self, value, state):
        if state is not None:
            lrange=value.config.lrange
            hrange=value.config.hrange
            state=min(state, value.config.max)
            state=max(state, value.config.min)
            if value.config.invert:
                state=100.0-state
            if lrange>0 or hrange<100:
                raw=10000/100.0*(lrange+(hrange-lrange)*state/100.0)
            else:
                raw=state/100.0*10000
            return int(raw)

    def onLoad(self, xml: XMLConfig):
        self.config.update('watchdog', xml.getInt('watchdog'))
        self.config.update('boards', xml.getInt('boards', vmin=1, vmax=7))
        self.config.update('extended', xml.getBool('extended'))
        if self.config.extended:
            self.NBCHANNELDI=8

        for board in range(self.config.boards):
            self.LEDR.append(self.valueDigital('ledr%d' % board, writable=True))
            self.LEDG.append(self.valueDigital('ledg%d' % board, writable=True))
            self.LEDB.append(self.valueDigital('ledb%d' % board, writable=True))

        self.BUZZER=self.valueDigital('buzzer', writable=True)
        self.T=self.value('t', unit='C', resolution=0.1)
        self.UPTIME=self.value('up', unit='h', resolution=0.1)

        for channel in range(self.NBCHANNELDI*self.config.boards):
            value=self.valueDigital('di%d' % channel, commissionable=True)
            value.config.set('invert', False)
            self.DI.append(value)

            item=xml.child(value.name)
            if item:
                if not item.getBool('enable', True):
                    value.disable()
                value.config.xmlUpdateBool(item, 'invert')

        for channel in range(self.NBCHANNELDO*self.config.boards):
            value=self.valueDigital('do%d' % channel, writable=True, commissionable=True)
            value.config.set('invert', False)
            value.config.set('default', None)
            self.DO.append(value)

            item=xml.child(value.name)
            if item:
                if not item.getBool('enable', True):
                    value.disable()
                value.config.xmlUpdateBool(item, 'invert')
                value.config.xmlUpdateBool(item, 'default')

        for channel in range(self.NBCHANNELAI*self.config.boards):
            value=self.value('ai%d' % channel, commissionable=True)
            value.config.set('type', '10v')
            value.config.set('resolution', 0.1)
            value.config.set('offset', 0)
            value.config.set('voffset', 0)
            self.AI.append(value)

            item=xml.child(value.name)
            if item:
                if not item.getBool('enable', True):
                    value.disable()
                value.config.xmlUpdate(item, 'type')
                value.config.xmlUpdateFloat(item, 'resolution', vmin=0)
                value.config.xmlUpdateFloat(item, 'offset')
                if value.config.contains('type', '10v'):
                    value.config.xmlUpdateFloat(item, 'voffset')
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
                if value.config.contains('type', 'pot'):
                    value.config.set('unit', 'ohm')
                    value.config.xmlUpdate(item, 'unit')
                    value.config.set('x0', 0.0)
                    value.config.xmlUpdateFloat(item, 'x0')
                    value.config.set('x1', 10000.0)
                    value.config.xmlUpdateFloat(item, 'x1')
                    value.config.set('y0', 0.0)
                    value.config.xmlUpdateFloat(item, 'y0')
                    value.config.set('y1', 10000.0)
                    value.config.xmlUpdateFloat(item, 'y1')
                if value.config.contains('type', '20ma'):
                    value.config.set('unit', '%')
                    value.config.xmlUpdate(item, 'unit')
                    value.config.set('y0', 0.0)
                    value.config.xmlUpdateFloat(item, 'y0')
                    value.config.set('y1', 100.0)
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

        for channel in range(self.NBCHANNELAO*self.config.boards):
            value=self.value('ao%d' % channel, unit='%', resolution=1, writable=True, commissionable=True)
            value.setRange(0, 100)
            value.config.set('default', None)
            value.config.set('invert', False)
            value.config.set('lrange', 0)
            value.config.set('hrange', 100)
            value.config.set('resolution', 1)
            value.config.set('min', 0)
            value.config.set('max', 100)
            value.config.set('ramp', 30)
            self.AO.append(value)

            item=xml.child(value.name)
            if item:
                if not item.getBool('enable', True):
                    value.disable()
                value.config.xmlUpdateFloat(item, 'default')
                value.config.xmlUpdateBool(item, 'invert')
                value.config.xmlUpdateFloat(item, 'lrange', vmin=0, vmax=100)
                value.config.xmlUpdateFloat(item, 'hrange', vmin=value.config.lrange, vmax=100)
                value.config.xmlUpdateFloat(item, 'resolution', vmin=0)
                value.config.xmlUpdateInt(item, 'min', vmin=0, vmax=100)
                value.config.xmlUpdateInt(item, 'max', vmin=value.config.min, vmax=100)
                value.config.xmlUpdateInt(item, 'ramp', vmin=0)
                value.config.xmlUpdateInt(item, 'ramp0', vmin=0)
                value.config.xmlUpdateInt(item, 'ramp1', vmin=0)
            value.resolution=value.config.resolution

    def getBoardConfigRegister0(self, board):
        return 35+(17*board)

    def poweronDI(self):
        pass

    def poweronDO(self):
        for board in range(self.config.boards):
            configRegister0=self.getBoardConfigRegister0(board)
            channel0=board*self.NBCHANNELDO
            data=0x0
            for channel in range(self.NBCHANNELDO):
                value=self.DO[channel0+channel]
                if value.config.default is not None:
                    state=value.config.default
                    if value.config.invert:
                        state=not state

                    if state:
                        data |= (0b01 << 2*channel)
                    else:
                        data |= (0b00 << 2*channel)
                else:
                    data |= (0b10 << 2*channel)

            self.writeRegistersIfChanged(configRegister0+8, data)

    def poweronAI(self):
        for board in range(self.config.boards):
            configRegister0=self.getBoardConfigRegister0(board)
            channel0=board*self.NBCHANNELAI
            for channel in range(self.NBCHANNELAI):
                value=self.AI[channel0+channel]
                data=0x0
                if value.config.type is not None:
                    if value.config.type=='+pt1000':
                        data |= 0b11
                        data |= (0b10 << 6)
                        value.unit='C'
                    elif value.config.type=='+pt100':
                        data |= 0b11
                        data |= (0b01 << 6)
                        value.unit='C'
                    elif value.config.type=='ntc':
                        data |= 0b00
                        data |= (0b01 << 6)
                        value.unit='C'
                    elif value.config.type=='+ni1000':
                        data |= 0b11
                        data |= (0b11 << 6)
                        value.unit='C'
                    elif '20ma' in value.config.type:
                        data |= 0b01
                        data |= (0b01 << 6)
                        value.unit='%'
                        if value.config.get('unit'):
                            value.unit=value.config.unit
                    elif '10v' in value.config.type:
                        data |= 0b10
                        data |= (0b00 << 6)
                        value.unit='V'
                        # allow custom unit
                        if value.config.get('unit'):
                            value.unit=value.config.unit
                    elif 'pot' in value.config.type:
                        data |= 0b10
                        data |= (0b00 << 6)
                        value.config.set('r2t', 'r')
                        value.unit='ohm'
                        # allow custom unit
                        if value.config.get('unit'):
                            value.unit=value.config.unit
                    elif value.config.type=='ohm':
                        data |= 0b11
                        data |= (0b00 << 6)
                        value.config.set('r2t', 'r')
                        value.unit='ohm'
                    elif value.config.type=='ohm10k':
                        data |= 0b00
                        data |= (0b00 << 6)
                        value.config.set('r2t', 'r')
                        value.unit='ohm'
                    elif value.config.type in ['pt1000', 'pt100', 'ni1000', 'ni1000-5k']:
                        # the conversion will be made by the mbio processor
                        # so, the ai channel is set to "ohm" mode
                        data |= 0b11
                        data |= (0b00 << 6)
                        value.config.set('r2t', value.config.type)
                        value.unit='C'
                else:
                    # +PT1000
                    value.config.type='pt1000'
                    data |= 0b11
                    data |= (0b00 << 6)
                    value.config.set('r2t', value.config.type)
                    value.unit='C'

                self.writeRegistersIfChanged(configRegister0+0+channel, data)

    def poweronAO(self):
        for board in range(self.config.boards):
            configRegister0=self.getBoardConfigRegister0(board)
            channel0=board*self.NBCHANNELAO
            for channel in range(self.NBCHANNELAO):
                value=self.AO[channel0+channel]

                # default value
                data=0x0
                if value.config.default is not None:
                    v=self.AO_state2raw(value, value.config.default) / 100.0
                    data |= (int(v) & 0xff)
                    # self.logger.warning('%s %d' %(value, v))
                else:
                    data |= (0b1 << 8)
                self.writeRegistersIfChanged(configRegister0+9+channel, data)

                # ramp
                data=0x0
                v0=max(min(value.config.ramp0 or value.config.ramp or 0, 255), 0)
                v1=max(min(value.config.ramp1 or value.config.ramp or 0, 255), 0)
                data=(v1 & 0xff) | ((v0 & 0xff) << 8)
                self.writeRegistersIfChanged(configRegister0+13+channel, data)

    def poweron(self):
        self.poweronDI()
        self.poweronDO()
        self.poweronAI()
        self.poweronAO()

        # set number of SIO boards
        self.writeRegistersIfChanged(172, self.config.boards)

        if self.config.watchdog is not None and self.config.watchdog>0:
            data=max(min(int(self.config.watchdog), 255), 0)
            self.writeRegistersIfChanged(171, data & 0xff)
        else:
            self.writeRegistersIfChanged(171, 0)

        return True

    def poweronsave(self):
        self.writeRegisters(199, 0xAAAA)

    def isreadytorun(self):
        r=self.readHoldingRegisters(199)
        if r and r[0]==0x5555:
            return True
        return False

    def poweroff(self):
        return True

    def refreshDI(self):
        r=self.readDiscreteInputs(0, 8*self.config.boards)
        if r:
            for board in range(self.config.boards):
                channel0=board*self.NBCHANNELDI
                for channel in range(self.NBCHANNELDI):
                    value=self.DI[channel0+channel]
                    state=r[board*8+channel]
                    if value.config.invert:
                        state=not state
                    value.updateValue(state)

    def refreshDO(self):
        r=self.readCoils(0, 8*self.config.boards)
        if r:
            self.BUZZER.updateValue(r[7])
            for board in range(self.config.boards):
                channel0=board*self.NBCHANNELDO
                for channel in range(self.NBCHANNELDO):
                    value=self.DO[channel0+channel]
                    state=r[board*8+channel]
                    if value.config.invert:
                        state=not state
                    value.updateValue(state)

                self.LEDR[board].updateValue(r[board*8+4])
                self.LEDG[board].updateValue(r[board*8+5])
                self.LEDB[board].updateValue(r[board*8+6])

    def refreshAI(self):
        r=self.readInputRegisters(0, self.config.boards*self.NBCHANNELAI)
        if r:
            for board in range(self.config.boards):
                channel0=board*self.NBCHANNELAI
                r0=self.NBCHANNELAI*board
                for channel in range(self.NBCHANNELAI):
                    value=self.AI[channel0+channel]
                    data=r[r0+channel]/10.0

                    try:
                        # value offset (expressed in measure unit : V or ohms)
                        data+=value.config.voffset
                    except:
                        pass

                    try:
                        # trap internal ohm->specific conversion curves
                        if value.config.r2t:
                            data=self.r2t(value.config.r2t, data)
                            # self.logger.warning(data)
                    except:
                        pass

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

    def refreshAO(self):
        r=self.readInputRegisters(64, self.config.boards*self.NBCHANNELAO)
        if r:
            for board in range(self.config.boards):
                channel0=board*self.NBCHANNELAO
                r0=self.NBCHANNELAO*board
                for channel in range(self.NBCHANNELAO):
                    value=self.AO[channel0+channel]
                    state=self.AO_raw2state(value, r[r0+channel])
                    value.updateValue(state)

    def refresh(self):
        if self.isTimeout(self._timeoutRefreshDI):
            self._timeoutRefreshDI=self.timeout(2.0)
            self.refreshDI()
            self.microsleep()

        if self.isTimeout(self._timeoutRefreshDO):
            self._timeoutRefreshDO=self.timeout(5.0)
            self.refreshDO()
            self.microsleep()

        if self.isTimeout(self._timeoutRefreshAI):
            self._timeoutRefreshAI=self.timeout(2.0)
            self.refreshAI()
            self.microsleep()

        if self.isTimeout(self._timeoutRefreshAO):
            self._timeoutRefreshAO=self.timeout(5.0)
            self.refreshAO()
            self.microsleep()

        if self.isTimeout(self._timeoutRefreshSlow):
            self._timeoutRefreshSlow=self.timeout(15)
            # for board in range(self.config.boards):
            r=self.readInputRegisters(98, 11)
            if r:
                value=self.T
                value.updateValue(float(r[9])/100.0)
                value=self.UPTIME
                value.updateValue((r[2]+r[3]*60+r[4]*3600+r[5]*86400)/3600.0)

        return 1.0

    def sync(self):
        for board in range(self.config.boards):
            self.microsleep()
            channel0=board*self.NBCHANNELDO
            for channel in range(self.NBCHANNELDO):
                value=self.DO[channel0+channel]
                if not value.isEnabled():
                    continue
                if value.isPendingSync():
                    self.signalRefresh(0.1)
                    state=value.toReachValue
                    if value.config.invert:
                        state=not state
                    self.writeCoils(board*8+channel, state)
                    value.clearSync()
                    self._timeoutRefreshDO=0

            value=self.LEDR[board]
            if value.isPendingSync():
                self.writeCoils(board*8+4, value.toReachValue)
                value.clearSync()
                self.signalRefresh(0.1)
            value=self.LEDG[board]
            if value.isPendingSync():
                self.writeCoils(board*8+5, value.toReachValue)
                value.clearSync()
                self.signalRefresh(0.1)
            value=self.LEDB[board]
            if value.isPendingSync():
                self.writeCoils(board*8+6, value.toReachValue)
                value.clearSync()
                self.signalRefresh(0.1)

        value=self.BUZZER
        if value.isPendingSync():
            self.writeCoils(7, value.toReachValue)
            value.clearSync()
            self._timeoutRefreshSlow=0
            self.signalRefresh(0.1)

        for board in range(self.config.boards):
            self.microsleep()
            channel0=board*self.NBCHANNELAO
            for channel in range(self.NBCHANNELAO):
                value=self.AO[channel0+channel]
                if not value.isEnabled():
                    continue
                if value.isPendingSync():
                    self.signalRefresh(1.0)
                    raw=self.AO_state2raw(value, value.toReachValue)
                    if self.writeRegisters(channel0+channel, raw):
                        # Write the corresponding MANUAL flag in the device
                        v=value.isManual() or value.isRemoteManual()
                        if self.writeCoils(64+channel0+channel, v):
                            value.clearSync()
                            self._timeoutRefreshAO=self.timeout(1.0)

        return True

    def off(self):
        for channel in range(self.NBCHANNELDO):
            self.DO[channel].off()

    def on(self):
        for channel in range(self.NBCHANNELDO):
            self.DO[channel].on()

    def toggle(self):
        for channel in range(self.NBCHANNELDO):
            self.DO[channel].toggle()
        for channel in range(self.NBCHANNELAO):
            if self.AO[channel].value:
                self.AO[channel].set(0)
            else:
                self.AO[channel].set(100)

    def probe(self):
        self.logger.debug('Probing device address %d with modbus TCP' % self.address)
        r=self.readInputRegisters(98, 1)
        if r and (r[0] & 0xFF00) == 0xA500:
            data={'version': str(r[0] & 0xff),
                  'model': 'SIO'}

            r=self.readInputRegisters(104, 3)
            if r:
                mac='%02x:%02x:%02x:%02x:%02x:%02x' % (r[0] >> 8, r[0] & 0xff,
                    r[1] >> 8, r[1] & 0xff,
                    r[2] >> 8, r[2] & 0xff)

                data['mac']=self.getMBIO().normalizeMAC(mac)
                self.logger.warning(data)
                return data

        return None


class SIOConfigurator(object):
    def __init__(self, host, token=None, logger=None):
        self._host=host
        self._token=token or 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'
        self._logger=logger
        self._config={}
        self._updated=False
        self.reset()

    @property
    def logger(self):
        return self._logger

    def reset(self):
        self._config={}
        self._updated=False

    @property
    def MAC(self):
        try:
            self.connect()
            return self._config['info']['mac']
        except:
            pass

    @property
    def IP(self):
        try:
            self.connect()
            return self._config['lan']['staticip']
        except:
            pass

    @property
    def MASK(self):
        try:
            self.connect()
            return self._config['lan']['staticnetmask']
        except:
            pass

    @property
    def GW(self):
        try:
            self.connect()
            return self._config['lan']['staticnetgw']
        except:
            pass

    @property
    def version(self) -> Version:
        try:
            self.connect()
            return Version(self._config['info']['swversion'])
        except:
            pass

    @property
    def hwversion(self) -> Version:
        try:
            self.connect()
            return Version(self._config['info']['hwversion'])
        except:
            pass

    def isDHCP(self):
        try:
            self.connect()
            if self._config['lan']['dhcp']:
                return True
        except:
            pass
        return False

    def isConnected(self):
        try:
            if self._config['info']['mac']:
                return True
        except:
            pass
        return False

    def url(self, path=None):
        url='http://%s/api/v1' % self._host
        if path:
            url += '/%s' % path
        return url

    def post(self, path, data=None):
        try:
            url=self.url(path)
            headers={'api_token': self._token}
            proxies = { 'http': '', 'https': '' }
            if data is None:
                data={}

            r=requests.post(url, headers=headers, json=data, verify=False, timeout=2.0, proxies=proxies)
            if r and r.ok:
                data=r.json()
                if data and data['status']=='success':
                    return True
        except:
            pass

    def get(self, path, data=None):
        try:
            url=self.url(path)
            headers={'api_token': self._token}
            proxies = { 'http': '', 'https': '' }
            if data is None:
                data={}

            r=requests.get(url, headers=headers, params=data, verify=False, timeout=2.0, proxies=proxies)
            if r and r.ok:
                data=r.json()
                return data
        except:
            pass

    def connect(self):
        if self.isConnected():
            return True

        config=self.get('system/info')
        if config:
            try:
                if config['info']['mac'] and config['info']['hwversion']:
                    self._config=config
                    return True
            except:
                pass
        return False

    def disconnect(self):
        self.reset()

    def __del__(self):
        self.disconnect()

    def isUpdated(self):
        return self._updated

    def reboot(self):
        if self.connect():
            api='system/reboot'
            if self.post(api):
                return True
        return False

    def setDHCP(self):
        if self.connect():
            if not self.isDHCP():
                api='system/lan'
                data=self.get(api)
                if data and not data['dhcp']:
                    if self.post(api, {'lan': {'dhcp': True}}):
                        self._updated=True
                        return True
        return False

    def setFixedIP(self, ip, mask, gw):
        if self.connect():
            try:
                n=ipcalc.Network('%s/%s' % (ip, mask))
                ip=n.to_tuple()[0]
                mask=str(n.netmask())
                if not self.isDHCP() and self.IP==ip and self.MASK==mask and self.GW==gw:
                    return True

                api='system/lan'
                config={'lan': {'dhcp': False, 'staticip': ip, 'staticnetmask': mask, 'staticgateway': gw}}
                if self.post(api, data=config):
                    self._updated=True
                    return True
            except:
                pass

        return False

    def upgrade(self, url):
        if url and self.connect():
            api='system/update'
            if self.post(api, {'url': url}):
                return True
        return False

    def dump(self):
        if self.connect():
            pprint.pprint(self._config)


class SIOScanner(MBIONetworkScanner):
    def onInit(self):
        self._token=None
        self._firmware=None

    @property
    def firmware(self):
        if self._firmware:
            return self._firmware['version']
        return None

    def extractFirmwareVersion(self, data) -> dict:
        if data:
            version={}

            matches=re.findall(b'FWMODEL=\\[SIO\\]', data)
            if matches:
                matches=re.findall(b'FWVERSION=\\[([0-9]+\\.[0-9]+\\.[0-9]+)\\]', data)
                if matches:
                    version['software']=Version(matches[0].decode())
                    return version

        self.logger.error('Unable to extract SIO firmware version')
        return None

    def downloadFirmware(self, fname=None):
        url='~netupdate/firmware/sio/sio.bin'
        fname=fname or '/tmp/sio.bin'
        if self.getMBIO().downloadFile(url, fname):
            data=self.mbio.wsGetFileContent(fname)
            version=self.extractFirmwareVersion(data)
            if version:
                return version
        return None

    def retrieveFirmware(self, download=False) -> Version:
        fname='sio.bin'
        falias='sio-firmware.bin'
        fpath='/tmp/%s' % fname
        p=pathlib.Path(fpath)

        if download or not p.is_file():
            self.downloadFirmware('/tmp/%s' % fname)

        url=self.mbio.wsExposeFile('/tmp/%s' % fname, alias=falias)
        if not url:
            url=self.mbio.wsExposeFile('/etc/sysconfig/digimat/firmware/%s' % fname, alias=falias)

        data=self.mbio.wsGetFileContent(falias)
        version=self.extractFirmwareVersion(data)

        if version:
            self._firmware={'name': falias, 'url': url,
                            'version': version['software']}
            self.logger.info('Found SIO firmware %s' % self._firmware)

        # this may contain a "huge" amount of RAM (>800kB)
        del data

        return self._firmware

    def upgrade(self, host, force=False):
        result=False
        firmware=self.retrieveFirmware()
        if firmware:
            c=self.configurator(host)
            if c and c.connect():
                if firmware['version']>c.version or force:
                    self.logger.info('Requesting SIO device %s [%s:%s] firmware upgrade...' %
                        (host, c.version, c.hwversion))
                    if c.upgrade(self._firmware['url']):
                        result=True
                else:
                    self.logger.warning('No valid firmware found for SIO device %s [%s:%s]' %
                        (host, c.version, c.hwversion))
                c.disconnect()
                return result
        return False

    def upgradeAll(self, fname=None):
        if not self._hosts:
            self.scan()
        if self._hosts:
            for host in self._hosts.keys():
                self.upgrade(host)

    def setToken(self, token):
        if token:
            self._token=token

    def configurator(self, host):
        return SIOConfigurator(host, token=self._token, logger=self.logger)

    def probe(self, host):
        hostid=None
        c=self.configurator(host)
        if c.connect():
            hostid=self.mbio.normalizeMAC(c.MAC)
        c.disconnect()
        return hostid

    def resetmbiogateway(self, host):
        try:
            gateway=self.getMBIO().gateway(host)
            if gateway is not None:
                gateway.reset()
                return True
        except:
            pass
        return False

    def configureHostFromGateway(self, host, gateway):
        c=self.configurator(host)
        if c.connect():
            mask=self.getMBIO().netmask()
            if mask is not None:
                if c.isDHCP() or c.IP!=gateway.host or c.MASK!=mask:
                    # self.logger.debug(c._config)
                    gw=self.getMBIO().gw
                    self.logger.warning('Reconfiguring SIO Gateway %s -> %s/%s/%s...' % (gateway.MAC, gateway.host, mask, gw))
                    self.getMBIO().beep()
                    c.setFixedIP(gateway.host, mask, gw)

                    # TODO: set RS485 and other things...

                    # Try to auto-upgrade firmware
                    if self.upgrade(host):
                        # Device reboot will be automatic
                        self.sleep(2)
                        self.logger.warning('Restarting SIO Gateway %s...' % (gateway.host))
                        gateway.reset()
                        return

                    if c.isUpdated():
                        self.logger.warning('Rebooting updated SIO Gateway %s...' % (gateway.MAC))
                        c.reboot()
                        self.sleep(2)
                        self.logger.warning('Restarting SIO Gateway %s...' % (gateway.host))
                        # Restart mbio gateway
                        gateway.reset()

    def __repr__(self):
        if self.firmware:
            return '%s(%u hosts, firmware %s)' % (self.__class__.__name__,
                self.count(), str(self.firmware))
        else:
            return super().__repr__()

if __name__ == "__main__":
    pass
