#
"""Python class for creating an ADO manager.
It is a wrapper of the am.py (designed by Al Marusic).
It adds some frequently used features: 

  - start/stop/exit commands: adoStatus
  - status reporting to adoStatus parameter
  - async data receiver from a list of ado:parameters specified in sourceName parameter
  - comprehensive error handling
  - performance monitoring, reported in perfM and adoProcTime parameters
  - password protection of parameter set requests
  - access restriction of parameter set requests, based on the requester hostname
  - lockout-tagout of parameters set requests

Usage:
  - inherit your object from the ampyClass, e.g. class Manager(ampy.ampyClass),
  - call super: super(Manager,self).__init__(**kwargs),
  - add user parameteters using addPar()
  - define set functions, if needed,
  - override the callback() function to process data from the source, 
  defined in the sourceName,
  - override the periodic_update(), if needed.
  
To test how it works:
  - ssh acnlin23
  - am simple
  - adoPet am_simple.0
"""
__version__ = 'v5.4.1 2024-12-19'#adoProcTime umits are ms
#TODO: improve the handling of numpy arrays.
#TODO: implement RBAC-compatible LOTO

import copy
import sys
import threading
import time
import traceback
from timeit import default_timer as timer

from cad_error import RhicError

#AS: comment the following line for local testing
from . import adoaccess
from . import adoIf as cns
from . import am as am
from . import rpc as rpc

#``````````````````Globals````````````````````````````````````````````````````
# some frequently used definitions
DBG_USER = 11
DBG_AMPY = 2
""" Feature bits
These are the sets of features that can be associated with a property.

    readable
    writable
    discrete ( as opposed to continuous )
    savable ( for save/restore clients )
    archivable ( in FEC cache )
    restorable ( from client level)
    editable ( via pet )
    diag_data ( diagnostic, not subject for logging)
    config_data ( configuration, not subject for logging)

The loggable data are readable and not witable and not diagnostic and not configuration.
"""
CNSF_R = cns.Feature.READABLE # minimal features
CNSF_S = cns.Feature.SAVABLE# AS: this feature seems to be useless because all WRITABLES shoulb be SAVABLE by default.
CNSF_RS = CNSF_R | cns.Feature.SAVABLE
CNSF_D = cns.Feature.DISCRETE
CNSF_W = cns.Feature.WRITABLE
CNSF_WS = CNSF_W | cns.Feature.SAVABLE
CNSF_RW = cns.Feature.READABLE | cns.Feature.WRITABLE
CNSF_RWS = cns.Feature.READABLE | cns.Feature.WRITABLE | cns.Feature.SAVABLE
CNSF_WE = CNSF_W | cns.Feature.EDITABLE
CNSF_RWE = CNSF_WE | CNSF_R
CNSF_WED = CNSF_WE | cns.Feature.DISCRETE
CNSF_RWED = CNSF_WED | CNSF_R
#CNSF_RE = CNSF_R | cns.Feature.EDITABLE
CNSF_WES = CNSF_WE | cns.Feature.SAVABLE
# Note: All WRITABLE and EDITABLE parameters should have ARCHIVABLE feature
CNSF_ARCHIVE = CNSF_WES | cns.Feature.ARCHIVABLE | cns.Feature.RESTORABLE
CNSF_RI = cns.Feature.READABLE | cns.Feature.DIAGNOSTIC
#CNSF_L = 0x0200 | CNSF_R#New: LOGGABLE. Parameter is subject for logging or pool-logging processing
#,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
#````````````````````````````Helper functions`````````````````````````````````
def _printi(msg): print('ampy_info: '+msg)
def _printw(msg): print('ampy_WARNING: '+msg)
def _printe(msg): print('ampy_ERROR: '+msg)
def _printv(msg):
    if ampyClass.DBG <= DBG_AMPY: print('ampy_DBG1: '+msg)
def _printvv(msg):
    if ampyClass.DBG <= DBG_AMPY-1: print('ampy_DBG2: '+msg)
