#!/bin/python

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .value import MBIOValue

from .netscan import MBIONetworkScanner
from .task import MBIOTask
from .xmlconfig import XMLConfig

import threading
# import base64
import httpx
import pprint
import json

from prettytable import PrettyTable

# https://developers.meethue.com/develop/get-started-2/#follow-3-easy-steps
# https://developers.meethue.com/develop/hue-api-v2/api-reference/


class HueResources(object):
    RESSOURCE_NAME=''

    def __init__(self, hue: Hue):
        self._hue=hue
        self._items={}
        self._services={}
        self.update()

    @property
    def hue(self):
        return self._hue

    @property
    def logger(self):
        return self.hue.logger

    def items(self):
        return self._items.values()

    def update(self, resource=None):
        resource=resource or self.RESSOURCE_NAME
        data=self.hue.getResourceData(resource)
        if data:
            try:
                for item in data:
                    self._items[item['id']]=item
                self.rebuildServicesIndex()
                return data
            except:
                pass

    def get(self, rid):
        if not self._items:
            self.update()
        try:
            return self._items[rid]
        except:
            pass

    def search(self, name):
        items=[]
        if name:
            name=name.strip().lower()
            for item in self._items.values():
                try:
                    if name in item['metadata']['name'].lower():
                        items.append(item['id'])
                except:
                    pass
        return items

    def first(self, name):
        try:
            return self.search(name)[0]
        except:
            pass

    def searchByServiceType(self, rtype):
        items=[]
        if rtype:
            rtype=rtype.strip().lower()
            for item in self._items.values():
                if self.getService(rtype, item['id']):
                    items.append(item['id'])
        return items

    def dumpdata(self):
        pprint.pprint(self._items)

    def services(self):
        try:
            return self._services.values()
        except:
            pass

    def hasServices(self):
        if self.services():
            return True
        return False

    def rebuildServicesIndex(self, force=False):
        if force or not self._services:
            for item in self.items():
                try:
                    for service in item['services']:
                        rtype=service['rtype']
                        rid=service['rid']
                        itemid=item['id']
                        self._services[rid]={'rtype': rtype, 'rid': rid, 'itemrid': itemid}
                except:
                    pass

    def getService(self, rtype, itemrid) -> str:
        item=self.get(itemrid)
        if item and rtype:
            try:
                # TODO: loop over small entries, but may be better
                for service in item['services']:
                    if service['rtype']==rtype:
                        return service['rid']
            except:
                pass

    def dump(self):
        t=PrettyTable()
        t.field_names=['TYPE', 'id', '...', 'name']
        t.align='l'

        for item in self.items():
            name=item['metadata']['name'].lower()
            idv1=''
            try:
                idv1=item['id_v1']
            except:
                pass
            t.add_row([self.__class__.__name__, item['id'], idv1, name])

        try:
            for service in self.services():
                name=service['itemrid']
                item=self.get(service['itemrid'])
                if item:
                    name=item['metadata']['name'].lower()
                t.add_row(['service', service['rid'], service['rtype'], '->%s' % name])
        except:
            pass

        print(t.get_string())


class HueService(object):
    def __init__(self, hue: Hue, rtype, rid):
        self._hue=hue
        self._rtype=rtype
        self._rid=rid
        self._data={}

    @property
    def hue(self):
        return self._hue

    @property
    def rid(self):
        return self._rid

    @property
    def rtype(self):
        return self._rtype

    def url(self):
        return self.hue.urlclip('resource/%s/%s' % (self.rtype, self.rid))

    @property
    def data(self):
        if not self._data:
            self.update()
        return self._data

    def update(self):
        try:
            r=self.hue.GET(self.url())
            if r:
                self._data=r['data'][0]
                return self._data
        except:
            pass


class HueServiceMotion(HueService):
    def getStateFromData(self, data):
        try:
            return bool(data['motion']['motion'])
        except:
            pass

    def state(self):
        return self.getStateFromData(self.data)


