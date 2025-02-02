===================
Python digimat.saia
===================

This is a Python 3 module allowing anyone to create **client** and/or **server** `SAIA EtherSBus <https://wiki.wireshark.org/EtherSBus>`_  nodes.
This code allow you to create low cost, fast and reliable communication services with any EtherSBus device, reading and writing data from/to them. By data (items),
we mean inputs, outputs, flags, registers, timers and counters. In the exemple below, a local SBus node with address 253 (station number, or localid, or lid in our terminology) is created. 

.. code-block:: python

    >>> from digimat.saia import SAIANode
    >>> node=SAIANode(253)

Congratulations ! You just have powered up your first EtherSNode device with 2 lines of code. A **background task handle now for you all the network SBus frames**. 
Open your SAIA PG5 Debugger and try to read/write some data **to** your node. Of course, you can also talk to other SAIA PCD EtherSBus devices directly 
from your node trough le LAN (read/write flags, registers, ... on remote PCDs). This will be explained below (see "EtherSBus Client" chapter). To give you an idea on how to use this module, you will find a basic `Python interactive session demo here <https://www.youtube.com/watch?v=QEPai3HXICY>`_. 

.. image:: https://st-sa.ch/img/figures/digimat-saia-asciinema.png
   :width: 360px
   :target: https://www.youtube.com/watch?v=QEPai3HXICY

When done, shutdown your node properly.

.. code-block:: python

    >>> node.stop()
    >>> quit()

Warning : if you observe a socket error at node start, this is probably due to the fact that the listening port is already opened on your machine from
an other process. The default listening port is 5050. Try changing it to see if this fix the problem

.. code-block:: python

    >>> node=SAIANode(253, port=15050)


Non exhaustive features list
============================

Out of the box features

* EtherSbus Server (expose local data to other EtherSBus nodes)
* EtherSBus Client (remote access to N remote EtherSBus nodes)
* Local Server AND Remote Client(s) simultaneous communication support
* Read/Write of local and remote Inputs/Outputs/Flags/Registers/Timers/Counters data values trough simple objects ".value" get/set
* Background task (thread) managing every server+clients messages once the node is started
* Registers value encoders allowing working transparently with float, float32 and some other encodings
* Automatic pooling in the background of every declared remote items (manual refresh is also possible)
* Node station address automatic resolution
* Automatic read/write requests aggregations (using one message for multiple items transfer)
* Prioritized request queuing allowing urgent transactions to be processed first, providing good 
  responsiveness even with tons of pooled items
* Lightweight enough to be comfortably run on "poor" hardware systems (Raspberry Pi)
* Compatible with the SAIA PG5 Debugger (display/write/clear orders)

Optional features

* Automatic *on-the-fly* local items creation when accessed by remote nodes (without prior declaration). This
  allows very easy EtherSBus node creation, working *out-of-the-box* once launched
* Periodic remote node discovering and declaration (trough broadcast messages)
* Automatic remote node information retrieval (trough READ_DBX blocks transfers),
  allowing to guess the PG5 compiler generated .map symbol file name ;) you will learn to love your .map files
* PG5 symbols files (.map) parsing, allowing flags, registers, timers and counters symbolic access !
* Dynamic objects creation at runtime when .map file is loaded to enhance Python 
  interactive sessions experience (autocompletion)
* Logging for local or remote debugging trough TCP/IP.


SAIA EtherSBus
==============

The EtherSBus is mainly an UDP encapsulated version of the serial SAIA S-Bus. The EtherSBus is `natively implemented <https://www.sbc-support.com/fr/product-category/communication-protocols/>`_
in any SAIA nodes having a LAN port, providing a very easy way to exchange (read/write) information with 3rd party devices. Using native S-Bus protocol instead 
of something more *standard* like Modbus/IP or BACnet/IP has some advantages

* No (or very few) setup is needed on the existing SAIA CPUs (means no or very few additional costs)
* Mapping SAIA variables to Modbus/BACnet variables require additional specific config and hardware ressources that you may not have
* Data communication using more sophisticated protocols like BACnet use more encapsulation around exchanged data. Using EtherSBus
  is more *lightweight* and efficient.

The digimat.saia module was mainly created to partially explore the S-Bus mecanisms on Raspberry Pi devices 
before starting a deeper implementation on our `Digimat <https://www.st-sa.ch/digimat.html>`_ HVAC BMS infrastructures. SAIA Burgess
has absolutely **no implication** on this project and cannot be held responsible for any problem of any kind if you decide to use this module.

