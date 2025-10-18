#!/usr/bin/env python3
# Al Marusic

"""ADO manager implemented in python."""

# __version__ = "2.22a"
__author__ = "Al Marusic"
__version__ = "v5.0.0 2022-10-26"  # Moved to using cad_error & adoIf

import collections
import inspect
import os
import select
import socket
import struct
import sys
import threading
import time
from datetime import datetime
from selectors import EVENT_READ, DefaultSelector
from typing import *

from cad_error import RhicError

from cad_io import adoIf

# mods by AS 2020-10-20:
from . import cns, notif, rpc


def usage():
    print(__doc__)
    print("am3.py  [-debug number]  showtests | start [manager_name]")


def dPrint(*values):
    msg = "am3 - {date} - {values}".format(
        date=datetime.now(), values=" ".join(str(value) for value in values)
    )
    print(msg)


# test this way:
# ~/bin/am.py showtests | while read c; do echo "##########" $c; $c; sleep 2; done

# TO DO, FIX:
# add automatic check for alarm conditions
# handle all exceptions
# during asyncInfo check async config of parameters
# FIX: clcEvent listConnections differentman
#      clcEvent: error - can't list connections on differentman
# ADOIF_ADO_NOT_FOUND = "adoIf - Server did not find ADO" is added in adoIf/adoIf.cxx

NOTIF_SERVER = "RHICNotifServer"

adoIf.keep_history(False)

activeServer = None

adodict = {}
debug = 0
DB_ERROR = 0x001
DB_REQUEST_B = 0x002
DB_REQUEST_NB = 0x004
DB_REQUEST_ASYNC = 0x008
DB_REQUEST_MISC = 0x010
DB_UPDATE = 0x020
DB_START = 0x040
DB_CLIENTS = 0x080
DB_CONNECTIONS = 0x100
DB_HB = 0x200
DB_INFO = 0x400
DB_ARCHIVE = 0x800
DB_ALL = (
    DB_ERROR
    | DB_REQUEST_B
    | DB_REQUEST_NB
    | DB_REQUEST_ASYNC
    | DB_REQUEST_MISC
    | DB_UPDATE
    | DB_START
    | DB_CLIENTS
    | DB_CONNECTIONS
    | DB_HB
    | DB_INFO
    | DB_ARCHIVE
)
CallerInfo = collections.namedtuple(
    "CallerInfo", "host, ip, program, version, procedure, port, pid"
)
# caller(host='acnlin25.pbn.bnl.gov', ip=2194106866, program=1073743748, version=1, procedure=2, port=38553, pid=1924)


def alarmLevelSetter(prop: "AdoProperty", value, ppmIndex, caller=None):
    if not (notif.NotifCategory.OK <= value <= notif.NotifCategory.EMERGENCY):
        return RhicError.ADO_VALUE_OUT_OF_RANGE

    if value != prop.getInternal(ppmIndex):
        prop.setInternal(value, ppmIndex)
        prop.parameter.generateAlarm(ppmIndex)
    return 0


def latchCountSetter(prop: "AdoProperty", value, ppmIndex, caller=None):
    prop.setInternal(value, ppmIndex)
    prop.parameter.checkTolerance(ppmIndex)
    return 0


def valueSetter(prop: "AdoProperty", value, ppmIndex, caller=None):
    st = prop.parameter.checkLimits(value, ppmIndex)
    if st:
        return st

    st = prop.parameter.checkLegal(value, ppmIndex)
    if st:
        return st

    # Added logic to optionally pass in "caller" argument if defined on setter
    old_value = prop.value
    prop.setInternal(value, ppmIndex)

    sig = inspect.signature(prop.parameter.set)
    if "caller" in sig.parameters:
        args = sig.bind(ppmIndex, caller=caller)
    else:
        args = sig.bind(ppmIndex)
    args.apply_defaults()
    st = prop.parameter.set(*args.args, **args.kwargs)
    # restore value if set() fails
    if st:
        prop.value = old_value

    return st


class CallerObject:
    """Class holding caller information."""

    CL_OK = 0
    CL_NON_RESPONSIVE = 100
    CL_NON_REACHABLE = 200
    CL_ASYNC_PAUSE = 300
    CL_UNUSED = 400
    CL_DELETED = 500
    CL_QUEUE_FULL = 600
    # They are 2 kinds of async send errors, the errors after which:
    # - the connection can not be reestablished, i.e. port is gone, etc.
    # - the connection can be reestablished, e.g. timeout happened, etc.
    # The connections encountering the first kind of errors were supposed to be put into
    # CL_NON_RESPONSIVE state and encountering the second into CL_NON_REACHABLE state.
    # Also CL_NON_RESPONSIVE state was supposed to turn into CL_NON_REACHABLE after a while.
    # This code associates CL_NON_RESPONSIVE state with RPC errors, and CL_NON_REACHABLE with socket errors
    # and treats them both the same way.

    def __init__(self, callerinfo):
        # def __init__(self, host, ip, program, version, port, pid):
        self.procedure = 0  # per request
        self.host = callerinfo.host
        self.ip = callerinfo.ip
        self.program = callerinfo.program
        self.version = callerinfo.version
        self.port = callerinfo.port
        self.pid = callerinfo.pid
        self.createTime = time.time()
        self.status = self.CL_OK
        self.sentCount = 0
        self.sentSize = 0
        self.lossCount = 0
        self.deleteCount = 0
        self.lastSendTime = 0
        self.clientObject = None
        self.requests = []

    def __str__(self):
        return "{0} = {1} : {2} / {3} port = {4} pid = {5}".format(
            self.host,
            socket.inet_ntoa(struct.pack("!I", self.ip)),
            self.program,
            self.version,
            self.port,
            self.pid,
        )

    def __eq__(self, other):
        return (
            self.host == other.host
            and self.program == other.program
            and self.version == other.version
            and self.port == other.port
            and self.pid == other.pid
        )

    def addRequest(self, requestedprops, proc, tid, ppm_index):
        """Add request."""
        prop = requestedprops[0]
        # check if caller, proc, tid already registered
        if prop.addRequest(self, proc, tid, requestedprops, ppm_index):
            self.requests.append(prop)

    def removeRequest(self, proc, tid):
        """Remove request."""
        removed = False
        for i in range(len(self.requests) - 1, -1, -1):
            prop = self.requests[i]
            if prop.removeRequest(self, proc, tid):
                del self.requests[i]
                if len(self.requests) == 0:
                    self.status = self.CL_UNUSED
                    if debug & DB_CLIENTS:
                        dPrint("declared {0} unused".format(self))
                removed = True
                if tid != 0:
                    break
        if not removed:
            if debug & DB_ERROR:
                dPrint(
                    "ERROR: request from {0} proc = {1} tid = {2} not found".format(
                        self, proc, tid
                    )
                )


XDformat_list = (
    ("b", "CharType"),
    ("B", "UCharType"),
    ("h", "ShortType"),
    ("H", "UShortType"),
    ("i", "LongType"),
    ("I", "ULongType"),
    ("f", "FloatType"),
    ("d", "DoubleType"),
    ("s", "StringType"),
    ("", "StructType"),
    ("", "VoidType"),
    ("B", "BlobType"),
    ("i", "IntType"),
    ("I", "UIntType"),
)
XDformat = dict([(adoIf.XDTYPE[t], f) for f, t in XDformat_list])
XDnative = {
    "CharType": str,
    "UCharType": str,
    "ShortType": int,
    "UShortType": int,
    "LongType": int,
    "ULongType": int,
    "FloatType": float,
    "DoubleType": float,
    "StringType": str,
    "StructType": None,
    "VoidType": None,
    "BlobType": bytes,
    "IntType": int,
    "UIntType": int,
}