class HueServiceLight(HueService):
    def getStateFromData(self, data):
        try:
            return bool(data['on']['on'])
        except:
            pass

    def getLevelFromData(self, data):
        try:
            return float(data['dimming']['brightness'])
        except:
            pass

    def state(self):
        return self.getStateFromData(self.data)

    def level(self):
        return self.getLevelFromData(self.data)

    def setState(self, state=True):
        try:
            data={'on': {'on': bool(state)}}
            r=self.hue.PUT(self.url(), data=data)
            if r is not None:
                return True
        except:
            pass

    def on(self):
        return self.setState(True)

    def off(self):
        return self.setState(False)

    def toggle(self):
        self.setState(not self.state())

    def setLevel(self, level):
        try:
            data={'dimming': {'brightness': float(level)}}
            r=self.hue.PUT(self.url(), data=data)
            if r is not None:
                return True
        except:
            pass

    def max(self):
        return self.setLevel(100.0)


class HueDevices(HueResources):
    RESSOURCE_NAME='device'

    def light(self, rid) -> HueServiceLight:
        rtype='light'
        servicerid=self.getService(rtype, rid)
        if servicerid:
            return HueServiceLight(self.hue, rtype, servicerid)

    def motion(self, rid) -> HueServiceMotion:
        rtype='motion'
        servicerid=self.getService(rtype, rid)
        if servicerid:
            return HueServiceMotion(self.hue, rtype, servicerid)


class HueRooms(HueResources):
    RESSOURCE_NAME='room'

    def light(self, rid) -> HueServiceLight:
        rtype='grouped_light'
        servicerid=self.getService(rtype, rid)
        if servicerid:
            return HueServiceLight(self.hue, rtype, servicerid)


class HueZones(HueResources):
    RESSOURCE_NAME='zone'

    def light(self, rid) -> HueServiceLight:
        rtype='grouped_light'
        servicerid=self.getService(rtype, rid)
        if servicerid:
            return HueServiceLight(self.hue, rtype, servicerid)


class Hue(object):
    def __init__(self, bridge, token, logger):
        self._logger=logger
        self._bridge=bridge
        self._token=token
        self._devices=HueDevices(self)
        self._rooms=HueRooms(self)
        self._zones=HueZones(self)

    @property
    def logger(self):
        return self._logger

    @property
    def devices(self):
        return self._devices

    @property
    def rooms(self):
        return self._rooms

    @property
    def zones(self):
        return self._zones

    def setBridge(self, host):
        if host:
            self._bridge=host

    def url(self, rootpath, subpath=None):
        url='https://%s/%s' % (self._bridge, rootpath)
        if subpath:
            return '%s/%s' % (url, subpath)
        return url

    def urlclip(self, subpath=None):
        return self.url('clip/v2', subpath)

    def urlapi(self, subpath=None):
        return self.url('api', subpath)

    def isAuth(self):
        if self._token:
            return True

    def GET(self, url, data={}):
        try:
            self.logger.debug('GET %s(%s)' % (url, data))
            headers={}
            if self.isAuth():
                headers['hue-application-key']=self._token
            r=httpx.get(url, headers=headers, params=data, verify=False, timeout=3.0)
            if r and r.status_code==httpx.codes.OK:
                data=r.json()
                # self.logger.debug(data)
                return data
            self.logger.error(r.text)
        except:
            # self.logger.exception('GET')
            pass

    def POST(self, url, data={}):
        try:
            self.logger.debug('POST %s(%s)' % (url, data))
            headers={}
            if self.isAuth():
                headers['hue-application-key']=self._token
            r=httpx.post(url, headers=headers, json=data, verify=False, timeout=3.0)
            if r and r.status_code==httpx.codes.OK:
                data=r.json()
                # self.logger.debug(data)
                return data
            self.logger.error(r.text)
        except:
            # self.logger.exception('POST')
            pass

    def PUT(self, url, data={}):
        try:
            self.logger.debug('PUT %s(%s)' % (url, data))
            headers={}
            if self.isAuth():
                headers['hue-application-key']=self._token
            r=httpx.put(url, headers=headers, json=data, verify=False, timeout=3.0)
            if r and r.status_code==httpx.codes.OK:
                data=r.json()
                self.logger.debug(data)
                return data
            self.logger.error(r.text)
        except:
            # self.logger.exception('PUT')
            pass

    def events(self):
        url=self.url('eventstream', 'clip/v2')
        headers={'Accept': 'text/event-stream'}
        if self.isAuth():
            headers['hue-application-key']=self._token
            try:
                with httpx.stream('GET', url, headers=headers, verify=False, timeout=60) as s:
                    # yield from s.iter_bytes()
                    yield from s.iter_lines()
            except:
                pass

    def ping(self):
        r=self.GET(self.urlapi('0/config'))
        return r

    def auth(self, clientid=None):
        if not self.isAuth():
            if not clientid:
                clientid='MBIOPROCESSOR'
            try:
                url=self.urlapi()
                data={'devicetype': clientid, 'generateclientkey': True}
                r=self.POST(url, data=data)
                data=r[0]['success']
                if data:
                    self.logger.info('Hue AUTH OK!')
                    self._token=data['username']
            except:
                self.logger.error('Hue AUTH FAILED!')

        return self._token

    def getResourceData(self, name) -> dict:
        try:
            r=self.GET(self.urlclip('resource/%s' % name))
            if r:
                data=r['data']
                return data
        except:
            pass