At this time, we don't have access to any S-Bus or EtherSBus protocol official specifications. This is the result of a "blind" protocol analysis, with
no information given by SAIA (no pain, no gain). If you own such documentation, please forward it to us (fhess [at] st-sa [dot] ch), 
as SAIA doesn't want to provide it to us ;( If you need to learn about this protocol, some good starting points may include :

* `WireShark EtherSBus plugin source code <https://github.com/boundary/wireshark/blob/master/epan/dissectors/packet-sbus.c>`_
* `SBPoll Python EtherSBus source code <http://mblogic.sourceforge.net/mbtools/sbpoll.html>`_
* `SAIA faq <http://www.sbc-support.ch/faq>`_
* The protocol specification *should* be theorically available upon request per email to SAIA at support [at] saia-pcd [dot] com, 
  but you will need to sign a non disclosure agreement. Ask for the "**Utilization Agreement for Saia S-Bus Developer Documentation**" document.
  We have never received any response to thoses requests ;(

Using the SAIA PG5 debugger may also help understanding how things works. Wireshark has an excellent protocol decoder 
and you will easily find some .pcap samples by googling "sbus pcap". Really useful.

Don't forget that the SAIA dynamic addressing won't be your friend here as you must know the address of the variable
you want to access (read/write). Consider fixing your variables to "static" addresses in your PG5 configuration (**read SAIA FAQ 101533**, to knows actions that may affect variables
address change). We have implemented some helpers to provide limited symbolic access using the PG5 .map file if you have it (see chapter "Symbolic Adressing" below).
There are some tricks available to help you using items tag name ;)

Oh, and of course, EtherSBus communication has to be enabled on your PCD device ;)


Installation
============

Nothing specific here, just use pip (which will also install modules dependencies)

.. code-block:: bash

    pip install -U digimat.saia

On Windows, you will need to install (if not already done) the `Microsoft Visual C++ Build Tool <https://visualstudio.microsoft.com/fr/downloads/>`_, required to install some dependencies. This can take some time to install it.


EtherSBus Node (Server)
=======================

Once created, the **SAIANode** object will implicitely start a background task responsible for protocol and bus variables management.
The task must be stop()ed before the program termination, to shutdown the background task. The node contains a server (allowing other nodes to read an write 
data to it), and may also connect (acting as a client) to other remote SBus servers to read/write remote data. Each server (local-node or remote-node)
has it's own memory representation (SAIAMemory) in the SAIANode object. Local-node memory is accessible trough node.memory (which is a shortcut to node.server.memory).

The **SAIAMemory** object handle every SBus variables (**inputs**, **outputs**, **flags**, **registers**, **timers**, **counters**). The SAIAMemory object provide a **SAIAItemFlags** object, 
accessible trough a .flags property, itself providing access to every registered SAIAItemFlag object (item). The same principle is used for inputs 
(**SAIAItemInputs**), outputs (**SAIAItemOutputs**), registers (**SAIAItemRegisters**), timers (**SAIAItemTimers**) and counters (**SAIAItemCounters**). Note that there are shortcuts implemented : 
*node.flags* can be used instead of *node.memory.flags*.

.. code-block:: python

    >>> node=SAIANode(253)
    >>> myflag=node.memory.flags[18]

    >>> myflag
    <SAIAItemFlag(index=18, value=OFF, age=1s)>

    >>> myflag.value=True
    >>> myflag.value
    True

The SAIAMemory object is initially created *empty* (with no items declared). Items are dynamically instanciated "on-the-fly" when they are accessed. In the example above,
the flag 18 is created on the first call, and returned in a SAIAItemFlag object. Any further call to this item will always return the same object instance.
Each item provide some helpers methods to facilitate value manipulation

.. code-block:: python

    >>> myflag.off()
    >>> myflag.on()
    >>> myflag.toggle()
    >>> myflag.set()
    >>> myflag.clear()
    >>> myflag.value=1
    >>> myflag.value=True
    >>> myflag.value
    1
    >>> myflag.isSet()
    True
    >>> myflag.isClear()
    False

By default, "on-the-fly-item-creation" is active. This means that any data item (flag, input, output, register) which is accessed (locally or remotely)
will be dynamically instanciated if it doesn't exists.  This can create a large amount of unwanted memory consumption in case of abuse or bug. This mode can
be disabled, and accessing a non pre-declared item will fail.

.. code-block:: python

    >>> node.memory.enableOnTheFlyItemCreation(False)
    >>> node.memory.flags[19]
    None

Items can be manually-created by "declaring" them, individually or by range

