#!/bin/python

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .mbio import MBIO

import time
import datetime
import socket
import hashlib

from digimat.lp import PacketManager, LP

from .task import MBIOTask
from .xmlconfig import XMLConfig

from .valuenotifier import MBIOValueNotifier


kLP_ST=20
kLP_MBIO=0xA4

kMBIO_PING=0
kMBIO_PONG=1
kMBIO_SYNC=2
kMBIO_RESTART=3
kMBIO_UPDATEVALUE=10
kMBIO_WRITEVALUE=11
kMBIO_UPDATEVALUEREQ=12
kMBIO_DECLAREVALUE=13
kMBIO_NOTIFYDISABLE=14
kMBIO_AUTH=15
kMBIO_BADAUTH=16
kMBIO_RAZCONFIG=20
kMBIO_BEEP=21
kMBIO_NETSCAN=22
kMBIO_IOMAPPING=23

# kST_DUPLICATERSRC=98


class MBIOLinkPacketManager(PacketManager):
    def __init__(self, link: MBIOLink, lid=0):
        super().__init__()
        self._link=link
        self._lid=lid

    @property
    def link(self):
        return self._link

    @property
    def logger(self):
        return self._link.logger

    def dispose(self):
        self.link.disconnect()
        super().dispose()

    def write(self, data):
        return self.link.write(data)

    def manager(self):
        data=self.link.read()
        if data:
            self.receive(data)

    def lp(self, lptype=kLP_MBIO, idRequest=None):
        lp=LP(packetmanager=self)
        if idRequest is None:
            idRequest=self._lid
        lp.create(lptype, idRequest=self._lid)
        return lp


