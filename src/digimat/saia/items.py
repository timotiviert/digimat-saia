from __future__ import print_function  # Python 2/3 compatibility

import time
from prettytable import PrettyTable

from threading import RLock
from threading import Event

from .formaters import SAIAValueFormaterFloat32
from .formaters import SAIAValueFormaterSwappedFloat32
from .formaters import SAIAValueFormaterInteger10
from .formaters import SAIAValueFormaterFFP
from .formaters import SAIAValueFormater


class SAIAItemGroup(object):
    def __init__(self, items=None):
        self._items=[]
        self._itemsIndexById={}
        self.add(items)

    @property
    def logger(self):
        # may fails if no items
        try:
            return self._item[0].logger
        except:
            pass

    def all(self):
        return self._items

    def count(self):
        return len(self._items)

    def __len__(self):
        return self.count()

    def __iter__(self):
        return iter(self.all())

    def __getitem__(self, key):
        try:
            return self._items[key]
        except:
            pass

    def add(self, item):
        if item:
            try:
                # accept arrays
                for i in item:
                    self.add(i)
                return
            except:
                pass

            self._itemsIndexById[id(item)]=self.count()
            self._items.append(item)
            return item

    def remove(self, item):
        if item:
            try:
                i = self._itemsIndexById.pop(id(item))
                self._items.pop(i)
            except:
                pass

    def refresh(self, urgent=False):
        if self._items:
            for item in self.all():
                item.clearUpdated()
                item.refresh(urgent)

    def read(self, timeout=15.0):
        if self._items:
            timeout=time.time()+timeout
            self.refresh(True)
            for item in self.all():
                t=timeout-time.time()
                if t<0 or not item.waitUpdated(t):
                    return False
            return True

    def isRaised(self, reset=True):
        if self._items:
            for item in self.all():
                if item.isRaised(reset):
                    return item
        return False

    def isChanged(self, reset=True):
        if self._items:
            for item in self.all():
                if item.isChanged(reset):
                    return item
        return False

    def isUpdated(self, reset=True):
        if self._items:
            for item in self.all():
                if item.isUpdated(reset):
                    return item
        return False

    def isAlive(self, maxAge=None):
        if self._items:
            for item in self.all():
                if not item.isAlive(maxAge):
                    return False
            return True

    def dump(self):
        if self._items:
            for item in self.all():
                print(item)

    def table(self, key=None):
        if self._items:
            t=PrettyTable()
            t.field_names = ['#', 'server', 'index', 'tag', 'value', 'age']
            t.align['#']='l'
            t.align['server']='l'
            t.align['index']='r'
            t.align['tag']='l'
            t.align['value']='r'
            t.align['age']='l'

            for n in range(self.count()):
                item=self._items[n]
                if key and not item.match(key):
                    continue
                deviceName=item.server.deviceName
                if not deviceName:
                    deviceName=item.server.host
                age='%.01fs' % item.age()
                t.add_row([n, deviceName, item.index, item.tag, item.formatedvalue, age])

            print(t)

    def __repr__(self):
        return '<%s(%d items)>' % (self.__class__.__name__, self.count())