.. code-block:: python

    >>> myflag=node.memory.flags.declare(index=18)
    >>> myflags=node.flags.declareRange(index=100, count=3)
    >>> myflags
    [<SAIAItemFlag(index=100, value=OFF, age=3s)>,
    <SAIAItemFlag(index=101, value=OFF, age=3s)>,
    <SAIAItemFlag(index=102, value=OFF, age=3s)>]

You will also later discover a powerful .declareForTagMatching() feature allowing to works with symbols names instead of indexes. Inputs, Outputs and Flags are boolean items. 
Registers, Timers and Counters are simple "32 bits uint values".

.. code-block:: python

    >>> myregister=node.memory.registers[0]
    >>> myregister.value=100
    >>> register.value
    100

Registers are always stored as "raw 32 bits" values (without encoding). Helpers are available to set/get the register value with common encodings

.. code-block:: python

    >>> myregister.float32=21.5
    >>> myregister.value
    1101791232
    >>> myregister.float32
    21.5

Actually, the following encoders/decoders accessors are implemented (each one is a derived class from **SAIAValueFormater**)

+-----------------------+-----------------------------------------------------+
| **.float32**          | IEEE float32 encoding (big-endian)                  |
+-----------------------+-----------------------------------------------------+
| **.sfloat32**         | Swapped IEEE float32 encoding (little-endian)       |
+-----------------------+-----------------------------------------------------+
| **.ffp**              | Motorola Fast Floating Point encoding (SAIA Float)  |
+-----------------------+-----------------------------------------------------+
| **.float**            | Alias for FFP encodings (easier to remember)        |
+-----------------------+-----------------------------------------------------+
| **.int10**            | x10 rounded value (21.5175 is encoded as 215)       |
+-----------------------+-----------------------------------------------------+
| **.formatedvalue**    | Reuse the last used formater                        |
+-----------------------+-----------------------------------------------------+

As in SAIA float values *seems* to be FFP encoded (not really sure about that), the ffp encoder is automatically used
when writing a float value to a register (instead of an int)

.. code-block:: python

    >>> myregister.value=2
    >>> myregister.value
    2
    >>> myregister.value=2.0
    >>> myregister.value
    2147483714
    >>> myregister.ffp
    2.0
    >>> myregister.float
    2.0

If for any reason you want your localnode to be read-only (for any 3rd party EtherSBus client), you can
lock your local memory

.. code-block:: python

    >>> node.memory.setReadOnly()

This can be very useful to implement a data-provider-only service, simply ignoring any incoming SBus write requests. Thoses
requests will be NAKed by your node. Timers are managed (those declared *in the local node*). This means that any timer created will be automatically decremented until reaching 0

.. code-block:: python

    >>> timer=node.server.timers[0]
    >>> timer.value=1000
    >>> # wait some time
    >>> timer.value
    874
    >>> timer.value
    510
    >>> timer.isTimeout()
    False
    >>> timer.clear()
    >>> timer.isTimeout()
    True

The default tickBaseTime is 100ms (decrement each counter by 1 every 100ms), which can be set on the timers object 

.. code-block:: python

    >>> node.server.timers.setTickBaseTimeMs(100)


EtherSBus Client
================

Now the best part. The node object allow access to (as many) remote EtherSBus node servers you need, registered in a **SAIAServers** object

.. code-block:: python

    >>> server1=node.servers.declare('192.168.0.100')
    >>> server2=node.servers.declare('192.168.0.101')
    >>> myRemoteFlag=server1.memory.flags[5]

The declaration process provide a **SAIAServer** object, containing a **SAIAMemory** object to access remote items. You don't have to store your servers
into variables. You can always retrieve later your servers from the ip or the address (lid)

.. code-block:: python

    >>> pcd=node.servers['192.168.0.100']   # access by ip
    >>> pcd=node.servers[50]                # access by address (lid)

In any case, redeclaring a server that was already declared don't create a double. The existing server, if found, is returned. Same concept with items (flags, registers, ...).

Thus, **local and remote data can be manipulated 
in the same manner**. When a remote data item (input, output, flag, register, timer or counter) is declared, an **automatic pooling mecanism** is launched in 
the background task (manager). An **optimiser mecanism try to group many items per request**, avoiding to launch 1 request for 1 item refresh.

The default refresh rate is **60s** per item, modifiable with a myRemoteFlag.setRefreshDelay() call. Alternatively, the refresh rate can be specified 
for the whole item collection, with a node.memory.flags.setRefreshDelay() call. Refresh can be triggered on demand with with theses kind of call

.. code-block:: python

    >>> node.servers.refresh() or node.refresh()
    >>> server.memory.refresh() or server.refresh()
    >>> server.memory.flags.refresh() or server.flags.refresh()
    >>> myRemoteFlag.refresh()