class MBIOLink(object):
    def __init__(self, mbio: MBIO, host, port=5000, lid=0, passkey=None):
        self._mbio=mbio
        self._host=host
        self._port=port
        self._lid=lid
        self._passkey=None
        if passkey:
            try:
                md5=hashlib.md5()
                md5.update(passkey.encode())
                self._passkey=md5.hexdigest()
            except:
                pass
        self._autoDeclareItems=[]
        self._pongReceived=False
        self._protocolVersion=0
        self._socket=None
        self._connected=False
        self._auth=False
        self._timeoutInhibit=3.0
        self._timeoutActivity=0
        self._delayAutoRefresh=0
        self._packetManager=MBIOLinkPacketManager(self, lid)
        self.registerHandlers()
        self.onInit()

    def onInit(self):
        pass

    @property
    def logger(self):
        return self._mbio.logger

    @property
    def packetManager(self):
        return self._packetManager

    def autoDeclareItemsManager(self):
        if self._autoDeclareItems:
            if self._connected and self._pongReceived:
                try:
                    count=16
                    while count>0:
                        count-=1
                        try:
                            data=self._autoDeclareItems.pop(0)
                            item=data['item']
                            skip=data['skip']
                            align=data['align']
                            value=data['value']
                            # self.logger.info('>DECLAREVALUE %s @%d/%d-%d' % (value.key, item, skip, align))
                            lp=self.packetManager.lp()
                            up=lp.up(kMBIO_DECLAREVALUE)
                            up.writeWord(item)  # start index
                            up.writeByte(skip)  # skip count for each group
                            up.writeStrField(value.key)
                            up.writeStrField(value.keyrootpart())
                            up.writeByte(value.flagsAsValue())
                            up.writeByte(align)
                            up.store()
                            lp.send()
                        except:
                            break
                except:
                    self.logger.exception('autoDeclareItemsManager')
                    self._autoDeclareItems=[]

    def manager(self):
        if time.time()>=self._timeoutActivity:
            self.ping()
        self.packetManager.manager()
        self.autoDeclareItemsManager()

    def resetActivityTimeout(self):
        self._timeoutActivity=time.time()+10

    def connect(self):
        try:
            if not self._connected:
                if time.time()>=self._timeoutInhibit:
                    host=self._mbio.resolveIpAliasToIpAddress(self._host)
                    self.logger.info('Opening link %s:%d' % (host, self._port))
                    self._socket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self._socket.settimeout(3)
                    interface=self._mbio.resolveIpAliasToIpAddress(self._mbio.interface)
                    if interface:
                        self.logger.info('Using interface ip %s' % interface)
                        # ifname=(self._interface+'\0').encode('utf-8')
                        # self._socket.setsockopt(socket.SOL_SOCKET, 25, ifname)
                        self._socket.bind((interface, 0))
                    address=(host, self._port)
                    self._socket.connect(address)
                    self._socket.settimeout(0)
                    self._connected=True
                    self._timeoutInhibit=time.time()+5
                    self.logger.info("Link connected to %s:%d" % (host, self._port))
                    self.resetActivityTimeout()
                    self.onConnect()
                    self._mbio.renotifyValues()
        except:
            self.logger.error("Unable to connect link to %s:%d" % (self._host, self._port))
            self._timeoutInhibit=time.time()+5

    def onConnect(self):
        self._auth=False
        self.ping()

    def isConnected(self):
        return self._connected

    def isAuth(self):
        return self._auth

    def disconnect(self):
        try:
            self._socket.close()
            self._socket=None
        except:
            pass

        if self._connected:
            self.logger.warning("Link disconnected from %s:%d" % (self._host, self._port))
            self._connected=False

    def write(self, data):
        try:
            self.connect()
            self._socket.send(data)
            self.resetActivityTimeout()
            return True
        except:
            self.disconnect()
        return False

    def read(self):
        try:
            self.connect()
            data = self._socket.recv(4096)
            if not data:
                self.disconnect()
                return

            self.resetActivityTimeout()
            return data
        except:
            pass

    def registerHandlers(self):
        self.packetManager.addHandler(kLP_MBIO, kMBIO_PONG, self.onPong)
        self.packetManager.addHandler(kLP_MBIO, kMBIO_SYNC, self.onSync)
        self.packetManager.addHandler(kLP_MBIO, kMBIO_RESTART, self.onRestart)
        self.packetManager.addHandler(kLP_MBIO, kMBIO_WRITEVALUE, self.onWriteValue)
        self.packetManager.addHandler(kLP_MBIO, kMBIO_UPDATEVALUEREQ, self.onUpdateValueRequest)
        self.packetManager.addHandler(kLP_MBIO, kMBIO_NOTIFYDISABLE, self.onNotifyDisable)
        self.packetManager.addHandler(kLP_MBIO, kMBIO_AUTH, self.onAuth)
        self.packetManager.addHandler(kLP_MBIO, kMBIO_BADAUTH, self.onBadAuth)
        self.packetManager.addHandler(kLP_MBIO, kMBIO_IOMAPPING, self.onIoMapping)

    def ping(self):
        if self._connected:
            self.logger.info('>PING')
            lp=self.packetManager.lp()
            up=lp.up(kMBIO_PING)
            up.store()
            lp.send()

    def md5(self, data):
        try:
            md5=hashlib.md5()
            md5.update(data.encode())
            return md5.hexdigest()
        except:
            pass

    def salt(self):
        try:
            data=str(datetime.datetime.now())
            return self.md5(data)
        except:
            pass

    def RAZCONFIG(self, what=None):
        if self._connected:
            what=what or '*'
            self.logger.warning('>RAZCONFIG(%s)' % what)
            lp=self.packetManager.lp()
            up=lp.up(kMBIO_RAZCONFIG)
            up.writeStr(what)
            up.store()
            if lp.send():
                return True

    def beep(self):
        if self._connected:
            self.logger.debug('>BEEP')
            lp=self.packetManager.lp()
            up=lp.up(kMBIO_BEEP)
            up.store()
            if lp.send():
                return True

    def netscan(self, network=None):
        if self._connected:
            self.logger.debug('>NETSCAN')
            lp=self.packetManager.lp()
            up=lp.up(kMBIO_NETSCAN)
            if network:
                up.writeStr(network)
            up.store()
            if lp.send():
                return True

    def auth(self, salt):
        if self._connected and salt:
            data='%s-%s' % (salt, self._passkey)
            md5=self.md5(data)
            self.logger.warning('>AUTH (salt:%s, key:%s)' % (salt, md5))
            lp=self.packetManager.lp()
            up=lp.up(kMBIO_AUTH)
            up.writeStr(md5)
            up.store()
            result=lp.send()
            if result:
                # Suppose AUTH is successful
                # FIXME: may me enhanced
                self._auth=True
                return True

    def resync(self):
        if self._connected:
            self.logger.info('>RESYNC')
            lp=self.packetManager.lp()
            up=lp.up(kMBIO_SYNC)
            up.store()
            lp.send()

    def updateValue(self, value):
        if value is not None and value.value is not None:
            try:
                # self.logger.debug('>UPDATEVALUE %s' % value)
                value._notifyCount+=1
                lp=self.packetManager.lp()
                up=lp.up(kMBIO_UPDATEVALUE)
                up.writeStr(value.key)
                up.writeFloat(float(value.value))
                up.writeFloat(value.resolution)
                unit=value.unit
                if unit is None:
                    unit=0xff
                up.writeByte(unit)
                up.writeByte(value.flagsAsValue())
                up.store()
                lp.send()
                if len(value.key)>32:
                    self.logger.error('value %s key name too long' % value)
            except:
                self.logger.exception('updateValue')
                self.logger.error(value)

    def onPong(self, up):
        rid=up.readWord()
        protocolRevision=up.readWord()
        maxNbItems=up.readWord()
        itemCount=up.readWord()
        self._delayAutoRefresh=up.readWord()
        self._pongReceived=True
        self.logger.warning('<PONG(id=%u, protocol=%u, %u/%u items, autoRefresh=%us)' %
            (rid, protocolRevision, itemCount, maxNbItems, self._delayAutoRefresh))

    def onSync(self, up):
        self.logger.warning('<SYNC')

    def onAuth(self, up):
        self.logger.warning('<AUTH')
        salt=up.readStr()
        self.auth(salt)
        self.resync()

    def onBadAuth(self, up):
        if self._auth:
            self.logger.error('<BADAUTH')
            self._auth=False

    def onRestart(self, up):
        self.logger.warning('<RESTART')
        self.disconnect()

    def onWriteValue(self, up):
        key=up.readStr()
        value=up.readFloat()
        unit=up.readByte()
        flags=up.readByte()
        self.logger.debug('<WRITEVALUE key=%s value=%.02f unit=%d flags=0x%02X' % (key, value, unit, flags))

        mbiovalue=self._mbio.value(key)
        if mbiovalue is not None:
            if mbiovalue.isWritable():
                mbiovalue.value=value
                if unit<0xfe:
                    mbiovalue.unit=unit

                # DEROGATION or MANUAL --> set RemoteManual flag on the mbio value
                # may be used to bypass some delays
                mbiovalue.setRemoteManual(flags & 0b1001000)
                # TODO: flags?
                # A change AUTO/MANU without value/unit change side CPU will not trigger the WRITEVALUE
            else:
                self.logger.error('<WRITEVALUE received for an unwritable %s' % key)
        else:
            self.logger.warning('<WRITEVALUE unknown value %s' % key)

    def onUpdateValueRequest(self, up):
        key=up.readStr()
        value=self._mbio.value(key)
        if value is not None:
            self.logger.warning('<UPDATEVALUEREQ %s' % key)
            value.enableNotify(True)
            value.notify(force=True)

    def onNotifyDisable(self, up):
        key=up.readStr()
        value=self._mbio.value(key)
        if value is not None:
            self.logger.warning('<NOTIFYDISABLE %s' % key)
            value.enableNotify(False)

    def onIoMapping(self, up):
        station=up.readByte()
        null0=up.readByte()
        installation=up.readWord()
        item=up.readWord()
        key=up.readStr()
        value=self._mbio.value(key)
        if value is not None:
            io='%umbio%u' % (station, item)
            self.logger.warning('<IOMAPPING %s<->%s' % (key, io))
            value.config.set('iomaptag', io)
            value.config.set('iomapinstallation', station)
            value.config.set('iomapcpu', station)
            value.config.set('iomapitem', item)
            value.config.set('iomapkey', 'r_%u_%u_mbio_%d_0' % (installation, station, item))

    # def onReadItemResponse(self, up):
        # pid=up.readWord()
        # index=up.readWord()
        # value=up.readFloat()
        # unit=up.readByte()
        # item=self._items.get(index)
        # if item:
            # item.value=value
            # item.unit=unit