class HueScanner(MBIONetworkScanner):
    def onInit(self):
        self._bridges={}

    def probe(self, host):
        url='http://%s/api/0/config' % host
        try:
            r=httpx.get(url, verify=False, timeout=3.0)
            if r and r.status_code==httpx.codes.OK:
                data=r.json()
                self.logger.debug(data)
                with self._lock:
                    bid=data['bridgeid'].lower()
                    self._bridges[bid]=host
                return True
        except:
            self.logger.error(url)

        return False

    def getBridgeIp(self, bid=None):
        try:
            bid=bid.lower()
            if self.scan():
                if bid:
                    return self._bridges[bid]
                for ip in self._bridges.values():
                    return ip
        except:
            pass


class HueResourceBag(object):
    # Used to store local info/ressources
    # Not a god name but nothing best found ;(
    # Proprietary format, not Hue format

    def __init__(self, resources: HueResources):
        self._resources=resources
        self._data={}
        self._values=[]

    @property
    def hue(self):
        return self._resources.hue

    @property
    def logger(self):
        return self.hue.logger

    def get(self, rid) -> dict:
        try:
            return self._data[rid]
        except:
            pass

    def search(self, name):
        items=[]
        if name:
            name=name.strip().lower()
            for item in self.items():
                try:
                    if name in item['name'].lower():
                        items.append(item['rid'])
                except:
                    pass
        return items

    def first(self, name):
        try:
            return self.search(name)[0]
        except:
            pass

    def items(self):
        return self._data.values()

    def values(self):
        return self._values

    def declare(self, rid, name, values, refresh=True):
        if not self.get(rid) and name:
            nonemptyvalues={}
            for value in values:
                if values[value] is not None:
                    nonemptyvalues[value]=values[value]

            data={'rid': rid, 'name': name, 'values': nonemptyvalues, 'refresh': refresh}
            self._data[rid]=data
            if values:
                for value in values.values():
                    self._values.append(value)
            return data

    def value(self, rid, name) -> MBIOValue:
        try:
            data=self.get(rid)
            return data['values'][name]
        except:
            pass

    def dump(self):
        t=PrettyTable()
        t.field_names=['Type', 'rid', 'Name']
        t.align='l'

        for item in self.items():
            t.add_row([self.__class__.__name__, item['rid'], item['name']])

        print(t.get_string())

    def updateValue(self, resource, name, v):
        try:
            if name and v is not None:
                if resource and resource['values']:
                    try:
                        resource['values'][name].updateValue(v)
                        return True
                    except:
                        pass
        except:
            pass
        return False