You can query the elapsed time (in seconds) since the last value update (refresh) with the myRemoteFlag.age() method.  If you really need to get the very 
actual value of an item (and not the last refreshed one), you need to initiate an item.refresh() and then 
wait *a certain amount of time* allowing the read queue to be processed by the background task. This is a crucial point, everything is done asynchronously : modifying the
value of a register, for example with register.value=100, simply queue a write order and returns (immediately). The write will be processed as soon as possible, but later.
If you have declared thousand of items, this *may* take a while. The whole thing can also be done more synchrounously with a simple item.read(),
returning the just refreshed item.value (or None in case of timeout)

.. code-block:: python

    >>> myRemoteFlag.read()
    True

Theses refresh orders are **processed with more priority** than other "standard" polling-read, providing better responsiveness.
A timeout can be passed to the read() function. **Changing** (**writing**) the remote data value is fully transparent

.. code-block:: python

    >>> myRemoteFlag.value=1

For a non local object, **this will automatically queue a write order** in the SAIAServer object with the new given value. **The actual value of the item
remains unchanged**. **When the write order has been executed**, **a refresh order is immediately triggered**, thus **allowing the actual value to be updated**. 
This tend to keep the value synchronized with the remote value, even if something goes wrong. As for read() orders, the read-after-write is
processed with **more priority** than standard pooling requests (more responsive). Please note that this approach *can* be problematic to write fast ON/OFF bursts.

If for any reason you want to deny writes to your remote server, you can lock your remote server memory as needed, 
allowing you to avoid some unwanted critical problems ;)

.. code-block:: python

    >>> server.setReadOnly()
    >>> server.flags.setReadOnly()
    >>> server.registers.setReadOnly()
    >>> server.registers[100].setReadOnly()
    >>> server.flags[10].setReadOnly()

The background manager try to be as reactive and idle as possible, keeping ressources for your application. Performance is really good, even with a lot of servers and/or items declared. 
We tried to trap most of the possible errors, allowing using this module to be used as a standalone service. Note that automatic SAIA address 
resolution is implemented, so that only remote IP address is required to register a remote node. If known, the SAIA station address *can* be
given during registration (this will avoid the initial address resolution requests to get the server address).

.. code-block:: python

    >>> server=node.servers.declare(host, lid=54, port=5050)

As with items, servers can be declared by range for more convenience, by giving the ip address of the first server. The example below creates for you
10 servers (from 192.168.0.100 to 192.168.0.109, assigned with station addresses 200..209). 

.. code-block:: python

    >>> servers=node.servers.declareRange('192.168.0.100', count=10, lid=200, port=5050)

Remember that declared servers can be retrieved at any time by lid or by ip address using the SAIAServers object 

.. code-block:: python

    >>> server=node.servers[200]
    >>> server1=node.servers['192.168.0.100']

The background task poll each declared servers to maintain their running status (with READ_PCD_STATUS_OWN requests). The actual
run status of a server is accessible trough the .status property 

.. code-block:: python

    >>> server.status
    82 (0x52)
    >>> server.isRunning()
    True
    >>> server.isStopped()
    False
    >>> server.isHalted()
    False

If your remote servers are stopped, this can be annoying ;) You can start them with the .run() method without 
using the PG5 or the Debugger programs (assuming that *you* know what your are doing) 

.. code-block:: python

    >>> server.run()    # .stop() and .restart() are also available -- be careful
    >>> servers.run()   # .stop() and .restart() are also available -- be careful


Data Transfers with Remote Servers
==================================

The SAIAServer object contains a **SAIATransferQueue** service allowing to submit and queue **SAIATransfer** jobs in the background, used
for processing transfers that require multiple packet exchange like *read-block*, for example. **When a remote server is declared**, **some
READ_DBX requests will be automatically done using a SAIATransferReadDeviceInformation with the remote server to retrieve the device 
information memory block**, containing this kind of config

.. code-block:: python

    PG5Licensee=DEMONSTRATION VERSION
    PG5DeveloperID=CH_xxxxxxxx
    PCName=WINFHE
    Originator=DEMONSTRATION VERSION
    PG5Version=V2.2.230
    ProjectName=Test1
    DeviceName=Device1
    PcdType=PCD1.M2220
    ANSICodePage=1252
    ProgramVersion=1.0
    ProgramID=E291E0E08F55CBEC
    ProgramCRC=061C66CD
    BuildDateTime=2017/08/18 17:46:50
    DownloadDateTime=2017/08/18 17:49:47

Once retrieved, theses informations may be accessed with the server.getDeviceInfo() method (case insensitive)

