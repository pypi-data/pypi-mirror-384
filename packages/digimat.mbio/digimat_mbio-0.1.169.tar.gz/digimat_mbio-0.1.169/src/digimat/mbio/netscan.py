#!/bin/python

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .mbio import MBIO


import time
from threading import Thread, Lock
from queue import Queue
import ipcalc


class MBIONetworkScanner(object):
    def __init__(self, mbio: MBIO, network=None, maxthreads=32):
        self._mbio=mbio
        self._network=network or mbio._network
        self._maxthreads=maxthreads
        self._queue=Queue()
        self._lock=Lock()
        self._hosts={}
        self.onInit()

    def onInit(self):
        pass

    def microsleep(self):
        time.sleep(0.001)

    def sleep(self, delay):
        time.sleep(delay)

    def reset(self):
        self._hosts={}

    def count(self):
        try:
            return len(self._hosts)
        except:
            pass
        return 0

    def getMBIO(self):
        return self._mbio

    @property
    def mbio(self):
        return self.getMBIO()

    @property
    def logger(self):
        return self.mbio.logger

    def hosts(self):
        hosts=[]
        try:
            n=ipcalc.Network(self._network)
            for host in n:
                hosts.append(str(host))
        except:
            pass
        return hosts

    def netmask(self, network=None):
        try:
            n=ipcalc.Network(network or self._network)
            return str(n.netmask())
        except:
            pass

    def probe(self, host):
        # to be overriden
        # should return the hostid (i.e. mac)
        return None

    def declareHost(self, host, hostid):
        if host and hostid:
            with self._lock:
                self.logger.warning('%s: found host %s (%s)...' % (self.__class__.__name__, host, hostid))
                if host not in self._hosts:
                    self._hosts[host]=hostid.lower()

    def probeNetwork(self):
        while True:
            try:
                host=self._queue.get(False)
            except:
                break

            try:
                # self.logger.debug('%s: scanning host %s...' % (self.__class__.__name__, host))
                self.microsleep()
                hostid=self.probe(host)
                if hostid:
                    self.declareHost(host, hostid)
            except:
                self.logger.exception('probe')
                pass

            # we must emit a task_done() for every queued element
            self._queue.task_done()

        # self.logger.debug('%s: exit scanning thread' % (self.__class__.__name__))

    def scan(self):
        self.logger.info('%s: scanning network...' % self.__class__)

        self.reset()
        if self._network:
            hosts=self.hosts()
            if hosts:
                for host in hosts:
                    self._queue.put(host)

                for t in range(self._maxthreads):
                    t = Thread(target=self.probeNetwork)
                    t.daemon = True
                    t.start()

                # wait each thread has called task_done()
                self._queue.join()
                return self._hosts

    def configureHostFromGateway(self, host, gateway):
        # to be overriden
        pass

    def configureNetwork(self):
        hosts=self.scan()
        if hosts:
            for host in hosts:
                self.microsleep()

                hostid=hosts[host]
                # check if the hostid (i.e MAC) is known on the declared gateways
                gateway=self.mbio.gateway(hostid)
                if gateway:
                    try:
                        self.configureHostFromGateway(host, gateway)
                    except:
                        self.logger.exception('reconfigureHostFromGateway')

    def __getitem__(self, key):
        try:
            key=key.lower()
            for host in self._hosts.keys():
                if key in host:
                    return host
        except:
            pass

    def __repr__(self):
        return '%s(%u hosts)' % (self.__class__.__name__, self.count())

if __name__=='__main__':
    pass
