# Copyright (c) 2021 Andrei Sukhanov. All rights reserved.
#
# Licensed under the MIT License, (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://github.com/ASukhanov/apstrim/blob/main/LICENSE
#
__version__ = '4.2.3 2025-10-17' # 1)do not safe_exit() after serialize, 2)output file name have form: prefix_yyyymmdd_hhmm.aps

import sys, time, string, copy
import os, pathlib, datetime
import threading
import signal
from timeit import default_timer as timer

import numpy as np

import msgpack as encoder
if encoder.version < (1, 0, 2):
    print(f'MessagePack too old: {msgpack.version}')
    sys.exit()
def encoderDump(buf):
    return encoder.packb(buf, use_single_float=True) 

# Try CBOR encoding
#import cbor2 as encoder
#encoderDump = encoder.dumps

#````````````````````````````Globals``````````````````````````````````````````
Nano = 0.000000001
MinTimestamp = 1600000000 # Minimal possible timestamp
MAXU8 = 256 - 1
MAXI8 = int(256/2) - 1
MAXU16 = int(256**2) - 1
MAXI16 = int(256**2/2) - 1
MAXU32 = int(256**4) - 1
MAXI32 = int(256**4/2) - 1
SPTime = 0
SPVal = 1
#````````````````````````````Helper functions`````````````````````````````````
def printTime(): return time.strftime("%m%d:%H%M%S")
def printi(msg): print(f'INFO_AS@{printTime()}: {msg}')
def printw(msg): print(f'WARN_AS@{printTime()}: {msg}')
def printe(msg): print(f'ERROR_AS@{printTime()}: {msg}')
def printv(msg):
    if apstrim.Verbosity > 0:
        print(f'DBG_AS1: {msg}')
def printvv(msg):
    if apstrim.Verbosity > 1:
        print(f'DBG_AS2: {msg}')

def croppedText(txt, limit=200):
    if len(txt) > limit:
        txt = txt[:limit]+'...'
    return txt

def packnp(key, data, use_single_float=True):
    """ Pack data for fast extraction. If data can be converted to numpy
    arrays, then it will be returned as
    {'dtype':dtype, 'shape':shape, 'value':nparray.tobytes()},
    if not, then they will be returned as is.
    In msgpack the unpacking of bytes is ~100 times faster than unpacking of
    integers"""
    # 50% time is spent here
    try:
        l1 = len(data)
    except:
        #print('Single element, no need to pack')
        return data
    if l1 == 0:
        #print('Empty list, no need to pack')
        return None
    atype = type(data[0])
    try:    l2 = [len(i) for i in data]
    except: l2 = [1]

    raggedArray = l2.count(l2[0])!=len(l2)
    if raggedArray:
        l2max = max(l2)
        printi(f'padding ragged array_{key} to {l2max}, smallest was {min(l2)}')
        #print(f'data: {data}')
        data = [list(a) + [0.]*(l2max - len(a)) for a in data]
        l2 = [len(i) for i in data]
        #print(f'padded: {l2}')
    
    if apstrim.Verbosity>0: printv(croppedText(f'packing{key}, {l1} of {atype}{l2}: {data}'))
    try:
        npdata = np.array(data)
    except Exception as e:
        printw(f'In packnp of item {key}: {e}')
        return None
    #print(f'npdata shape: {npdata.shape} of {npdata.dtype}')
    if npdata.shape == ():
        return data
    if npdata.dtype == 'int64':
        mn = npdata.min()
        mx = npdata.max()
        if -MAXI32 < mn and mx < MAXI32:
            if -MAXI16 < mn and mx < MAXI16:
                if -MAXI8 < mn and mx < MAXI8:
                    npdata = npdata.astype('int8')
                else:
                    npdata = npdata.astype('int16')
            else:
                npdata = npdata.astype('int32')
    else:
        if npdata.dtype == 'float64' and use_single_float:
            npdata = npdata.astype('float32')
    return {'dtype':str(npdata.dtype), 'shape':npdata.shape
    ,'bytes':npdata.tobytes()}