.. code-block:: python

    >>> server.getDeviceInfo('DeviceName')
    'Device1'

The DeviceName, DeviceType (PcdType) and BuildDateTime can also be directly accessed as a server's property method

.. code-block:: python

    >>> server.deviceName
    'Device1'
    >>> server.deviceType
    'PCD1.M2220'
    >>> server.buildDateTime
    datetime.datetime(2017, 8, 18, 17, 46, 50)

You can force a deviceInfo refresh later if anything goes wrong

.. code-block:: python

    >>> server.submitTransferReadDeviceInformation()

If the deviceName is compatible with Python class variable naming convention, the SAIAServer object is automatically mapped (mounted)
to a variable with the same name (but lowercase and normalized) accessible in the node.servers (SAIAServers) object

.. code-block:: python

    >>> server=node.servers.device1

This is really useful in interactive sessions when combined with automatic node discovering (see below). 


Network nodes discovering
=========================

Every SAIANode has a local SAIAServer object (node.server) allowing local data to be accessed by other SAIA EtherSBus clients. This local server
has a manager() periodically called by the background task. You can ask this task to periodically scan the network and potentially discover
other EtherSBus servers online on the LAN

.. code-block:: python

    >>> node.server.enableNetworkScanner(True)

This will periodically broadcast a READ_STATIONNUMBER on the network (255.255.255.255) using a SAIATransferDiscoverNodes transfer service.
When discovering mode is active, any response to this message received by the local node (not comming from a local network interface) will be 
accepted and the corresponding remote server will be automatically declared for you. For convenience, the discover process is automatically started in Python interactive mode. In fact,
you can decide if network scanning should be active or not at the node creation

.. code-block:: python

    >>> node=SAIANode()              # network scanner is enabled only in interactive sessions
    >>> node=SAIANode(scanner=True)  # scanner is enabled
    >>> node=SAIANode(scanner=False) # scanner is disabled

Warning : we have seen some problems with node discovering enabled if nodes stations addresses are not unique. This has to be fixed in the future.


Symbolic Addressing
===================

The EtherSBus doesn't provide item access by name (symbol name, tag). But **if you own the PG5 .map file generated at compile time**, you may have some help by passing
this file during server declaration process. This will create a **SAIASymbols** object associated with the server, ready to serve you the requested **SAIASymbol**

.. code-block:: python

    >>> server=node.servers.declare('192.168.0.48', mapfile='xxxxx.map')
    >>> server.symbols.count()
    2140

    >>> symbol=server.symbols['RIO.Station_A12.Sonde3_16_Cmd_Reduit_Ch'] 
    >>> symbol.index
    2295
    >>> symbol.attribute
    'f'
    >>> symbol.isFlag()
    True

    >>> symbol=server.symbols.register(2295)
    >>> symbol.tag
    'rio.station_a12.sonde3_16_cmd_reduit_ch' 

**This allows bidirectional mapping between symbols names (tag) and items indexes**, **assuming that your map file is uptodate** ! Cool. The symbolic access is in fact implemented
in all SAIAItem objects index access, so that syntaxes like this are perfectly working

.. code-block:: python

    >>> server.registers[2295].value=99
    >>> server.registers['rio.station_a12.sonde3_16_cmd_reduit_ch'].value
    99

    >>> flag=server.flags.declare('Sonde3_42_Lib')
    >>> flag.index
    4634

The SAIASymbols class may be used to retrieve any *existing item in a .map file*, allowing to declare easily 
any existing flag or registers in a given address range. The trick is to pass a range or an array of addresses (indexes) to
the symbols.register retrieve method. This will return an array of registers instead of a simple register. This returns
only items that are declared in the .map file.

.. code-block:: python

    >>> for symbol in server.symbols.register(range(1000, 2000)):
    >>>    server.registers.declare(symbol.address)


Use it carefully. For ease of use, symbolic access is implemented *case insensitive*. In interactive mode,
you can try to **mount** flags and registers symbols (SAIASymbol) as SAIASymbols object variables
so that the **interpreter autocompletion** will save you some precious keystroke

.. code-block:: python

    >>> symbols=server.symbols
    >>> symbols.mount()

    >>> symbols.flags.sonde3_1<TAB>
    s.sonde3_10_defaut    s.sonde3_13_defaut      s.sonde3_19_defaut
    s.sonde3_10_lib       s.sonde3_13_lib         s.sonde3_19_setpoint
    s.sonde3_10_timeout   s.sonde3_13_timeout     s.sonde3_19_temp
    s.sonde3_11_defaut    s.sonde3_14_defaut      s.sonde3_19_timeout
    s.sonde3_11_lib       s.sonde3_14_lib         s.sonde3_1_defaut
    s.sonde3_11_timeout   s.sonde3_14_timeout     s.sonde3_1_timeout
    s.sonde3_12_defaut    s.sonde3_15_defaut
    s.sonde3_12_lib       s.sonde3_15_lib
    s.sonde3_12_timeout   s.sonde3_15_timeout

    >>> symbols.flags.sonde3_11_timeout.index
    3936

