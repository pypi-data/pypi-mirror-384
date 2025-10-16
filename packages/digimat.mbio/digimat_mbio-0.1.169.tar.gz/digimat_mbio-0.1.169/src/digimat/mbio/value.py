#!/bin/python

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .mbio import MBIO

from .items import Items
from .config import MBIOConfig

import time

# from prettytable import PrettyTable
from digimat.units import Units


FLAG_ERROR = (0x1 << 0)
FLAG_MANUAL = (0x1 << 1)
FLAG_OVERRIDE = (0x1 << 2)
FLAG_DISABLED = (0x1 << 3)
FLAG_REMOTEMANUAL = (0x1 << 4)
FLAG_COMMISSIONABLE = (0x1 << 5)
FLAG_MANAGED = (0x1 << 6)
FLAG_WRITABLE = (0x1 << 7)

# READ PRINCIPLE (values refresh)
# manager->refresh() retrieve I/O state and call value.updateValue(state)
# will set value._value (value.value)
# and call value.notify() if needed (queue values updates notifications in MBIO for dispatching)

# WRITE PRINCIPLE (value change orders)
# value.value=state or value.set(state)
# will set value._toReachValue (value.toreachValue) and call value.signalSync()
# manager->sync() checks value.isPendingSync(), update I/O and call value.clearSync()
# Note: a write don't update the value.value, which will be updated by the refresh process.
# If the value isn't auto refreshed, use value.clearSyncAndUpdateValue() instead of .clearSync()
# In the manager->sync() a device->signalRefresh() is automatically called after a manager->sync() to
# speedup the value refresh

# FIXME: the value managed attribute (init) means that it's .manager() has to be called
# This has nothing to do with the .isManaged() flag that indicates if this value is actively written by the CPU
# Kind of name conflict here


