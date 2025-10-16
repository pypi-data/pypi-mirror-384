import asyncio
import threading
import time
import logging

from xknx import XKNX
from xknx.io import ConnectionConfig, ConnectionType
from xknx.core import XknxConnectionState
from xknx.telegram import Telegram
from xknx.tools import (
    group_value_read,
    group_value_response,
    group_value_write,
    read_group_value
)

# from xknx.telegram.address import DeviceGroupAddress
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite
from xknx.io import GatewayScanner
# from xknx.devices import Switch

# https://bbc.github.io/cloudfit-public-docs/asyncio/asyncio-part-5.html

class KNXValue(object):
    def __init__(self, parent, address, timeout=None, data=None):
        self._parent=parent
        self._address=address
        self._data=data
        self._timeout=timeout
        self._stamp=0

        logging.getLogger("xknx.log").disabled=True
        logging.getLogger("xknx.knx").disabled=True

    @property
    def parent(self):
        return self._parent

    @property
    def client(self):
        try:
            return self._parent._client
        except:
            pass

    @property
    def address(self):
        return self._address

    @property
    def data(self):
        return self._data

    def setData(self, data):
        if data is not None:
            self._data=data
            self._stamp=time.time()

    def getData(self):
        return self._data

    def age(self):
        return time.time()-self._stamp

    def isTimeout(self):
        if self._timeout:
            if self.age()>=self._timeout:
                return True
        return False

    def refresh(self):
        try:
            self.client.refreshgroup(self.address)
        except:
            pass

    def refreshIfTimeout(self):
        if self.isTimeout():
            self.refresh()

    def write(self, data=None):
        try:
            if data is None:
                data=self.getData()
            if data is not None:
                self.parent.client.writegroup(self.address, data)
                self.refresh()
        except:
            pass

    def rewrite(self):
        self.write(self.data)


class KNXValues(object):
    def __init__(self, client, timeout=15):
        self._client=client
        self._timeout=timeout
        self._values={}

    @property
    def client(self):
        return self._client

    def get(self, address) -> KNXValue:
        try:
            return self._values[address]
        except:
            pass

    def add(self, address, timeout=None):
        if address:
            value=self.get(address)
            if value is None:
                if timeout is None:
                    timeout=self._timeout

                value=KNXValue(self, address, timeout=timeout)
                self._values[address]=value
            return value

    def set(self, address, data):
        value=self.add(address)
        if value is not None:
            value.setData(data)

    def update(self, address, data):
        value=self.get(address)
        if value is not None:
            value.setData(data)

    def getData(self, address):
        value=self.get(address)
        if value is not None:
            return value.getData()

    def refresh(self):
        for value in self._values.values():
            value.refresh()

    def refreshIfTimeout(self):
        for value in self._values.values():
            if value.isTimeout():
                value.refresh()