#````````````````````````````Serializer class`````````````````````````````````
class apstrim():
    """
    Create an object streamer.
    
    **publisher**:  Is a class, providing a subscribe() method.
    
    **devPar**:     List of device:parameter strings.
    
    **sectionInterval**:     Data collection period. Data are collected
     continously into a section, which is periodically dumped into the
     logbook file with this time interval (in seconds). 
    
    **compression**:        Enable Compression flag.
    
    **quiet**:              Do not print the section writing progress,
    
    **use_single_float**:     Use single precision float type for float. (default: True)
    
    **dirSize**:    Size of a Table Of Contents, which is written as a first
     object in the logbook file. It contains file positions of sections and
     used for random-access retrieval.
     Default is 10KB, which is good for ~700 entries. If number of sections
     becomes too big, then the table is downsampled twice to fit into this size. 
"""
    EventExit = threading.Event()
    """Calling the EventExit.set() will safely exit the application."""
    Verbosity = 0
    """Show dedugging messages."""
    _eventStop = threading.Event()

    def __init__(self, publisher, devPars:list, sectionInterval=60.
#    , compress=False, quiet=False, use_single_float=True, dirSize=10240):
    , compress=False, quiet=False, dirSize=10240):
        printi(f'apstrim  {__version__}, sectionInterval {sectionInterval}')
        print(f'v: {self.Verbosity}')
        signal.signal(signal.SIGINT, _safeExit)
        signal.signal(signal.SIGTERM, _safeExit)

        self.lock = threading.Lock()
        self.publisher = publisher
        self.devPars = devPars
        self.sectionInterval = sectionInterval
        self.quiet = quiet
        #self.use_single_float = use_single_float

        # table of contents - related variables
        self.dirSize = dirSize
        self.contents_downsampling_factor = 1# No downsampling 

        # create a section Abstract
        self.abstractSection = {'abstract':{'apstrim':__version__,
            'encoder':encoder.__name__, 'sectionInterval':sectionInterval}}
        abstract = self.abstractSection['abstract']

        if compress:
            import lz4framed
            self.compress = lz4framed.compress
            abstract['compression'] = 'lz4framed'
        else:
            self.compress = None
            abstract['compression'] = 'None'
        printi(f'Abstract section: {self.abstractSection}')

        # create par2Index map
        #self.par2Index = [p:(i,pslice) for p in enumerate(self.devPars)]
        #self.par2Index = [p for p in self.devPars]
        self.par2Index = {}
        for idx,dp in enumerate(self.devPars):
            nameRange = dp.rsplit('[')
            _name = nameRange[0]
            if len(nameRange) == 1:
                pslice = None
            else:
                if nameRange[1][-1] != ']':
                    printe(f'PV syntax error: {dp}')
                    sys.exit(1)
                pslice = [int(i) for i in nameRange[1][:-1].split(':')]
                if len(pslice) == 1:
                    pslice = pslice[0],pslice[0]+1
            self.par2Index[_name]= idx,pslice

        if len(self.par2Index) == 0:
            printe(f'Could not build the list of parameters')
            sys.exit()
        printi(f'parameters: {self.par2Index}')

        # a section has to be created before subscription
        self._create_logSection()

        # subscribe to parameters
        for pname in self.par2Index:
            idx,pslice = self.par2Index[pname]
            if apstrim.EventExit.is_set():
                sys.exit(1)
            devPar = tuple(pname.rsplit(':',1))
            # check if PV is alive
            printv(f'check if PV {devPar} is alive')
            try:
                r = self.publisher.get(devPar)
                if isinstance(r,str):
                    raise IOError(r)
                if 'error' in r[devPar]:
                    raise IOError(r[devPar])
                self.publisher.subscribe(self._delivered, devPar)
            except Exception as e:
                printe(f'Could not subscribe for {pname}: {e}')
                sys.exit(1)
                continue
            printv(f'Subscribed: {devPar}')

        # Create the Index section
        pvlist = []
        for  pvname,value in self.par2Index.items():
            idx,pslice = value
            if pslice is not None:
                pvname = f'{pvname}[{pslice[0]}:{pslice[1]}]'
            pvlist.append(pvname)
        self.indexSection = encoderDump({'index':pvlist})
        #printi(f'IndexSection: {self.indexSection}')

    def start(self, prefix='apstrim', howLong=99e6):
        """Start the streaming of the data objects to the logbook file.
        prefix: the file name will have form: prefix_yyyymmdd_hhmm.aps
        **howLong**: Time interval (seconds) for data collection.
        """
        self._eventStop.clear()
        self.howLong = howLong
        #modificationTime = pathlib.Path(fileName).stat().st_mtime
        #dt = datetime.datetime.fromtimestamp(modificationTime)
        #suffix = dt.strftime('_%Y%m%d_%H%M')
        suffix = time.strftime('_%Y%m%d_%H%M.aps')
        fileName = os.path.expanduser(prefix+suffix)

        self.logbook = open(fileName, 'wb')

        # write a preliminary 'Table of contents' section
        self.contentsSection = {'contents':{'size':self.dirSize}, 'data':{}}
        self.dataContents = self.contentsSection['data']
        self.logbook.write(encoderDump(self.contentsSection))
        # skip the 'Table of contents' zone of the logbook
        self.logbook.seek(self.dirSize)

        # write the sections Abstract and Index
        printv(f'write Abstract@{self.logbook.tell()}')
        self.logbook.write(encoderDump(self.abstractSection))
        printv(f'write Index@{self.logbook.tell()}')
        self.logbook.write(self.indexSection)
        savedPos = self.logbook.tell()

        self._create_logSection()

        #printi('starting serialization  thread')
        myThread = threading.Thread(target=self._serialize_sections)
        myThread.start()

        printi(f'Logbook file: {fileName} created')

    def stop(self):
        """Stop the streaming."""
        printv('>stop()')
        self._eventStop.set()
        #self.logbook.close()

    def _delivered(self, *args):
        """Callback, specified in the subscribe() request. 
        Called when the requested data have been changed.
        args is a map of delivered objects."""
        if apstrim.Verbosity > 0:
            printvv(f'delivered: {args}')
        with self.lock:
          for devPar,props in args[0].items():
            #print(croppedText(f'devPar: {devPar,props}'))
            try:
                if isinstance(devPar, tuple):
                    # EPICS and ADO packing
                    if len(devPar) > 1:
                        dev,par = devPar
                        devpar = devPar[0]+':'+devPar[1]
                    else:
                        devpar = devPar[0]
                    value = props['value']
                    timestamp = props.get('timestamp')# valid in EPICS and LITE
                    if timestamp == None:# decode ADO timestamp 
                        timestamp = int(props['timestampSeconds']/Nano
                        + props['timestampNanoSeconds'])
                    else:
                        timestamp = int(timestamp/Nano)
                    if timestamp < MinTimestamp:
                        # Timestamp is wrong, discard the parameter
                        printv(f'timestamp is wrong {timestamp, MinTimestamp}')
                        continue
                    skey,pslice = self.par2Index[devpar]
                    self.timestamp = int(timestamp*Nano)
                    self.sectionPars[skey][SPTime].append(timestamp)
                    if pslice is not None:
                        _slice = slice(*pslice)
                        value = value[_slice]
                    self.sectionPars[skey][SPVal].append(value)
                elif devPar == 'ppmuser':# ADO has extra item, skip it.
                    continue
                else:
                    #LITE packing:
                    dev = devPar
                    pars = props
                    ##print(croppedText(f'pars: {pars}'))
                    for par in pars:
                        try:
                            value = pars[par]['v']
                            timestamp = int(pars[par]['t'])
                        except: # try an old LITE packing
                            value = pars[par]['value']
                            timestamp = int(pars[par]['timestamp']/Nano)
                        if timestamp < MinTimestamp:
                            # Timestamp is wrong, discard the parameter
                            continue
                        skey,pslice = self.par2Index[dev+':'+par]
                        # add to parameter list
                        self.timestamp = int(timestamp*Nano)
                        self.sectionPars[skey][SPTime].append(timestamp)
                        #print(croppedText(f'value: {value}'))
                        self.sectionPars[skey][SPVal].append(value)
                #print(f'devPar {devPar}@{timestamp,skey}:{timestamp,value}')
            except Exception as e:
                printw(f'exception in unpacking: {e}')
                continue
        #print(croppedText(f'section: {self.section}'))
        
    def _create_logSection(self):
        with self.lock:
            #print('create empty section')
            try:
                tstart = self.timestamp
            except:
                #tstart = int(time.time()/Nano)
                tstart = int(time.time())
            #self.sectionPars = {i:([],[]) for i in self.par2Index.values()}
            self.sectionPars = {i:([],[]) for i in range(len(self.par2Index))}
            self.section = {'tstart':tstart, 'tend':None
            ,'pars':self.sectionPars}

    def _serialize_sections(self):
        periodic_update = time.time()
        statistics = [0, 0, 0, 0, 0.]#
        NSections, NParLists, BytesRaw, BytesFinal, LogTime = 0,1,2,3,4
        maxSections = 0 if self.howLong == self.sectionInterval\
          else self.howLong//self.sectionInterval
        printv(f'serialize_sections started.')
        try:
          while statistics[NSections] <= maxSections\
              and not self._eventStop.is_set():
            self._eventStop.wait(self.sectionInterval)
            logTime = timer()

            # register the section in the table of contents,
            # this should be skipped when the contents downsampling is active.
            rf = self.contents_downsampling_factor
            if rf <=1 or (statistics[NSections]%rf) == 0:
                self.dataContents[self.section['tstart']]\
                = self.logbook.tell()
                packed = encoderDump(self.contentsSection)
                if len(packed) < self.dirSize:
                    self.packedContents = packed
                else:
                    printw((f'The contents size is too small for'
                    f' {len(packed)} bytes. Half of the entries will be'
                    ' removed to allow for more entries.}'))
                    self.contents_downsampling_factor *= 2
                    downsampled_contents = dict(list(self.dataContents.items())\
                      [::self.contents_downsampling_factor])
                    self.contentsSection['data'] = downsampled_contents
                    printv(f'downsampled contentsSection:{self.contentsSection}')
                    self.packedContents = encoderDump(self.contentsSection)

            # Update Directory section on the file.
            currentPos = self.logbook.tell()
            self.logbook.seek(0)
            self.logbook.write(self.packedContents)
            self.logbook.seek(currentPos)

            statistics[NSections] += 1
            printv(f'section{statistics[NSections]} {self.section["tstart"]} is ready for writing to logbook @ {self.logbook.tell()}')
            try:
                self.section['tend'] = self.timestamp
            except:
                printw(f'No data recorded in section {statistics[NSections]}')
                #sys.exit()
                continue

            # pack to numpy/bytes, they are very fast to unpack
            npPacked = {}
            with self.lock:
                for key,val in self.sectionPars.items():
                    statistics[NParLists] += 1
                    #print(croppedText(f'sectItem:{key,val}'))
                    sptimes = packnp(key, val[SPTime])
                    if sptimes is None:
                        continue
                    spvals = packnp(key, val[SPVal])
                    npPacked[key] = (sptimes, spvals)
            if apstrim.Verbosity >= 2:
                printvv(croppedText(f"npPacked: {self.section['tstart'], npPacked.keys()}"))
                for i,kValues in enumerate(npPacked.items()):
                    printvv(croppedText(f'Index{i}: {kValues[0]}'))
                    for ii,value in enumerate(kValues[1]):
                        printvv(croppedText(f'kValue{ii}[{len(value["bytes"])}]: {value}'))

            # msgpack
            toPack = {'tstart':self.section['tstart']
            ,'tstart':self.section['tstart'],'pars':npPacked}
            packed = encoderDump(toPack)
            statistics[BytesRaw] += len(packed)

            # compress, takes almost no time.
            if self.compress is not None:
                compressed = self.compress(packed)
                packed = encoderDump(compressed)
            statistics[BytesFinal] += len(packed)

            # write to file
            self.logbook.write(packed)
            self.logbook.flush()

            # update statistics
            self._create_logSection()
            timestamp = time.time()
            dt = timestamp - periodic_update
            statistics[LogTime] += timer() - logTime
            if dt > 10.:
                periodic_update = timestamp
                if not self.quiet:
                    dt = datetime.datetime.fromtimestamp(self.timestamp)
                    print(f'{dt.strftime("%y-%m-%d %H:%M:%S")} Logged'
                    f' {statistics[NSections]} sections,'
                    f' {statistics[NParLists]} parLists,'
                    f' {statistics[BytesFinal]/1000.} KBytes,'
                    f' {round(statistics[BytesRaw]/statistics[LogTime]/1e6,1)} MB/s')                    
        except Exception as e:
            printe(f'Exception in serialize_sections: {e}')

        # logging is finished
        # rewrite the contentsSection
        self.logbook.seek(0)
        self.logbook.write(self.packedContents)

        # print status
        msg = (f'Logging finished for {statistics[NSections]} sections,'
        f' {statistics[NParLists]} parLists,'
        f' {statistics[BytesFinal]/1000.} KB.')
        if self.compress is not None:
            msg += f' Compression ratio:{round(statistics[BytesRaw]/statistics[BytesFinal],2)}'
        print(msg)
        self.logbook.close()
                
def _safeExit(_signo=None, _stack_frame=None):
    print('safeExit')
    apstrim._eventStop.set()
    apstrim.EventExit.set()