class Ado:
    """Class representing ADO."""

    def __init__(self, name: str, description: str, adoclass: str, version: str):
        self.name: str = name
        self.parameter_dict: MutableMapping[str, "AdoParameter"] = {}
        self.meta: List[AdoProperty] = []
        self.metadict: Dict[Tuple[str, str], AdoProperty] = {}
        self.doarchive: bool = False
        adodict[self.name] = self
        """
        add default parameters:
        fecName value StringType 1 0 configData = configData read
        description value StringType 1 0 configData = configData read
        constructTime value UIntType 1 0 configData = configData read
        version value StringType 1 0 configData = configData read
        className value StringType 1 0 configData = configData read
        commandBuffer value StringType 1 0 contMeas = read
        commandBuffer desc StringType 1 0 configData = configData read
        commandBufferLength value UIntType 1 0 diagData = diagData write read save restore archive
        commandBufferLength desc StringType 1 0 configData = configData read
        """
        self.addParameter(
            "fecName",
            "StringType",
            1,
            0,
            adoIf.Feature.CONFIGURATION | adoIf.Feature.READABLE,
            socket.gethostname(),
        )
        self.addParameter(
            "description",
            "StringType",
            1,
            0,
            adoIf.Feature.CONFIGURATION | adoIf.Feature.READABLE,
            description,
        )
        self.addParameter(
            "constructTime",
            "UIntType",
            1,
            0,
            adoIf.Feature.CONFIGURATION | adoIf.Feature.READABLE,
            int(time.time()),
        )
        self.addParameter(
            "version",
            "StringType",
            1,
            0,
            adoIf.Feature.CONFIGURATION | adoIf.Feature.READABLE,
            version + " / ADO " + __version__,
        )
        self.addParameter(
            "className",
            "StringType",
            1,
            0,
            adoIf.Feature.CONFIGURATION | adoIf.Feature.READABLE,
            adoclass,
        )

    @property
    def parameters(self) -> Tuple["AdoParameter", ...]:
        return tuple(self.parameter_dict.values())

    # FIX: it would have been nice that ppmSize has default value
    def addParameter(self, name, ptype, count, ppmSize, features, value):
        """Add parameter to this ADO."""
        if name in self.parameter_dict:
            return
        self.parameter_dict[name] = ado = AdoParameter(
            self, name, ptype, count, features, value, ppmSize=ppmSize
        )
        return ado

    def writeCache(self):
        """Write values of all archivable properties to file."""
        file_name = AdoServer.cache_dir + "/" + self.name
        # write temp file and than rename
        with open(file_name + ".tmp", "wb") as f:
            if debug & DB_ARCHIVE:
                dPrint("writing cache file =", file_name)
            f.write(struct.pack("4s", b"ACF"))
            f.write(struct.pack("i", 1))

            for par in self.parameters:
                for prop in par.properties:
                    prop.writeCache(f)
            f.write(struct.pack("B", 4))
            f.write(struct.pack("4s", b"|/|/"))
        os.rename(f.name, file_name)

    def readCache(self):
        """Read values saved in cache file."""
        file_name = AdoServer.cache_dir + "/" + self.name
        try:
            with open(file_name, "rb") as f:
                if debug & DB_ARCHIVE:
                    dPrint("reading cache file =", file_name)
                ftype = struct.unpack("4s", f.read(4))[0]
                fver = struct.unpack("i", f.read(4))[0]
                if ftype != b"ACF\x00" or fver != 1:
                    print("ERROR: file type = {0}, version = {1}".format(ftype, fver))
                # print("type =", ftype, type(ftype), "length", len(ftype))
                # print("version =", fver)

                while True:
                    parameter_name_length = struct.unpack("B", f.read(1))[0]
                    parameter_name = struct.unpack(
                        str(parameter_name_length) + "s", f.read(parameter_name_length)
                    )[0].decode()
                    # print(parameter_name, parameter_name_length)
                    if parameter_name == "|/|/":
                        break

                    property_name_length = struct.unpack("B", f.read(1))[0]
                    property_name = struct.unpack(
                        str(property_name_length) + "s", f.read(property_name_length)
                    )[0].decode()
                    # print(property_name, property_name_length)

                    try:
                        prop = self.metadict[(parameter_name, property_name)]
                    except KeyError:
                        # if debug & DB_ERROR:
                        dPrint(
                            "ERROR: found {0}:{1} property in cache file".format(
                                parameter_name, property_name
                            )
                        )
                        prop = None

                    ptype = struct.unpack("i", f.read(4))[0]
                    count = struct.unpack("i", f.read(4))[0]
                    ppmSize = struct.unpack("i", f.read(4))[0]
                    # print(ptype, count, ppmSize)
                    if ppmSize <= 0:
                        ppmSize = 1
                    if ptype == adoIf.XDTYPE["StringType"]:
                        for ppmIndex in range(ppmSize):
                            value_length = struct.unpack("I", f.read(4))[0]
                            value = struct.unpack(
                                str(value_length) + "s", f.read(value_length)
                            )[0].decode(errors="surrogateescape")
                            # print("{0} : {1} (PPM = {2}) = {3}".format \
                            #       ( parameter_name, property_name, ppmIndex, value ))
                            if prop:
                                prop.readCache(value, ppmIndex)
                    elif count == 0 or ptype == adoIf.XDTYPE["BlobType"]:
                        value_format = XDformat[ptype]
                        if value_format == "":
                            continue
                        value_size = struct.calcsize(value_format)
                        for ppmIndex in range(ppmSize):
                            value_length = struct.unpack("I", f.read(4))[0]
                            if ptype == adoIf.XDTYPE["BlobType"]:
                                value = f.read(value_length)
                            else:
                                value = struct.unpack(
                                    str(value_length // value_size) + value_format,
                                    f.read(value_length),
                                )
                            # print("{0} : {1} (PPM = {2}) = {3}".format \
                            #       ( parameter_name, property_name, ppmIndex, value ))
                            if prop:
                                prop.readCache(value, ppmIndex)
                    else:
                        value_format = XDformat[ptype]
                        if value_format == "":
                            continue
                        value_size = struct.calcsize(value_format)
                        for ppmIndex in range(ppmSize):
                            value = struct.unpack(
                                str(count) + value_format, f.read(value_size * count)
                            )
                            # print("{0} : {1} (PPM = {2}) = {3}".format \
                            #       ( parameter_name, property_name, ppmIndex, value ))
                            if prop:
                                prop.readCache(value, ppmIndex)
        except (IOError, struct.error) as err:
            dPrint("ERROR", err, "reading", file_name, "cache file")
            pass
        # for par in self.parameters:
        #    for prop in par.properties:
        #        if prop.features & adoIf.Feature.ARCHIVABLE:
        #            print(prop, prop.features)


class AdoParameter:
    """Class representing ADO parameter."""

    contAuxSettingFeature = (
        adoIf.Feature.READABLE
        | adoIf.Feature.WRITABLE
        | adoIf.Feature.ARCHIVABLE
        | adoIf.Feature.SAVABLE
        | adoIf.Feature.RESTORABLE
    )
    contSettingFeature = (
        adoIf.Feature.WRITABLE
        | adoIf.Feature.READABLE
        | adoIf.Feature.EDITABLE
        | adoIf.Feature.ARCHIVABLE
        | adoIf.Feature.SAVABLE
        | adoIf.Feature.RESTORABLE
    )

    def __init__(
        self,
        ado: Ado,
        name: str,
        ptype: str,
        count: int,
        features: int,
        value: Any,
        ppmSize=0,
    ):
        self.ado: Ado = ado
        self.name: str = name
        self._saved_status = [-1] * (ppmSize or 1)
        # Used for alarmDelay counting
        self._alarm_count = 0

        self.property_dict: MutableMapping[str, "AdoProperty"] = {}
        self.addProperty("value", ptype, count, ppmSize, features, value)
        # add timestamps to settings
        if (features & adoIf.Feature.WRITABLE) != 0 and (
            features & (adoIf.Feature.CONFIGURATION | adoIf.Feature.DIAGNOSTIC)
        ) == 0:
            self.addProperty(
                "timestampSeconds",
                "UIntType",
                1,
                self.value.ppmSize,
                adoIf.Feature.READABLE | adoIf.Feature.ARCHIVABLE,
                0,
            )
            self.addProperty(
                "timestampNanoSeconds",
                "UIntType",
                1,
                self.value.ppmSize,
                adoIf.Feature.READABLE | adoIf.Feature.ARCHIVABLE,
                0,
            )

    @property
    def properties(self) -> Tuple["AdoProperty", ...]:
        return tuple(self.property_dict.values())

    def add(self, name, value):
        """Add one of default properties to this parameter."""
        if name == "desc":
            # desc                 StringType    1  0    configData  = configData read
            self.addProperty(
                "desc",
                "StringType",
                1,
                0,
                adoIf.Feature.CONFIGURATION | adoIf.Feature.READABLE,
                value,
            )
        elif name == "units":
            # units                StringType    1  0    contSetting = write read save restore archive
            self.addProperty(
                "units", "StringType", 1, 0, AdoParameter.contAuxSettingFeature, value
            )
        elif name == "format":
            # format               StringType    1  0    contSetting = write read save restore archive
            self.addProperty(
                "format", "StringType", 1, 0, AdoParameter.contAuxSettingFeature, value
            )
        elif name == "timestamps":
            # timestampSeconds     UIntType      1  0    contMeas    = read archive
            # code in __init__ adds adoIf.Feature.ARCHIVABLE for timestamps of settings
            self.addProperty(
                "timestampSeconds",
                "UIntType",
                1,
                self.value.ppmSize,
                adoIf.Feature.READABLE,
                0,
            )
            # timestampNanoSeconds UIntType      1  0    contMeas    = read archive
            self.addProperty(
                "timestampNanoSeconds",
                "UIntType",
                1,
                self.value.ppmSize,
                adoIf.Feature.READABLE,
                0,
            )
            if value != 0:
                self.setTimestamps(value)
        elif name == "cycle":
            # cycle UIntType 1 0 contMeas = read
            self.addProperty(
                "cycle", "UIntType", 1, self.value.ppmSize, adoIf.Feature.READABLE, 0
            )
        elif name == "legalValues":
            # legalValues          StringType    1  0    contMeas    = read
            self.addProperty(
                "legalValues",
                adoIf.InverseXDTYPE[self.value.type],
                1,
                0,
                adoIf.Feature.READABLE,
                value,
            )  # ensure value is of correct type FIX
            # self.value.check = self.value.checkLegal
        elif name == "alarm":
            # alarmLevel           UIntType      1  0    contSetting = write read archive
            self.addProperty(
                "alarmLevel",
                "UIntType",
                1,
                self.value.ppmSize,
                adoIf.Feature.READABLE
                | adoIf.Feature.WRITABLE
                | adoIf.Feature.ARCHIVABLE,
                0,
            )
            # alarmThreshold       UIntType      1  0    contSetting = write read save restore archive
            self.addProperty(
                "alarmThreshold",
                "UIntType",
                1,
                self.value.ppmSize,
                AdoParameter.contAuxSettingFeature,
                0,
            )
        elif name in ("engHigh", "engLow", "opHigh", "opLow"):
            # engHigh              UIntType      1  0    contSetting = write read save restore archive
            # engLow               UIntType      1  0    contSetting = write read save restore archive
            # if type is not numeric, forbid FIX
            self.addProperty(
                name,
                adoIf.InverseXDTYPE[self.value.type],
                1,
                0,
                AdoParameter.contAuxSettingFeature,
                value,
            )
            # self.value.check = self.value.checkLimits
        elif name == "toleranceValues":
            # insure 10 values
            if len(value) != 10:
                raise ValueError("size of toleranceValues properly must be 10")
            # toleranceValues      DoubleType   10  0    contSetting = write read save restore archive
            self.addProperty(
                name,
                adoIf.InverseXDTYPE[self.value.type],
                10,
                0,
                AdoParameter.contAuxSettingFeature,
                value,
            )  # ensure value is of correct type FIX
        # maybe add: conversionValues, nudge, nudgeVal, latchCount, granularity FIX
        # conversionValues     DoubleType   10  0    contSetting = write read save restore archive
        else:
            # print(name, "property is unsupported")
            raise ValueError("{0} property is unsupported".format(name))

    # FIX: it would have been nice that ppmSize has default value
    def addProperty(self, name, ptype, count, ppmSize, features, value):
        """Add any property to this parameter."""
        # check if property already exists
        if name in self.property_dict:
            return
        self.property_dict[name] = prop = AdoProperty(
            self, name, ptype, count, features, value, ppmSize=ppmSize
        )

        return prop

    def setTimestamps(self, t=None, ppmIndex=0):
        """Set timestamp properties."""
        try:
            if t is None:
                t = time.time()
            self.timestampSeconds.setInternal(int(t), ppmIndex)
            self.timestampNanoSeconds.setInternal(
                int((t - int(t)) * 1e9), ppmIndex
            )  # ceil
        except AttributeError:
            pass

    def updateValueTimestamp(self, ppmIndex=0):
        """Publish timestamps and value properties."""
        try:
            self.timestampSeconds.update(ppmIndex)
            self.timestampNanoSeconds.update(ppmIndex)
        except AttributeError:
            pass
        self.value.update(ppmIndex)

    def getValue(self, prop: str = "value", ppmIndex: int = 0):
        """Get property by name."""
        if prop in self.property_dict:
            return self.property_dict[prop].getValue(ppmIndex)
        else:
            return None

    def generateAlarm(self, ppmIndex=0):
        if "alarmLevel" not in self.property_dict:
            return

        topic = "ADO:{ado}:{parameter}".format(ado=self.ado.name, parameter=self.name)

        level = self.alarmLevel.getValue(ppmIndex)
        thresh = self.getValue("alarmThreshold", ppmIndex) or notif.NotifCategory.OK
        latch = self.getValue("latchCount", ppmIndex) or -1

        if level < thresh:
            level = notif.NotifCategory.OK

        alarm_text = self.getValue("alarmText", ppmIndex) or "range error"
        alarm_text = ("[L] {error}" if latch >= 0 else "{error}").format(
            error=alarm_text
        )

        if self.value.ppmSize > 0:
            alarm_string = "{error} PPM={ppm}".format(
                error=alarm_text, ppm=ppmIndex + 1
            )
        else:
            alarm_string = "{error}".format(error=alarm_text)
        notif.send(NOTIF_SERVER, topic, alarm_string, category=level)

    def checkLimits(self, value, ppmIndex=0):
        """Check if value is between engLow and engHigh or opLow and opHigh limits if they exist."""
        # use getattr() or exceptions
        if type(value) is tuple and not value:
            # if we're testing against an array and it is variable length size zero assume we're ok
            return 0

        low = self.getValue("engLow", ppmIndex)
        if low is not None:
            if type(value) is tuple:
                if low > min(value):
                    return RhicError.ADOERROPLOW
            else:
                if low > value:
                    return RhicError.ADOERRENGLOW
        low = self.getValue("opLow", ppmIndex)
        if low is not None:
            if type(value) is tuple:
                if low > min(value):
                    return RhicError.ADOERROPLOW
            else:
                if low > value:
                    return RhicError.ADOERROPLOW
        high = self.getValue("engHigh", ppmIndex)
        if high is not None:
            if type(value) is tuple:
                if high < max(value):
                    return RhicError.ADOERROPHIGH
            else:
                if high < value:
                    return RhicError.ADOERRENGHIGH
        high = self.getValue("opHigh", ppmIndex)
        if high is not None:
            if type(value) is tuple:
                if high < max(value):
                    return RhicError.ADOERROPHIGH
            else:
                if high < value:
                    return RhicError.ADOERROPHIGH
        return 0

    def checkLegal(self, value, ppmIndex=0):
        lv = self.getValue("legalValues", ppmIndex)
        if lv is None:
            return

        type_ = adoIf.InverseXDTYPE[self.value.type]
        native_type = XDnative[type_]
        if native_type is None:
            # We get here if we are struct or void type
            return

        nlv = [native_type(v) for v in lv.split(",")]
        if nlv and value not in nlv:
            return RhicError.ADOERRBADDISCRETE

    def checkTolerance(self, ppmIndex):
        # This method is called to check for alarming conditions
        valueProp: AdoProperty = self.value
        tolProp: Optional[AdoProperty] = self.property_dict.get("toleranceValues")
        alarmLevelProp: Optional[AdoProperty] = self.property_dict.get("alarmLevel")

        # this is for custom alarm function only. this specify the alarm values set which parameter should alarms if the parameter's value is one of the set values.
        # this is equielent to the tolerance arrays [low, high, ....]
        alarmValueProp: Optional[AdoProperty] = self.property_dict.get("alarmValues")

        # this is for custom alarm function only. It specify the tolerance level. Like the thrid element in the tolerace array [low, high, tol_level...]
        tolLevelProp: Optional[AdoProperty] = self.property_dict.get("toleranceLevel")
        legalValuesProp: Optional[AdoProperty] = self.property_dict.get("legalValues")

        tol_func: Optional[Callable[[Any, Any, Any], notif.NotifCategory]] = getattr(
            self, "toleranceFunction", None
        )

        # It only works if the parameter has at least a toleranceValues property
        # so return if not

        if not alarmLevelProp or (not tolProp and not tol_func and not legalValuesProp):
            return

        # Get the value to work with
        value = valueProp.getValue(ppmIndex)

        # for custom tolerance function data setting
        alarm_Values = None
        if alarmValueProp is not None:
            alarm_Values = alarmValueProp.getValue(ppmIndex)

        tol_Level = None
        if tolLevelProp is not None:
            tol_Level = tolLevelProp.getValue(ppmIndex)

        # Check to see if a custom tolerance function was specified, and use if so
        if tol_func:
            # value--parameter vale;  alarm_Values: this is the values set specify on what value alarm sent; tol_Level: specify tolerance level--the alarm level.
            # this function have to be defined in ADO class.  An example of this function can be found in Watch2 ADO, the function
            # named watch_tol_function, search this name to see how it be used.
            alarm_level = tol_func(value, alarm_Values, tol_Level)
            alarm = alarm_level != notif.NotifCategory.OK
        elif tolProp is not None:
            # Values are a 2-tuple, so extract the high & low values
            low, high, *rest = tolProp.getValue(ppmIndex)

            if legalValuesProp is not None:
                # Handling a discrete measurement
                legal_values = legalValuesProp.getValue(ppmIndex).split(",")

                alarm = str(value) not in legal_values
            else:
                # Handling a continuous measurement
                # If the value being set is not a list, make it one so there's only one case to check
                if not isinstance(value, list):
                    value = [value]

                # If any values in the list are outside the tolerance range, sound an alarm
                alarm = any(v < low or v > high for v in value)

            alarm_level = (
                rest[0]
                if (
                    notif.NotifCategory.DEBUG
                    <= rest[0]
                    <= notif.NotifCategory.EMERGENCY
                )
                else notif.NotifCategory.WARNING
            )
            alarm_level = alarm_level if alarm else notif.NotifCategory.OK
        else:
            # If we are here, then neither tol_func and tolProp exist,
            # and tolerance checking should be skipped
            return

        # Now do the delay logic
        delay = self.getValue("alarmDelay", ppmIndex)
        if alarm_level == notif.NotifCategory.OK:
            self._alarm_count = 0
        else:
            self._alarm_count += 1
            if self._alarm_count < delay:
                alarm_level = notif.NotifCategory.OK

        # Now do the latch logic
        latchProp = self.property_dict.get("latchCount")
        if latchProp:
            if self._saved_status[ppmIndex] == -1:
                self._saved_status[ppmIndex] = self.getValue("alarmLevel", ppmIndex)

            if alarm_level != notif.NotifCategory.OK:
                self._saved_status[ppmIndex] = alarm_level

            latch_count = latchProp.getValue(ppmIndex)
            if latch_count > -1 and (
                (latch_count & 1 == 0 and alarm) or (latch_count & 1 == 1 and not alarm)
            ):
                latch_count += 1
                latchProp.setInternal(latch_count, ppmIndex)
                latchProp.update(ppmIndex)

            if latch_count > 0:
                alarm_level = self._saved_status[ppmIndex]

        if debug & DB_INFO:
            dPrint("Alarm level:", alarm_level)
        alarmLevelProp.setExternal(alarm_level, ppmIndex)
        alarmLevelProp.update(ppmIndex)

    def get(self, ppmIndex=0):
        """Default get code, overload for specific behavior."""
        if debug & DB_INFO:
            dPrint("get code for {0} called".format(self.name))
        return 0

    def set(self, ppmIndex=0):
        """Default set code, overload for specific behavior."""
        if debug & DB_INFO:
            dPrint("set code for {0} called".format(self.name))
        return 0

    def __str__(self):
        return self.ado.name + ":" + self.name

    def __getattr__(self, name) -> "AdoProperty":
        """Get property by name."""
        try:
            return self.property_dict[name]
        except KeyError as e:
            raise AttributeError(e)


class AdoProperty:
    """Class representing ADO property."""

    def __init__(
        self,
        adoparameter: AdoParameter,
        name: str,
        ptype: str,
        count: int,
        features: int,
        value: Any,
        ppmSize=0,
    ):
        self.parameter: AdoParameter = adoparameter
        self.name = name
        self.type = adoIf.XDTYPE[ptype]  # type is number now
        self.count = count
        self.ppmSize = int(ppmSize)
        self.features = features
        self.async_requests: List[
            Tuple[Any, ...]
        ] = []  # array of (caller, proc, tid, requestedprops, ppm_index)
        self.setter: Optional[
            Callable[["AdoProperty", Any, int, CallerInfo], int]
        ] = None

        if not (0 <= self.ppmSize <= 16):
            raise ValueError("PPM size must be between 0 and 16")
        if self.ppmSize <= 1:
            self.value = value
        else:
            self.value = [value] * self.ppmSize

        # Attach default setters to the property
        if name == "alarmLevel":
            self.setter = alarmLevelSetter
        elif name == "latchCount":
            self.setter = latchCountSetter
        elif name == "value":
            self.setter = valueSetter

        adoparameter.ado.meta.append(self)
        adoparameter.ado.metadict[(self.parameter.name, self.name)] = self

    def __str__(self):
        return self.parameter.ado.name + ":" + self.parameter.name + ":" + self.name

    def getInternal(self, ppmIndex):
        """Get code called internaly to get value of this property."""
        if self.ppmSize <= 1:
            return self.value
        elif ppmIndex < self.ppmSize:
            return self.value[ppmIndex]

    def getExternal(self, ppmIndex):
        """Get code called to get this property from outside this ADO."""
        # dPrint("get code for {0} called".format( self ))
        if self.name == "value":
            st = self.parameter.get(ppmIndex)
            if st != 0:
                return None, st
        if self.ppmSize <= 1:
            return self.value, 0
        elif ppmIndex < self.ppmSize:
            return self.value[ppmIndex], 0

    def getValue(self, ppmIndex=0):
        """Get value of this property."""
        if self.ppmSize <= 1:
            return self.value
        elif ppmIndex < self.ppmSize:
            return self.value[ppmIndex]

    def setInternal(self, value, ppmIndex, checkTol=True):
        """Set code called internaly to set this property."""
        # sclark - added alarm fix - 2/15/22
        if self.ppmSize <= 1:
            self.value = value
        elif ppmIndex < self.ppmSize:
            self.value[ppmIndex] = value

        if self.features & adoIf.Feature.ARCHIVABLE:
            self.parameter.ado.doarchive = True

        if self.name == "value" and checkTol:
            self.parameter.checkTolerance(ppmIndex)

    def setExternal(self, value, ppmIndex, caller=None):
        """Set code called to set this property from outside this ADO."""

        # Make sure it's a writeable property
        if self.features & adoIf.Feature.WRITABLE == 0:
            return RhicError.ADO_NOT_SETTABLE

        # Ensure a valid PPM index
        if self.ppmSize and self.ppmSize <= ppmIndex:
            return RhicError.ADO_WRONG_PPM_INDEX

        # if metadata.type != self.type or
        #   metadata.count != self.count:
        #   return ADO_NOT_VALID_AS_CONFIGURED FIX

        # We let the custom setter handle it, if it exists
        if self.setter:
            st = self.setter(self, value, ppmIndex, caller)
        else:
            # Otherwise, we use the default setter
            self.setInternal(value, ppmIndex)
            st = 0

        if st == 0 and self.features & adoIf.Feature.ARCHIVABLE:
            self.parameter.ado.doarchive = True

        return st

    def addRequest(self, caller, proc, tid, requestedprops, ppm_index):
        """Add request for this property to list of requests."""
        if self.ppmSize <= 1:
            ppm_index = 0
        if (caller, proc, tid, requestedprops, ppm_index) not in self.async_requests:
            self.async_requests.append((caller, proc, tid, requestedprops, ppm_index))
            if debug & DB_CLIENTS:
                dPrint(
                    "adding request for {0} from {1} proc = {2} tid = {3}, {4} request(s)".format(
                        self, caller, proc, tid, len(self.async_requests)
                    )
                )
            return True
        return False

    def removeRequest(self, caller, proc, tid):
        """Remove request for this property from list of requests."""
        removed = False
        # if proc is 0, cancel all asyncs for this caller
        if proc == 0:
            for i in range(len(self.async_requests) - 1, -1, -1):
                if self.async_requests[i][0] == caller:
                    proc = self.async_requests[i][1]
                    tid = self.async_requests[i][2]
                    del self.async_requests[i]
                    removed = True
                    if debug & DB_CLIENTS:
                        dPrint(
                            "removing request for {0} from {1} proc = {2} tid = {3}, {4} requests".format(
                                self, caller, proc, tid, len(self.async_requests)
                            )
                        )
        else:
            rtid = tid
            for i in range(len(self.async_requests) - 1, -1, -1):
                # if tid is 0, cancel all asyncs for this caller and proc
                if tid == 0:
                    rtid = self.async_requests[i][2]
                if (
                    self.async_requests[i][0] == caller
                    and self.async_requests[i][1] == proc
                    and self.async_requests[i][2] == rtid
                ):
                    del self.async_requests[i]
                    removed = True
                    if debug & DB_CLIENTS:
                        dPrint(
                            "removing request for {0} from {1} proc = {2} tid = {3}, {4} requests".format(
                                self, caller, proc, tid, len(self.async_requests)
                            )
                        )
                    if tid != 0:
                        return True
        if debug & DB_CLIENTS:
            if not removed:
                dPrint(
                    "removing request for {0} from {1} proc = {2} tid = {3} failed, {4} requests".format(
                        self, caller, proc, tid, len(self.async_requests)
                    )
                )
        return removed

    def update(self, ppmIndex):
        """Send new value to clients."""
        if self.ppmSize <= 1:
            ppmIndex = 0
        for i in range(len(self.async_requests) - 1, -1, -1):
            caller, proc, tid, requestedprops, ppm_index = self.async_requests[i]
            if ppm_index != ppmIndex:
                continue
            if debug & DB_UPDATE:
                dPrint("sending update of {0} to {1}".format(self, caller))
            values = [prop.getInternal(ppmIndex) for prop in requestedprops]
            st = sendProperty(
                caller,
                proc,
                tid,
                requestedprops,
                0,
                [0] * len(requestedprops),
                values,
                ppmIndex,
            )
            if debug & DB_ERROR:  # was DB_UPDATE:
                if st is not None:
                    dPrint(
                        "sending update of {0} to {1} failed with status {2}".format(
                            self, caller, st
                        )
                    )

    def writeCache(self, file_object):
        """Write value of property to file if it is archivable."""
        if self.features & adoIf.Feature.ARCHIVABLE == 0:
            return

        file_object.write(struct.pack("B", len(self.parameter.name)))
        file_object.write(
            struct.pack(
                str(len(self.parameter.name)) + "s", self.parameter.name.encode()
            )
        )

        file_object.write(struct.pack("B", len(self.name)))
        file_object.write(struct.pack(str(len(self.name)) + "s", self.name.encode()))
        file_object.write(struct.pack("i", self.type))
        file_object.write(struct.pack("i", self.count))
        file_object.write(struct.pack("i", self.ppmSize))

        if self.ppmSize <= 1:
            value_list = [self.value]
        else:
            value_list = self.value
        # len(value_list) should be equal to self.ppmSize when self.ppmSize != 0
        if self.type == adoIf.XDTYPE["StringType"]:
            for value in value_list:
                # dPrint("{0} : {1} (PPM = {2}) = {3}".format( self.parameter.name, self.name, self.ppmSize, value ))
                file_object.write(struct.pack("I", len(value)))
                file_object.write(
                    struct.pack(
                        str(len(value)) + "s", value.encode(errors="surrogateescape")
                    )
                )
        elif self.count == 0 or self.type == adoIf.XDTYPE["BlobType"]:
            value_format = XDformat[self.type]
            # for k, v in XDformat.items():
            #     dPrint(k, v, struct.calcsize( v ))
            if value_format != "":
                value_size = struct.calcsize(value_format)
                for value in value_list:
                    # dPrint("{0} : {1} (PPM = {2}) = {3}".format( self.parameter.name, self.name, self.ppmSize, value ))
                    file_object.write(struct.pack("I", len(value) * value_size))
                    file_object.write(
                        struct.pack(str(len(value)) + value_format, *value)
                    )
        else:
            value_format = XDformat[self.type]
            if value_format != "":
                for value in value_list:
                    # dPrint("{0} : {1} (PPM = {2}) = {3}".format( self.parameter.name, self.name, self.ppmSize, value ))
                    if self.count == 1:
                        file_object.write(struct.pack(value_format, value))
                    else:
                        file_object.write(
                            struct.pack(str(len(value)) + value_format, *value)
                        )

    def readCache(self, value, ppmIndex):
        """Set value which was read from cache."""
        if self.features & adoIf.Feature.ARCHIVABLE == 0:
            dPrint(
                "property {0} : {1} is not ARCHIVABLE".format(
                    self.parameter.name, self.name
                )
            )
            return
        if self.ppmSize <= 1:
            cvalue = self.value
        else:
            cvalue = self.value[ppmIndex]
        if debug & DB_ARCHIVE:
            dPrint(
                "{0} : {1} (PPM = {2}) = {3} <-- {4}".format(
                    self.parameter.name, self.name, ppmIndex, cvalue, value
                )
            )
        # enforce size
        if (
            self.type != adoIf.XDTYPE["StringType"]
            and self.type != adoIf.XDTYPE["BlobType"]
        ):
            if self.count == 1:
                value = value[0]
            elif self.count != 0 and len(value) != self.count:
                value = value[0 : self.count]
        # enforce types FIX
        if self.ppmSize <= 1:
            self.value = value
        elif ppmIndex < self.ppmSize:
            self.value[ppmIndex] = value


class AdoMUnpacker(adoIf.ADOUnpacker):  # rpc.Unpacker
    """Unpacker for messages to ADO Manager."""

    def unpack_name(self):
        self.unpack_uint()
        self.unpack_uint()  # tid
        self.unpack_uint()  # nprop
        return self.unpack_string().decode()

    def unpack_nameparam(self):
        self.unpack_uint()
        ppm_index = self.unpack_uint() & 0xF
        nprop = self.unpack_uint()
        request = []
        for x in range(nprop):
            adoname = self.unpack_string().decode()
            paramname = self.unpack_string().decode()
            propname = self.unpack_string().decode()
            request.append([adoname, paramname, propname])
        return request, ppm_index

    def unpack_nameparamdata(self):
        self.unpack_uint()
        ppm_index = self.unpack_uint() & 0xF
        request = self.unpack_data()
        return request, ppm_index

    def unpack_callback(self):
        host = self.unpack_string().decode()
        ip = self.unpack_uint()
        program = self.unpack_uint()
        version = self.unpack_uint()
        procedure = self.unpack_uint()
        port = self.unpack_uint() & 0xFFFF
        pid = self.unpack_uint()
        # dPrint(host, hex(ip), program, version, procedure, port, pid)
        return CallerInfo(host, ip, program, version, procedure, port, pid)

    def unpack_nameparamcallback(self, filter=True):
        caller = self.unpack_callback()
        self.unpack_uint()
        tid = self.unpack_uint()
        ppm_index = (tid >> 24) & 0xF
        tid &= 0xFFFFFF
        nprop = self.unpack_uint()
        request = []
        for x in range(nprop):
            adoname = self.unpack_string().decode()
            paramname = self.unpack_string().decode()
            propname = self.unpack_string().decode()
            request.append([adoname, paramname, propname])
        if filter:
            ftype = self.unpack_int()
            if ftype:
                if (
                    ftype == adoIf.FilterType["SKIP_FACTOR"]
                    or ftype == adoIf.FilterType["MIN_TIME_INTERVAL"]
                ):
                    self.unpack_uint()
                elif ftype == adoIf.FilterType["MINIMUM_CHANGE"]:
                    self.unpack_double()
        # dPrint(nprop, adoname, paramname, propname, caller, tid, ftype)
        return request, caller, tid, ppm_index

    def unpack_nameparamdatacallback(self):
        caller = self.unpack_callback()
        self.unpack_uint()
        tid = self.unpack_uint()
        ppm_index = (tid >> 24) & 0xF
        tid &= 0xFFFFFF
        request = self.unpack_data()
        return request, caller, tid, ppm_index

    def unpack_data(self):
        nprop = self.unpack_uint()
        request = []
        allrequest: List[Tuple[str, str, str, str, int]] = []
        for _ in range(nprop):
            adoname = self.unpack_string().decode()
            paramname = self.unpack_string().decode()
            propname = self.unpack_string().decode()
            dtype = adoIf.InverseXDTYPE[self.unpack_enum()]
            count = self.unpack_uint()
            allrequest.append((adoname, paramname, propname, dtype, count))

        for (adoname, paramname, propname, dtype, count) in allrequest:
            try:
                func = self.XDTYPE_unpack[dtype]
                if dtype == "StringType":
                    value = func().decode(errors="surrogateescape")
                elif count == 1:
                    value = func()
                elif count:
                    value = self.unpack_farray(count, func)  # returns list
                else:
                    value = self.unpack_array(func)  # returns list
            except KeyError:  # 'VoidType'
                value = None  # VoidType will end up here
            # dPrint(r, "=", value)
            request.append([adoname, paramname, propname, value])
        return request

    def unpack_controlcallback(self):
        self.unpack_uint()
        tid = self.unpack_uint()  # transaction ID
        self.unpack_uint()  # nprop
        caller = self.unpack_callback()
        return caller, tid

    def unpack_header(self):
        self.unpack_uint()
        self.unpack_uint()


class AdoMPacker(adoIf.ADOPacker):  # rpc.Packer):
    """Packer for messages from ADO Manager."""

    def __init__(self):
        super().__init__()
        self.custom_get_buffer: Optional[Callable[[], bytes]] = None

    def get_buffer(self) -> bytes:
        if self.custom_get_buffer:
            return self.custom_get_buffer()

        return super().get_buffer()

    def pack_meta(self, meta):
        self.pack_uint(0)
        self.pack_uint(0)
        self.pack_uint(len(meta))
        for x in meta:
            self.pack_uint(x.features)
            self.pack_string(x.parameter.name.encode())
            self.pack_string(x.name.encode())
            self.pack_enum(x.type)
            self.pack_uint(x.count)
            self.pack_int(x.ppmSize)

    def pack_data(self, args):
        propList, tid, summary, istatus, valueList, ppmIndex = args
        self.pack_uint(0)
        self.pack_uint((ppmIndex << 24) | (tid & 0xFFFFFF) | 0xC0000000)
        noOfProp = len(propList)  # = len(istatus) = len(valueList)
        self.pack_uint(noOfProp)
        self.pack_int(summary)
        for st in istatus:
            self.pack_int(st)
        for ip in range(0, noOfProp):
            if istatus[ip]:
                continue
            self.pack_enum(propList[ip].type)
            self.pack_uint(propList[ip].count)
        for ip in range(0, noOfProp):
            if istatus[ip]:
                continue
            ctype = adoIf.InverseXDTYPE[propList[ip].type]
            try:
                func = self.XDTYPE_pack[ctype]
            except KeyError:  # 'VoidType'
                continue  # VoidType will end up here
            if ctype == "StringType":
                func(valueList[ip].encode(errors="surrogateescape"))
            elif propList[ip].count == 1:
                func(valueList[ip])
            elif propList[ip].count:
                self.pack_farray(propList[ip].count, valueList[ip], func)
            else:
                self.pack_array(valueList[ip], func)

    def pack_status(self, args):
        tid, summary, istatus = args
        self.pack_uint(0)
        self.pack_uint(tid)
        self.pack_uint(len(istatus))
        self.pack_int(summary)
        for st in istatus:
            self.pack_int(st)

    def pack_callback(self, caller):
        """Pack callback data."""
        self.pack_string(caller.host.encode())
        self.pack_uint(caller.ip)
        self.pack_uint(caller.program)
        self.pack_uint(caller.version)
        self.pack_uint(caller.procedure)
        self.pack_uint(caller.port)
        self.pack_uint(caller.pid)

    def pack_diagnostic(self, ado_server):
        """Pack diagnostic data."""
        ip = ado_server.ip
        sock = ado_server.sock
        pno = ado_server.prog
        vno = ado_server.vers
        startuptime = int(ado_server.starttime + 0.5)
        asyncclients = ado_server.asyncclients
        address, port = sock.getsockname()
        # dPrint(socket.gethostname(), socket.gethostbyname( socket.gethostname() ), ip)
        self.pack_uint(ip)  # IP address
        self.pack_uint(startuptime)
        self.pack_uint(pno)
        self.pack_uint(vno)
        self.pack_int(sock.fileno())
        self.pack_int(port)
        self.pack_int(
            sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        )  # socket receive size
        self.pack_int(
            sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
        )  # socket send size
        self.pack_int(0)  # timeout seconds
        self.pack_int(0)  # timeout microseconds
        num_requests = 0
        for client in asyncclients:
            num_requests += len(client.requests)
        self.pack_int(num_requests)  # number of async requests
        self.pack_uint(ado_server.num_requests)  # number of sync messages handled
        self.pack_uint(0)  # number of async messages handled
        num_asyncclients = len(asyncclients)
        self.pack_int(num_asyncclients)  # number of async clients
        self.pack_array(asyncclients, self.pack_callback)  # addresses

        self.pack_array([x.status for x in asyncclients], self.pack_uint)  # statuses
        self.pack_array(
            [int(x.createTime) for x in asyncclients], self.pack_uint
        )  # creation times
        self.pack_array(
            [x.deleteCount for x in asyncclients], self.pack_uint
        )  # number of tries
        self.pack_array(
            [int(x.lastSendTime) for x in asyncclients], self.pack_uint
        )  # send time
        self.pack_array(
            [len(x.requests) for x in asyncclients], self.pack_uint
        )  # handler count
        self.pack_array(
            [x.lossCount for x in asyncclients], self.pack_uint
        )  # loss count
        self.pack_array(
            [x.sentCount for x in asyncclients], self.pack_uint
        )  # sent count
        self.pack_array(
            [x.sentSize for x in asyncclients], self.pack_uint
        )  # bytes sent


class SendPropertyClient(rpc.RawTCPClient):  # was TCPClient
    packer: AdoMPacker
    unpacker: rpc.Unpacker

    def addpackers(self):
        self.packer = AdoMPacker()
        self.unpacker = rpc.Unpacker(b"")

    def do_call(self):
        call = self.packer.get_buf()
        rpc.sendrecord(self.sock, call)
        self.unpacker.reset(b"")

    def callP(self, arg):
        procedure, tid, props, summary, istatus, values, ppmIndex = arg
        return self.make_call(
            procedure,
            (props, tid, summary, istatus, values, ppmIndex),
            self.packer.pack_data,
            None,
        )

    def callS(self, arg):
        procedure, tid, summary, istatus = arg
        return self.make_call(
            procedure, (tid, summary, istatus), self.packer.pack_status, None
        )


def sendProperty(client, proc, tid, props, summarystatus, istatus, values, ppmIndex):
    """Send property data to this client."""
    if client.status != client.CL_OK:  # client is supposed to be CallerObject
        client.lossCount += 1
        return None
    try:
        c = client.clientObject
        if c is None:
            c = SendPropertyClient(
                client.host, client.program, client.version, client.port
            )
            client.clientObject = c
            c.addpackers()
        if debug & DB_UPDATE:
            dPrint(
                "calling {0} : {1} / {2} proc = {3} tid = {4} to report data".format(
                    client.host, client.program, client.version, proc, tid
                )
            )
        reply = c.callP((proc, tid, props, summarystatus, istatus, values, ppmIndex))
    except RuntimeError as msg:  # program not registered
        if debug & DB_ERROR:
            dPrint("RuntimeError during update:", msg)
            dPrint(
                "suspending updates for {0} proc = {1} tid = {2}".format(
                    client, proc, tid
                )
            )
        client.status = client.CL_NON_RESPONSIVE
        client.deleteCount += 1
        client.lastSendTime = time.time()
        return msg
    except socket.error as msg:  # error: (111, 'Connection refused'), [Errno 32] Broken pipe
        if debug & DB_ERROR:
            dPrint("socket error during update:", msg)
            dPrint(
                "suspending updates for {0} proc = {1} tid = {2}".format(
                    client, proc, tid
                )
            )
        client.status = client.CL_NON_REACHABLE
        client.deleteCount += 1
        client.lastSendTime = time.time()
        return msg
    client.sentCount += 1
    client.lastSendTime = time.time()
    # client.sentSize += sum([len(x) * (1 if isinstance(x, str) else 4) for x in values])
    # dPrint('call returned', repr(reply))
    return reply


def sendStatus(client, proc, tid, summary, istatus):
    """Send status to this client."""
    if client.status != client.CL_OK:  # client is supposed to be CallerObject
        client.lossCount += 1
        return 0
    c = client.clientObject
    if c is None:
        c = SendPropertyClient(client.host, client.program, client.version, client.port)
        client.clientObject = c
        c.addpackers()
    if debug & DB_UPDATE:
        dPrint(
            "calling {0} : {1} / {2} proc = {3} tid = {4} to report status".format(
                client.host, client.program, client.version, proc, tid
            )
        )
    # check for exceptions, just like sendProperty() does FIX
    reply = c.callS((proc, tid, summary, istatus))
    # dPrint('call returned', repr(reply))
    return reply


def adoZero(client):
    if debug & DB_HB:
        dPrint(
            "{0} HB to {1} : {2} / {3} (port {4}, pid {5})".format(
                time.strftime("%H:%M:%S"),
                client.host,
                client.program,
                client.version,
                client.port,
                client.pid,
            )
        )
    c = rpc.RawTCPClient(
        client.host, client.program, client.version, client.port
    )  # was TCPClient
    reply = c.call_0()
    # dPrint('call returned', repr(reply))
    return reply


class AdoServer(rpc.TCPServer):
    """Ado server class."""

    cache_dir: str = ""

    packer: AdoMPacker
    unpacker: AdoMUnpacker

    def __init__(self, name, host="", prog=None, vers=None):
        reply = cns.cnslookup(name)
        if reply is None:
            raise RuntimeError("{0} not in CNS".format(name))
        if debug & DB_START:
            dPrint("CNS reply =", reply)
        if reply.type == "SERVER":
            prog = reply.longA
            vers = reply.longB
        else:
            raise RuntimeError(
                "{0} manager is not server, but {1}".format(name, reply.type)
            )
        self.name = name
        AdoServer.cache_dir = adoCacheDir = os.path.join(
            "/operations/app_store/adoCache", self.name
        )

        try:
            os.mkdir(adoCacheDir)
        except OSError:
            pass

        localname = socket.gethostname()
        if localname.split(".")[0] != reply.value:
            raise RuntimeError(
                "{0} manager should run on {1}, this is {2}".format(
                    name, reply.value, localname
                )
            )
        port = 0 if prog > 0xFFFF else prog
        super().__init__(host, prog, vers, port)
        self.wait = DefaultSelector()
        self.connections = {}  # all connected clients
        self.asyncclients = []  # list of CallerObjects
        notif.origin = name
        self.run = True
        self.HBrun = True
        self.HBThread = threading.Thread(target=self.HBProc, args=())  # strange
        self.HBThread.daemon = True
        self.HBThread.start()
        self.archiveThread = threading.Thread(target=self.archiveProc, args=())
        self.archiveThread.daemon = True
        self.archiveThread.start()
        self.repeat = 0
        self.num_requests = 0
        # for diagnostic request
        self.ip = socket.htonl(
            struct.unpack(
                "I", socket.inet_aton(socket.gethostbyname(socket.gethostname()))
            )[0]
        )
        self.starttime = time.time()
        if not isinstance(self.wait, list) and prog > 0xFFFF:
            # because on Windows this raises socket.error
            try:
                rpc.TCPServer.unregister(self)
            except (RuntimeError, socket.error) as msg:
                dPrint(
                    "AdoServer: error during call to unregister:",
                    msg.__class__.__name__,
                    msg,
                    "(ignored)",
                )
            try:
                rpc.TCPServer.register(self)
            except socket.error as msg:
                dPrint(
                    "AdoServer: error during call to register:",
                    msg.__class__.__name__,
                    msg,
                    "(ignored)",
                )

    def startThread(self):
        """Start running loop() procedure in thread."""
        self.thread = threading.Thread(target=self.loop, args=())
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Make server stop."""
        if not isinstance(self.wait, list):
            try:
                self.unregister()
            except:
                pass  # do not care for errors
        self.HBrun = False
        self.run = False

    def HBProc(self):
        """Run HB() procedure and send HB messages to notif server periodically."""
        counter = 0
        while self.HBrun:
            time.sleep(20.0)
            notif.send(NOTIF_SERVER, "HB", self.name, category=notif.NOTIFY_WARNING)
            counter += 1
            if counter >= 10:  # 200 sec in C++ managers, now also in Python??
                self.HB()
                counter = 0

    def archiveProc(self):
        """Run writeCache() procedures periodically."""
        while self.run:
            time.sleep(20.0)
            for name, ado in adodict.items():
                # write after change only
                if ado.doarchive:
                    ado.doarchive = False
                    ado.writeCache()

    def cleanup(self, fd):
        """Remove file descriptor from list of file descriptors."""
        self.wait.unregister(fd)
        self.connections[fd].close()
        del self.connections[fd]
        if debug & DB_CONNECTIONS:
            dPrint(
                "{0} closing fd {1}, {2} remaining".format(
                    time.strftime("%H:%M:%S"), fd, len(self.connections)
                )
            )

    def HB(self):
        """Call procedure 0 of all clients to insure them this server is live."""
        # make copy of callers, self.asyncclients can be modified
        # is lock needed here? FIX
        callers = self.asyncclients[:]
        for caller in callers:
            if caller.status == caller.CL_UNUSED and len(caller.requests) == 0:
                # maybe delete them in main thread, here declare them CL_DELETED FIX
                self.asyncclients.remove(caller)
                if debug & DB_CLIENTS:
                    dPrint(
                        "deleted client {0}, {1} async client(s)".format(
                            caller, len(self.asyncclients)
                        )
                    )
                continue
            # if bad for long, delete them
            if caller.deleteCount >= 5 and (
                caller.status == caller.CL_NON_REACHABLE
                or caller.status == caller.CL_NON_RESPONSIVE
            ):
                caller.status = caller.CL_UNUSED
                caller.removeRequest(0, 0)
                continue
            try:
                adoZero(caller)
                caller.status = caller.CL_OK
                caller.deleteCount = 0
            except socket.error as msg:  # error: (111, 'Connection refused')
                if debug & DB_ERROR:
                    dPrint("socket error during HB:", msg)
                caller.status = caller.CL_NON_REACHABLE
                caller.lastSendTime = time.time()
                caller.deleteCount += 1
            except RuntimeError as msg:  # program not registered
                if debug & DB_ERROR:
                    dPrint("RuntimeError during HB:", msg)
                caller.status = caller.CL_NON_RESPONSIVE
                caller.lastSendTime = time.time()
                caller.deleteCount += 1

    def loop(self):
        """Wait indefinitely for messages to this server and process them."""
        global activeServer
        activeServer = self
        self.sock.listen(64)
        self.wait.register(self.sock, EVENT_READ)
        while self.run:
            fd_list = self.wait.select(10.0)
            for desc, event in fd_list:
                fd = desc.fd
                if fd == self.sock.fileno():
                    new_socket, address = self.sock.accept()
                    self.wait.register(new_socket, EVENT_READ)
                    if debug & DB_ERROR:
                        if new_socket.fileno() in self.connections:
                            dPrint(
                                "file descriptor {0} already registered".format(
                                    self.connections[new_socket.fileno()]
                                )
                            )
                    self.connections[new_socket.fileno()] = new_socket
                    if debug & DB_CONNECTIONS:
                        dPrint(
                            "{0} opening fd {1} from {2}, {3} open".format(
                                time.strftime("%H:%M:%S"),
                                new_socket.fileno(),
                                address,
                                len(self.connections),
                            )
                        )
                elif event & EVENT_READ:
                    try:
                        self.session(self.connections[fd])
                    except (socket.error, EOFError):
                        self.cleanup(fd)
                else:
                    if debug & DB_ERROR:
                        dPrint("unknown poll event {0} for fd {1}".format(event, fd))
                    self.cleanup(fd)

            if debug & DB_INFO:
                self.repeat += 1
                if self.repeat > 10000:
                    dPrint("processed sockets {0} times".format(self.repeat))
                    self.repeat = 0

    def session(self, sock):
        """Process request on socket."""
        try:
            call = rpc.recvrecord(sock)
        except EOFError:
            if debug & DB_ERROR:
                dPrint("EOF on fd {0} during processing request".format(sock.fileno()))
            # it is OK if socket has no data to read
            self.cleanup(sock.fileno())
            return
        except socket.error as msg:  # socket.error: (104, 'Connection reset by peer')
            if debug & DB_ERROR:
                dPrint("socket error during read:", msg)
            self.cleanup(sock.fileno())
            return
        self.num_requests += 1
        self.last_caller = sock.getpeername()
        try:
            reply = self.handle(call)
        except rpc.xdrlib.Error as msg:  # xdrlib.Error: unextracted data remains
            if debug & DB_ERROR:
                dPrint("XDR error during read:", msg)
            # read / clear that data? FIX
            return
        if reply is not None:
            try:
                rpc.sendrecord(sock, reply)
            except socket.error as msg:  # socket.error: (104, 'Connection reset by peer')
                if debug & DB_ERROR:
                    dPrint("socket error during write:", msg)

    def addpackers(self):
        self.packer = AdoMPacker()
        self.unpacker = AdoMUnpacker("")

    def addCaller(self, callerinfo):
        for x in self.asyncclients:
            if x == callerinfo:
                if x.status == x.CL_UNUSED:
                    x.status = x.CL_OK
                return x
        else:
            caller = CallerObject(callerinfo)
            self.asyncclients.append(caller)
            if debug & DB_CLIENTS:
                dPrint(
                    "adding client {0}, {1} async client(s)".format(
                        caller, len(self.asyncclients)
                    )
                )
            return caller

    @staticmethod
    def dummy():
        return None

    def handle_0(self):
        """Handle NULL message."""
        self.packer.custom_get_buffer = (
            self.packer.get_buffer
        )  # without this call will fail
        self.turn_around()
        if debug & DB_CONNECTIONS:
            dPrint("{0} 0 message received".format(time.strftime("%H:%M:%S")))

    def handle_4(self):
        """Respond to "get metadata" request."""
        adoname = self.unpacker.unpack_name()
        self.packer.custom_get_buffer = (
            self.packer.get_buffer
        )  # because of dummy() assigment
        self.turn_around()
        if debug & DB_REQUEST_B:
            dPrint("request for metadata of", adoname)
        try:
            meta = adodict[adoname].meta
        except KeyError:
            # wrong self.packer.pack_status((0, RhicError.ADO_NO_SUCH_NAME, []))
            self.packer.pack_meta([])
            if debug & DB_ERROR:
                dPrint("ERROR: request for metadata of", adoname)
            return
        self.packer.pack_meta(meta)

    def handle_2(self):
        """Respond to "get data" request."""
        request, ppm_index = self.unpacker.unpack_nameparam()
        self.packer.custom_get_buffer = (
            self.packer.get_buffer
        )  # because of dummy() assigment
        self.turn_around()
        summarystatus = 0
        istatus = []
        plist = []
        vlist = []
        prop: Optional[AdoProperty]
        v: Optional[Any]
        for adoname, paramname, propname in request:
            if debug & DB_REQUEST_B:
                dPrint(
                    "request to get {0} : {1}:{2} PPM = {3}".format(
                        adoname, paramname, propname, ppm_index
                    )
                )
            try:
                ado = adodict[adoname]
                prop = ado.metadict[(paramname, propname)]
                v, st = prop.getExternal(ppm_index)
                if st:
                    summarystatus = RhicError.ADO_FAILED
            except KeyError:
                # return error
                prop = v = None
                st = RhicError.ADO_NO_SUCH_NAME
                summarystatus = RhicError.ADO_FAILED
                if debug & DB_ERROR:
                    dPrint(
                        "ERROR: request to get {0} : {1}:{2} PPM = {3}".format(
                            adoname, paramname, propname, ppm_index
                        )
                    )
            plist.append(prop)
            vlist.append(v)
            istatus.append(st)
        # propList, tid, summary, istatus, valueList, ppmIndex
        self.packer.pack_data((plist, 0, summarystatus, istatus, vlist, ppm_index))

    def handle_1(self):
        """Respond to "set data" request."""
        request, ppm_index = self.unpacker.unpack_nameparamdata()
        self.packer.custom_get_buffer = (
            self.packer.get_buffer
        )  # because of dummy() assigment
        self.turn_around()
        caller = self.get_cred()

        summarystatus = 0
        istatus = []
        for adoname, paramname, propname, value in request:
            if debug & DB_REQUEST_B:
                dPrint(
                    "request to set {0} : {1}:{2} PPM = {3} to {4}".format(
                        adoname, paramname, propname, ppm_index, value
                    )
                )
            try:
                ado = adodict[adoname]
                prop = ado.metadict[(paramname, propname)]
                st = prop.setExternal(value, ppm_index, caller=[caller, self.get_cred()])
                if st:
                    summarystatus = RhicError.ADO_FAILED
                else:
                    # send new value to clients
                    if propname == "value":
                        prop.parameter.setTimestamps(None, ppm_index)
                        prop.parameter.updateValueTimestamp(ppm_index)
                    else:
                        prop.update(ppm_index)
            except KeyError:
                # return error
                summarystatus = RhicError.ADO_FAILED
                st = RhicError.ADO_NO_SUCH_NAME
                if debug & DB_ERROR:
                    dPrint(
                        "ERROR: request to set {0} : {1}:{2} PPM = {3} to {4}".format(
                            adoname, paramname, propname, ppm_index, value
                        )
                    )
            istatus.append(st)
        self.packer.pack_status((0, summarystatus, istatus))

    def handle_5(self):
        """Respond to "get data not-blocking" request."""
        request, callerinfo, tid, ppm_index = self.unpacker.unpack_nameparamcallback(
            filter=False
        )
        self.packer.custom_get_buffer = AdoServer.dummy
        self.turn_around()
        self.packer.reset()
        if debug & DB_REQUEST_NB:
            dPrint(
                "not-blocking request from {0} to get PPM = {1} data of:".format(
                    callerinfo, ppm_index
                )
            )
        summarystatus = 0
        istatus = []
        props = []
        values = []
        prop: Optional[AdoProperty]
        v: Optional[Any]
        for adoname, paramname, propname in request:
            if debug & DB_REQUEST_NB:
                dPrint("    {0} : {1}:{2}".format(adoname, paramname, propname))
            try:
                ado = adodict[adoname]
                prop = ado.metadict[(paramname, propname)]
                v, st = prop.getExternal(ppm_index)
                if st != 0:
                    summarystatus = RhicError.ADO_FAILED
            except KeyError:
                # return error asynchronously
                prop = v = None
                st = RhicError.ADO_NO_SUCH_NAME
                summarystatus = RhicError.ADO_FAILED
                if debug & DB_ERROR:
                    dPrint(
                        "ERROR: not-blocking request to get {0} : {1}:{2} PPM = {3}".format(
                            adoname, paramname, propname, ppm_index
                        )
                    )
            props.append(prop)
            values.append(v)
            istatus.append(st)
        caller = self.addCaller(callerinfo)
        # ( client, proc, tid, props, summarystatus, istatus, values, ppmIndex )
        sendProperty(
            caller,
            callerinfo.procedure,
            tid,
            props,
            summarystatus,
            istatus,
            values,
            ppm_index,
        )
        if caller.status == 0 and len(caller.requests) == 0:
            caller.status = caller.CL_UNUSED

    def handle_16(self):
        """Respond to "set data not-blocking" request."""
        (
            request,
            callerinfo,
            tid,
            ppm_index,
        ) = self.unpacker.unpack_nameparamdatacallback()
        self.packer.custom_get_buffer = AdoServer.dummy
        self.turn_around()
        self.packer.reset()
        if debug & DB_REQUEST_NB:
            dPrint(
                "not-blocking request from {0} to set PPM = {1} data of:".format(
                    callerinfo, ppm_index
                )
            )
        caller = self.addCaller(callerinfo)

        summarystatus = 0
        istatus = []
        for adoname, paramname, propname, value in request:
            if debug & DB_REQUEST_NB:
                dPrint(
                    "    {0} : {1}:{2} to {3}".format(
                        adoname, paramname, propname, value
                    )
                )
            try:
                ado = adodict[adoname]
                prop = ado.metadict[(paramname, propname)]
                st = prop.setExternal(value, ppm_index, caller=[caller, self.get_cred()])
                if st:
                    summarystatus = RhicError.ADO_FAILED
                else:
                    # send new value to clients
                    if propname == "value":
                        prop.parameter.setTimestamps(None, ppm_index)
                        prop.parameter.updateValueTimestamp(ppm_index)
                    else:
                        prop.update(ppm_index)
            except KeyError:
                # return error asynchronously
                summarystatus = RhicError.ADO_FAILED
                st = RhicError.ADO_NO_SUCH_NAME
                if debug & DB_ERROR:
                    dPrint(
                        "ERROR: not-blocking request to set {0} : {1}:{2} PPM = {3} to {4}".format(
                            adoname, paramname, propname, ppm_index, value
                        )
                    )
            istatus.append(st)
        sendStatus(caller, callerinfo.procedure, tid, summarystatus, istatus)
        if caller.status == 0 and len(caller.requests) == 0:
            caller.status = caller.CL_UNUSED

    def handle_3(self):
        """Respond to "get data updates = get data asynchronously" request."""
        request, callerinfo, tid, ppm_index = self.unpacker.unpack_nameparamcallback()
        self.packer.custom_get_buffer = (
            self.packer.get_buffer
        )  # because of dummy() assigment
        self.turn_around()
        if debug & DB_REQUEST_ASYNC:
            dPrint(
                "request from {0} tid = {1} for updates of PPM = {2} data of:".format(
                    callerinfo, tid, ppm_index
                )
            )
        requestedprops = []
        for adoname, paramname, propname in request:
            if debug & DB_REQUEST_ASYNC:
                dPrint("    {0} : {1}:{2}".format(adoname, paramname, propname))
            try:
                ado = adodict[adoname]
                requestedprops.append(ado.metadict[(paramname, propname)])
            except KeyError:
                # return error
                error = RhicError.ADO_NO_SUCH_NAME
                self.packer.pack_status((tid, error, [error] * len(request)))
                if debug & DB_ERROR:
                    dPrint(
                        "ERROR: request for updates of {0} : {1}:{2} PPM = {3}".format(
                            adoname, paramname, propname, ppm_index
                        )
                    )
                return
        caller = self.addCaller(callerinfo)
        caller.addRequest(requestedprops, callerinfo.procedure, tid, ppm_index)
        self.packer.pack_status((tid, 0, [0] * len(request)))

    def handle_7(self):
        """Respond to "stop data updates" request."""
        callerinfo, tid = self.unpacker.unpack_controlcallback()
        self.packer.custom_get_buffer = AdoServer.dummy
        self.turn_around()
        self.packer.reset()
        if debug & DB_REQUEST_ASYNC:
            dPrint("request from {0} to cancel tid {1}".format(callerinfo, tid))
        self.cancelRequest(callerinfo, tid)

    def handle_19(self):
        """Respond to "get diagnostic data" request."""
        self.unpacker.unpack_header()
        self.packer.custom_get_buffer = (
            self.packer.get_buffer
        )  # because of dummy() assigment
        self.turn_around()
        if debug & DB_REQUEST_MISC:
            dPrint("request for diagnostic data")
        self.packer.pack_diagnostic(self)

    def get_cred(self):
        """Unpack 'cred' field of the current RPC packet.
        It supposed to be called from parameter.get(), or .set() methods.
        Otherwise the cred could be overwritten by other requests"""
        if self.cred[0] != rpc.AUTH_UNIX:
            return {"error": "rpc cred is not AUTH_UNIX"}

        buf = self.cred[1]
        r: Dict[str, Any] = {}
        u = rpc.xdrlib.Unpacker(buf)
        r["stamp"] = u.unpack_uint()
        r["machinename"] = u.unpack_string().decode()
        r["uid"] = u.unpack_uint()
        r["gid"] = u.unpack_uint()
        n = u.unpack_uint()
        if n > 0:
            r["gids"] = [u.unpack_uint() for i in range(n)]
        return r

    """
    missing:
#define CONNECT_EVENT_PROC         8u
#define DISCONNECT_EVENT_PROC      9u
#define LIST_EVENT_PROC           10u
#define LIST_CONNECTIONS_PROC     11u
#define LIST_LOGICAL_EVENTS_PROC  12u

#define ASYNC_PAUSE_PROC          14u
#define ASYNC_RESUME_PROC         15u
    """

    def cancelRequest(self, callerinfo, tid):
        """Remove request from list of requests."""
        for caller in self.asyncclients:
            if caller == callerinfo:
                caller.removeRequest(callerinfo.procedure, tid)
                break
        else:
            dPrint("no client {0} to cancel".format(callerinfo))
            return


def createSpecialAdos(ADO_manager_name):
    """Start example python ADO manager."""
    ADO_manager_name_prefix = "differentman"
    if not ADO_manager_name.startswith(ADO_manager_name_prefix):
        dPrint("ADO manager name should start with 'differentman'")
        return
    suffix = ADO_manager_name[len(ADO_manager_name_prefix) :]
    if suffix == "":
        suffix = "1"
    # get ADO_names from CNS instead ?
    # ADO_name = "different.1"
    # ADO2_name = "different2.1"
    ADO_name = "different." + suffix
    ADO2_name = "different2." + suffix
    dPrint("creating", ADO_name, "and", ADO2_name, "ADOs")
    # ask CNS if these names exist? FIX
    server = AdoServer(ADO_manager_name)

    # ADO	 different different.1 cscompile01 1000250 1 special n/
    special = Ado(ADO_name, "my example python ADO", "different", "wonderful")

    mydata = special.addParameter(
        "mydata", "IntType", 1, 0, adoIf.Feature.READABLE, 101010
    )
    mydata.add("desc", "my int parameter which increments by one every second")
    mydata.add("units", "wishes")
    mydata.add("timestamps", 0)

    myidata = special.addParameter(
        "myidata", "IntType", 1, 0, AdoParameter.contSettingFeature, 303
    )
    myidata.add("desc", "my int setting which accepts only odd values")
    myidata.add("units", "odders")
    myidata.set = (
        lambda _: 0 if myidata.value.value % 2 else RhicError.ADO_VALUE_OUT_OF_RANGE
    )

    myblobdata = special.addParameter(
        "myblobdata", "BlobType", 1, 0, AdoParameter.contSettingFeature, b""
    )
    myblobdata.add("desc", "my blob setting")

    myfarray = special.addParameter(
        "myfarray", "DoubleType", 5, 0, AdoParameter.contSettingFeature, [0, 1, 2, 3, 4]
    )
    myfarray.add("desc", "my fixed length double array parameter")
    myfarray.add("units", "wishes")

    myvarray = special.addParameter(
        "myvarray",
        "DoubleType",
        0,
        0,
        AdoParameter.contSettingFeature,
        [-2, -1, -0, -1, -2, -3, -4, -5, -6],
    )
    myvarray.add("desc", "my variable length double array parameter")
    myvarray.add("units", "wishes")

    mystringdata = special.addParameter(
        "mysdata", "StringType", 1, 0, AdoParameter.contSettingFeature, "Hello"
    )
    mystringdata.add("desc", "my string parameter")
    mystringdata.addProperty(
        "unique",
        "StringType",
        1,
        0,
        adoIf.Feature.CONFIGURATION | adoIf.Feature.READABLE,
        "no",
    )

    mylstringdata = special.addParameter(
        "mylsdata",
        "StringType",
        1,
        0,
        adoIf.Feature.DISCRETE | AdoParameter.contSettingFeature,
        "Great",
    )
    mylstringdata.add("desc", "my legal string parameter")
    mylstringdata.add("legalValues", "Great,Greatest")
    mylstringdata.legalValues.features += adoIf.Feature.EDITABLE

    myadata = special.addParameter(
        "myadata", "IntType", 1, 0, adoIf.Feature.READABLE, 22
    )
    myadata.add("desc", "my alarmable int parameter")
    myadata.add("units", "wishes")
    myadata.add("timestamps", 0)
    myadata.add("alarm", 0)
    myadata.add("toleranceValues", [0] * 10)

    mydataPPM = special.addParameter(
        "mydataPPM", "IntType", 1, 8, AdoParameter.contSettingFeature, -555
    )
    mydataPPM.add("desc", "my int PPM parameter")
    mydataPPM.add("units", "horses")
    mydataPPM.add("engHigh", 1000000)
    mydataPPM.add("engLow", -1000000)
    for i in range(mydataPPM.value.ppmSize):
        mydataPPM.value.value[i] = -5000 - i - 1

    myopdata = special.addParameter(
        "myopdata", "FloatType", 1, 0, AdoParameter.contSettingFeature, 5005.0
    )
    myopdata.add("desc", "my op limited setting")
    myopdata.add("opHigh", 1000)
    myopdata.add("opLow", -2000)

    myengdata = special.addParameter(
        "myengdata", "DoubleType", 1, 0, AdoParameter.contSettingFeature, 900009.0
    )
    myengdata.add("desc", "my eng limited setting")
    myengdata.add("engHigh", 4000000)
    myengdata.add("engLow", -1000000)

    mygetdata = special.addParameter(
        "mygetdata", "UIntType", 1, 0, AdoParameter.contSettingFeature, 0
    )
    mygetdata.add("desc", "my get example parameter")
    mygetdata.add("units", "counts")

    mysinarraysize = special.addParameter(
        "mysinarraysize",
        "UIntType",
        1,
        0,
        adoIf.Feature.WRITABLE | adoIf.Feature.READABLE | adoIf.Feature.EDITABLE,
        0,
    )
    mysinarraysize.add(
        "desc", "my parameter which determines the size of mysinarray parameter"
    )

    mysinarray = special.addParameter(
        "mysinarray", "DoubleType", 0, 0, adoIf.Feature.READABLE, []
    )
    mysinarray.add("desc", "my parameter which contains sin waveform")
    mysinarray.add("timestamps", 0)

    def sin_generate(parameter, parametersize):
        import math

        offset = 0
        while True:
            # made this update on the second FIX
            time.sleep(1.0)
            num_points = parametersize.value.value
            if num_points == 0:
                offset = 0
                continue
            period = 2.0 * math.pi / num_points * 1.76666666666
            parameter.value.value = [
                math.sin((x + offset) * period) for x in range(num_points)
            ]
            parameter.setTimestamps()
            parameter.updateValueTimestamp()
            offset += num_points - 1

    mysinarray_update = threading.Thread(
        target=sin_generate, args=(mysinarray, mysinarraysize)
    )
    mysinarray_update.daemon = True
    mysinarray_update.start()

    # use a.func_code.co_argcount to avoid ppmIndex argument FIX
    def count_gets(ppmIndex=0):
        mygetdata.value.value += 1
        if mygetdata.value.value % 10 == 0:
            return RhicError.ADO_NO_DATA
        mygetdata.setTimestamps()
        mygetdata.updateValueTimestamp()
        return 0

    mygetdata.get = count_gets

    my_ext_meas = special.addParameter(
        "externalMeasurement", "DoubleType", 1, 0, adoIf.Feature.READABLE, 0.001
    )
    my_ext_meas.add("desc", "my external measurement parameter")
    my_ext_meas.add("timestamps", 0)
    my_ext_meas.value.features |= adoIf.Feature.WRITABLE
    my_ext_meas.timestampSeconds.features |= adoIf.Feature.WRITABLE
    my_ext_meas.timestampNanoSeconds.features |= adoIf.Feature.WRITABLE
    my_ext_meas.setTimestamps = (
        lambda *args, **kwargs: None
    )  # (self, t=None, ppmIndex=0):

    exitparam = special.addParameter(
        "exit",
        "VoidType",
        1,
        0,
        adoIf.Feature.WRITABLE
        | adoIf.Feature.READABLE
        | adoIf.Feature.EDITABLE
        | adoIf.Feature.DIAGNOSTIC,
        None,
    )
    exitparam.add("desc", "set will stop manager")
    exitparam.set = lambda _: sys.exit(0)

    debugparam = special.addParameter(
        "debug",
        "IntType",
        1,
        0,
        adoIf.Feature.WRITABLE | adoIf.Feature.READABLE | adoIf.Feature.DIAGNOSTIC,
        debug,
    )
    debugparam.add("desc", "debug flag")

    def debugparam_set(ppmIndex=0):
        global debug
        debug = debugparam.value.value
        if debug & DB_INFO:
            dPrint("set debug to", debug)
        return 0

    debugparam.set = debugparam_set

    def parameter_increment(parameter):
        value_property = parameter.value
        while True:
            time.sleep(1.0)
            value_property.value += 1
            parameter.setTimestamps()
            parameter.updateValueTimestamp()
            # dPrint(parameter.name, "=", value_property.value)

    mydata_update = threading.Thread(target=parameter_increment, args=(mydata,))
    mydata_update.daemon = True
    mydata_update.start()

    special.readCache()

    # second ADO
    # ADO      different2 different2.1 cscompile01 1000250 1 special2 n/
    special2 = Ado(ADO2_name, "my example second python ADO", "different2", "yes")

    import platform

    os_param = special2.addParameter(
        "os",
        "StringType",
        1,
        0,
        adoIf.Feature.CONFIGURATION | adoIf.Feature.READABLE,
        platform.platform(),
    )
    os_param.add("desc", "OS of host this manager is running on")

    special2.readCache()

    dPrint(server.name, "manager started...")
    try:
        server.loop()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        dPrint(server.name, "manager stopped.")


if __name__ == "__main__":

    args = sys.argv[1:]
    while len(args) > 0:
        if args[0] == "-debug":
            args.pop(0)
            debug = -1
            if len(args) > 0:
                debug = int(args.pop(0), 0)
        elif args[0] == "showtests":
            args.pop(0)
            print(
                """
 adoMetaData special
 adoIf special version
 adoIf special -get mydata mysdata

 adoIf special myidata 25
 adoIf special -set myidata 3 -set mysdata help

 adoIfA -n special version
 adoIfA -n -g special mydata mysdata

 adoIfSetA special myidata 11111
 adoIfSetA special -set myidata -22221 -set mysdata "no-no"

 adoIfA -T -stop 5 special mydata mydata:timestampSeconds mydata:timestampNanoSeconds
 adoIfA -T -stop 5 -g special mydata mydata:timestampSeconds mydata:timestampNanoSeconds
 asyncInfo differentman

 adoIf -2 special mydataPPM 32
 adoIf -2 special mydataPPM
 adoIf -4 special mydataPPM 3232
 adoIfSetA -4 special mydataPPM -3232
 adoIfA -n -4 special mydataPPM

 adoIf special version "new version"
 adoIf special myidata 2
 adoIfSetA special myidata 2
 adoIf special mylsdata:legalValues
 adoIf special mylsdata Bad
 adoIf special mylsdata Great
 adoIf special -get myopdata:opHigh myopdata:opLow
 adoIf special myopdata -2001
 adoIf special myopdata -2000
 adoIf special myopdata 1000
 adoIf special myopdata 1001
 adoIf special -get myengdata:engHigh myengdata:engLow
 adoIf special myengdata -1000001
 adoIf special myengdata -1000000
 adoIf special myengdata 4000000
 adoIf special myengdata 4000001
 adoIf special -set myidata -44441 -set mylsdata "yes-yes"
 adoIfSetA special -set myidata -22221 -set mylsdata "no-no"
 adoIf special -get myidata mylsdata
            """
            )
            sys.exit(0)
        elif args[0] == "start":
            args.pop(0)
            ADO_manager = "differentman"
            if len(args) > 0:
                ADO_manager = args.pop(0)
            createSpecialAdos(ADO_manager)
            sys.exit(0)
        else:
            break
    usage()

"""
to compare:
diff <( sed 's/xrange/range/;s/iteritems/items/' ~/bin/am.py) <( sed 's/.decode()//;s/.encode()//' ~/bin/am3.py)
"""