class SAIAItem(object):
    def __init__(self, parent, index, value=0, delayRefresh=None, readOnly=False):
        self._parent=parent
        self._index=index
        self._value=self.validateValue(value)
        self._pushValue=None
        self._stamp=0
        self._inhibitTimeout=0
        self._readOnly=readOnly
        self._delayRefresh=delayRefresh
        self._eventPush=Event()
        self._eventPull=Event()
        self._eventValue=Event()
        self._eventRaised=Event()
        self._eventChanged=Event()
        self._eventUpdated=Event()
        self.onInit()
        self.logger.debug('%s->creating %s' % (self.server.host, self))

    @property
    def parent(self):
        return self._parent

    @property
    def logger(self):
        return self.parent.logger

    @property
    def server(self):
        return self.parent.server

    @property
    def memory(self):
        return self.server.memory

    @property
    def index(self):
        return self._index

    def next(self, n=1):
        """
        return the next item (i.e. the one with index=self.index+1)
        return none if index+1 don't exists
        """
        return self.parent.item(self.index+n)

    def previous(self, n=1):
        """
        return the previous item (i.e. the one with index=self.index-1)
        return none if index-1 don't exists
        """
        return self.parent.item(self.index-n)

    def match(self, key):
        try:
            if key in self.tag:
                return True
        except:
            pass

        try:
            if int(key)==self.index:
                return True
        except:
            pass
        return False

    def onInit(self):
        pass

    def setRefreshDelay(self, delay):
        self._delayRefresh=delay

    def getRefreshDelay(self):
        try:
            if self._delayRefresh is not None:
                return self._delayRefresh
            return self.parent.getRefreshDelay()
        except:
            return 60

    def validateValue(self, value):
        return value

    def setReadOnly(self, state=True):
        self._readOnly=state

    def isReadOnly(self):
        if self._readOnly or self.parent.isReadOnly():
            return True
        return False

    def signalPush(self, value):
        if self.parent.isLocalNodeMode():
            self.setValue(value)
        else:
            if not self._eventPush.isSet():
                self._eventPush.set()
                self._parent.signalPush(self)
            with self._parent._lock:
                self._pushValue=value

    def isPendingPushRequest(self):
        if self._eventPush.isSet():
            return True
        return False

    def clearPush(self):
        self._eventPush.clear()

    def signalPull(self, urgent=False):
        if not self.parent.isLocalNodeMode():
            if not self._eventPull.isSet():
                self._eventPull.set()
                self._eventValue.clear()
                self._parent.signalPull(self, urgent)

    def clearPull(self):
        self._eventPull.clear()

    def isPendingPullRequest(self):
        if self._eventPull.isSet():
            return True
        return False

    def setValue(self, value, force=False):
        # we must be able to setValue from a readItemResponse
        if value is not None and (force or not self.isReadOnly()):
            value=self.validateValue(value)
            with self._parent._lock:
                # only if we have already received a value
                if self._stamp>0 or self.server.isLocalNodeMode():
                    if not self._value and value:
                        self._eventRaised.set()
                    if value!=self._value:
                        self._eventChanged.set()
                self._stamp=time.time()
                self._value=value
            self._eventValue.set()
            self._eventUpdated.set()

    def getValue(self):
        with self._parent._lock:
            return self._value

    @property
    def value(self):
        return self.getValue()

    @value.setter
    def value(self, value):
        if not self.isReadOnly():
            value=self.validateValue(value)
            with self._parent._lock:
                if self._value!=value:
                    self.signalPush(value)

    def isRaised(self, reset=True):
        raised=self._eventRaised.isSet()
        if raised and reset:
            self._eventRaised.clear()
        return raised

    def isChanged(self, reset=True):
        changed=self._eventChanged.isSet()
        if changed and reset:
            self._eventChanged.clear()
        return changed

    def isUpdated(self, reset=True):
        if self._eventUpdated.isSet():
            if reset:
                self.clearUpdated()
            return True
        return False

    def clearUpdated(self):
        self._eventUpdated.clear()

    def waitUpdated(self, timeout=3.0):
        try:
            self._eventUpdated.wait(timeout)
            return True
        except:
            pass
        return False

    @property
    def bool(self):
        if self.value:
            return True
        return False

    @property
    def pushValue(self):
        with self._parent._lock:
            return self._pushValue

    def age(self):
        with self._parent._lock:
            return time.time()-self._stamp

    def isAlive(self, maxAge=None):
        if self.server.isAlive():
            if maxAge is None:
                maxAge=max(self.getRefreshDelay()*1.5, 15.0)
            if self.age()<=maxAge:
                return True
        return False

    def pull(self):
        return False

    def push(self):
        return False

    def manager(self):
        age=self.age()
        if age>=self.getRefreshDelay():
            if age<180:
                self.signalPull()
            else:
                # special case for non responsive items, avoiding
                # permanent retries
                if time.time()>=self._inhibitTimeout:
                    self.signalPull()
                    self._inhibitTimeout=time.time()+10.0

    def refresh(self, urgent=False):
        self.signalPull(urgent)

    def read(self, timeout=15.0):
        self.refresh(urgent=True)
        try:
            if timeout<=0:
                timeout=None
            self._eventValue.wait(timeout)
            return self.value
        except:
            pass
        return None

    def clear(self):
        self.value=0

    def strValue(self):
        try:
            return str(self.value)
        except:
            pass
        return ''

    @property
    def tag(self):
        return None

    def __repr__(self):
        tag=self.tag
        raised=self._eventRaised.isSet()
        changed=self._eventChanged.isSet()
        if tag:
            return '<%s(index=%d, tag=%s, value=%s, age=%ds, refresh=%.01fs, alive=%d, raised=%d, changed=%d)>' % (self.__class__.__name__,
                self.index, tag, self.strValue(), self.age(), self.getRefreshDelay(), self.isAlive(), raised, changed)
        else:
            return '<%s(index=%d, value=%s, age=%ds, refresh=%.01fs, alive=%d, raised=%d, changed=%d)>' % (self.__class__.__name__,
                self.index, self.strValue(), self.age(), self.getRefreshDelay(), self.isAlive(), raised, changed)

    @property
    def formatedvalue(self):
        return self.value

    @formatedvalue.setter
    def formatedvalue(self, value):
        self.value=value


