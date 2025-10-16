#!/bin/python

from .task import MBIOTask
from .xmlconfig import XMLConfig


class MBIOTaskScanner(MBIOTask):
    def initName(self):
        return 'scanner'

    def onInit(self):
        self.config.set('refresh', 0)
        self.config.set('threads', 32)
        self.config.set('network', self.getMBIO().network)
        self._scan=False
        self._sio=False
        self._tokenSIO=None
        self._mc=False
        # Wait some time before launching first scan after start
        self._timeoutRefresh=self.timeout(15)

    def onLoad(self, xml: XMLConfig):
        self.config.update('refresh', xml.getInt('refresh', vmin=60))
        self.config.update('threads', xml.getInt('threads', vmax=64))
        self.config.update('network', xml.get('network'))

        item=xml.child('sio')
        if item is not None:
            self._tokenSIO=item.get('token')
            self._sio=True

        item=xml.child('mc')
        if item is not None:
            self._mc=True

    def poweron(self):
        return True

    def poweroff(self):
        return True

    def isDeviceOffline(self, vendor, model):
        devices=self.getMBIO().gateways.retrieveDevicesFromModel(vendor, model)
        if devices:
            for device in devices:
                if not device.isOnline():
                    return True
        return False

    def scanSIO(self, force=False):
        try:
            if force or self.isDeviceOffline('digimat', 'sio'):
                from .digimatsmartio import SIOScanner
                self.logger.debug('%s: Starting SIO scan...' % (self.__class__.__name__))
                s=SIOScanner(self.getMBIO(),
                            network=self.config.network,
                            maxthreads=self.config.threads)
                s.setToken(self._tokenSIO)
                s.configureNetwork()
                self.logger.debug('%s: SIO scan done' % (self.__class__.__name__))
            else:
                # self.logger.debug('%s: Skiping SIO scan (system is online)' % (self.__class__.__name__))
                pass
        except:
            pass


    def scanMC(self, force=False):
        try:
            if force or self.isDeviceOffline('metzconnect', None):
                self.logger.debug('%s: Starting MetzConnect scan...' % (self.__class__.__name__))
                from .metzconnect import MCScanner
                s=MCScanner(self.getMBIO(),
                            network=self.config.network,
                            maxthreads=self.config.threads)
                s.configureNetwork()
                self.logger.debug('%s: Scan done' % (self.__class__.__name__))
        except:
            pass

    def run(self):
        if self.isTimeout(self._timeoutRefresh):
            period=self.config.getInt('refresh')
            if not self._scan or period>0:
                if self._sio:
                    self.scanSIO()

                if self._mc:
                    self.scanMC()

                self._timeoutRefresh=self.timeout(max(60, period))
                self._scan=True

        return 15.0


if __name__ == "__main__":
    pass