class MBIOTaskHue(MBIOTask):
    def initName(self):
        return 'hue'

    @property
    def hue(self):
        return self._hue

    @property
    def rooms(self):
        return self._rooms

    @property
    def zones(self):
        return self._zones

    @property
    def devices(self):
        return self._devices

    def onInit(self):
        self._hue=None
        self._rooms=None
        self._zones=None
        self._devices=None
        self.config.set('refreshperiod', 5)
        self._timeoutRefresh=0
        self._retry=3
        self.valueDigital('comerr', default=False)
        self._threadHueEvents=None

    def onLoad(self, xml: XMLConfig):
        self.config.set('bridge', xml.get('host'))
        if not self.config.bridge:
            self.config.update('bridge', self.pickleRead('bridge'))
        self.config.set('bridgeid', xml.get('id'))

        self.config.set('token', self.pickleRead('token'))
        self.config.update('token', xml.get('token'))
        self.pickleWrite('token', self.config.token)

        self.config.update('refreshperiod', xml.getInt('refresh'))
        self._hue=Hue(self.config.bridge, self.config.token, self.logger)
        self._rooms=HueResourceBag(self.hue.rooms)
        self._zones=HueResourceBag(self.hue.zones)
        self._devices=HueResourceBag(self.hue.devices)

        for room in xml.children('room'):
            name=room.get('name')
            rid=room.get('id')
            dimmable=room.getBool('dimmable')
            refresh=room.getBool('refresh', True)
            if name:
                state=self.valueDigital('%s_state' % name, writable=True, commissionable=True)
                if dimmable:
                    level=self.value('%s_level' % name, unit='%', resolution=1, writable=True)
                    level.setRange(0, 100)
                else:
                    level=None
                self.rooms.declare(rid, name, values={'state': state, 'level': level}, refresh=refresh)

        for zone in xml.children('zone'):
            name=zone.get('name')
            rid=zone.get('id')
            dimmable=zone.getBool('dimmable')
            if name:
                state=self.valueDigital('%s_state' % name, writable=True, commissionable=True)
                if dimmable:
                    level=self.value('%s_level' % name, unit='%', resolution=1, writable=True)
                    level.setRange(0, 100)
                else:
                    level=None
                self.zones.declare(rid, name, values={'state': state, 'level': level})

        for device in xml.children('ir'):
            name=device.get('name')
            rid=device.get('id')
            if name:
                motion=self.valueDigital('%s_motion' % name, commissionable=True)
                self.devices.declare(rid, name, values={'motion': motion})

    def hueEventManager(self):
        halt=False

        self.logger.info('Starting starting hue events thread')
        while not halt:
            for event in self.hue.events():
                if self.state not in [self.STATE_RUN]:
                    halt=1
                    break

                if not halt and event[:6]=='data: ':
                    try:
                        # self.logger.warning(event)
                        data=json.loads(event[6:])
                        for e in data:
                            # eid=data['id']
                            etype=e['type']
                            edata=e['data']
                            for item in edata:
                                self.dispatchEvent(etype, item)
                    except:
                        self.logger.exception('event')

            if not halt:
                # Auto restart event stream if closed
                self.sleep(5)

        self.logger.info('Exiting hue events thread')
        self._threadHueEvents=None

    def dispatchEvent(self, etype, data):
        self.logger.debug('HUE/EVENT %s %s' % (etype, data))
        if etype=='update':
            try:
                owner=data['owner']['rid']
            except:
                return

            room=self.rooms.get(owner)
            if room:
                service=self.hue.rooms.light(room['rid'])

                v=service.getStateFromData(data)
                self.rooms.updateValue(room, 'state', v)
                v=service.getLevelFromData(data)
                self.rooms.updateValue(room, 'level', v)
                return

            zone=self.zones.get(owner)
            if zone:
                service=self.hue.zones.light(zone['rid'])

                v=service.getStateFromData(data)
                self.zones.updateValue(zone, 'state', v)
                v=service.getLevelFromData(data)
                self.zones.updateValue(zone, 'level', v)
                return

            device=self.devices.get(owner)
            if device:
                # self.logger.warning("EVENT for device %s" % device)
                service=self.hue.devices.motion(device['rid'])
                if service:
                    v=service.getStateFromData(data)
                    self.devices.updateValue(device, 'motion', v)
                return

        self.logger.warning('Untrapped HUE/EVENT %s %s' % (etype, data))

    def poweron(self):
        if not self._hue.ping():
            bid=self.config.bridgeid
            scanner=HueScanner(self.getMBIO())
            # if bid is None, get the first ip dicovered
            ip=scanner.getBridgeIp(bid)
            if ip:
                self.logger.warning('Bridge %s found @%s' % (bid, ip))
                self._hue._bridge=ip
                self.config.update('bridge', ip)
                self.pickleWrite('bridge', ip)

        if self._hue.ping():
            token=self.hue.auth()
            if token:
                self.hue._token=token
                self.pickleWrite('token', token)
            else:
                self.values.comerr.updateValue(True)
                return False

            self.hue.devices.update()
            self.hue.rooms.update()
            self.hue.zones.update()
            return True
        return False

    def poweroff(self):
        return True

    def syncRooms(self):
        for room in self.rooms.items():
            self.microsleep()
            values=room['values'].values()
            service=self.hue.rooms.light(room['rid'])
            if values and service:
                for value in values:
                    if value.isPendingSync():
                        if value.isDigital():
                            if service.setState(value.toReachValue):
                                value.clearSyncAndUpdateValue()
                        else:
                            if service.setLevel(value.toReachValue):
                                value.clearSyncAndUpdateValue()

    def syncZones(self):
        for zone in self.zones.items():
            self.microsleep()
            values=zone['values'].values()
            service=self.hue.zones.light(zone['rid'])
            if values and service:
                for value in values:
                    if value.isPendingSync():
                        if value.isDigital():
                            if service.setState(value.toReachValue):
                                value.clearSyncAndUpdateValue()
                        else:
                            if service.setLevel(value.toReachValue):
                                value.clearSyncAndUpdateValue()

    def refreshRooms(self):
        result=True
        for room in self.rooms.items():
            self.microsleep()

            service=self.hue.rooms.light(room['rid'])
            if service:
                # refresh data
                data=service.update()

                v=service.getStateFromData(data)
                self.rooms.updateValue(room, 'state', v)
                v=service.getLevelFromData(data)
                self.rooms.updateValue(room, 'level', v)
                continue

            for value in room['values'].values():
                if value:
                    value.setError(True)
            result=False

        return result

    def refreshZones(self):
        result=True
        for zone in self.zones.items():
            self.microsleep()

            service=self.hue.zones.light(zone['rid'])
            if service:
                # refresh data
                data=service.update()

                v=service.getStateFromData(data)
                self.zones.updateValue(zone, 'state', v)
                v=service.getLevelFromData(data)
                self.zones.updateValue(zone, 'level', v)
                continue

            for value in zone['values'].values():
                if value:
                    value.setError(True)
            result=False

        return result

    def refreshDevices(self):
        result=True
        for device in self.devices.items():
            self.microsleep()

            service=self.hue.devices.motion(device['rid'])
            if service:
                # refresh data
                data=service.update()

                v=service.getStateFromData(data)
                self.devices.updateValue(device, 'state', v)
                continue

            for value in device['values'].values():
                if value:
                    value.setError(True)
            result=False

        return result

    def run(self):
        if not self.hue.isAuth():
            for value in self.rooms.values():
                if value:
                    value.setError(True)
            for value in self.zones.values():
                if value:
                    value.setError(True)

        if not self._threadHueEvents:
            self._threadHueEvents=threading.Thread(target=self.hueEventManager, daemon=True)
            self._threadHueEvents.start()

        self.syncRooms()
        self.syncZones()

        if self.isTimeout(self._timeoutRefresh):
            self._timeoutRefresh=self.timeout(self.config.refreshperiod)
            error=False

            if not self.refreshRooms():
                error=True
            if not self.refreshZones():
                error=True
            if not self.refreshDevices():
                error=True

            if not error:
                self._timeoutRefresh=self.timeout(self.config.refreshperiod)
                self._retry=3
                self.values.comerr.updateValue(False)
            else:
                self._timeoutRefresh=self.timeout(60)
                if self._retry>0:
                    self._retry-=1
                    if self._retry==0:
                        self.values.comerr.updateValue(True)
                        self.state=self.STATE_ERROR

        return 3.0

    def discover(self, network=None):
        scanner=HueScanner(self.getMBIO(), network)
        if scanner.scan():
            return scanner._bridges


if __name__ == "__main__":
    pass