class XKNXClient(object):
    def __init__(self, logger, host=None, timeoutRefresh=15):
        self._logger=logger
        self._host=host
        self._xknx=None
        self._connectState=None
        self._loop=None
        self._thread=None
        self._values=KNXValues(self, timeout=timeoutRefresh)

    @property
    def logger(self):
        return self._logger

    def setHost(self, host):
        if host:
            self._host=host

    def getValue(self, address) -> KNXValue:
        return self._values.get(address)

    def getValueData(self, address) -> KNXValue:
        value=self._values.get(address)
        if value is not None:
            return value.data

    def setValue(self, address, data):
        if data:
            value=self._values.add(address)
            if value is not None:
                value.setData(data)

    def refreshValues(self):
        self._values.refresh()

    def refreshValuesIfTimeout(self):
        self._values.refreshIfTimeout()

    def onConnectionStateChanged(self, state: XknxConnectionState):
        self.logger.debug(state)
        self._connectState=state

    def onGroupValueResponse(self, telegram: Telegram):
        self.logger.debug('KNX: %s' % telegram)
        address=str(telegram.destination_address)
        data=telegram.payload.value.value
        self._values.update(address, data)

    def onGroupValueRead(self, telegram: Telegram):
        # as said by xknx, usually not trapped
        self.logger.debug('KNX: %s' % telegram)
        pass

    def onGroupValueWrite(self, telegram: Telegram):
        # as said by xknx, usually not trapped
        self.logger.debug('KNX: %s' % telegram)
        pass

    def onTelegramReceived(self, telegram: Telegram):
        if isinstance(telegram.payload, GroupValueWrite):
            self.onGroupValueWrite(telegram)
        elif isinstance(telegram.payload, GroupValueResponse):
            self.onGroupValueResponse(telegram)
        elif isinstance(telegram.payload, GroupValueRead):
            self.onGroupValueRead(telegram)
        else:
            self.logger.warning('KNX: unhandled telegram %s' % telegram)

    async def connect(self):
        if not self._xknx and self._host:
            config=ConnectionConfig(
                connection_type=ConnectionType.TUNNELING,
                gateway_ip=self._host)

            self.logger.info('KNX: connecting to gateway %s...' % self._host)
            self._xknx=XKNX(connection_config=config,
                    daemon_mode=True,
                    state_updater=True,
                    connection_state_changed_cb=self.onConnectionStateChanged,
                    telegram_received_cb=self.onTelegramReceived)

        if self._xknx:
            await self._xknx.start()

    async def disconnect(self):
        if self._xknx:
            self.logger.info('KNX: disconnecting from gateway %s...' % self._host)
            await self._xknx.stop()
            self._xknx=None

        if self._loop:
            self._loop.stop()

    def asyncioRunOnce(self):
        self.submit(asyncio.sleep(0))

    def submit(self, coro, timeout=0):
        if self.isRunning():
            try:
                future=asyncio.run_coroutine_threadsafe(coro, self._loop)
                result=future.result(timeout)
                return result
            except TimeoutError:
                pass
            except:
                # FIXME:
                self.logger.exception('KNX: submit()')
                pass

    def submitNoWait(self, coro):
        if self.isRunning():
            try:
                asyncio.run_coroutine_threadsafe(coro, self._loop)
            except:
                pass

    # def switch(self, name, addres):
        # device=Switch(self._xknx, name, addres)
        # self._xknx.devices.async_add(device)

    def readgroup(self, address, timeout=2.0):
        if self.isRunning():
            return self.submit(read_group_value(self._xknx, address), timeout)

    def refreshgroup(self, address):
        if self.isRunning():
            # response will come later via callback
            self.submitNoWait(read_group_value(self._xknx, address))

    def writegroup(self, address, value, value_type=None):
        # FIXME: why this call return None (not as read) ?
        # as coro is None, we can't sumbit it to the asyncio loop
        coro=group_value_write(self._xknx, address, value, value_type)
        if coro is not None:
            self.logger.warning('KNX: coroutine is not None, which seems good but not handled')

        # FIXME: without this, the telegram is not sent until next message
        self.asyncioRunOnce()

    def knxmanager(self):
        try:
            asyncio.set_event_loop(self._loop)
            asyncio.run_coroutine_threadsafe(self.connect(), self._loop)
            self.logger.info('KNX: async loop started')
            self._loop.run_forever()
            self.logger.info('KNX: async loop halted')
        except KeyboardInterrupt:
            self.logger.info("KNX: STOP!")
        except:
            pass

    def start(self):
        if not self._thread:
            self._loop = asyncio.new_event_loop()
            self._thread=threading.Thread(target=self.knxmanager)
            self._thread.daemon=True
            self._thread.start()
            self.logger.info('KNX: thread started')

    def stop(self):
        try:
            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(self.disconnect(), self._loop)
        except:
            if self._loop:
                self.logger.info('KNX: stopping aysyncio loop')
                self._loop.stop()

        if self._thread:
            # wait for thread (loop) termination
            self._thread.join()
            self.logger.info('KNX: thread halted')
            if self._loop:
                self.logger.info('KNX: closing asyncio loop')
                self._loop.close()
                self._loop=None
            self._thread=None
            self._connectState=None

    def isRunning(self):
        if self._thread:
            return True
        return False

    def isConnected(self):
        if self.isRunning():
            if self._connectState==XknxConnectionState.CONNECTED:
                return True
        return False

    def discover(self, interface, stopOnFound=False):
        gateways={}

        scanner=GatewayScanner(self._xknx, local_ip=interface, stop_on_found=stopOnFound)
        items=self.submit(scanner.scan(), 15)

        try:
            for gateway in items:
                self.logger.debug(gateway)
                data={'address': gateway.individual_address,
                    'name': gateway.name.strip(),
                    'host': gateway.ip_addr, 'port': gateway.port,
                    'secure': gateway.supports_secure,
                    'tcp': gateway.supports_tunnelling_tcp,
                    'udp': gateway.supports_tunnelling}

                gateways[gateway.ip_addr]=data
        except:
            pass

        return gateways

    def __del__(self):
        self.stop()


if __name__ == '__main__':
    pass