When Python interactive mode is detected, symbols.mount() is automatically called for you. Items declaration can also be passed 
as a SAIASymbol object, so that autocompletion is your friend

.. code-block:: python

    >>> server.flags.declare(symbols.flags.sonde3_11_timeout)
    >>> server.flags.declare(symbols['sonde3_11_timeout'])

As said in the last section, we can access the deviceInformation properties, allowing to guess the .map filename. If the deviceName is "MySuperDevice", the associated 
.map file produced by the SAIA PG5 compiler will be "MySuperDevice.map" by default. In fact, this can help us to do things automagically. 
**When a server is declared, the deviceInformation block is automatically retrieved and a try is made to load the default associated .map file**. By default, the map
file has to be stored in the current directory. This can be changed with the node.setMapFileStoragePath() method.

In Python 2.7, you may need to `enable autocompletion <https://stackoverflow.com/questions/246725/how-do-i-add-tab-completion-to-the-python-shell>`_ 
on your ~/.pythonrc setup file. Alternatively you can use IPython, Jupyter or something simpler like `ptpython <https://github.com/jonathanslenders/ptpython>`_ for
interactive sessions. **Don't miss** the excellent `bpython <https://www.bpython-interpreter.org/>`_ project.

Keep an eye open on your memory ressources when enabling symbols ;) as this can declare thousands of variables.


Tips & Tricks
=============

Servers (SAIAServers), items (SAIAItemFlags/Registers/Inputs/Outputs/Timers/Counters) are *iterable* objects. This allows things like

.. code-block:: python

    >>> server.flags.declareRange(0, 4096)
    >>> # give a little time allowing the background task to refresh thoses 4K items
    >>> flagsThatAreON=[flag for flag in server.flags if flag.value is True]

    >>> for flag in server.flags:
    >>>    flag.value=1

When working with registers, timers and counters,  accessing to the hex or bin value representation can be useful

.. code-block:: python

    >>> register=server.registers[50]
    >>> register.value=100
    >>> register.value
    100
    >>> register.hex
    '0x64'
    >>> register.bin
    '1100100'

When symbols are loaded, SAIAFlags, SAIARegisters, SAIATimers and SAIACounters objects can be declared by a *search* upon a *part* of their
tag name.

.. code-block:: python

    >>> registers=server.registers.declareForTagMatching('sonde')
    >>> len(registers)
    626
    >>> registers=server.registers['*sonde']  # equivalent trick, using a '*' prefix

The *searched argument* may also be a compiled regex

.. code-block:: python

    >>> pattern=re.compile('sonde[0-9]+_[0-9]+_temp')
    >>> registers=server.registers.declareForTagMatching(pattern)

If for any reason you want to *pause* one remote server communications, you can use the server.pause(60) call (seconds). This is for example
internally used to stop server communications when a station address conflict (duplicate address) is detected.


Dumping & Debugging
===================

By default, the module create and use a socket logger pointing on localhost. Launch your own tcp logger server
and you will see the EtherSBus frames. If you don't have one, you can try our simple (and dirty) digimat.logserver

.. code-block:: python

    pip install -U digimat.logserver
    python -m digimat.logserver

You can apply some basic output filtering with optional "--filter string" parameter. You can also give your own logger to the SAIANode

.. code-block:: python

    >>> node=SAIANode(253, logger=mylogger)

By default, the logging output is limited to maximize performance. You can enable (or disable) full messages logging with

.. code-block:: python

    >>> node.debug()
    >>> node.debug(True)
    >>> node.debug(False)

    # or at node creation with
    >>> node=SAIANode(..., debug=True)

If you want to completely disable the logger, just pass a logger=SAIALogger().null() parameter.  Limited dump-debug can 
also be done with objects .dump() methods. Try node.dump(), node.memory.dump(), node.memory.flags.dump(), 
node.servers.dump(), server.dump(), server.registers.dump(), server.flags.dump(), etc. You can also use .table() methods instead of .dump() to get a more "human readable" output style,
a bit like mysql does.