class MBIOValue(object):
    def __init__(self, parent: MBIOValues, name, unit=None, default=None, resolution=0.1, writable=False, commissionable=False):
        assert(isinstance(parent, MBIOValues))
        self._parent=parent
        if not name:
            name='%d' % parent.count()
        self._name=name
        self._key=parent.computeValueKeyFromName(name)
        self._writable=writable
        self._enable=True
        if type(unit)==str:
            unit=parent.units.getByName(unit)
        self._unit=unit
        self._error=False
        self._manual=None
        self._override=False
        self._remotemanual=False
        self._commissionable=commissionable
        self._stamp=0
        self._min=None
        self._max=None
        self._default=self.normalizeValue(default)
        self._value=self._default
        self._flags=None
        self._config=MBIOConfig()
        self._resolution=resolution
        self._enableNotify=True
        self._lastValueNotified=None
        self._timeoutNotifyRefresh=0
        self._timeoutManaged=0
        self._notifyCount=0
        self.onInit()
        self.updateFlags()
        self._parent.add(self)
        if self._default is not None:
            self.updateValue(self._default)

    def hasManager(self):
        return False

    def manager(self):
        # to be overriden for managed values
        self.logger.warning("MANAGER %s" % self)
        pass

    def timeout(self, delay):
        return time.time()+delay

    def checkIfValueWillTriggerNotify(self, v):
        if v is not None:
            try:
                if type(self._value) is bool:
                    if v != self._value:
                        return True
                    return False
                if self._resolution is not None:
                    if abs(self._value-v)>=self._resolution:
                        return True
                    return False
                if v!=self._value:
                    return True
            except:
                pass
        return False

    def checkNotify(self):
        if not self._enableNotify:
            return False
        try:
            if type(self._value) is bool or self._lastValueNotified is None:
                return True
            if self._resolution is not None:
                if abs(self._value-self._lastValueNotified)>=self._resolution:
                    return True
                return False
        except:
            pass
        return True

    @property
    def type(self):
        return self.__class__.__name__

    def notify(self, force=False, delayAutoRefresh=0):
        if self._enableNotify and force or self.checkNotify():
            self.parent.getMBIO().signalValueUpdateNotify(self)
            self._lastValueNotified=self.value
            if delayAutoRefresh>0:
                self._timeoutNotifyRefresh=self.timeout(delayAutoRefresh)
            else:
                self._timeoutNotifyRefresh=self.timeout(30)

    def notifyManager(self, delayAutoRefresh=0):
        if self._value is not None:
            if time.time()>=self._timeoutNotifyRefresh:
                self.notify(True, delayAutoRefresh)

    def enableNotify(self, state=True):
        self._enableNotify=state

    @property
    def notifyCount(self):
        return self._notifyCount

    @property
    def config(self) -> MBIOConfig:
        return self._config

    @property
    def parent(self) -> MBIOValues:
        return self._parent

    @property
    def logger(self):
        return self._parent.logger

    @property
    def key(self):
        return self._key

    @property
    def tag(self):
        return self.config.iomaptag

    def keyparts(self, part=None):
        try:
            parts=self.key.split('_')
            if part is None:
                return parts
            return parts[parts[part]]
        except:
            pass

    def keyrootpart(self):
        key=self.key
        size=len(self.parent.prefix)
        return key[:size+1]

    def keyleafpart(self):
        return self.name

    @property
    def name(self):
        return self._name

    def onInit(self):
        pass

    def setRange(self, vmin, vmax):
        self._min=vmin
        self._max=vmax

    @property
    def resolution(self):
        return self._resolution

    @resolution.setter
    def resolution(self, value):
        self._resolution = value

    def normalizeValue(self, value):
        if value is not None:
            # self.logger.warning(value)
            value=float(value)
            if self._min is not None:
                value=max(self._min, value)
            if self._max is not None:
                value=min(self._max, value)
        return value

    def isWritable(self):
        if self._writable:
            return True
        return False

    def isPendingSync(self, reset=False):
        return False

    def isError(self):
        return self._error

    def isManual(self):
        if self._manual is not None:
            return True
        return False

    def isManaged(self):
        """Return True if the value is writable and seems to be managed (value written not too long ago)"""
        return False

    def isRemoteManual(self):
        if self._remotemanual:
            return True
        return False

    def isCommissionable(self):
        if self._commissionable:
            return True
        return False

    def signalSync(self, value=None):
        pass

    def signalNotified(self):
        """The value has been sent to the notifiers (CPU)"""
        pass

    def manual(self, value=None):
        if value is None:
            value=self.value
        if value is not None:
            value=self.normalizeValue(value)
            if value!=self._manual:
                self._manual=value
                self.updateFlags()
            if self.isWritable():
                self.signalSync(self._manual)
            else:
                self.updateValue(self._manual)
                self._stamp=time.time()

    def auto(self):
        if self._manual is not None:
            self._manual=None
            self.updateFlags()

    @property
    def override(self):
        return self._override

    def setOverride(self, state=True):
        state=bool(state)
        if state!=self._override:
            self._override=state
            self.updateFlags()

    def setRemoteManual(self, state=True):
        state=bool(state)
        if state!=self._remotemanual:
            self._remotemanual=state
            self.updateFlags()

    def setError(self, state=True):
        state=bool(state)
        if state!=self._error:
            self._error=state
            self.updateFlags()

    def isEnabled(self):
        return self._enable

    def enable(self, state=True):
        state=bool(state)
        if state!=self._enable:
            self._enable=state
            self.updateFlags()

    def disable(self):
        self.enable(False)

    def age(self):
        return time.time()-self._stamp

    def isTimeout(self, delay):
        if self.age()>=delay:
            return True
        return False

    @property
    def value(self):
        if self.isError() and self._default is not None:
            return self._default
        return self._value

    def valuestr(self, sigdigits=1):
        if self.value is None:
            return None
        if self.isDigital():
            if self.value:
                return 'ON'
            return 'OFF'
        try:
            decimal=float(self.resolution) % 1
            if abs(decimal)>0:
                r=str(decimal)
                dcount=len(r[r.find('.')+1:])
                fmt='%%.0%df%%s' % dcount
            else:
                fmt='%.0f%s'
            return fmt % (self.value, self.unitstr())
        except:
            self.logger.exception('FMT %s' % fmt)
            pass
        try:
            return str(self.value)+self.unitstr()
        except:
            pass
        return str(self.value)

    def richvaluestr(self, sigdigits=1):
        if self.value is None:
            return "[bold blue]None[/bold blue]"
        if self.isDigital():
            if self.value:
                return '[bold green]ON[/bold green]'
            return '[bold red]OFF[/bold red]'
        try:
            decimal=float(self.resolution) % 1
            if abs(decimal)>0:
                r=str(decimal)
                dcount=len(r[r.find('.')+1:])
                fmt='[bold magenta]%%.0%df%%s[/bold magenta]' % dcount
            else:
                fmt='[bold magenta]%.0f%s[/bold magenta]'
            return fmt % (self.value, self.unitstr())
        except:
            self.logger.exception('FMT %s' % fmt)
            pass
        try:
            return str(self.value)+self.unitstr()
        except:
            pass
        return str(self.value)

    @property
    def flags(self):
        return self._flags

    def isFlag(self, flag):
        try:
            for f in flag:
                if f.upper() in self._flags:
                    return True
        except:
            pass
        return False

    def flagsAsValue(self):
        value=0
        if self.isFlag('E'):
            value |= FLAG_ERROR
        if self.isFlag('*'):
            value |= FLAG_OVERRIDE
        if self.isFlag('M'):
            value |= FLAG_MANUAL
        if self.isFlag('X'):
            value |= FLAG_DISABLED
        if self.isWritable():
            value |= FLAG_WRITABLE
            if self.isManaged():
                value |= FLAG_MANAGED
        if self.isFlag('C'):
            value |= FLAG_COMMISSIONABLE
        if self.isFlag('R'):
            value |= FLAG_REMOTEMANUAL

        return value

    def updateFlags(self):
        flags=''
        if self.override:
            flags+='*'
        if self.isError():
            flags+='E'
        if self.isManual():
            flags+='M'
        if self.isCommissionable():
            flags+='C'
        if not self.isEnabled():
            flags+='X'
        if self.isRemoteManual():
            flags+='R'

        if self.isWritable():
            flags+='W'
            if not self.isManaged():
                flags+='!'

        if flags!=self._flags:
            self._flags=flags
            # Force notify
            self.notify(True)

            # A flag change (as REMOTEMANUAL) may have an impact
            # on the way the value is processed (i.e. AnalogOutput delays)
            # So request a sync
            self.signalSync()
            return True

        return False

    def updateValue(self, value, unit=None):
        if self.isManual():
            if not self.isWritable():
                value=self._manual
        else:
            self._stamp=time.time()
        value=self.normalizeValue(value)
        notify=self._lastValueNotified is None
        if unit is not None and self._unit!=unit:
            self._unit=unit
            notify=True
        if value!=self._value:
            self._value=value
            notify=True
        if notify:
            self.notify()

    def updateValidValue(self, value, unit=None):
        self.updateValue(value, unit)
        self.setError(False)

    def isValid(self):
        if self.isEnabled() and self._value is None:
            return False
        return True

    @property
    def unit(self):
        return self._unit

    @unit.setter
    def unit(self, value):
        if type(value)==str:
            value=self.parent.units.getByName(value)
        if self.isDigital():
            value=15
        if self._unit!=value:
            self._unit=value
            self.notify()

    def unitstr(self):
        return self.parent.units.str(self.unit)

    def isDigital(self):
        # FIXED: a value is digital only if the object is a MBIODigitalValue instance
        # and not by it's unit. Otherwise, in case an analog value is falsy written with a digital unit,
        # the value object tends to be locked in a digital value.
        # if self.parent.units.isDigital(self.unit):
            # return True
        return False

    def isMultistate(self):
        return False

    def __bool__(self):
        self.logger.warning('WARNING: *************************** %s used as bool' % self)
        try:
            if self.isDigital():
                return self.isOn()
        except:
            pass
        if self.value!=0:
            return True
        return False

    def __repr__(self):
        if self.updateFlags():
            # should not be called
            self.logger.warning('%s --> updateFlags TRUE', self.key)
        age=int(self.age())
        if age>3600:
            age='N/A'
        if self._flags:
            return '%s(%s=%s, flags=[%s], %ss, #%d, tag=%s)' % (self.__class__.__name__, self.key,
                self.valuestr(), self._flags, age, self._notifyCount, self.tag)
        return '%s(%s=%s, %ss, #%d, tag=%s)' % (self.__class__.__name__, self.key, self.valuestr(), age, self._notifyCount, self.tag)

    def richstr(self):
        self.updateFlags()
        age=int(self.age())
        if age>3600:
            age='N/A'
        if self._flags:
            color='[white]'
            if self.isFlag('AE'):
                color='[red]'
            if self.isFlag('MR*'):
                color='[green]'
            if self.isFlag('X'):
                color='[bright_black]'

            return '%s%s[/]([bold]%s[/bold]=%s, flags=[[bold]%s[/bold]], %ss, #%d, tag=%s)' % (color, self.__class__.__name__, self.key,
                self.richvaluestr(), self._flags, age, self._notifyCount, self.tag)
        return '%s([bold]%s[/bold]=%s, %ss, #%d, tag=%s)' % (self.__class__.__name__, self.key, self.richvaluestr(), age, self._notifyCount, self.tag)

    def refpath(self):
        path=[]
        ref=self
        while True:
            try:
                ref=ref.parent
            except:
                break
            if isinstance(ref, MBIOValues):
                continue
            if ref is None:
                break
            path.insert(0, str(ref))
        return '->'.join(path)

    def match(self, key):
        try:
            if key is None:
                return True
            if key.lower() in self._key:
                return True
            if key=='*':
                return True
            if key[0]=='*' and key[-1]:
                key=key[1:-1].lower()
                if key in self._key:
                    return True
            if key[0]=='*':
                key=key[1:].lower()
                if self._key[-len(key):]==key:
                    return True
            if key[-1]=='*':
                key=key[:-1].lower()
                if self._key[0:len(key)]==key:
                    return True
        except:
            pass
        return False


