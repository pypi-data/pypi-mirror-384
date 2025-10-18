#
""" Class for ADO access using cns3.py by Al Marusic.
"""
# __version__ = "3.7.2 2022-03-14"# Fixed unsubscribe across multiple instances
__version__ = "v5.0.0 2022-10-26" # Moved to use adoIf

import sys
import threading
import traceback
from itertools import groupby
from operator import itemgetter

from cad_error import RhicError

from cad_io import adoIf

from . import cns

rpc_version = "1831" if hasattr(cns.rpc, "PortMapError") else "1057"
short_prog_name = (__file__.rsplit("/", 1)[-1:][0]).split(".")[0]

import logging

logger = logging.getLogger(short_prog_name)  # prepend the logging with program name.
logger.handlers.clear()
# create console handler with a lower log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
chFormatter = logging.Formatter("%(name)s: %(levelname)-8s %(message)s")
ch.setFormatter(chFormatter)
# add the handlers to logger
logger.addHandler(ch)
logger.setLevel(logging.INFO)

if sys.version_info < (3, 0):
    raise ImportError("Must use Python 3.0 or higher!")

CNS_features = dict(vars(adoIf.Feature))

#def _iterable(v):
#    # Return iterable object of v. 
#    try:
#        if len(v):
#            return v
#    except:    return [v]