class MBIOTaskLinkNotifier(MBIOTask):
    def initName(self):
        count=self._parent.tasks.count()
        if count==0:
            return 'station'
        return 'station%d' % count

    def onInit(self):
        self._link=None
        self._notifier=MBIOValueNotifier(self.getMBIO())
        self._iterValues=None

    def onLoad(self, xml: XMLConfig):
        mbio=self.getMBIO()

        host=xml.get('host')
        port=xml.getInt('port', 5000)
        lid=xml.getInt('id', 0)
        passkey=xml.get('passkey')

        if host:
            self._link=MBIOLink(mbio, host, port=port, lid=lid, passkey=passkey)
        else:
            self.logger.error('Unable to create MBIOLink')

        items={}
        for declare in xml.children('declare'):
            item=declare.getInt('item', 0)
            skip=declare.getInt('autoskip', 0)
            align=declare.getInt('autoalign', 0)
            for value in declare.children('values'):
                values=mbio.values(value.get('key'), sort=True)
                for v in values:
                    if v.key not in items:
                        items[v.key]=v
                        self._link._autoDeclareItems.append({'item': item, 'skip': skip, 'align': align, 'value': v})

            # Just in case someone used "Value" insteaf of "Values"
            if declare.children('value'):
                self.logger.warning('WARNING: found <Value> instead of <Values> in MBIO config file (Notifier)')


    def RAZCpuConfig(self, what=None):
        try:
            return self._link.RAZCONFIG(what)
        except:
            pass

    def beep(self):
        return self._link.beep()

    def poweron(self):
        self._link.connect()
        return True

    def poweroff(self):
        self._link.disconnect()
        return True

    def notifyRefreshManager(self):
        count=32
        while count>0:
            count-=1
            if count % 16 == 0:
                self.microsleep()
            if self._iterValues is None:
                try:
                    # reset list
                    self._iterValues=iter(self.getMBIO()._valuesByKey.values())
                except:
                    pass
            try:
                value=next(self._iterValues)
                # self.logger.warning(value)
                value.notifyManager(self._link._delayAutoRefresh)
            except:
                # force reinit list
                self._iterValues=None
                break

    def run(self):
        self._link.manager()
        if self._link.isConnected():
            if self._link.isAuth():
                if not self._link._autoDeclareItems:
                    count=64
                    while count>0:
                        value=self._notifier.get()

                        if value is None:
                            break

                        count-=1
                        # self.logger.debug('NOTIFYUPDATE %s' % value)
                        self.updateValue(value)
                        if count % 16 == 0:
                            self.microsleep()

                    self.notifyRefreshManager()
                return 0.1
        return 0.5

    def isError(self):
        if super().isError():
            return True
        if not self._link.isConnected():
            return True
        return False

    def updateValue(self, value):
        self._link.updateValue(value)
        value.signalNotified()


if __name__ == "__main__":
    pass