class SAIABooleanItem(SAIAItem):
    def validateValue(self, value):
        try:
            return bool(value)
        except:
            return False

    def on(self):
        self.value=True

    def isOn(self):
        if self.value:
            return True
        return False

    def off(self):
        self.value=False

    def isSet(self):
        return self.bool

    def isOff(self):
        return not self.bool

    def isClear(self):
        return self.isOff()

    def set(self):
        self.on()

    def clear(self):
        self.off()

    def toggle(self):
        self.value=not self.value

    def strValue(self):
        if self.value:
            return 'ON'
        return 'OFF'


class SAIAAnalogItem(SAIAItem):
    def onInit(self):
        super(SAIAAnalogItem, self).onInit()
        self._formater=None

    def validateValue(self, value):
        try:
            if type(value)==float:
                formater=SAIAValueFormaterFFP()
                return formater.encode(value)

            return int(value)
        except:
            pass
        return value

    def setFormater(self, formater):
        if formater:
            assert isinstance(formater, SAIAValueFormater)
            self._formater=formater

    @property
    def formatedvalue(self):
        try:
            return self._formater.decode(self.getValue())
        except:
            return self.value

    @formatedvalue.setter
    def formatedvalue(self, value):
        try:
            self.value=self._formater.encode(value)
        except:
            self.value=value

    @property
    def float32(self):
        formater=SAIAValueFormaterFloat32()
        if not self._formater:
            self._formater=formater
        return formater.decode(self.getValue())

    @float32.setter
    def float32(self, value):
        formater=SAIAValueFormaterFloat32()
        if not self._formater:
            self._formater=formater
        self.value=formater.encode(value)

    @property
    def sfloat32(self):
        formater=SAIAValueFormaterSwappedFloat32()
        if not self._formater:
            self._formater=formater
        return formater.decode(self.getValue())

    @sfloat32.setter
    def sfloat32(self, value):
        formater=SAIAValueFormaterSwappedFloat32()
        if not self._formater:
            self._formater=formater
        self.value=formater.encode(value)

    @property
    def int10(self):
        formater=SAIAValueFormaterInteger10()
        if not self._formater:
            self._formater=formater
        return formater.decode(self.getValue())

    @int10.setter
    def int10(self, value):
        formater=SAIAValueFormaterInteger10()
        if not self._formater:
            self._formater=formater
        self.value=formater.encode(value)

    @property
    def ffp(self):
        formater=SAIAValueFormaterFFP()
        if not self._formater:
            self._formater=formater
        return formater.decode(self.getValue())

    @ffp.setter
    def ffp(self, value):
        formater=SAIAValueFormaterFFP()
        if not self._formater:
            self._formater=formater
        self.value=formater.encode(value)

    @property
    def float(self):
        formater=SAIAValueFormaterFFP()
        if not self._formater:
            self._formater=formater
        return formater.decode(self.getValue())

    @float.setter
    def float(self, value):
        formater=SAIAValueFormaterFFP()
        if not self._formater:
            self._formater=formater
        self.value=formater.encode(value)

    def strValue(self):
        if self.value is not None:
            return '%d' % self.value
        return '<null>'

    @property
    def hex(self):
        try:
            return hex(self.value)
        except:
            return

    @property
    def bin(self):
        try:
            return bin(self.value)
        except:
            return