#`````````````````````````````````````````````````````````````````````````````
class TokenAdoClient(rpc.TCPClient):
    """Class for access tokenMan. It is abridged version of the cns.adoClient
    with modified mkcred().
    """
    def __init__(self, host, prog, vers):
        self.tokenAdo = cns.CreateAdo('token')
        if prog <= 0xffff:
            rpc.RawTCPClient.__init__(self, host, prog, vers, prog)
        else:
            rpc.TCPClient.__init__(self, host, prog, vers)
        self.packer = cns.AdoPacker()
        self.unpacker = cns.AdoUnpacker('')

    def mkcred(self):
        # Overridden to use user-supplied credentials
        self.cred = copy.copy(self.activeCred)
        if ampyClass.DBG >= 1: _printv(f'cns3.mkcred: {self.cred}')
        return self.cred

    def call_2(self, *arg, cred=None):
        if ampyClass.DBG >= 1: _printv(f'call_2: {cred}')
        if cred is None:
            self.activeCred = (rpc.AUTH_UNIX, rpc.make_auth_unix_default())
        else:
            self.activeCred = (rpc.AUTH_UNIX, rpc.make_auth_unix(cred['stamp'],
              cred['machinename'].encode(), cred['uid'], cred['gid'], []))
        return self.make_call( 2, arg, \
                                   self.packer.pack_nameparam, \
                                   self.unpacker.unpack_data )

