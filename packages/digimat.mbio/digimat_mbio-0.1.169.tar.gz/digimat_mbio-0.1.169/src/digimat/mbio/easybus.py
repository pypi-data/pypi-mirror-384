#!/bin/python

from __future__ import annotations


from .xmlconfig import XMLConfig
from .gateway import MBIOGateway
from .device import MBIODevice


# VAV: setpoint (%) : 2V=0%=vmin, 10V=100%=vmax
# feedback (%) : 0V=closed, 2V-10V = %vnom


class MBIOGatewayEasybus(MBIOGateway):
    def onInit(self):
        self.GROUP={}

    def loadDevices(self, xml: XMLConfig):
        try:
            bus=xml.children('bus')
            if bus:
                for b in bus:
                    if not b.getBool('enable', True):
                        continue

                    address=b.getInt('address')
                    try:
                        if self.device(address):
                            self.logger.error('Duplicate DEVICE declaration GW%s[%d]' % (self.key, address))
                            continue

                        MBIODeviceEasybusMaster(self, address, xml=b)
                    except:
                        self.logger.error('Error declaring DEVICE GW:%s (%s)' % (self.key, b.tostring()))
        except:
            self.logger.exception('loadDevices(GW:%s)' % self.key)

    def declareDeviceFromName(self, vendor, model, address, xml: XMLConfig = None):
        raise NotImplementedError('declareDeviceFromName')

    def probe(self, address):
        try:
            self.logger.debug('Probing device address %d' % address)
            self.checkIdleAfterSend()
            r=self._client.read_input_registers(0, 10, slave=address)
            self.signalMessageTransmission()
            if r and not r.isError():
                regs=r.registers
                if regs[5]>0:
                    data={'address': address,
                        'vendor': 'Easybus3',
                        'model': 'Easy-M',
                        'version': str(regs[5])}
                    self.logger.info('Found device [%s] [%s] %s at address %d' %
                                    (data['vendor'], data['model'], data['version'], address))
                    return data
        except:
            pass

    def group(self, ccf):
        try:
            group=ccf['group']
            if group:
                return self.GROUP[group.lower()]
        except:
            pass

    def addToGroup(self, group, ccf):
        if group and ccf:
            if not self.group(ccf):
                group=group.lower()
                data={'ccf': [],
                      'open': False, 'closed': False, 'smoke': False, 'error': False, 'cmd': None,
                      'values': {}}
                data['values']['open']=self.valueDigital('ccf%s_open' % group, commissionable=True)
                data['values']['closed']=self.valueDigital('ccf%s_closed' % group, commissionable=True)
                data['values']['error']=self.valueDigital('ccf%s_err' % group)
                data['values']['smoke']=self.valueDigital('ccf%s_smoke' % group)
                data['values']['cmd']=self.valueDigital('ccf%s_cmd' % group, writable=True, commissionable=True)
                self.GROUP[group]=data
            self.GROUP[group]['ccf'].append(ccf)

    def groupRefresh(self):
        if self.GROUP:
            for group in self.GROUP.values():
                if group['ccf']:
                    group['open']=True
                    group['closed']=True
                    group['smoke']=False
                    group['error']=False
                    for ccf in group['ccf']:
                        if ccf['open'] is not True:
                            group['open']=False
                        if ccf['closed'] is not True:
                            group['closed']=False
                        if ccf['smoke']:
                            group['smoke']=True
                        if ccf['error']:
                            group['error']=True

                    error=group['error']
                    group['values']['open'].updateValue(group['open'])
                    group['values']['open'].setError(error)
                    group['values']['closed'].updateValue(group['closed'])
                    group['values']['closed'].setError(error)
                    group['values']['smoke'].updateValue(group['smoke'])
                    group['values']['smoke'].setError(error)
                    group['values']['error'].updateValue(error)

    def configurator(self):
        return None

    def signalSync(self, delay=0):
        for device in self.devices:
            device.sync()


