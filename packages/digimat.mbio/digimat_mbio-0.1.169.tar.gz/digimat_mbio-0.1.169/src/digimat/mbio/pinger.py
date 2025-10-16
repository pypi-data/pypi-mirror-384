#!/bin/python

from .task import MBIOTask
from .xmlconfig import XMLConfig


import socket
import struct
import time
import select
import os
import sys


ICMP_ECHO_REQUEST = 8


class Pinger(object):
    def __init__(self, target_host, timeout, logger):
        self._logger=logger
        self.target_host = target_host
        self.timeout = timeout
        self.packet_size = 56

    @property
    def logger(self):
        return self._logger

    def checksum(self, source):
        sum = 0
        count = 0
        length = len(source)

        # Sum 16-bit words
        while count + 1 < length:
            val = (source[count] << 8) + source[count + 1]
            sum += val
            sum &= 0xffffffff
            count += 2

        # Add remaining byte if odd length
        if count < length:
            sum += (source[count] << 8)
            sum &= 0xffffffff

        # Fold 32-bit sum to 16 bits
        while (sum >> 16):
            sum = (sum & 0xFFFF) + (sum >> 16)

        return ~sum & 0xFFFF  # No htons here!

    def create_packet(self, packet_id):
        try:
            header = struct.pack(">bbHHh", ICMP_ECHO_REQUEST, 0, 0, packet_id, 1)
            data = bytes((192 + (x % 64) for x in range(self.packet_size)))
            checksum_val = self.checksum(header + data)
            header = struct.pack(">bbHHh", ICMP_ECHO_REQUEST, 0, checksum_val, packet_id, 1)
            return header + data
        except Exception as e:
            return None

    def receive_ping(self, s, packet_id, time_sent):
        time_remaining = self.timeout
        while time_remaining > 0:
            start_select = time.time()
            try:
                ready = select.select([s], [], [], time_remaining)

                duration = time.time() - start_select
                if not ready[0]:
                    return None
                time_received = time.time()
                rec_packet, addr = s.recvfrom(1024)

                if len(rec_packet) < 28:
                    continue  # ignore malformed packet

                icmp_header = rec_packet[20:28]
                _type, _code, _checksum, rec_id, _ = struct.unpack(">bbHHh", icmp_header)

                if rec_id == packet_id:
                    return (time_received - time_sent) * 1000  # ms
            except socket.timeout:
                return None
            except Exception as e:
                return None

            time_remaining -= duration
        return None

    def ping(self):
        try:
            target_ip = socket.gethostbyname(self.target_host)
        except Exception as e:
            return

        try:
            proto=socket.getprotobyname("ICMP")
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW, proto)
            s.settimeout(self.timeout)
        except Exception as e:
            return

        with s:
            packet_id = os.getpid() & 0xFFFF
            packet = self.create_packet(packet_id)
            if not packet:
                return

            try:
                s.sendto(packet, (target_ip, 0))
                time_sent = time.time()
                delay = self.receive_ping(s, packet_id, time_sent)
            except Exception as e:
                return

            if delay is None:
                return False
            return True


class MBIOTaskPinger(MBIOTask):
    def initName(self):
        return 'ping'

    def onInit(self):
        self.config.set('period', 15)
        self.config.set('timeout', 60)
        self._hosts={}
        self._timeoutRefresh=0
        self.valueDigital('comerr', default=False)

    def onLoad(self, xml: XMLConfig):
        self.config.update('period', xml.getInt('period'))
        self.config.update('timeout', xml.getInt('timeout'))

        items=xml.children('host')
        if items:
            for item in items:
                name=item.get('name').lower()
                ip=item.get('ip')
                if name and ip and not self._hosts.get(name):
                    data={}
                    value=self.valueDigital(name)
                    value.config.set('ip', ip)
                    value.config.set('timeout', self.config.getInt('timeout'))
                    value.config.xmlUpdateInt(item, 'timeout', vmin=5)
                    data['value']=value
                    data['timeout']=self.timeout(value.config.timeout)
                    self._hosts[name]=data

    def poweron(self):
        self._timeoutRefresh=0
        return True

    def poweroff(self):
        return True

    def ping(self, host, timeout=1):
        if host:
            try:
                # require admin rights to send an icmp packet
                p=Pinger(host, timeout, self.logger)
                if p.ping():
                    # self.logger.debug("PING %s" % host)
                    return True
            except:
                pass

            self.logger.error("PING %s" % host)
        return False

    def run(self):
        if self.isTimeout(self._timeoutRefresh):
            self._timeoutRefresh=self.timeout(self.config.period)
            error=False
            for name in self._hosts.keys():
                self.microsleep()
                host=self._hosts[name]
                value=host['value']
                try:
                    if self.ping(value.config.ip, 1.0):
                        host['timeout']=self.timeout(value.config.timeout)
                        value.updateValue(True)
                        value.setError(False)
                        continue
                    else:
                        if self.isTimeout(host['timeout']):
                            value.updateValue(False)
                            value.setError(False)
                            error=True
                            continue
                except:
                    pass

            value=self.values.comerr
            self.logger.warning(value)
            value.updateValue(error)

        return 5.0


if __name__ == "__main__":
    pass