class MBIOConstant(MBIOValue):
    def __init__(self, parent: MBIOValues, name, value, unit):
        super().__init__(parent, name=name, unit=unit, default=value)


# FIXME: duplicated code MBIOValueWritable - MBIOValueDigitalWritable
class MBIOValueWritable(MBIOValue):
    def __init__(self, parent: MBIOValues, name, unit=None, default=None, resolution=0.1, commissionable=False):
        super().__init__(parent, name=name, unit=unit, default=default, writable=True, resolution=resolution, commissionable=commissionable)
        self._toReachValue=None
        self._pendingSync=False

    def isManaged(self):
        """Return True if the value is writable and seems to be managed (value written not too long ago)"""
        if self.isValid() and time.time()<self._timeoutManaged:
            return True
        return False

    @MBIOValue.value.setter
    def value(self, value):
        if value is not None:
            if self.isEnabled():
                if self.isManual():
                    value=self._manual
                value=self.normalizeValue(value)
                resolution=self._resolution
                if resolution is not None and resolution>0:
                    if self.value is None or abs(value-self.value)>=resolution:
                        self.signalSync(value)
                else:
                    if value != self.value:
                        self.signalSync(value)
                self._timeoutManaged=self.timeout(180)
                self.updateFlags()

    def set(self, value):
        self.value=value

    def off(self):
        self.set(0)

    def min(self):
        if self._min is not None:
            self.set(self._min)

    def max(self):
        if self._max is not None:
            self.set(self._max)

    def signalSync(self, value=None):
        if value is not None:
            self._toReachValue=value
        self._pendingSync=True
        self.parent.signalSync()

    def isPendingSync(self, reset=False):
        if self._pendingSync and self._toReachValue is not None:
            if reset:
                self.clearSync()
            return True
        return False

    @property
    def toReachValue(self):
        return self._toReachValue

    def clearSync(self):
        self._pendingSync=False

    def clearSyncAndUpdateValue(self):
        self.clearSync()
        if self.toReachValue is not None:
            self.updateValue(self.toReachValue)
            self._stamp=time.time()