#`````````````````````````````````````````````````````````````````````````````
class ampyClass( object ):
    DBG = 12
    def __init__(self, debug=12,
            version: str = '',
            mgrName: str = '',
            className: str = '',
            adoName: str = '',
            sourceName: str = '',
            ppm_user = 1,
            readCache: bool = True,
            childCommands: str = '',
            perfMon: bool = False,
            description: str = 'N/A',
            password: str = '',
            periodicUpdate: float = 10.
            ):
        """
        Arguments:        

  - **mgrName**:  	ADO manager name, i.e. 'ampy' or am_simple.
  - **className**: 	ADO class name.
  - **adoName**:    ADO name.
  - **sourceName**: source parameter, i.e. 'simple.test:degM.
If supplied, then an async get request will be instrumented for it
  - **readCache**:	force the reading of the initial parameter values from ADO 		cache.
  - **childCommands**: user commands for extending the adoCommand parameter
  - **perfMon**:    enable parameters for performance monitoring.
  - **description**:    description.
  - **password**:  	password protection feature, to enable, provide it with a 				string.
  - **periodicUpdate**:	period of the periodic update. If 0 then no periodic update.
    	"""
        # find versions of the related libraries
        self.iface = adoaccess.IORequest()
        try: # check, which rpc version is active
            dummy = rpc.PortMapError()
            rpcVersion = '1831'
        except: rpcVersion = '1057'
        #self.amVersion = am.__version__.split(' ')[0]
        self.__version__ = version
        _printi('Version:'+self.__version__)

        if adoName == '': # use mgrName with last '_' replaced with '.'
            tokens = mgrName.rsplit('_',1)
            if len(tokens) == 1: tokens.append('0')
            else:
                try: i = int(tokens[1])
                except:
                    tokens = (mgrName+'_0').rsplit('_',1)
            adoName = tokens[0] + '.' + tokens[1]

        # check if ADO is already active
        try:
            print(f'get `{adoName}`')
            v = self.iface.get((adoName,'version'))
            print(f'version: {version}')
        except:
            pass
        else:
            print(f'ERROR: ADO {adoName} is already active.',file=sys.stderr)
            sys.exit(1)

        # instantiate the manager
        self.mgrName = mgrName
        try:
          self.server = am.AdoServer( self.mgrName )
        except Exception as e:
          _printe('Constructing server '+self.mgrName+', check if it is configured in fecManager.')
          print('Exception: '+str(e))
          #self._run_stop()
          sys.exit(1)

        self.className = mgrName if className == '' else className
        self.servCount = 0
        self.adoProcTimeV = [0.]*8
        self.adoCounterV = [0.]*4 # general purpose counters, free to use
        self.stopped = True
        self.asyncServer = None
        self.tid = None # transaction ID for CNS
        self.timestamp = None# #removed un v57, restored in 3.6.8
        self.password = password
        self._passwordOK = False if password else True
        self.periodicUpdateSleep = periodicUpdate
        self._tokenAdoClient = None
        self.eventExit = threading.Event()

        #printi('Creating ADO:'+str((adoName, description, self.className, self.__version__)))
        self.mainAdoName = adoName
        self.ado = {adoName:am.Ado(adoName, description, self.className, self.__version__)}
        #printi('ADO:'+str(self.ado[self.mainAdoName].name))

        self.adoDebug = self.addPar('adoDebug',
        (f'Printout severity level: 14:ERROR, 13:WARNING, 12:INFO,'
        f' {DBG_USER}-{DBG_AMPY+1}:USER, {DBG_AMPY}-1:AMPY,'
        ' bits[15:4] are used for am.py'),
          debug, features = CNSF_WE)
        self.adoDebug.set = self._adoDebug_set
        self._adoDebug_set()

        self.adoStatus = self.addPar('adoStatus'\
        , 'Status, warning or error messages from manager and libraries', '', alarm = 0, features = CNSF_WE)
        self.adoStatus.set = self._adoStatus_set

        if password != '':
            self.adoPass = self.addPar('adoPass'\
            , 'Set it to valid password to enable setting of certain parameters during 10s window of opportunity'\
            , '', features = CNSF_ARCHIVE)
            self.adoPass.set = self._adoPass_set

        self.adoInputS = None
        if sourceName != '':
            self.adoInputS = self.addPar('adoInputS'\
            , 'Input ADO:parameter', sourceName, features = CNSF_ARCHIVE)
            self.adoInputS.set = self._adoInputS_set
            self._adoInputS_set()

            self.adoInputM = self.addPar('adoInputM'\
            , 'Received data', 0., features = CNSF_R)
            #v29:removed#self.adoInputM.set = self.adoInputM_set
            self.ppm_user = ppm_user

        self.adoPerf = None
        if perfMon:
            self.adoPerf = self.addPar('adoPerf'\
            , 'performance monitor [event/s]', 0., features = CNSF_R)

            self.adoProcTime = self.addPar('adoProcTime',
'performance times, [0]: callback time of adoInputS, [1:7]: user defined',
            self.adoProcTimeV, features = CNSF_R, format = '%0.3f', units='ms')

            self.adoCounter = self.addPar('adoCounter'\
            , 'diagnostic counters', self.adoCounterV, features = CNSF_R)

        self.adoCommand = self.addPar('adoCommand'\
        , 'Stop run, Start run, Exit manager', 'Stopped', features = CNSF_WED\
        , legalValues = 'Stop,Start,Exit'+childCommands)
        self.adoCommand.set = self._command_set
        
        # add user-defined parameters
        self.add_more_parameters()

        self.initiated = False# It will be set True in first _run_start()
        self.readCache = readCache

    def add_ado(self,adoName,description):
        """Add ADO to the server"""
        self.ado[adoName]\
        = am.Ado(adoName, description, self.className, self.__version__)

    def update_par(self,*args, **kwargs):
        """Obsolete, use publish() instead"""
        raise ValueError('update_par() is obsolete, use publish() instead')

    def publish(self, par, value = None, timestamp = None, ppm_index=0):
        """Publish ADO parameter and timestamp. 

  - If timestamp is not None then it will be used.
  - If timestamp is None and self.timestamp is not None then
the self.timestamp will be used for timestamping.
  - If timestamp is None and self.timestamp is None, then
the parameter will be timestamped by am.py using system time.
        """
        if value is not None:
            if par.value.ppmSize <= 1:
                par.value.value = value
            else:
                try:
                    par.value.value[ppm_index] = value
                except Exception as e:
                    msg = 'Could not set '+par.name+str(ppm_index)+' to '+str(value)+':'
                    _printe('PPM'+str(ppm_index)+' issue.'+msg+str(e))
                    return 1
        if timestamp is None:
            timestamp = self.timestamp
        par.setTimestamps(timestamp, ppm_index)
        par.updateValueTimestamp(ppm_index)
        return 0

    def publish_adoStatus(self, msg:str):
        """Publish adoStatus parameter."""
        try:
            self.adoStatus.value.value = msg
            self.adoStatus.setTimestamps(None, 0)
            self.adoStatus.updateValueTimestamp(0)
        except:
            print(msg)
        return 0

    def _adoDebug_set(self, *args):
        """adoDebug setter"""
        ampyClass.DBG = self.adoDebug.value.value
        return 0
            
    def _adoInputS_set(self, *args):
        """adoInput set handler"""
        _printi(f'adoInputS changed to {self.adoInputS.value.value}')
        if not self.stopped:
            _printi('restarting run')
            self._run_stop()
            self._run_start()
        return 0

    def _command_set(self, *args):
        """adoCommand handler"""
        cmd = self.adoCommand.value.value
        _printi('adoCommand: '+str(cmd))
        if cmd == 'Exit':
            self.exit()
        elif cmd == 'Restart': sys.exit(99)
        elif cmd == 'Stop': 
            self.publish(self.adoCommand,'Stopped')
            self._run_stop()
        elif cmd == 'Start':
            self._run_start()
            if not self.stopped:
                self.publish(self.adoCommand,'Started')
            else:
                return 1
        self.child_command_set(*args)
        return 0

    def loop(self):
        """Enter the ADO manager event loop"""
        _printi(f'Manager {self.mgrName} for ADOs {list(self.ado.keys())} started')

        self._run_start()
        try:
            self.server.loop()
        except Exception as e:
            # do not work?
            _printe('Server loop exception:\n'+traceback.format_exc())
            self._run_stop()
        finally:
            self.exit()
            self.server.unregister()
            self.server.HBrun = False
            _printi('Manager '+self.mgrName+' stopped')
        
    def exit(self):
        """Safe exit of the manager"""
        self._run_stop()
        self.publish(self.adoStatus,'Exited')
        self.server.run = False
        self.eventExit.set()
        #sys.exit(0)
        
    def child_command_set(self,*args):
        """Override it for processing of the user keywords in adoCommand"""
        _printi('default command_set_child: '+str(self.adoCommand.value.value))
        return 0

    def _run_start(self):
        """Called when run is started, starts async receiving of the
        parameter, specified in adoInputS."""
        if not self.stopped:
            msg = 'Manager is already running.'
            self.publish(self.adoStatus,msg)
            _printw(msg)
            #self._run_stop()
            return
        _printi('ampy: starting run')

        if not self.initiated:
            self.initiated = True
            # all parameters have been created, read cache to restore parameters
            if self.readCache:
                try:
                    self.ado[self.mainAdoName].readCache()
                except Exception as e:
                    _printe('In readCache: {e}')

        self.stopped = False
        self._start_diagnostic_thread()
        if self.adoInputS:
            #TODO quick stop/start leaves the first thread unfinished, need some locking
            time.sleep(1)
            aname,pname = self.adoInputS.value.value.rsplit(':', 1)
            # get the first reading synchronously
            try:
                r = self.iface.get((aname,pname), ppm_user = self.ppm_user)
            except Exception as e:
                _printe('during run_start: '+str(e))
                self.stopped = True
                return
            #print('adoGet='+str(r)[:200]+'...')
            self._receiver_thread_callback(r)
            self.iface.subscribe(self._receiver_thread_callback, (aname,pname)\
            , ppm_user = self.ppm_user)
        self.run_startx()
        if not self.stopped:
            self.publish(self.adoCommand,'Started')
            self.publish(self.adoStatus,'Started')
        self.adoProcTimeV = [ 0. for x in self.adoProcTimeV ] # clear adoProcTimeV counters
        self.adoCounterV = [ 0. for x in self.adoCounterV ] # clear adoCounters
        
    def run_startx(self):
        """Overridable, Called when the run is started."""
        pass

    def _run_stop(self):
        """Stop command handler"""
        #printi('stopping run')
        try:
            self.iface.unsubscribe()
        except: pass
        self.run_stopx()
        self.stopped = True
        _printi('run_stopped: '+str(self.stopped))
        self.publish(self.adoStatus,'Stopped')

    def run_stopx(self):
        """Overridable, called when the run is stopped"""
        pass
        
    def _start_diagnostic_thread(self):
        if self.periodicUpdateSleep == 0:
            return
        self.diagnostic_thread = threading.Thread(\
          target=self._diagnostic_thread_proc, daemon = True)
        self.diagnostic_thread.start()
        _printi('diagnostic thread started, updates every %d s'\
          %self.periodicUpdateSleep)

    def add_more_parameters(self):
        """Obsolete. Please use super() instead."""
        pass
        
    def add_par(self, *args):
        """Outdated function, replaced by addPpar().
        Add parameter using 
        am.ado.addParameter( name, ptype, count, ppmSize, features, value)
        and add a timestamp feature"""
        a = [str(arg) if type(arg) == str else arg for arg in args]
        
        par = self.ado[self.mainAdoName].addParameter(*a)
        _printv('add_par:'+str(par))
        par.add('timestamps', time.time())
        return par

    def addPar(self, name: str, desc: str, value, adoName=None, **kwargs):
        """Concise method to add a parameter.
        Keyword arguments:

  - **count**:    if not supplied, it will be deduced from the length of the value
  - **ptype**:    if not supplied, it will be deduced from the type(value[0])
  - **features**=CNSF_RWE: parameter features
  - **ppmSize**=0: max number of ppm users
  - **units**:    i.e: 'V', 'm', 'Gauss'... 
  - **format**: i.e: '.2f'
  - **cycle**:    UIntType, use it for your needs
  - **legalValues**: i.e: 'Enable,Disable'
  - **alarm**: 
  - **engHigh, engLow, opHigh, opLow**:
  - **toleranceValues**: array of 10 floats
        """
        if adoName is None:
            adoName = self.mainAdoName
        count = None
        if 'count' in kwargs:
            # count is provided, remove it from kwargs
            count = kwargs['count']
            del kwargs['count']
        # determine count and type of the parameter
        try:
            # assume that the value is list or tuple
            if isinstance(value,str):
                raise
            if count is None:
                count = len(value)
                # the value has length
                if count == 1:  count = 0 # variable size array
            try:    initialType = type(value[0])
            except: initialType = type(value)
        except:
            # the value is int, double, string, or bytes
            if count is None:
                count = 1
            initialType = type(value)
        if isinstance(value,(bytearray,bytes)):
            initialType = type(bytes())
        #print(f'initialType: {initialType}, count:{count}, value:{value}'[:300])
        if 'numpy' in str(initialType):
            initialType = 'numpy'
            #value = 0.
        try:
            # convert type of the parameter to acceptable form for am.py
            ptype = {type(0):'IntType', type(0.):'DoubleType'\
                ,type('0'):'StringType', type(None):'VoidType'\
                ,type(bytes()):'BlobType','numpy':'BlobType'}\
                [initialType]
                #,type(bytes()):'UCharType','numpy':'UCharType'}\
        except:
            raise TypeError('ERROR in ampy.addPar: unsupported type of '\
            + name)
        #print(f'ptype of {name}:{ptype}')

        # determine the features and ppmsize
        d = {"features":CNSF_RWE, "ppmsize":0}
        for key in d:
            if key in kwargs:
                d[key] = kwargs[key]
                del kwargs[key]

        lv = kwargs.get('legalValues')
        if lv is not None:
            #print(f'par {name} has legalValues, its features are set to WED')
            d['features'] |= CNSF_WED

        # create the parameter
        if ptype == 'BlobType':
            count = 1
        par = self.ado[adoName].addParameter\
        (name, ptype, count, d['ppmsize'], d['features'], value)
        par.add('desc',desc)
        par.add('timestamps', time.time())
        if initialType == 'numpy':
            par.addProperty('shape', 'IntType', 0, d['ppmsize'], CNSF_R\
            , [0])
            par.addProperty('dtype', 'StringType', 0, d['ppmsize'], CNSF_R\
            , str(value.dtype))
            
        for key,v in kwargs.items():
            if v is not None:
                par.add(key,v)
        return par
        
    def cache_in(self, adoName = None):
        """Force to call set() methods for all archived parameters.
        It is used to be called after the manager was initialized to react on 
        parameters, retrieved from the ADO cache.
        """
        if adoName is None:
            adoName = self.mainAdoName        
        archivable = cns.Feature.ARCHIVABLE
        ppmIndex = 0#TODO: No idea how to deal with ppm here
        for par in self.ado[adoName].parameters:
            if (par.value.features & archivable) != 0:
                #print('archivable: '+par.name,hex(par.value.features))
                par.set(ppmIndex)

    #````````````````````````Monitoring/diagnostic thread`````````````````````
    def _diagnostic_thread_proc(self):
        """Diagnostic thread, it updates the performance counters (if enabled)
        and calls a user overridable function periodic_update()
        then sleeps for self.periodicUpdateSleep seconds and repeats
        """
        prevCount = self.servCount
        while True:
            if self.stopped:
                break
            if self.adoPerf:
                cycles = self.servCount - prevCount
                prevCount = self.servCount
                #_printv('cycles:'+str((cycles,['%0.3g' % i for i in self.adoProcTimeV])))
                self.publish(self.adoPerf,cycles/self.periodicUpdateSleep)
                vv = [ (round(x/cycles if cycles else x, 6)) for x in self.adoProcTimeV ]
                #_printv(str(['%0.3g' % i for i in vv]))
                self.publish(self.adoProcTime,vv)
                self.publish(self.adoCounter,self.adoCounterV)
                self.adoProcTimeV = [ 0. for x in self.adoProcTimeV ] # clear all counters after reporting
                self.adoCounterV = [ 0. for x in self.adoCounterV ] # clear adoCounters
                #_printv('cleared:'+str(['%0.3g' % i for i in self.adoProcTimeV]))
            self.periodic_update()
            #time.sleep(self.periodicUpdateSleep)
            self.eventExit.wait(self.periodicUpdateSleep)
            if self.eventExit.is_set():
                break
        #self._run_stop()
        _printi('Diagnostic thread finished')
        return
    #,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
    #````````````````````````Data processing thread```````````````````````````
    def _receiver_thread_callback(self,*args):
        """ Callback function, invoked when data have been received.
        the data source is recovered in variables: ado, adoparameter, adoproperty
        It calls a user-overridable function self.callback()
        """
        self.servCount +=1;
        if self.DBG  <= DBG_AMPY: _printv('thread_callback:'+str(self.servCount)+': args:'+str(args))
        procStart = timer() # timestamp for perfomance analysis
        self.callback(*args)
        self.adoProcTimeV[0] += (timer() - procStart)*1000.
    #,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
    #````````````````````````User-oveloadable functions```````````````````````
    def periodic_update(self):
        """Overridable. Called periodically, the interval defined by self.periodicUpdateSleep.
        """
        _printv('dummy periodic_update()')
        
    def callback(self, *args):
        """This function could be overridden in a derived class if sourceName
        was specified. It is called when new data arrived from the source.
        """
        if self.DBG  <= DBG_AMPY: _printv('callback('+str(args)+')')
        if not isinstance(args,dict): args = args[0]
        try:
            val = list(args.values())[0]['value']
        except TypeError:
            raise ReferenceError('in callback: '+str(args))
        #print(val)
        
        # update the adoInputM
        if isinstance(val,list): val = val[0]
        try: val = float(val)
        except: val = 0. 
        self.publish(self.adoInputM,val)
    #,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
    #````````````````````````Helper functions````````````````````````    
    def _pass_thread(self):
        """Opens a time window during which the password can be changed"""
        self._passwordOK = True
        for i in range(10,0,-1):
            self.publish(self.adoPass,'_Open for '+str(i)+'s')
            time.sleep(1)
        self._passwordOK = False
        self.publish(self.adoPass,'_Closed')

    def _adoPass_set(self,*argv):
        """Password changing procedure"""
        v = self.adoPass.value.value
        if v[0] == '_': return 0
        if v == self.password:
            thread = threading.Thread(target=self._pass_thread, daemon = True)
            thread.start()
        else: self.publish(self.adoPass,'_Wrong password')
        #return 1 # to disable it from viewing
        return 0
        
    def is_password_wrong(self,*args):
        return 0 if self._passwordOK else 1
        
    def _adoStatus_set(self,*args):
        """Change alarm level for messages starting with E (error) 
        and W (warning), this can be used for coloring the text in a petpage"""
        msg2color = {'E':8,'W':6}
        try:
            self.adoStatus.alarmLevel.value \
            = msg2color[self.adoStatus.value.value[0]]
        except Exception as e:
            self.adoStatus.alarmLevel.value = 0
        self.adoStatus.alarmLevel.update(0)
        self.publish(self.adoStatus)        
        return 0

    def evaluate_role(self, allowedRoles:set):
        """Returns non zero error code if access to ADO is not granted.
        Typical resolution time is <2 ms, and most of the time
        is spend in retrieving the token. TODO: cache tokens."""
        import base64
        import hashlib
        import socket

        from cryptography.fernet import Fernet

        #PERF#ts = [0.]*4
        #PERF#ts[0] = time.perf_counter()
        # get cred map from rpc packet
        cred = self.server.get_cred()
        _printv(f'cred: {cred}')
        uid = self.server.get_cred().get('uid')
        if uid is None:
            return RhicError.AUTHERROR,\
              'ERR: User credentials are not supplied in RPC request'
        digest = hashlib.sha256(str(uid).encode()).digest()
        key = base64.b64encode(digest)
        fernet = Fernet(key)

        # get token from tokenMan
        try:
            token = self._get_token(cred)
        except (socket.error, EOFError) as e:
            return RhicError.CANTRECV, 'Exception in get_token: {e}'
        except Exception as e:
            return RhicError.CANTRECV, f'Token not available for {cred}: {e}'
        token = bytes(token.encode())
        #PERF#ts[1] = time.perf_counter()
        #PERF#_printv(f'token: {token}, elapsed:{round(ts[1]-ts[0], 6)}')

        # evaluate roles
        role = ''
        msg = f'ERR: Invalid token'
        try:
            tokenTimestamp = fernet.extract_timestamp(token)
            decrypted = fernet.decrypt(token)
            #printv(f'decrypted: {decrypted}')
            expiration, basicRole, elevatedRole,  = decrypted.decode().split()
            expiration = float(expiration)
            if expiration == -1.:
                expiration = 1E99
            if time.time() >= expiration:
                role = basicRole
                msg = f'ERR: Token expired. Your basicRole is {role}'
            else:
                role = elevatedRole
                msg = f'ERR: Access denied. You are not allowed to modifify ADO parameters'
        except:
            return RhicError.ADO_PERMISSION_DENIED, msg
        roles = set(role.split(','))

        # authorization
        privileges = roles & allowedRoles
        #PERF#ts[2] = time.perf_counter()
        #PERF#_printv(f'privileged: {privileges}, role:{roles}, allowed:{allowedRoles}, elapsed:{round(ts[2]-ts[1], 6)}')
        if len(privileges) == 0:
            return RhicError.ADO_PERMISSION_DENIED, f'{msg}. UID: {uid}.'
        #PERF#ts[3] = time.perf_counter()
        #PERF#_printv(f'isUserPrivileged elapsed time: {round(ts[3]-ts[0], 6)}')
        return 0, ''

    def _get_token(self, cred):
        # the standard get() cannot be used because it will use cred of the manager.
        if self._tokenAdoClient is None:
            ado = cns.create_ado('token')
            if ado is None:
                return False, "Could not find ADO 'token'"
            self._tokenAdoClient = TokenAdoClient( ado.server, ado.program, ado.version )
        names = (('token','token','value'),)
        ppmIndex = 0
        reply, tid, status, istatus\
        = self._tokenAdoClient.call_2( names, ppmIndex, cred=cred) # tid not used
        #print(f'reply: {reply}, status: {status}, istatus: {istatus}')
        if status != 0:
            if any(istatus): # Return True if any element of the iterable is true.
                if len(istatus) == 1:
                    status = istatus[0]
                else:
                    status = istatus
                if len(reply) == 0:
                    raise RuntimeError(f"Token not available for uid {cred['uid']}, ErrCode: {status}")
        return reply[0][0]
    #,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
#,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
# For simple examples see am_simple.py and am_restrictedMan.py