.. code-block:: python

    >>> node.table()
    +-------+-------------------------+-------+------+
    | index | tag                     | value | age  |
    +-------+-------------------------+-------+------+
    |  5848 | ep16.s2.zone01.t1.tm_me |   234 | 3.9s |
    |  5859 | ep16.s2.zone02.t1.tm_me |   236 | 3.8s |
    |  5870 | ep16.s2.zone03.t1.tm_me |   233 | 3.7s |
    |  5881 | ep16.s2.zone04.t1.tm_me |   238 | 3.7s |
    |  5965 | ep16.s2.zone21.t1.tm_me |   241 | 3.3s |
    |  5974 | ep16.s2.zone89.t1.tm_me |   246 | 3.3s |
    |  5983 | ep16.s2.zone90.t1.tm_me |   243 | 3.2s |
    |  5992 | ep16.s2.zone91.t1.tm_me |   242 | 3.2s |
    |  6001 | ep16.s2.zone96.t1.tm_me |   230 | 3.1s |
    |  6010 | ep16.s2.zone98.t1.tm_me |   238 | 3.1s |
    +-------+-------------------------+-------+------+

You can pass a "filter" argument to the .table() method to filter results, i.e node.table('temperature'). There is a little secret trick implemented 
in the SAIAServers object allowing you to be more efficient in interactive mode, simplifying the access 
to flags, registers and other items. Don't use this on your non interactive scripts.

.. code-block:: python

    >>> pcd=node.servers['192.168.0.100']
    >>> register=pcd.r50 # equivalent to pcd.registers[50] or pcd.registers.declare(50)
    >>> flag=pcd.f1000 # equivalent to pcd.flags[1000] or pcd.flags.declare(1000)

If you want to ping yours servers (your remote nodes), you can use the builtin server's ping command which force sending an immediate read-status request to the remote device, then wait for
the response and return True if someting was received. Remeber that you can log the communication traffic by enabling the debug mode on your node (with node.debug())

.. code-block:: python

    >>> server.ping()
    True

There are some useful helpers to check for dead servers or items

.. code-block:: python

    >>> server.isAlive()
    True
    >>> server.flags[10].isAlive()
    True
    >>> node.servers.isAlive()
    True # every server is alive
    >>> onlineServers=node.servers.alive()
    >>> offlineServer=node.servers.dead()
    >>> onlineFlags=server.flags.alive()
    >>> offlineRegisters=server.registers.dead()

An item is considered as alive if it's server is alive and if the item.age() is less than 1.5 times it's refresh delay (=90s by default). And now, a bit of brain manipulation. 
For debugging purposes, you can simulate a remote node by registering a remote server pointing on yourself (woo!)

.. code-block:: python

    >>> server=node.servers.declare('127.0.0.1')
    >>> localFlag=node.memory.flags[1]
    >>> remoteFlag=server.memory.flags[1]

    >>> localFlag.value, remoteFlag.value
    False, False

    >>> remoteFlag.value=1

    # network data synchronisation is done by the background manager task
    # so, remoteFlag and localFlag are two different registers but mirrored

    >>> localFlag.value
    True

In this example, localFlag and remoteFlag points to the same "value", but the remoteFlag is a networked synchronized 
mirror representation of the localFlag. Don't know if this feature could be useful yet, but this is fun.

SAIA* objects *.__repr__* magic method are redefined to provide some useful information about the current state of the object.
This can be useful to gather some informations about your data

.. code-block:: python

    >>> node
    <SAIANode(lid=253, port=5050, 2 servers, booster=0)>

    >>> node.servers
    <SAIAServers(2 items)>

    >>> node.servers[101]
    <SAIAServer(host=192.168.0.49, lid=101, status=0x52)>

    >>> server.memory
    <SAIAMemory(144 items, queues 0R:0R!:0W)>
    # 0R  = number of actual pending item-read in queue (background polling/refresh process)
    # 0R! = number of actual pending urgent item-read in queue (manual refresh, read-after-write)
    # 0W  = number of actual pending item-write in queue

    >>> server.flags
    <SAIAFlags(48 items, max=65535, readOnly=0, current=32, refresh=60s)>

    >>> server.flags[28]
    <SAIAItemFlag(index=28, value=OFF, age=8s, refresh=60s)>


Items groups
============

The module is providing a concept of item group (item collection), allowing you to give more flexibility
on how to read/poll declared items. When your project has a lot of items to manage, this is not always
easy to deal with the background refresh timing of some items. Do you remember the SAIAItem .read() and .refresh()
methods described above ? As a reminder, these refresh orders are **processed with more priority** than other "standard" polling-read, providing better responsiveness.
Remember that the communication process is always fully asynchronous, so that a blocking read is equivalent to "tag some items as poll-urgent and
wait a certain amount of time until they are all refreshed by the background task". 