class MBIODeviceEasybusMaster(MBIODevice):
    def buildKey(self, gateway, address):
        return '%sb%d' % (gateway.key, address)

    def normalizeResistor(self, r):
        # 0..1600 ohms as 0..10V equivalent
        # allow usage of the Digimat-3 conversion formulas
        if (r>=0 and r<=1600):
            return r/1600.0 * 10.0
        return None

    def pt100(self, r):
        f=self.normalizeResistor(r)
        if f is not None:
            f=0.0769632 * (f**3) + 0.2946681 * (f**2) + 6.98698436 * (f) - 3.59148152
            return f*550.0/10.0-50.0

    def pt1000(self, r):
        f=self.normalizeResistor(r)
        if f is not None:
            f=0.00011683 * (f**3) + 0.01047814 * (f**2) + 1.90211508 * (f) - 9.82603617
            return f*200.0/10.0-50.0

    def ni1000_tk5000(self, r):
        f=self.normalizeResistor(r)
        if f is not None:
            f=0.00354046 * (f**3) - 0.1557009 * (f**2) + 3.65814114 * (f) - 14.70477509
            return f*170.0/10.0-50.0

    def ni1000(self, r):
        f=self.normalizeResistor(r)
        if f is not None:
            f=0.00229944 * (f**3) - 0.10339928 * (f**2) + 2.74480809 * (f) - 10.73874259
            return f*170.0/10.0-50.0

    def r2t(self, stype, r):
        if stype=='pt1000':
            return self.pt1000(r)
        if stype=='pt100':
            return self.pt100(r)
        if stype=='ni1000':
            return self.ni1000(r)
        if stype=='ni1000_5k':
            return self.ni1000_tk5000(r)
        if stype=='ohm':
            return r

    def probe(self):
        self.logger.debug('Probing device address %d' % self.address)
        r=self.readInputRegisters(0, 10)
        if r and r[5]>0:
            data={'version': str(r[5]),
                  'vendor': 'Easybus3',
                  'model': 'Easy-M'}
            return data

    def load(self, xml: XMLConfig):
        if xml:
            try:
                self.onLoad(xml)
            except:
                self.logger.exception('%s:%s:load()' % (self.__class__.__name__, self.key))

    def onInit(self):
        self.setPingInputRegister(0)
        self.valueDigital('run')
        self.valueDigital('fire')
        self.value('slaves', unit=0xff)
        self.value('slaveserr', unit=0xff)
        self.value('cycle', unit='ms', resolution=5.0)
        self.CCF={}
        self.VAV={}

    def ccf(self, address=None):
        if self.CCF:
            if address is None:
                return self.CCF.values()

            try:
                return self.CCF[int(address)]
            except:
                pass
        return {}

    def vav(self, address=None):
        if self.VAV:
            if address is None:
                return self.VAV.values()
        try:
            return self.VAV[int(address)]
        except:
            pass
        return {}

    def onLoadCCF(self, xml: XMLConfig):
        for ccf in xml.children('ccf'):
            if not ccf.getBool('enable', True):
                continue

            hidden=ccf.getBool('hidden')
            address=ccf.getInt('address')
            group=ccf.get('group')
            if address is not None:
                data={'type': 'ccf', 'address': address, 'group': None, 'hidden': hidden,
                      'open': False, 'closed': False, 'error': False, 'smoke': False, 'cmd': None,
                      'info': None, 'state': 0,
                      'values': {'cmd': None}}

                # CCF that is not grouped can't be hidden (must have a cmd value)
                if not group or not hidden:
                    data['values']['open']=self.valueDigital('ccf%d_open' % address, commissionable=True)
                    data['values']['closed']=self.valueDigital('ccf%d_closed' % address, commissionable=True)
                    data['values']['error']=self.valueDigital('ccf%d_err' % address)
                    data['values']['smoke']=self.valueDigital('ccf%d_smoke' % address)
                if group:
                    data['group']=group
                    self.gateway.addToGroup(group, data)
                else:
                    if not hidden:
                        data['values']['cmd']=self.valueDigital('ccf%d_cmd' % address, writable=True, commissionable=True)

                self.CCF[address]=data

    def onLoadVAV(self, xml: XMLConfig):
        for vav in xml.children('vav'):
            if not vav.getBool('enable', True):
                continue

            address=vav.getInt('address')
            if address is not None:
                data={'type': 'vav', 'address': address,
                    'sensors': {},
                    'index': {}}

                for device in vav.children('device'):
                    index=device.getInt('address')
                    if index is not None and index in [0, 1]:
                        d={}

                        key='vav%d.%d' % (address, index)
                        d['values']={}

                        d['vmin']=device.getFloat('vmin', vmin=0)
                        d['vmax']=device.getFloat('vmax', vmin=d['vmin'])
                        d['vnom']=device.getFloat('vnom', vmin=d['vmax'])

                        if d['vnom'] is None or d['vmin'] is None or d['vmax'] is None:
                            continue

                        if device.getBool('showconfig', False):
                            d['values']['vmin']=self.constant('%s_vmin' % key, d['vmin'], 'm3/h')
                            d['values']['vmax']=self.constant('%s_vmax' % key, d['vmax'], 'm3/h')
                            d['values']['vnom']=self.constant('%s_vnom' % key, d['vnom'], 'm3/h')

                        d['values']['sp']=self.value('%s_sp' % key, unit='%', writable=True, resolution=1.0, commissionable=True)
                        d['values']['v']=self.value('%s_v' % key, unit='m3/h', resolution=0.1)
                        d['values']['vr']=self.value('%s_vr' % key, unit='%', resolution=1.0, commissionable=True)

                        data['index'][index]=d

                for n in range(4):
                    data['sensors'][n]={'type': None}

                for sensor in vav.children('sensor'):
                    if not sensor.getBool('enable', True):
                        continue

                    n=sensor.getInt('address')
                    if n is not None and data['sensors'].get(n):
                        stype=sensor.get('type', 'pt1000')
                        offset=sensor.getFloat('offset', 0.0)
                        resolution=sensor.getFloat('resolution', 0.1)

                        if stype in ['pt100', 'pt1000', 'ni1000', 'ni1000_5k']:
                            value=self.value('%s_ai%d' % (key, n), unit='C', resolution=resolution, commissionable=True)
                            data['sensors'][n]={'address': n, 'type': stype, 'offset': offset, 'value': value}
                        elif stype=='ohm':
                            value=self.value('%s_ai%d' % (key, n), unit='ohm', resolution=resolution, commissionable=True)
                            data['sensors'][n]={'address': n, 'type': stype, 'offset': offset, 'value': value}
                        elif stype=='10v':
                            unit=sensor.get('unit', 'V')
                            y0=sensor.getFloat('y0', 0.0)
                            y1=sensor.getFloat('y1', 10.0)
                            value=self.value('%s_ai%d' % (key, n), unit=unit, resolution=resolution, commissionable=True)
                            data['sensors'][n]={'address': n, 'type': stype, 'offset': offset, 'y0': y0, 'y1': y1, 'value': value}
                        elif stype=='pot':
                            unit=sensor.get('unit', 'C')
                            x0=sensor.getFloat('x0', 0.0)
                            y0=sensor.getFloat('y0', -3.0)
                            x1=sensor.getFloat('x1', 1000.0)
                            y1=sensor.getFloat('y1', 3.0)
                            value=self.value('%s_ai%d' % (key, n), unit=unit, resolution=resolution, commissionable=True)
                            data['sensors'][n]={'address': n, 'type': stype, 'offset': offset,
                                                'x0': x0, 'x1': x1, 'y0': y0, 'y1': y1,
                                                'value': value}

                self.VAV[address]=data

    def onLoad(self, xml: XMLConfig):
        self.onLoadCCF(xml)
        self.onLoadVAV(xml)

    def setbit(self, value, bit):
        bit=(1 << bit)
        return value | bit

    def clearbit(self, value, bit):
        bit=(1 << bit)
        return (value & ~(bit)) & 0xffff

    def poweron(self):
        # Setup VAV Sensors
        if self.VAV:
            r=self.readHoldingRegisters(426, 32)
            if r:
                for vav in self.vav():
                    if vav['sensors']:
                        for sensor in vav['sensors'].values():
                            if sensor['type'] is not None:
                                n=((vav['address']-1) // 4)
                                sh=((vav['address']-1) % 4) * 4
                                sh+=sensor['address']
                                if sensor['type']=='10v':
                                    r[n]=self.clearbit(r[n], sh)
                                else:
                                    r[n]=self.setbit(r[n], sh)

                self.writeRegistersIfChanged(324, r)

        return True

    def poweroff(self):
        return True

    def powerlost(self):
        # TODO: set CCF to ERR O=OFF, C=OFF
        pass

    def refreshCCF(self):
        if not self.CCF:
            return

        r=self.readInputRegisters(300, 32)
        if r:
            for ccf in self.ccf():
                self.microsleep()

                address=ccf['address']
                n=((address-1) // 4)
                sh=(address-1) % 4
                v=((r[n]) >> (4*sh)) & 0xf

                # bits 3210:FOCE (F=Fire, O=Open, C=Closed, E=Error)
                ccf['state']=v

                ccf['open']=False
                ccf['closed']=False
                ccf['error']=False
                ccf['smoke']=False

                if v & 0x1:
                    ccf['error']=True
                if v & 0x2:
                    ccf['closed']=True
                if v & 0x4:
                    ccf['open']=True
                if v & 0x8:
                    ccf['smoke']=True

                # This field is generic and refreshed globally
                if ccf['info'] is not None:
                    if ccf['info'] not in [5, 6] or ccf['info'] & 0x80:
                        ccf['error']=True

                # Update values
                error=ccf['error']
                if not ccf['hidden']:
                    ccf['values']['error'].updateValue(error)
                    ccf['values']['open'].updateValue(ccf['open'])
                    ccf['values']['open'].setError(error)
                    ccf['values']['closed'].updateValue(ccf['closed'])
                    ccf['values']['closed'].setError(error)
                    ccf['values']['smoke'].updateValue(ccf['smoke'])
                    ccf['values']['smoke'].setError(error)
                    if ccf['values']['cmd'] is not None:
                        ccf['values']['cmd'].setError(error)
        else:
            if not ccf['hidden']:
                ccf['values']['error'].updateValue(True)
            for value in ccf['values'].values():
                if value is not None:
                    value.setError(True)

        self.gateway.groupRefresh()

    def minmax(self, v, vmin, vmax):
        if v<vmin:
            return vmin
        if v>vmax:
            return vmax
        return v

    def refreshVAV(self):
        if not self.VAV:
            return

        for vav in self.vav():
            self.microsleep()

            address=vav['address']
            n=(address-1)*2
            base=460
            r=self.cacheReadInputRegisters(base+n, 2, 64, base)
            if r:
                error=False
                if vav['info'] is not None:
                    if vav['info'] not in [4] or vav['info'] & 0x80:
                        error=True

                # update flow
                for index in range(2):
                    device=vav['index'].get(index)
                    if device is None:
                        continue

                    vmin=device['vmin']
                    vmax=device['vmax']
                    vnom=device['vnom']

                    v=r[index]/100.0
                    if v>0.5:
                        v=self.minmax(v, 2.0, 10.0)
                        v=(v-2.0)/8.0*vnom

                        vr=(v-vmin)/(vmax-vmin)*100.0
                        vr=self.minmax(vr, 0.0, 100.0)
                    else:
                        v=0
                        vr=0

                    device['values']['vr'].updateValue(vr)
                    device['values']['vr'].setError(error)
                    device['values']['v'].updateValue(v)

                    # update setpoint
                    rsp=self.cacheReadHoldingRegisters(base+n, 2, 64, base)
                    if rsp:
                        v=rsp[0]
                        if v>0:
                            v=(v/100.0-2.0)/8.0*100.0
                        device['values']['sp'].updateValue(v)

                # update sensors
                for sensor in vav['sensors'].values():
                    if sensor['type']:
                        n=(address-1)*2
                        base=716
                        index=sensor['address']
                        r=self.cacheReadInputRegisters(base+n+index, 1, 64, base)
                        if r:
                            if sensor['type']=='10v':
                                v=r[0]/65535.0*10.0
                                if v==0 or v==10.0:
                                    error=True
                                v=(sensor['y1']-sensor['y0'])*v+sensor['y0']
                                v+=sensor['offset']
                                sensor['value'].updateValue(v)
                                sensor['value'].setError(error)
                            elif sensor['type']=='ohm':
                                v=r[0]
                                if v==0 or v==65535.0:
                                    error=True
                                v+=sensor['offset']
                                sensor['value'].updateValue(v)
                                sensor['value'].setError(error)
                            elif sensor['type']=='pot':
                                v=r[0]
                                if v==0 or v==65535.0:
                                    error=True

                                v=self.minmax(v, sensor['x0'], sensor['x1'])
                                v=(v-sensor['x0'])
                                dy=sensor['y1']-sensor['y0']
                                dx=sensor['x1']-sensor['x0']
                                try:
                                    v=(dy/dx)*v+sensor['y0']
                                except:
                                    v=sensor['y0']

                                v+=sensor['offset']
                                sensor['value'].updateValue(v)
                                sensor['value'].setError(error)
                            else:
                                v=r[0]
                                if v==0 or v==65535.0:
                                    error=True
                                v=self.r2t(sensor['type'], r[0])
                                v+=sensor['offset']
                                sensor['value'].updateValue(v)
                                sensor['value'].setError(error)

    def refresh(self):
        self.cachePrune(5)

        r=self.readInputRegisters(0, 10)
        if r:
            self.values.slaves.updateValue(r[1])
            self.values.slaveserr.updateValue(r[2])
            self.values.fire.updateValue(r[0]==3)
            self.values.run.updateValue(r[0]==1)
            self.values.cycle.updateValue(r[4])

        r=self.readInputRegisters(10, 64)
        if r:
            for ccf in self.CCF.values():
                address=ccf['address']
                n=((address-1) // 2)
                sh=(address-1) % 2
                v=((r[n]) >> (8*sh)) & 0xff
                ccf['info']=v
            for vav in self.VAV.values():
                address=vav['address']
                n=((address-1) // 2)
                sh=(address-1) % 2
                v=((r[n]) >> (8*sh)) & 0xff
                vav['info']=v

        # Try to auto-reset Easy-M mode to RUN
        # FIXME: good idea ? Not sure.
        r=self.readInputRegisters(0, 1)
        if r and r[0] in [0, 3]:
            self.writeHoldingRegisters(0, 1)

        self.refreshCCF()
        self.refreshVAV()
        return 3.0

    def syncCCF(self):
        # read actual cmd registers
        r=self.readHoldingRegisters(300, 8)
        if r:
            for ccf in self.ccf():
                address=ccf['address']
                n=((address-1) // 16)
                sh=(address-1) % 16

                cmd=ccf['values']['cmd']
                group=self.gateway.group(ccf)
                if group:
                    cmd=group['values']['cmd']

                if cmd.toReachValue is not None:
                    if cmd.toReachValue:
                        r[n] |= (1 << sh)
                    else:
                        r[n] = (r[n] & (~(1 << sh) & 0xffff))

            # update cmd registers
            if self.writeHoldingRegisters(300, r):
                for ccf in self.CCF.values():
                    if ccf['values']['cmd'] is not None:
                        ccf['values']['cmd'].clearSyncAndUpdateValue()
                for group in self.gateway.GROUP.values():
                    group['values']['cmd'].clearSyncAndUpdateValue()

    def syncVAV(self):
        for vav in self.vav():
            for index in range(2):
                device=vav['index'].get(index)
                if device is None:
                    continue
                value=device['values']['sp']
                address=vav['address']
                n=460+(address-1)*2+index
                if value.isPendingSync():
                    if value.toReachValue<0.5:
                        v=0
                    else:
                        v=(value.toReachValue/100.0*8.0+2.0)*100.0
                    if self.writeHoldingRegisters(n, int(v)):
                        value.clearSync()

    def sync(self):
        self.syncCCF()
        self.syncVAV()


if __name__ == "__main__":
    pass