class MBIOValueDigital(MBIOValue):
    def __init__(self, parent: MBIOValues, name, default=None, writable=False, commissionable=False):
        super().__init__(parent, name=name, unit=15, default=default, writable=writable, commissionable=commissionable)

    def isDigital(self):
        return True

    def normalizeValue(self, value):
        if value is not None:
            if type(value) is bool:
                return value
            if type(value) is int:
                return bool(value)
            if value is None:
                return False
            return bool(value)
        return value

    def isOn(self):
        if self.value:
            return True
        return False

    def isOff(self):
        return not self.isOn()


class MBIOValueTrigger(MBIOValueDigital):
    def __init__(self, parent: MBIOValues, name, delay=15, commissionable=False):
        super().__init__(parent, name=name, default=False, commissionable=commissionable)
        self._triggerDelay=delay
        self._triggerNotified=False
        self._timeoutTrigger=0

    def hasManager(self):
        return True

    def trigger(self):
        if not self.isOn():
            self._triggerNotified=False
            self._timeoutTrigger=self.timeout(self._triggerDelay)
            self.updateValue(True)
            self.logger.warning('TRIGGER %s' % self)

    def manager(self):
        if self.isOn():
            if time.time()>=self._timeoutTrigger:
                self.updateValue(False)
                self.logger.warning("TRIGGERDONE %s" % self)

    def signalNotified(self):
        if self.isOn() and not self._triggerNotified:
            self._triggerNotified=True
            self.logger.debug('TRIGGER NOTIFIED %s' % self)