class SAIAItems(object):
    def __init__(self, memory, itemType, maxsize, readOnly=False):
        assert memory.__class__.__name__=='SAIAMemory'
        self._memory=memory
        self._localNodeMode=memory.isLocalNodeMode()
        self._lock=RLock()
        self._itemType=itemType
        self._maxsize=maxsize
        self._readOnly=readOnly
        self._items=[]
        self._indexItem={}
        self._timeoutSort=0
        self._currentItem=0
        self._delayRefresh=60

    @property
    def memory(self):
        return self._memory

    @property
    def server(self):
        return self.memory.server

    @property
    def logger(self):
        return self.memory.logger

    def isLocalNodeMode(self):
        return self._localNodeMode

    def setReadOnly(self, state=True):
        self._readOnly=state

    def isReadOnly(self):
        if self._readOnly or self.memory.isReadOnly():
            return True
        return False

    def setRefreshDelay(self, delay):
        self._delayRefresh=delay

    def getRefreshDelay(self):
        return self._delayRefresh

    def count(self):
        with self._lock:
            return len(self._items)

    def resolveIndex(self, index):
        """
        Provide a name (tag) to index resolution mecanism
        Must be implemented by subclass if needed
        """
        return None

    def validateIndex(self, index):
        try:
            try:
                n=int(index)
            except:
                try:
                    n=self.resolveIndex(index)
                except:
                    pass

            if n>=0 and n<self._maxsize:
                return n
        except:
            pass

    def isIndexValid(self, index):
        if self.validateIndex(index) is not None:
            return True
        return False

    def all(self):
        return self._items

    def alive(self, maxAge=None):
        with self._lock:
            return [item for item in self.all() if item.isAlive(maxAge)]

    def dead(self, maxAge=None):
        with self._lock:
            return [item for item in self.all() if not item.isAlive(maxAge)]

    def __iter__(self):
        return iter(self.all())

    def active(self):
        return [item for item in self.all() if item.value]

    def item(self, index):
        try:
            with self._lock:
                return self._indexItem[self.validateIndex(index)]
        except:
            pass

    def isItemDeclared(self, index):
        if self.item(index):
            return True
        return False

    def __getitem__(self, index):
        item=self.item(index)
        if item:
            return item
        try:
            # allow items['*pattern'] usage
            if index[0]=='*':
                return self.declareForTagMatching(index[1:])
        except:
            pass
        if self.memory.isOnTheFlyItemCreationEnabled():
            return self.declare(index)

    def declare(self, index, value=0):
        index=self.validateIndex(index)
        if index is not None:
            item=self.item(index)
            if item:
                return item

            item=self._itemType(self, index, value)
            # item.setReadOnly(self._readOnly)
            with self._lock:
                self._items.append(item)
                self._indexItem[index]=item
                self._timeoutSort=time.time()+10.0
                item.signalPull()
                return item

    def declareFromList(self, indexes, value=0):
        items=[]
        for index in indexes:
            item=self.declare(index, value)
            if item:
                items.append(item)
        return items

    def declareRange(self, index, count, value=0):
        with self._lock:
            items=[]
            for n in range(count):
                item=self.declare(index+n, value)
                items.append(item)
            return items

    def declareFromTo(self, indexFrom, indexTo, value=0):
        count=abs(indexTo-indexFrom)+1
        return self.declareRange(indexFrom, count, value)

    def searchSymbolsWithTag(self, key):
        return

    def declareForTagMatching(self, key):
        items=[]
        try:
            for symbol in self.searchSymbolsWithTag(key):
                items.append(self.declare(symbol.index))
        except:
            pass
        return items

    def signalPush(self, item):
        self.memory._queuePendingPush.put(item)

    def signalPull(self, item, urgent=False):
        if urgent:
            self.memory._queuePendingPriorityPull.put(item)
        else:
            self.memory._queuePendingPull.put(item)

    def refresh(self):
        with self._lock:
            for item in self._items:
                item.refresh()

    def manager(self):
        count=min(64, len(self._items))
        while count>0:
            count-=1
            try:
                with self._lock:
                    item=self._items[self._currentItem]
                    self._currentItem+=1

                try:
                    item.manager()
                except:
                    self.logger.exception('manager()')
            except:
                self._currentItem=0
                if self._timeoutSort>0:
                    with self._lock:
                        if time.time()>self._timeoutSort:
                            # sortimg indexes is useful for request index optimisers
                            self.logger.info('%s re-sorting items indexes' % self)
                            self._items.sort(key=lambda i: i.index)
                            self._timeoutSort=0
                break

    def dump(self):
        with self._lock:
            for item in self._items:
                print(item)

    def table(self, key=None):
        with self._lock:
            if self.count()>0:
                t=PrettyTable()
                t.field_names = ['server', 'index', 'tag', 'value', 'age']
                t.align['server']='l'
                t.align['index']='r'
                t.align['tag']='l'
                t.align['value']='r'
                t.align['age']='l'

                deviceName=self.server.deviceName
                if not deviceName:
                    deviceName=self.server.host

                for item in self._items:
                    if key and not item.match(key):
                        continue
                    age='%.01fs' % item.age()
                    t.add_row([deviceName, item.index, item.tag, item.formatedvalue, age])

                print(t)

    def clear(self):
        with self._lock:
            for item in self._items:
                item.clear()

    def __repr__(self):
        return '<%s(%d items, max=%d, readOnly=%d, current=%d, refresh=%.01fs)>' % (self.__class__.__name__,
                    self.count(),
                    self._maxsize,
                    bool(self._readOnly),
                    self._currentItem,
                    self._delayRefresh)


if __name__ == "__main__":
    pass