class IORequest:
    """
    Access to ADO namespace.
    """

    # Class-level async attributes
    # Solves race conditions when multiple IORequest instances are used
    _async_thread = None
    _async_callbacks = {}
    _async_keys = {}
    _async_receiver = None
    _async_lock = threading.Lock()
    _handles = {}

    async_include_status=False

    def __init__(self):
        self.interface = "Direct"
        self.__version__ = f"{__version__}, rpc: {rpc_version}, cns: {cns.__version__}"
        logger.debug("adoaccess Instantiated")

        # aliases for obsolete names
        self.get_async = self.subscribe
        self.cancel_async = self.unsubscribe
        self._async_requests = {}
        self._async_next_id = 0

        # sclark 3/3/22: Unnecssary, so removed
        # self.async_tids = []# task IDs

    def _get_ado_handle(self, name):
        """get handle to ADO if it was already created, 
        otherwise, create the new one"""
        rval = ""
        if name in self._handles:
            ado_handle = self._handles[name]
        else:
            where = cns.cnslookup(name)
            if where is None:
                rval = "no such name: " + str(name)
                logger.warning(rval)
                #return None, rval
                raise LookupError(rval)
            ado_handle = adoIf.ADOName.create(where)
            if not isinstance(ado_handle, adoIf.ADOName):
                rval = "no such ADO: " + str(name)
                logger.warning(rval)
                #return None, rval
                raise LookupError(rval)

            # This section is essential only for subsequent adoSet,
            # it will need the metadataDict.
            meta_data, st = adoIf.adoMetaData(ado_handle)
            if st != 0:
                rval = str(st)
                #logger.warning(rval)
                #return None, rval
                raise LookupError('Metadata not found for %s: '%str(name)\
                +rval)

            logger.debug("ado created: " + name)
            self._handles[name] = ado_handle
        return ado_handle, rval

    def generic_name(self, name: str):
        """Returns the Generic ADO name. """
        return self._get_ado_handle(name)[0].genericName

    def get_meta(self, ado: str, param=None, all=False):
        """ Obsolete, please use info() instead.

        Get metadata for ado
        :param ado: Name of ADO; returns list of parameters
        :param param: Name of parameter (optional); returns list of properties & values
        :param all: Returns dict of all parameters, properties, and values (optional)
        :return: list or dict
        """
        try:
            # first argument is always ADO
            ado_handle, r = self._get_ado_handle(ado)
            meta, st = adoIf.adoMetaData(ado_handle)
            if st != 0:
                return []

            if all:
                return meta
            if param is not None:
                return meta[(param, "value")]._asdict()
            return [x[0][0] for x in list(meta.items()) if x[0][1] == "value"]
        except:
            return []

    def info(self, arg):
        """Returns a 3-level dictionary d[parName][propName][attributes]
        of all parameters of an ADO. The attributes are: 
        parameter, property, type, count, ppmSize, features.

        Standard call:  info((dev,par)), par can be '*' for all parameters.

        Old-fashioned call: info(dev), equivalent to info((dev,'*'))
        """
        if isinstance(arg, (tuple,list)):
            ado,argPar = arg
        else:
            ado,argPar = arg,'*'
        metadata = self.get_meta(ado, all=True)
        pars = [metadata[i][0] for i in metadata if i[1] == 'value']
        r = {}
        for par in pars:
            if argPar != '*' and argPar != par:
                continue
            props = [metadata[i][1] for i in metadata if i[0] == par]
            r[par] = {}
            for prop in props:
                r[par][prop] = dict(metadata[(par,prop)]._asdict())
 
                def features2str(featurecode):
                    fd = {'READABLE':'R','WRITABLE':'W','DISCRETE':'D'\
                    , 'ARCHIVABLE':'A', 'EDITABLE':'E', 'CONFIGURATION':'C'\
                    , 'SAVABLE':'S', 'DIAGNOSTIC':'I'}
                    features = ''
                    for i in fd:
                        v = CNS_features[i]
                        if featurecode & v:
                            features += fd[i]
                    return features

                featureBits = r[par][prop]['features'] 
                r[par][prop]['features'] = features2str(featureBits)
        return r

    def get(self, *args, timestamp=True, ppm_user:int=1):
        """
        Get ADO parameters synchronously.

  - **args**: One or more tuple(ado_name, parameter_name, [property_name]);
		property_name defaults to 'value'.
  - **timestamp**: boolean; should timestamps be included (default True)
  - **ppm_user**: int; PPM User 1 - 8 (default 1)

Return: dict. Example:

    twoPars = ('simple.test','sinM'),('different.1','myopdata','opHigh')
    print(ioRequest.get(*twoPars))
    {('simple.test', 'sinM'): {'value': 0.9945219159126282,
      'timestampSeconds': 1589382540,
      'timestampNanoSeconds': 961195359},
     ('different.1', 'myopdata'): {'opHigh': 1000.0,
      'timestampSeconds': 1588713264,
      'timestampNanoSeconds': 755950927}}

        """
        #SLOW#logger.debug("request_list:" + str((request_list)))
        request_list = self._unpack_args(
            *args, timestamp_required=timestamp
        )
        rval = {} #OrderedDict()
        # Check if PPM User is valid
        if ppm_user < 1 or ppm_user > 8:
            raise ValueError("PPM User must be 1 - 8")

        if len(request_list) == 0:
            msg = "ADO not found: " + str(args)
            raise ValueError(msg)

        adoreturn = {}
        try:
            for ado, group in request_list.items():
                requests = list(group.values())
                group_return, status = adoIf.adoGet(list=requests, ppmIndex=ppm_user - 1)
                adoreturn[ado] = group_return, status
        except IndexError:
            msg = "One of the parameters is invalid: " + str(args)
            logger.error(msg)
            raise ValueError(msg)
        
        #print(f'adoreturn:{adoreturn}'[:200])
        # adoreturn = adoreturn[0] # adoReturn is list of lists
        # pack ADO result to the returned dictionary
        return_dict = {}
        for ado, retval in adoreturn.items():
            values, err = retval
            #print(f'err:{err}, results:{results}'[:70])
            if values is None:
                msg = f'error in adoaccess: {err}'
                raise ConnectionRefusedError(msg)
            #ts = timer()
            results = [result[0] if result is not None and len(result) == 1\
              else result for result in values]
            
            keys = request_list[ado].keys()
            if err != 0:
                if not isinstance(err, (list,tuple)):
                    err = [err]
                #print(f'err: {err} keys: {keys}')
                ir = iter(results)
                # errSting = cns.getErrorString
                results_dict = {
                  pair[0]  if pair[1] == 0 else (*pair[0][:2], "error"):\
                  next(ir) if pair[1] == 0 else str(pair[1])\
                  for pair in zip(keys, err)}
                #print(f'Error reported: {results_dict}')
            else:
                results_dict = dict(zip(keys, results))
            for key, vals in groupby(results_dict, itemgetter(0, 1)):
                return_dict.setdefault(key, {})
                return_dict[key].update({key[2]: results_dict[key] for key in vals})
            #print(f'timing {timer()-ts} of {return_dict}'[:200])
        return return_dict

    def get_valueAndTimestamp(self, adoName, parName):
        """Fast get of an ADO parameter. Returns tuple (value, timestampSeconds,
        timestampNanoSeconds)
        """
        key = (adoName, parName)
        r = self.get(key)
        #ts = timer()
        #r = tuple(next(iter(r.values())).values())
        # the following is 3 times faster and more readable
        r = r[key]['value'], r[key]['timestampSeconds'], r[key]['timestampNanoSeconds']
        #print(f'gvt took {timer()-ts} s top get {r}'[:200])
        return r

    def set(self, *args, ppm_user=1):
        """
        Synchronously set ADO parameters.

  - **args**: One or more tuple(ado_name, parameter_name, [property_name], 
  value); property_name defaults to 'value'
  - **ppm_user**: int; PPM User 1 - 8 (default 1)
  - **return**: True if successful.
        """
        if ppm_user < 1 or ppm_user > 8:
            raise ValueError("PPM User must be 1 - 8")
        request_list = self._unpack_args(*args\
        , timestamp_required=False, is_set=True)
        #SLOW#logger.debug("request_list:" + str((request_list)))
        if len(request_list) == 0:
            msg = "Request not created"
            logger.error(msg)
            #return 2
            raise ValueError('Request not created')
        results = []
        for ado_name, group in request_list.items():
            requests = list(group.values())
            _, err_codes = adoIf.adoSet(list=requests, ppmIndex=ppm_user - 1)
            if any(err_codes):
                if any(err == RhicError.ADOIF_PROPERTY_ID_NOT_FOUND for err in err_codes):
                    err_msg = "no such parameter / property"
                elif any(err == RhicError.ADOIF_CANNOT_CONVERT_DATA_TYPE for err in err_codes):
                    err_msg = str(RhicError.ADOIF_CANNOT_CONVERT_DATA_TYPE)
                else:
                    err_msg = str([str(err) for err in err_codes])
                msg = f"Error setting for {list(group.keys())}: {err_msg}"
                logger.error(msg)
                raise ValueError(msg)                
        return True

    def subscribe(self, callback, *args, timestamp=True, ppm_user=1, return_id: bool=False):
        """
        Subscribe to ADO parameters. The callback function will be called when
        the first of the requested parameters have been changed.

  - **callback**: Callable object taking arguments device, param, data, ppm_user
  - **args**: One or more tuple(ado_name, parameter_name, [property_name]); 
  property_name defaults to 'value'.
  - **timestamp**: boolean; should timestamps be included.
  - **ppm_user**: int; PPM User 1 - 8 (default 1).
  - **return_id**: boolean; return the subscription id instead, for use with unsubscribe().
  - **return**: asyncReceiver object if return_id == False else id to use with unsubscribe.

IMPORTANT: Please do not carry long processing in the callback.
The data processing rate should be faster than the data incoming rate!

Example of how to iterate arguments in the callback:

    def callback(*args):
        for adoPar, rDict in args[0].items():
            if not isinstance(rDict,dict): continue
            print(f'got value {rDict["value"]} from {adoPar}')
    """
        if not callable(callback):
            raise ValueError("Callback must be callable")
        if ppm_user < 1 or ppm_user > 8:
            raise ValueError("PPM User must be 1 - 8")
        logger.debug("args[" + str(len(args)) + "]:" + str(args))
        request_list = self._unpack_args(*args\
        , timestamp_required=timestamp)
        self._setup_async()

        logger.debug("request_list:" + str(request_list))

        req_id = self._async_next_id
        self._async_next_id += 1
        self._async_requests[req_id] = tid_list = []

        for _, group in request_list.items():
            #status, tid = cns.adoGetAsync(list=(group, self._async_receiver)\
            requests = list(group.values())
            tid, status = adoIf.adoGetAsync(list=(requests)\
            , ppmIndex=ppm_user - 1, callback=IORequest._unpack_callback)
            # sclark 3/3/22: Unnecssary, so removed
            # self.async_tids.append(tid)
            tid_list.append(tid)
            self._async_callbacks[tid] = callback
            self._async_keys[tid] = list(group.keys())
            logger.debug("adoGetAsync status, tid:" + str((status, tid)))
            if any(status):
                msg = "adoGetAsync:" + str(status) + ", failed for "\
                + str(requests)
                #logger.error(msg)
                # raise RuntimeError(msg)
                print(msg)
            logger.debug("receiver_thread started, tid:" + str(tid))

        return req_id if return_id else self._async_receiver

    def unsubscribe(self, *requests):
        """Cancel subscriptions to all parameters."""
        if self._async_receiver is None:
            return

        if requests:
            try:
                tids = [tid 
                    for request in requests 
                    for tid in self._async_requests[request] 
                ]
            except KeyError as e:
                raise ValueError("Invalid async ID {}".format(e))
        else:
            # tids = list(self._async_keys.keys())
            tids = [tid for tids in self._async_requests.values() for tid in tids]

        for tid in tids:
            _, rc = adoIf.adoStopAsync(self._async_receiver, tid)
            del self._async_keys[tid]
            del self._async_callbacks[tid]

            if rc:
                logger.error(f"Error stopping async server for tid {tid}; connections may still be alive! (return code {rc})")

        if requests:
            for request in requests:
                del self._async_requests[request]
        else:
            self._async_requests.clear()

    def dataQueueLength(self) -> int:
        """Returns size of the _async_receiver.dataqueue"""
        #l = len(self._async_receiver.dataqueue)# in case of newdata()
        l = self._async_receiver.dataqueue.qsize()# in case of newdataT()
        return l
    
    # Private Methods
    def _unpack_args(self, *argv, timestamp_required=True, is_set=False):
        request_list = dict()
        for ado_name, entries in groupby(argv, itemgetter(0)):
            request_list.setdefault(ado_name, {})
            ado_handle, r = self._get_ado_handle(ado_name)
            for entry in entries:
                entry_len = len(entry)
                if (is_set and (entry_len < 3 or entry_len > 4))\
                  or (not is_set and (entry_len < 2 or entry_len > 3)):
                    raise ValueError(f"{entry}: invalid entry")
                param_name = entry[1]
                prop_name = (
                    entry[2]
                    if entry_len == 4 and is_set or entry_len == 3\
                      and not is_set
                    else "value"
                )
                key = (ado_name, param_name, prop_name)
                if not ado_handle:
                    break
                if is_set:
                    value = entry[-1]
                    request_list[ado_name][key]\
                      = (ado_handle, param_name, prop_name, value)
                else:
                    request_list[ado_name][key]\
                      = (ado_handle, param_name, prop_name)
                    if timestamp_required:
                        ts_entry = (*key[:2], "timestampSeconds")
                        request_list[ado_name][ts_entry]\
                          = (ado_handle, param_name, "timestampSeconds")

                        ts_entry = (*key[:2], "timestampNanoSeconds")
                        request_list[ado_name][ts_entry]\
                          = (ado_handle, param_name, "timestampNanoSeconds")

        return request_list

    @classmethod
    def _setup_async(cls):
        if cls._async_receiver is None:
            cls._async_receiver = adoIf.AsyncReceiver.global_inst()

    @classmethod
    def _unpack_callback(cls, data):
        with cls._async_lock:
            # internal function to return dictionary
            # if self.dbg <=3:
            #SLOW#logger.debug(f'_unpack_callback:{args}')
            # values = args[0][0]
            # tid = args[0][1]
            # ppmusers = args[0][3]  # ppmuser should be one for whole groupfo
            values, tid, _, status, ppmusers = data
            keys = cls._async_keys[tid]

            adopar_dict = {}
            results = [result[0] if result is not None and len(result) == 1\
              else result for result in values]
            results_dict = dict(zip(keys, results))
            for key, vals in groupby(results_dict, itemgetter(0, 1)):
                adopar_dict.setdefault(key, {})
                adopar_dict[key].update({key[2]: results_dict[key] for key in vals})
            if not adopar_dict:
                return
            
            adopar_dict["ppmuser"] = ppmusers
            if cls.async_include_status:
                adopar_dict["statuses"] = status
            #SLOW#logger.debug("adopar_dict:" + str(adopar_dict))
            cb = cls._async_callbacks.get(tid)
            if callable(cb):
                cb(adopar_dict)
#,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