class MBIOValueDigitalWritable(MBIOValueDigital):
    def __init__(self, parent: MBIOValues, name, default=None, commissionable=False):
        super().__init__(parent, name=name, default=default, writable=True, commissionable=commissionable)
        self._toReachValue=None
        self._pendingSync=False

    def isManaged(self):
        """Return True if the value is writable and seems to be managed (value written not too long ago)"""
        try:
            if self.isValid() and time.time()<self._timeoutManaged:
                return True
            return False
        except:
            self.logger.exception('xx')

    @MBIOValueDigital.value.setter
    def value(self, value):
        if value is not None:
            if self.isEnabled():
                if self.isManual():
                    value=self._manual
                value=self.normalizeValue(value)
                if value!=self.value:
                    self.signalSync(value)
                self._timeoutManaged=self.timeout(180)
                self.updateFlags()

    def set(self, value):
        self.value=value

    def signalSync(self, value=None):
        if value is not None:
            self._toReachValue=value
        self._pendingSync=True
        self.parent.signalSync()

    def isPendingSync(self, reset=False):
        if self._pendingSync and self._toReachValue is not None:
            if reset:
                self.clearSync()
            return True
        return False

    @property
    def toReachValue(self):
        return self._toReachValue

    def clearSync(self):
        self._pendingSync=False

    def clearSyncAndUpdateValue(self):
        self.clearSync()
        if self.toReachValue is not None:
            self.updateValue(self.toReachValue)
            self._stamp=time.time()

    def toggle(self):
        self.value=not self.value

    def on(self):
        self.value=True

    def off(self):
        self.value=False


class MBIOValueMultistate(MBIOValue):
    def __init__(self, parent: MBIOValues, name, vmax, vmin=0, default=None, writable=False, commissionable=False):
        super().__init__(parent, name=name, unit=53, default=default, resolution=1.0, writable=writable, commissionable=commissionable)
        if vmin is None or vmin<0:
            vmin=0
        self.setRange(vmin, vmax)

    def isDigital(self):
        return False

    def isMultistate(self):
        return True

    def normalizeValue(self, value):
        value=super().normalizeValue(value)
        try:
            return int(value)
        except:
            pass
        return self._min