The SAIAItemGroup object provides a simple way to use this specific "urgent" polling for groups of items. An item group is an instance of the SAIAItemGroup object

.. code-block:: python

   >>> from digimat.saia import SAIAItemGroup
   >>> group=SAIAItemGroup()

which can be populated with any declared item (registers, flags, ...), via the .add() method, one by one
or by array

.. code-block:: python

   >>> group.add(myflag)
   >>> group.add([myflag, myregister])
   >>> group.add(server.registers.declareRange(100, 200))
   
   # note that you can pass items in the group constructor
   >>> group=SAIAItemGroup(server.registers.declareForTagMatching('temperature'))

   # note that the SAIANode and the SAIAServer objects provide a method 
   # helper to create a group instance
   >>> group=node.group(myflag)

A group provide the same .dump() and .table() methods exposed above, allowing to trace this specific data content. An item can
be added to more than one group if needed. Groups can be compared to "vitual structures" that expose some useful methods
to deal with the whole item content

.. code-block:: python

   # force a backgroud high priority refresh of every group's items (non blocking) 
   >>> group.refresh()

   # force a blocking read (refresh and wait for refresh done) 
   # of every group's items (blocking)
   >>> group.read()
   >>> True

   # you can pass the maximum blocking time (s) allowed 
   # return False if every item hasn't be refreshed
   >>> group.read(3.0)
   >>> True
   >>> group.table()
       +----+--------+-------+-------------------------+-------+------+
       | #  | server | index | tag                     | value | age  |
       +----+--------+-------+-------------------------+-------+------+
       | 0  | 1_SUD  |  5994 | ep16.s1.zone01.t1.tm_me |   181 | 2.7s |
       | 1  | 1_SUD  |  6005 | ep16.s1.zone02.t1.tm_me |   197 | 2.7s |
       | 2  | 1_SUD  |  6016 | ep16.s1.zone03.t1.tm_me |   208 | 2.7s |
       | 3  | 1_SUD  |  6027 | ep16.s1.zone11.t1.tm_me |   206 | 2.7s |
       | 4  | 1_SUD  |  6038 | ep16.s1.zone12.t1.tm_me |   218 | 2.7s |
       | 5  | 1_SUD  |  6049 | ep16.s1.zone13.t1.tm_me |   206 | 2.7s |
       +----+--------+-------+-------------------------+-------+------+

A group object is iterable and accessable as an array, allowing you to process items one by one. There are some useful other methods

+-----------------------+-------------------------------------------------------------------------------------------------+
| **.isAlive()**        | check is **every** item of the group is alive                                                   |
+-----------------------+-------------------------------------------------------------------------------------------------+
| **.isChanged()**      | return the **next** item of the group who's value was changed (see above), or None if no more   |
+-----------------------+-------------------------------------------------------------------------------------------------+
| **.isRaised()**       | return the **next** item of the group who's value was raised (see above), or None if no more    |
+-----------------------+-------------------------------------------------------------------------------------------------+


Demo Node
=========

Using command line interpreter is cool, but for debugging, you will need to launch and relaunch your node. 
Here is a minimal empty node implementation, stopable with <CTRL-C> 

.. code-block:: python

    from digimat.saia import SAIANode

    node=SAIANode(253)

    # customize your node here...

    while node.isRunning():
        try:
            # using integrated node.sleep() will 
            # handle CTRL-C and propagate node.stop()
            node.sleep(3.0)

            node.dump()
        except:
            break

    node.stop()


Open your SAIA Debugger on this node, and try reading/writing some items. 
You can also use SBus *clear* requests with i,o,f and r items. For your convenience, 
you can run the demo node shown above with this simple command line

.. code-block:: python

    python -m digimat.saia


TODO
====

Documentation is very incomplete. Don't know if this is useful for someone. Tell it to us.

There is still some more locking mecanisms to implement making the background task really thread safe. The
Python GIL make things yet wrongly safe (but it works very fine).

We have no way to test what the 'S-Bus gateway' feature is. When enabled, a PCD may be able? to expose S-Bus
sub nodes on its EtherSBus interface. This "proxy" mode access? is not supported yet.

A nice idea would be to develop an user interface based on `npyscreen <https://npyscreen.readthedocs.io/#>`_ allowing
rapid online debugging with saia devices ! 


SUPPORTING
==========

If you like this module, or find a useful way to use it, please tell it to the world by posting a message 
on your favorites social networks, including a link to this `digimat.saia's page <https://pypi.org/project/digimat.saia/>`_ !
