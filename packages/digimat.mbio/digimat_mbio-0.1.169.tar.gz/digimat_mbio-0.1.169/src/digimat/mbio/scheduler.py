from __future__ import annotations
from typing import TYPE_CHECKING

from functools import total_ordering

from datetime import datetime

from .task import MBIOTask
from .xmlconfig import XMLConfig

import requests
import io
import csv

from prettytable import PrettyTable


@total_ordering
class Trigger(object):
    def __init__(self, dow: str, t: str, state: bool = True, setpoints=None, variant: int = 0):
        self._dow=str(dow).lower()
        self._variant=int(variant)
        self._state=bool(state)
        self._setpoints=setpoints
        self._h=None
        self._m=None
        self._stamp=None
        self.parseTime(t)

    @property
    def dow(self):
        return self._dow

    @property
    def variant(self):
        return self._variant

    @property
    def h(self):
        return self._h

    @property
    def m(self):
        return self._m

    @property
    def stamp(self):
        return self._stamp

    @property
    def state(self):
        return self._state

    def sp(self, name):
        try:
            return float(self._setpoints[name])
        except:
            pass

    def t(self, offset=0):
        stamp=self.stamp+offset
        return '%02d:%02d' % (stamp // 60, stamp % 60)

    @property
    def key(self):
        return '%d:%s:%d' % (self.variant, self.dow, self.stamp)

    def parseTime(self, t):
        try:
            t=str(t).replace('h', ':')
            if ':' in t:
                items=list(t.split(':'))
                self._h=int(items[0])
                self._m=int(items[1])
                if self._m is None:
                    self._m=0
            else:
                self._h=int(t)
                self._m=0

            self._stamp=self._h*60+self._m
        except:
            pass

    def matchDow(self, variant, date=None):
        try:
            variant=int(variant)
            if variant != self.variant:
                return False
            if self._h is not None and self._m is not None:
                if not date:
                    date=datetime.now()
                dow=date.isoweekday()
                if str(dow) in self._dow:
                    return True
                if '*' in self._dow:
                    return True
                if dow in [6, 7] and self._dow=='we':
                    return True
                if dow<6 and self._dow=='wd':
                    return True
        except:
            pass
        return False

    def __eq__(self, other):
        if self.stamp==other.stamp:
            if self.dow==other.dow:
                return True
        return False

    def __lt__(self, other):
        if self.stamp==other.stamp:
            if self.dow=='*' and other.dow!='*':
                return True
            if self.dow!='*' and other.dow=='*':
                return False
            if len(self.dow)>len(other.dow):
                return True
            return False
        if self.stamp<other.stamp:
            return True
        return False

    def __repr__(self):
        return '<%s(dow=%s, t=%02d:%02d, state=%d, sp=%s)>' % (self.__class__.__name__,
            self.dow, self.h, self.m, self._state, self._setpoints)


class Scheduler(object):
    def __init__(self, parent: Schedulers, name):
        self._parent=parent
        self._triggers=[]
        self._triggersByKey={}
        self._name=name
        self._sorted=False
        self._variants=[]

    @property
    def parent(self):
        return self._parent

    def reset(self):
        self._triggers=[]
        self._triggersByKey={}
        self._sorted=False

    @property
    def name(self):
        return self._name

    @property
    def variants(self):
        return self._variants

    def hasVariants(self):
        if len(self._variants)>1:
            return True
        return False

    def now(self):
        return datetime.now()

    def dow(self, date):
        return date.isoweekday()

    def addTrigger(self, trigger: Trigger):
        if trigger is not None:
            if not self._triggersByKey.get(trigger.key):
                self._triggers.append(trigger)
                self._triggersByKey[trigger.key]=trigger
                self._sorted=False
                if trigger.variant not in self._variants:
                    self._variants.append(trigger.variant)
                return trigger

    def normalizeSetpoints(self, setpoints):
        if not setpoints:
            return None
        try:
            data={}
            for sp in setpoints:
                if self.parent.hasSp(sp):
                    try:
                        v=setpoints[sp]
                        if v not in ['n/a', 'none', 'null', '']:
                            data[sp]=float(setpoints[sp])
                    except:
                        pass
        except:
            pass
        return data

    def on(self, dow: str, t: str, setpoints=None, variant=0):
        try:
            if dow and t:
                if t not in ['n/a', 'none', 'null']:
                    data=self.normalizeSetpoints(setpoints)
                    return self.addTrigger(Trigger(dow, t, state=True, setpoints=data, variant=variant))
        except:
            pass

    def off(self, dow: str, t: str, setpoints=None, variant=0):
        try:
            if dow and t:
                if t not in ['n/a', 'none', 'null']:
                    data=self.normalizeSetpoints(setpoints)
                    return self.addTrigger(Trigger(dow, t, state=False, setpoints=data, variant=variant))
        except:
            pass

    def slot(self, dow: str, t: str, duration: int, setpoints=None, variant=0):
        try:
            duration=int(duration)
            if dow and t and duration>0:
                if t not in ['n/a', 'none', 'null']:
                    data=self.normalizeSetpoints(setpoints)
                    t0=Trigger(dow, t, state=True, setpoints=data, variant=variant)
                    t1=Trigger(dow, t0.t(duration), state=False, variant=variant)
                    self.addTrigger(t0)
                    self.addTrigger(t1)
                    return t0, t1
        except:
            pass

    def eval(self, variant=0, logger=None):
        date=self.now()
        if not self._sorted:
            self._triggers.sort()
            self._sorted=True

        state=False
        setpoints={}

        if date is not None:
            stamp=date.hour*60+date.minute
            for t in self._triggers:
                if t.matchDow(variant, date):
                    if stamp>=t.stamp:
                        state=t.state
                        try:
                            for name in t._setpoints.keys():
                                value=t.sp(name)
                                if value not in [None, '', 'n/a']:
                                    setpoints[name]={'value': value, 'stamp': t.stamp}
                        except:
                            pass
                    else:
                        # Triggers are sorted
                        break

        return state, setpoints

    def dump(self, variant=0):
        t=PrettyTable()
        t.field_names=['%s%d' % (self.name, variant), '1:MON', '2:TUE', '3:WED', '4:THU', '5:FRI', '6:SAT', '7:SUN']
        t.align='l'

        for n in range(0, 24*60):
            row=['' for dow in range(8)]
            empty=True
            for dow in range(1, 8):
                key1='%d:%s:%d' % (variant, dow, n)
                key2='%d:*:%d' % (variant, n)
                trigger=self._triggersByKey.get(key1) or self._triggersByKey.get(key2)
                if trigger and trigger.variant==variant:
                    row[0]=trigger.t()
                    state='OFF'
                    if trigger.state:
                        state='ON '

                    data='%s' % (state)
                    if self.parent._setpoints:
                        for name in self.parent._setpoints:
                            sp=trigger.sp(name)
                            if sp is not None:
                                data += ' %s=%.01f' % (name, sp)
                    row[dow]=data
                    empty=False
            if not empty:
                t.add_row(row)

        print(t.get_string())


class Schedulers(object):
    def __init__(self):
        self._schedulers={}
        self._constants={}
        self._setpoints={}

    def constant(self, name, default=None):
        try:
            return self._constants[str(name).strip().lower()]
        except:
            pass
        return default

    def constantFloat(self, name, default=None):
        try:
            return float(self.constant(name, default))
        except:
            pass
        return default

    def constantInt(self, name, default=None):
        try:
            return int(self.constant(name, default))
        except:
            pass
        return default

    def setConstant(self, name, value):
        try:
            name=str(name).strip().lower()
            if name:
                self._constants[name]=value
                return True
        except:
            pass
        return False

    def hasConstant(self, name):
        try:
            name=str(name).strip().lower()
            self._constants[name]
            return True
        except:
            pass
        return False

    def updateConstant(self, name, value):
        if self.hasConstant(name) and value not in [None, '', 'n/a', 'none', 'null']:
            self.setConstant(name, value)

    def constants(self):
        return self._constants.keys()

    def sp(self, name, default=None):
        try:
            return self._setpoints[str(name).strip().lower()]
        except:
            pass
        return default

    def spFloat(self, name, default=None):
        try:
            return float(self.sp(name, default))
        except:
            pass
        return default

    def spInt(self, name, default=None):
        try:
            return int(self.sp(name, default))
        except:
            pass
        return default

    def setSp(self, name, value):
        try:
            name=str(name).strip().lower()
            if name:
                self._setpoints[name]=value
                return True
        except:
            pass
        return False

    def hasSp(self, name):
        try:
            self._setpoints[str(name).strip().lower()]
            return True
        except:
            pass
        return False

    def updateSp(self, name, value):
        if self.hasSp(name) and value not in [None, '', 'n/a', 'none', 'null']:
            self.setSp(name, value)

    def reset(self):
        for scheduler in self._schedulers.values():
            scheduler.reset()

    def get(self, name):
        try:
            return self._schedulers[name.lower()]
        except:
            pass

    def __getitem__(self, key):
        return self.get(key)

    def __iter__(self):
        return iter(self._schedulers.values())

    def create(self, name):
        if name:
            scheduler=self.get(name)
            if not scheduler:
                scheduler=Scheduler(self, name)
                self._schedulers[name.lower()]=scheduler
            return scheduler

    def programs(self):
        return self._schedulers.keys()

    def getField(self, row, n, default=None):
        try:
            return row[n].strip().lower()
        except:
            pass
        return default

    def getFieldInt(self, row, n, default=None):
        try:
            return int(row[n].strip())
        except:
            pass
        return default

    def getFieldFloat(self, row, n, default=None):
        try:
            return float(row[n].strip())
        except:
            pass
        return default

    # dialect: unix, excel, excel-tab (see csv.list_dialects())
    def loadcsv(self, f, delimiter=',',  dialect='excel', logger=None):
        try:
            if delimiter:
                delimiter=delimiter.lower().replace('tab', '\t')
            reader=csv.reader(f, dialect=dialect, delimiter=delimiter)
            self.reset()
            valid=False
            for row in reader:
                try:
                    # logger.warning(row)
                    action=self.getField(row, 0)
                    if action in ['on', 'off']:
                        valid=True
                        scheduler=self.get(self.getField(row, 1))
                        if scheduler:
                            variant=self.getFieldInt(row, 2, 0)
                            dow=self.getField(row, 3)
                            t=self.getField(row, 4)
                            setpoints={}
                            col=5
                            for sp in self._setpoints.keys():
                                setpoints[sp]=self.getFieldFloat(row, col)
                                col+=1

                            if action=='on':
                                scheduler.on(dow, t, setpoints=setpoints, variant=variant)
                            else:
                                scheduler.off(dow, t, setpoints=setpoints, variant=variant)

                    elif action=='set':
                        valid=True
                        name=self.getField(row, 1)
                        value=self.getField(row, 2)
                        # logger.debug("***SET %s=%s" % (name, value))
                        self.updateConstant(name, value)
                except:
                    if logger:
                        logger.exception('csv-trigger')
            return valid

        except:
            if logger:
                logger.exception('csv')

        return False

    def dump(self, variant=0, key=None):
        for scheduler in self._schedulers.values():
            if not key or key.lower() in scheduler.name.lower():
                scheduler.dump(variant)


class MBIOTaskScheduler(MBIOTask):
    def initName(self):
        return 'sch'

    @property
    def schedulers(self):
        return self._schedulers

    @property
    def programs(self):
        return list(self._programs.keys())

    def onInit(self):
        self._schedulers=Schedulers()
        self._programs={}
        self._timeoutreload=0
        self.config.set('reloadperiod', 0)
        self.config.set('reloadurl', None)
        self._minute=None

    def onLoadProgram(self, scheduler, xml: XMLConfig):
        if scheduler is not None and xml is not None:
            items=xml.children('*')
            if items:
                for item in items:
                    setpoints={}
                    for sp in scheduler.setpoints():
                        v=item.getFloat(sp)
                        if v is not None:
                            setpoints[sp]=v

                    if item.tag=='on':
                        scheduler.on(item.get('dow'), item.get('time'),
                                     setpoints=setpoints,
                                     variant=item.getInt('variant', 0))
                    elif item.tag=='off':
                        scheduler.off(item.get('dow'), item.get('time'),
                                      setpoints=setpoints,
                                      variant=item.getInt('variant', 0))
                    elif item.tag=='slot':
                        scheduler.slot(item.get('dow'), item.get('time'), item.get('duration'),
                                      setpoints=setpoints,
                                      variant=item.getInt('variant', 0))

    def onLoadSetpoints(self, scheduler, xml: XMLConfig):
        if scheduler is not None and xml is not None:
            items=xml.children('*')
            if items:
                for item in items:
                    name=item.tag
                    v=item.getFloat('value')
                    if self._schedulers.setSp(name, v):
                        unit=item.get('unit', 'C')
                        resolution=item.getFloat('resolution', 0.1)
                        self.value('sp_%s' % name, unit=unit, resolution=resolution, default=v)

    def onLoadConstants(self, scheduler, xml: XMLConfig):
        if scheduler is not None and xml is not None:
            items=xml.children('*')
            if items:
                for item in items:
                    name=item.tag
                    unit=item.get('unit', 0xff)
                    v=item.getFloat('value')
                    if self._schedulers.setConstant(name, v):
                        self.value('cst_%s' % name, unit=unit, default=v)

    def onLoad(self, xml: XMLConfig):
        items=xml.children('program')
        if items:
            self.value('variant', unit=0xff, default=0, writable=True)
            for item in items:
                name=item.get('name')
                if name and not self._schedulers.get(name):
                    scheduler=self._schedulers.create(name=name)

                    program={'state': self.valueDigital('%s_state' % name)}
                    self._programs[name]=program

                    self.onLoadProgram(scheduler, item.child('triggers'))

        self.onLoadConstants(scheduler, xml.child('constants'))
        self.onLoadSetpoints(scheduler, xml.child('setpoints'))

        item=xml.child('download')
        if item and item.child('url'):
            try:
                self.valueDigital('comerr', default=False)
                self._timeoutReload=0
                self._reloadDataValid=False
                self.config.set('type', item.get('type', 'csv'))
                self.config.set('separator', item.get('separator', ','))
                self.config.set('dialect', item.get('dialect'))
                self.config.reloadperiod=item.getInt('period', 60)
                self.config.reloadurl=item.child('url').text()
                self.logger.error(self.config.url)
                self.reload()
            except:
                pass

    def poweron(self):
        return True

    def poweroff(self):
        return True

    def loadcsv(self, f):
        try:
            if self._schedulers.loadcsv(f, dialect=self.config.dialect,
                                        delimiter=self.config.separator,
                                        logger=self.logger):
                return True
        except:
            pass

    def refreshConstants(self):
        constants=self.schedulers.constants()
        if constants:
            for c in constants:
                value=self.value('cst_%s' % c)
                if value is not None:
                    value.updateValue(self.schedulers.constantFloat(c))

    def reload(self):
        self._timeoutReload=self.timeout(60*60)
        if self.config.reloadperiod>0 and self.config.reloadurl:
            try:
                url=self.config.reloadurl
                self.logger.debug('scheduler(%s)->%s' % (self.name, url))
                # keep proxies (internet usage)
                r=requests.get(url, timeout=10.0)
                if r and r.ok:
                    data=r.text
                    # self.logger.warning(data)

                    if data and self.config.type=='csv':
                        with io.StringIO(data) as f:
                            if self.loadcsv(f):
                                self._reloadDataValid=True
                                try:
                                    with io.BytesIO(r.content) as f:
                                        hcode=self.computeDataHashCodeForFile(f)
                                    if not self.checkLocalDataStorageHashCode(self.config.type, hcode):
                                        self.updateLocalDataStorage(self.config.type, r.content)
                                except:
                                    pass

                                self.values.comerr.updateValue(False)
                                self._timeoutReload=self.timeout(self.config.reloadperiod*60)
                                self.refreshConstants()
                                return True
            except:
                self._timeoutReload=self.timeout(60)

        self.logger.error('scheduler(%s)->reload error' % (self.name))
        # self.logger.warning(data)
        self.values.comerr.updateValue(True)

        if self.config.type=='csv':
            if not self._reloadDataValid:
                self.logger.error('Scheduler(%s) unable to load initial CSV data. Trying to reload local cache.' % self.name)
                try:
                    with open(self.getLocalDataStorageFilePath(self.config.type), 'r') as f:
                        if self.loadcsv(f):
                            self._reloadDataValid=True
                            self.refreshConstants()
                except:
                    pass

        return False

    def run(self):
        if self.config.reloadperiod>0 and self.isTimeout(self._timeoutReload):
            self.reload()

        # Eval one a minute
        now=datetime.now()
        if self._minute is not None and self._minute==now.minute:
            return
        self._minute=now.minute

        try:
            value=self.values.variant
            if value.isPendingSync():
                value.clearSyncAndUpdateValue()
        except:
            pass

        # {'t': {'value': 23.0, stamp: 630}}
        setpoints={}

        # import declared setpoints and fill them with default values
        for sp, value in self._schedulers._setpoints.items():
            setpoints[sp]={'value': value, 'stamp': 0}

        for scheduler in self._schedulers:
            program=self._programs[scheduler.name]

            variant=0
            try:
                variant=int(self.values.variant.value)
            except:
                pass

            state, sps = scheduler.eval(variant=variant, logger=self.logger)

            # We have to keep only the latest sp value for each sp
            # sps: {'t': {'value': 23.0, stamp: 630}}
            if sps:
                for sp, value in sps.items():
                    if sp in setpoints:
                        if sps[sp]['stamp']>=setpoints[sp]['stamp']:
                            setpoints[sp]=value

            program['state'].updateValue(state)
            # self.logger.warning(setpoints)

        try:
            for sp in setpoints.keys():
                value=self.values.getByName('sp_%s' % sp)
                if value is not None:
                    value.updateValue(setpoints[sp]['value'])
        except:
            pass

        return 1.0


if __name__ == '__main__':
    pass