class MBIOValueMultistateWritable(MBIOValueMultistate):
    def __init__(self, parent: MBIOValues, name, vmax, vmin=0, default=None, commissionable=False):
        super().__init__(parent, name=name, vmax=vmax, vmin=vmin, default=default, writable=True, commissionable=commissionable)
        self._toReachValue=None
        self._pendingSync=False

    def isManaged(self):
        """Return True if the value is writable and seems to be managed (value written not too long ago)"""
        if self.isValid() and time.time()<self._timeoutManaged:
            return True
        return False

    @MBIOValueDigital.value.setter
    def value(self, value):
        if value is not None:
            if self.isEnabled():
                if self.isManual():
                    value=self._manual
                value=self.normalizeValue(value)
                if value!=self.value:
                    self.signalSync(value)
                self._timeoutManaged=self.timeout(180)
                self.updateFlags()

    def set(self, value):
        self.value=value

    def signalSync(self, value=None):
        if value is not None:
            self._toReachValue=value
        self._pendingSync=True
        self.parent.signalSync()

    def isPendingSync(self, reset=False):
        if self._pendingSync and self._toReachValue is not None:
            if reset:
                self.clearSync()
            return True
        return False

    @property
    def toReachValue(self):
        return self._toReachValue

    def clearSync(self):
        self._pendingSync=False

    def clearSyncAndUpdateValue(self):
        self.clearSync()
        if self.toReachValue is not None:
            self.updateValue(self.toReachValue)
            self._stamp=time.time()

    def next(self):
        if self.value is not None:
            self.value=self.value+1
        else:
            self.value=self._min

    def prev(self):
        if self.value is not None:
            self.value=self.value-1
        else:
            self.value=self._min


class MBIOValues(Items):
    def __init__(self, parent, prefix, logger):
        super().__init__(logger)
        self._parent=parent
        self._prefix=prefix
        self._items: list[MBIOValue]=[]
        self._itemByKey={}
        self._itemByName={}
        self._units=Units()
        self._hasWritableValue=False

    @property
    def parent(self):
        return self._parent

    @property
    def prefix(self):
        return self._prefix

    @property
    def units(self):
        return self._units

    def computeValueKeyFromName(self, name):
        if self._prefix:
            return '%s_%s' % (self._prefix, name)
        return name

    def getByKeyComputedFromName(self, name):
        return self.getByKey(self.computeValueKeyFromName(name))

    def getMBIO(self) -> MBIO:
        return self._parent.getMBIO()

    def item(self, key):
        item=super().item(key)
        if item is not None:
            return item

        item=self.getByKey(key)
        if item is not None:
            return item

        item=self.getByName(key)
        if item is not None:
            return item

        try:
            return self[key]
        except:
            pass

    def hasWritableValue(self):
        if self._hasWritableValue:
            return True
        return False

    def add(self, value: MBIOValue) -> MBIOValue:
        if isinstance(value, MBIOValue):
            super().add(value)
            self._itemByKey[value.key]=value
            self._itemByName[value.name]=value
            try:
                attr=getattr(self, value.name)
                if attr is not None:
                    self.logger.warning('possible value variable name [%s] conflict with values object' % value.name)
                else:
                    setattr(self, value.name, value)
            except:
                setattr(self, value.name, value)
            if value._writable:
                self._hasWritableValue=True
            try:
                self.getMBIO().registerValue(value)
            except:
                pass

    def getByKey(self, key):
        try:
            return self._itemByKey[key]
        except:
            pass

    def getByName(self, key):
        try:
            return self._itemByName[key]
        except:
            pass

    def __radd__(self, other):
        self.add(other)

    def signalSync(self):
        try:
            self._parent.signalSync()
        except:
            pass

    # Force return None if called with an unknown attribute (value name)
    def __getattr__(self, name):
        try:
            return getattr(self, name)
        except:
            pass
        return None


if __name__ == "__main__":
    pass
