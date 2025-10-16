#!/bin/python

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .mbio import MBIO

from .items import Items
# from .config import MBIOConfig
from .xmlconfig import XMLConfig
from .device import MBIODevices, MBIODeviceGeneric

from .value import MBIOValues, MBIOValue, MBIOValueWritable
from .value import MBIOValueDigital, MBIOValueDigitalWritable
from .value import MBIOValueMultistate, MBIOValueMultistateWritable


import time
import threading
import socket

from prettytable import PrettyTable

from pymodbus.client import ModbusTcpClient
import pymodbus

import logging
# import ipcalc


# Modbus Clients Examples
# https://pymodbus.readthedocs.io/en/dev/source/examples.html

# TODO: remove binary encoder/decoder
# https://pymodbus.readthedocs.io/en/latest/source/client.html#client-response-handling
# value_int32 = client.convert_from_registers(rr.registers, data_type=client.DATATYPE.INT32)
# convert_to_registers()


# FORMAT = ('%(asctime)-15s %(threadName)-15s '          '%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
# logging.basicConfig(format=FORMAT)
# log = logging.getLogger()
# log.setLevel(logging.DEBUG)


class MBIOGateway(object):
    """MBIOGateway object, containing MBIOValues containing every MBIOValue"""
    def __init__(self, parent: MBIO, name, host, port=502, interface=None, timeout=2, retries=3, xml: XMLConfig = None):
        self._parent: MBIO = parent
        self._name=str(name).lower()
        if not name:
            name='gw%d' % parent.gateways.count()
        self._host=host
        self._model=None
        self._MAC=None
        self._password=None
        self._interface=interface
        self._port=port
        self._timeout=timeout
        self._retries=retries
        self._error=False

        self._key='%s' % self._name

        self._client: ModbusTcpClient=None
        self._timeoutClient=0
        self._timeoutIdleAfterSend=0

        self._devices=MBIODevices(parent.logger)
        self._values=MBIOValues(self, self._key, self.logger)
        self._sysvalues=MBIOValues(self, self.key, self.logger)
        self._sysComErr=MBIOValueDigital(self._sysvalues, 'comerr')

        self.logger.info('Declaring GW:%s', self.host)

        self._eventStop=threading.Event()

        self.load(xml)

        # loop=self.get_or_create_eventloop()
        loop=None

        # FIXME: daemon=True ?
        self._thread=threading.Thread(target=self.manager, args=(loop,))
        self.logger.info("Starting background GW:%s task" % self.host)
        self._thread.start()

        self.onInit()

        self.loadDevices(xml)

    # FIXME:
    def get_or_create_eventloop(self):
        try:
            import asyncio
            return asyncio.get_event_loop()
        except RuntimeError as ex:
            if "There is no current event loop in thread" in str(ex):
                self.logger.error("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return asyncio.get_event_loop()
            else:
                raise ex

    def onInit(self):
        pass

    def loadDevices(self, xml: XMLConfig):
        try:
            devices=xml.children('device')
            if devices:
                for d in devices:
                    if not d.getBool('enable', True):
                        continue

                    vendor=d.get('vendor')
                    model=d.get('model')
                    address=d.getInt('address')

                    if address is None:
                        if vendor=='digimat' and model=='sio':
                            address=0

                    try:
                        if self.device(address):
                            self.logger.error('Duplicate DEVICE declaration GW%s[%d]' % (self.key, address))
                            continue

                        self.declareDeviceFromName(vendor, model, address, xml=d)

                    except:
                        self.logger.exception('x')
                        self.logger.error('Error declaring DEVICE GW:%s (%s)' % (self.key, d.tostring()))

            item=xml.child('discover')
            if item:
                start=item.getInt('start', 1)
                end=item.getInt('end', 32)
                maxerrors=item.getInt('maxerrors', 3)
                self.discover(start, end, maxerrors)
        except:
            self.logger.exception('loadDevices(GW:%s)' % self.key)

    @property
    def parent(self) -> MBIO:
        return self._parent

    def getMBIO(self) -> MBIO:
        return self._parent

    @property
    def logger(self):
        return self._parent.logger

    @property
    def values(self):
        return self._values

    @property
    def sysvalues(self):
        return self._sysvalues

    def value(self, name, unit=0xff, default=None, writable=False, resolution=0.1, commissionable=False):
        key=self.values.computeValueKeyFromName(name)
        value=self.values.item(key)
        if value is None:
            if writable:
                value=MBIOValueWritable(self.values, name=name, unit=unit, default=default, resolution=resolution, commissionable=commissionable)
            else:
                value=MBIOValue(self.values, name=name, unit=unit, default=default, resolution=resolution, commissionable=commissionable)
        return value

    def valueDigital(self, name, default=None, writable=False, commissionable=False):
        key=self.values.computeValueKeyFromName(name)
        value=self.values.item(key)
        if value is None:
            if writable:
                value=MBIOValueDigitalWritable(self.values, name=name, default=default, commissionable=commissionable)
            else:
                value=MBIOValueDigital(self.values, name=name, default=default, commissionable=commissionable)
        return value

    def valueMultistate(self, name, vmax, vmin=0, default=None, writable=False, commissionable=False):
        key=self.values.computeValueKeyFromName(name)
        value=self.values.item(key)
        if value is None:
            if writable:
                value=MBIOValueMultistateWritable(self.values, name=name, vmax=vmax, vmin=vmin, default=default, commissionable=commissionable)
            else:
                value=MBIOValueMultistate(self.values, name=name, vmax=vmax, vmin=vmin, default=default, commissionable=commissionable)
        return value

    def configurator(self):
        # To be overriden
        pass

    def onLoad(self, xml: XMLConfig):
        pass

    def load(self, xml: XMLConfig):
        if xml:
            try:
                self._MAC=self.getMBIO().normalizeMAC(xml.get('mac'))
                self._model=xml.get('model')
                self._password=xml.get('password')
                if xml.isConfig('gateway'):
                    self.onLoad(xml)
            except:
                self.logger.exception('%s:%s:load()' % (self.__class__.__name__, self.key))

    @property
    def key(self):
        return self._key

    def timeout(self, delay):
        return time.time()+delay

    def isTimeout(self, t):
        if time.time()>=t:
            return True
        return False

    def isOpen(self):
        if self._client and self._client.is_socket_open():
            return True
        return False

    def open(self):
        if self._client is None:
            try:
                self.logger.info('Connecting to GW %s:%d (interface %s, timeout=%ds)' %
                    (self._host, self._port, self._interface, self._timeout))
                source=(self._interface, 0)
                if not self._interface:
                    source=None

                logger=logging.getLogger('pymodbus')
                if logger:
                    logger.setLevel(logging.CRITICAL)

                self._client=ModbusTcpClient(host=self._host, port=self._port,
                            # broadcast_enable=True,
                            # strict=True,
                            # name='GW(%s)' % self.name,
                            source_address=source,
                            reconnect_delay=1,
                            timeout=self._timeout,
                            retries=self._retries)

                self._client.connect()
                self._timeoutIdleAfterSend=0
            except:
                # self.logger.exception('open')
                pass

        if self._client:
            if not self._client.connected:
                self.logger.warning('Automatic client reconnect GW(%s)' % self.name)
                self._client.connect()
            return self._client

            # FIXME ------------------------------------------------------------------
            self.logger.error("Client %s isn't connected!" % self.name)
            try:
                if self.isTimeout(self._timeoutClient):
                    self._timeoutClient=self.timeout(15)
                    if self._client.connect():
                        return self._client
            except:
                # self.logger.exception("CONNECT()")
                pass
            # FIXME ------------------------------------------------------------------

    def close(self):
        try:
            if self._client is not None:
                self.logger.info('Connecting to GW %s:%d' % (self._host, self._port))
                self._client.close()
        except:
            pass
        self._client=None

    @property
    def client(self):
        return self.open()

    @property
    def name(self):
        return self._name

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def MAC(self):
        return self._MAC

    @property
    def model(self):
        return self._model

    @property
    def password(self):
        return self._password

    def probe(self, address):
        try:
            self.logger.debug('Probing modbus device address %d' % address)
            self.checkIdleAfterSend()
            r=self.client.read_device_information(slave=address)
            self.signalMessageTransmission()
            if r and not r.isError():
                data={'address': address,
                      'vendor': r.information[0].decode(),
                      'model': r.information[1].decode(),
                      'version': r.information[2].decode()}
                self.logger.info('Found device [%s] [%s] %s at address %d' %
                                 (data['vendor'], data['model'], data['version'], address))
                return data

            self.logger.warning('probe: %s' % r)
        except:
            pass

    # FIXME: implement a better MBIODevice class registration
    def declareDeviceFromName(self, vendor, model, address, xml: XMLConfig = None):
        try:
            address=int(address)
            model=model or 'unknown'

            if vendor and address>0:
                vendor=vendor.lower()
                model=model.lower()
                device=None

                # TODO: better design

                if 'metz' in vendor:
                    if 'di10' in model:
                        try:
                            from .metzconnect import MBIODeviceMetzConnectMRDI10
                            device=MBIODeviceMetzConnectMRDI10(self, address, xml=xml)
                        except:
                            self.logger.exception('device')
                    if 'di4' in model:
                        try:
                            from .metzconnect import MBIODeviceMetzConnectMRDI4
                            device=MBIODeviceMetzConnectMRDI4(self, address, xml=xml)
                        except:
                            self.logger.exception('device')
                    elif 'do4' in model:
                        try:
                            from .metzconnect import MBIODeviceMetzConnectMRDO4
                            device=MBIODeviceMetzConnectMRDO4(self, address, xml=xml)
                        except:
                            self.logger.exception('device')
                    elif 'aop4' in model or 'ao4' in model:
                        try:
                            from .metzconnect import MBIODeviceMetzConnectMRAO4
                            device=MBIODeviceMetzConnectMRAO4(self, address, xml=xml)
                        except:
                            self.logger.exception('device')
                    elif 'ai8' in model:
                        try:
                            from .metzconnect import MBIODeviceMetzConnectMRAI8
                            device=MBIODeviceMetzConnectMRAI8(self, address, xml=xml)
                        except:
                            self.logger.exception('device')

                elif 'belimo' in vendor:
                    if 'p22rth' in model:
                        try:
                            from .belimo import MBIODeviceBelimoP22RTH
                            device=MBIODeviceBelimoP22RTH(self, address, xml=xml)
                        except:
                            self.logger.exception('device')
                    if 'actuator' in model:
                        try:
                            from .belimo import MBIODeviceBelimoActuator
                            device=MBIODeviceBelimoActuator(self, address, xml=xml)
                        except:
                            self.logger.exception('device')

                elif 'digimat' in vendor:
                    if 'sio' in model:
                        try:
                            from .digimatsmartio import MBIODeviceDigimatSIO
                            device=MBIODeviceDigimatSIO(self, address, xml=xml)
                        except:
                            self.logger.exception('device')

                elif 'ebm' in vendor:
                    if 'base' in model:
                        try:
                            from .ebm import MBIODeviceEBM
                            device=MBIODeviceEBM(self, address, xml=xml)
                        except:
                            self.logger.exception('device')

                elif 'sensortec' in vendor:
                    if 'eld' in model:
                        try:
                            from .sensortec import MBIODeviceSensortecELD
                            device=MBIODeviceSensortecELD(self, address, xml=xml)
                        except:
                            self.logger.exception('device')
                    elif model=='el':
                        try:
                            from .sensortec import MBIODeviceSensortecEL
                            device=MBIODeviceSensortecEL(self, address, xml=xml)
                        except:
                            self.logger.exception('device')

                elif 'isma' in vendor:
                    if '4i4oh' in model:
                        try:
                            from .isma import MBIODeviceIsma4I4OH
                            device=MBIODeviceIsma4I4OH(self, address, xml=xml)
                        except:
                            self.logger.exception('device')
                    elif '4i4ohip' in model:
                        try:
                            from .isma import MBIODeviceIsma4I4OHIP
                            device=MBIODeviceIsma4I4OHIP(self, address, xml=xml)
                        except:
                            self.logger.exception('device')
                    elif '4u4ah' in model:
                        try:
                            from .isma import MBIODeviceIsma4U4AH
                            device=MBIODeviceIsma4U4AH(self, address, xml=xml)
                        except:
                            self.logger.exception('device')
                    elif '4u4ahip' in model:
                        try:
                            from .isma import MBIODeviceIsma4U4AHIP
                            device=MBIODeviceIsma4U4AHIP(self, address, xml=xml)
                        except:
                            self.logger.exception('device')

                elif 'generic' in vendor:
                    device=MBIODeviceGeneric(self, address, xml=xml)

                if device is None:
                    self.logger.error('Unable to create device %s/%s' % (vendor/model))

                return device
        except:
            pass

    def discover(self, start=1, end=32, maxerrors=3):
        devices=[]
        errors=0
        for address in range(start, end+1):
            data=self.probe(address)
            if data:
                if not self.device(address):
                    device=self.declareDeviceFromName(data['vendor'], data['model'], address)
                    if device:
                        devices.append(device)
                continue
            errors+=1
            maxerrors-=1
            if maxerrors>0 and errors>maxerrors:
                break
        return devices

    def ping(self, address):
        try:
            self.checkIdleAfterSend()
            r=self.client.diag_read_bus_message_count(slave=address)
            self.signalMessageTransmission()
            if r:
                if not r.isError():
                    return True
            self.logger.error('Unable to ping device %d' % address)
        except:
            pass
        return False

    def netPing(self, timeout=1.0):
        result=False
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect((self._host, self._port))
            result=True
        except:
            s.close()
        return result

    def stop(self):
        self.halt()
        self._eventStop.set()

    def waitForThreadTermination(self):
        self.stop()
        self._thread.join()
        self.close()

    def sleep(self, delay=1.0):
        try:
            if self._eventStop.is_set():
                return True
            return self._eventStop.wait(delay)
        except:
            pass

    def checkIdleAfterSend(self):
        while not self.isTimeout(self._timeoutIdleAfterSend):
            self.sleep(0.001)

    def signalMessageTransmission(self):
        # https://minimalmodbus.readthedocs.io/en/stable/serialcommunication.html
        # 19200bps->2ms
        self._timeoutIdleAfterSend=self.timeout(0.002)

    def signalSync(self, delay=0):
        # TODO: incomplete sync management in MBIOGateway (check MBIODevice)
        pass

    def manager(self, loop):
        try:
            if loop:
                # FIXME:
                self.logger.warning("DEBUG: INIT LOOP")
                import asyncio
                asyncio.set_event_loop(loop)
        except:
            pass

        while True:
            self.sleep(0.1)
            try:
                halted=True
                error=False
                for device in self._devices:
                    device.manager()
                    device.microsleep()
                    if device.isError():
                        error=True
                    if not device.isHalted():
                        halted=False

                self._error=error
                self._sysComErr.updateValue(self._error)

                if self._eventStop.is_set():
                    if halted:
                        self.logger.info("Exiting background GW:%s task" % self.host)
                        self.close()
                        return
            except:
                self.logger.exception("Background GW:%s task" % self.host)

    def isError(self):
        return self._error

    @property
    def devices(self):
        return self._devices

    def retrieveDevicesFromModel(self, vendor, model=None):
        try:
            devices=[]
            if self._devices:
                vendor=vendor.lower()
                model=model.lower()
                for device in self._devices:
                    if device.vendor.lower()==vendor and (model is None or device.model.lower()==model):
                        devices.append(device)
            return devices
        except:
            pass

    def device(self, did):
        return self._devices.item(did)

    def reset(self, address=None):
        if address is not None:
            try:
                self.device(address).reset()
            except:
                pass
        else:
            self._devices.reset()

    def resetHalted(self):
        self._devices.resetHalted()

    def halt(self, address=None):
        if address is not None:
            try:
                self.device(address).halt()
            except:
                pass
        else:
            self._devices.halt()

    def dump(self):
        if self._devices:
            t=PrettyTable()
            t.field_names=['ADR', 'Key', 'Vendor', 'Model', 'Version', 'Class', 'State', 'Error', 'Values', 'msg']
            t.align='l'
            for device in self._devices:
                msg='%d/%d' % (device._countMsg, device._countMsgErr)
                t.add_row([device.address, device.key, device.vendor, device.model, device.version,
                           device.__class__.__name__, device.statestr(), str(device.isError()), device.values.count(), msg])

        print(t.get_string(sortby="ADR"))

    def count(self):
        return len(self._devices)

    def __getitem__(self, key):
        return self.device(key)

    def __repr__(self):
        state='CLOSED'
        if self.isOpen():
            state='OPEN'
        return '%s(%s=%s:%d, %d devices, %s)' % (self.__class__.__name__, self.name, self.host, self.port, self.count(), state)

    def richstr(self):
        state='[bold red]CLOSED[/bold red]'
        if self.isOpen():
            state='[bold green]OPEN[/bold green]'
        return '[yellow]%s[/yellow]([bold]%s[/bold]=%s:%d, %d devices, %s)' % (self.__class__.__name__, self.name, self.host, self.port, self.count(), state)


class MBIOGatewayMetzConnect(MBIOGateway):
    def configurator(self):
        from .metzconnect import MCConfigurator
        return MCConfigurator(self.host, self.password)

    # FIXME: for METZ only
    def rs485(self, speed, parity='E'):
        data=0x5300

        parity=parity.upper()
        if parity[0]=='E':
            data|=0x10
        elif parity[0]=='O':
            data|=0x20
        else:
            data|=0x30

        try:
            n=[1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200].index(int(speed))
            data|=(0x1+n)
        except:
            return

        self.checkIdleAfterSend()
        self.client.write_registers(0x41, data, slave=0)
        self.signalMessageTransmission()
        # self.client.diag_restart_communication(False, slave=0)
        # for device in self._devices:
        for device in range(1, 32):
            print("Set speed 0x%02X for device %d" % (data, device))
            self.checkIdleAfterSend()
            self.client.write_registers(0x41, data)
            self.signalMessageTransmission()

    # FIXME: debug
    def toggle(self):
        for device in self.devices:
            try:
                device.toggle()
            except:
                pass

    def on(self):
        for device in self.devices:
            try:
                device.on()
            except:
                pass

    def off(self):
        for device in self.devices:
            try:
                device.off()
            except:
                pass

    def auto(self):
        for device in self.devices:
            device.auto()

    def manual(self):
        for device in self.devices:
            device.manual()


class MBIOGateways(Items):
    def __init__(self, logger):
        super().__init__(logger)
        self._items: list[MBIOGateway]=[]
        self._itemByHost={}
        self._itemByKey={}
        self._itemByName={}
        self._itemByMAC={}

    def item(self, key):
        item=super().item(key)
        if item:
            return item

        item=self.getByKey(key)
        if item:
            return item

        item=self.getByHost(key)
        if item:
            return item

        item=self.getByName(key)
        if item:
            return item

        item=self.getByMAC(key)
        if item:
            return item

        try:
            return self[key]
        except:
            pass

    def add(self, item: MBIOGateway) -> MBIOGateway:
        if isinstance(item, MBIOGateway):
            super().add(item)
            self._itemByName[item.name]=item
            self._itemByKey[item.key]=item
            self._itemByHost[item.host]=item
            self._itemByHost['%s:%d' % (item.host, item.port)]=item
            mac=item.MAC
            if mac:
                self._itemByMAC[mac.lower()]=item

    def getByHost(self, host):
        try:
            return self._itemByHost[host]
        except:
            pass

    def getByName(self, name):
        try:
            return self._itemByName[name]
        except:
            pass

    def getByKey(self, key):
        try:
            return self._itemByKey[key]
        except:
            pass

    def getByMAC(self, key):
        try:
            return self._itemByMAC[key]
        except:
            pass

    def stop(self):
        for item in self._items:
            item.stop()

    def reset(self):
        for item in self._items:
            item.reset()

    def halt(self):
        for item in self._items:
            item.halt()

    def resetHalted(self):
        for item in self._items:
            item.resetHalted()

    def waitForThreadTermination(self):
        for item in self._items:
            item.waitForThreadTermination()

    def discover(self):
        for item in self._items:
            item.discover()

    def retrieveDevicesFromModel(self, vendor, model):
        devices=[]
        if self._items:
            for gateway in self._items:
                d=gateway.retrieveDevicesFromModel(vendor, model)
                if d:
                    devices.extend(d)
        return devices

    # def dump(self):
        # if not self.isEmpty():
            # t=PrettyTable()
            # t.field_names=['#', 'Key', 'Name', 'Host', 'Open']
            # t.align='l'
            # for item in self._items:
                # t.add_row([self.index(item), item.key, item.name, item.host, item.isOpen()])

        # print(t.get_string(sortby="Key"))


if __name__ == "__main__":
    pass
