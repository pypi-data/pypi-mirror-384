import collections
import logging
import os
import socket
import struct
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, IntEnum
from queue import Queue
from selectors import EVENT_READ, DefaultSelector
from typing import Any, Callable, Dict, Hashable, List, Optional, Set

from cad_error import RhicError

from . import cns, rpc, setHistory

__version__ = "v5.0.1 2022-10-31"

# Constants
HB_FREQ = 30  # how often to send HB call to ADO, in seconds
NO_ACTIVITY_TIMEOUT = 250  # if no activity in 250 seconds, then try reconnect
DEFAULT_TIMEOUT = 2.0 # trap blocking calls after 2 seconds

# Global state
_clients: Dict = {}  # dict
_clients_lock = threading.Lock()

_globaltid = 1  # should be between 1 and (1 << 24) - 1, not enforced FIX
_globaltid_lock = threading.Lock()
_metadata_dict: Dict = {}  # dict of dict of classes

XDTYPE = {
    "CharType": 0,
    "UCharType": 1,
    "ShortType": 2,
    "UShortType": 3,
    "LongType": 4,
    "ULongType": 5,
    "FloatType": 6,
    "DoubleType": 7,
    "StringType": 8,
    "StructType": 9,
    "VoidType": 10,
    "BlobType": 11,
    "IntType": 12,
    "UIntType": 13,
}
InverseXDTYPE = dict(zip(XDTYPE.values(), XDTYPE.keys()))


class Feature(IntEnum):
    WRITABLE = 0x0001
    READABLE = 0x0002
    DISCRETE = 0x0004
    ARCHIVABLE = 0x0008
    CONFIGURATION = 0x0010
    DIAGNOSTIC = 0x0020
    SAVABLE = 0x0040
    RESTORABLE = 0x0080
    EDITABLE = 0x0100


FilterType = dict(
    FILTER_NONE=0,
    SKIP_FACTOR=1,
    MIN_TIME_INTERVAL=2,
    MINIMUM_CHANGE=3,
    OUT_OF_TOLERANCE=4,
)


class ADOName(object):
    def __init__(self, sn, gn, s, p, v, c):
        self.systemName = sn
        self.genericName = gn
        self.server = s
        self.program = p
        self.version = v
        self.adoClass = c
        # print self.systemName, self.genericName, self.adoClass, \
        #      self.server, self.program, self.version

    def __repr__(self):
        return "{0}".format(self.systemName)

    def __str__(self):
        return "{0} {1} {2} {3} {4} {5}".format(
            self.systemName,
            self.genericName,
            self.adoClass,
            self.server,
            self.program,
            self.version,
        )

    @classmethod
    def create(thisclass, reply):
        if len(reply) > 6 and reply[0] == "ADO":
            return ADOName(reply[6], reply[2], reply[3], reply[4], reply[5], reply[1])
        else:
            return None


def keep_history(state: bool):
    """Send sets to set history server?"""
    setHistory.storageOff = not state


def create_ado(adoname: str):
    """Create ADO object."""
    where = cns.cnslookup(adoname)
    if where is None:
        print("no such name:", adoname)
        return None

    ado = ADOName.create(where)
    if not isinstance(ado, ADOName):
        print("no such ADO:", adoname)
        return None

    _, st = adoMetaData(ado)
    if st != 0:
        return None

    return ado


class ADOPacker(rpc.Packer):
    def __init__(self):
        rpc.Packer.__init__(self)
        # assign pack function to each XDTYPE
        self.XDTYPE_pack: Dict[str, Callable] = dict(
            CharType=self.pack_int,
            UCharType=self.pack_uint,
            ShortType=self.pack_int,
            UShortType=self.pack_uint,
            LongType=self.pack_int,
            ULongType=self.pack_uint,
            FloatType=self.pack_float,
            DoubleType=self.pack_double,
            StringType=self.pack_string,
            BlobType=self.pack_bytes,
            IntType=self.pack_int,
            UIntType=self.pack_uint,
        )
        # let VoidType raise KeyError exception
        # VoidType = lambda *a, **b: None,

    def pack_name(self, name):
        self.pack_uint(0)
        self.pack_uint(0)  # tid
        self.pack_uint(1)  # nprop
        self.pack_string(name.encode())

    # adoGet and part of adoGetAsync and adoGetNoBlock messages
    def pack_nameparam(self, names_ppmIndex, tid=0):
        """pack the list of ADO names, parameters and properties"""
        self.pack_uint(0)
        names, ppmIndex = names_ppmIndex
        if tid == 0:  # get call
            self.pack_uint(0x80000000 | ppmIndex)
        else:
            self.pack_uint(0x80000000 | (ppmIndex << 24) | tid)  # transaction ID
        self.pack_uint(len(names))  # nprop
        for adoname, paramname, propname in names:
            self.pack_string(adoname.encode())
            self.pack_string(paramname.encode())
            self.pack_string(propname.encode())

    # adoSet and part of adoSetNoBlock messages
    def pack_nameparamdata(self, names_values_ppmIndex, tid=0):
        """pack the list of ADO names, parameters, properties and data"""
        self.pack_uint(0)
        names_values, ppmIndex = names_values_ppmIndex
        if tid == 0:  # set call
            self.pack_uint(0x80000000 | ppmIndex)
        else:
            self.pack_uint(0x80000000 | (ppmIndex << 24) | tid)  # transaction ID
        self.pack_uint(len(names_values))  # nprop
        for adoname, paramname, propname, dtype, count, value, _ in names_values:
            self.pack_string(adoname.encode())
            self.pack_string(paramname.encode())
            self.pack_string(propname.encode())
            self.pack_uint(XDTYPE[dtype])
            self.pack_uint(count)
        for adoname, paramname, propname, dtype, count, value, _ in names_values:
            if dtype == "StringType":
                self.pack_string(str(value).encode(errors="surrogateescape"))
            elif dtype == "BlobType":
                # self.pack_bytes( struct.pack( str(len(value)) + 'B', *map(int, value) ) ) # b = signed char
                self.pack_bytes(bytes(value))
            else:
                try:
                    func = self.XDTYPE_pack[dtype]
                except KeyError:  # 'VoidType'
                    continue  # VoidType will end up here
                convfunc = int if dtype not in ("FloatType", "DoubleType") else float
                if count == 1:
                    func(convfunc(value))
                elif count:
                    # if len(value) != count, pack_farray will raise ValueError, 'wrong array size'
                    self.pack_farray(count, list(map(convfunc, value)), func)
                else:
                    self.pack_array(list(map(convfunc, value)), func)

    def pack_callback(self, server: "AsyncServer", procnumber):
        """pack callback data"""
        host = socket.gethostname()
        port = server.port
        program = server.prog
        version = server.vers

        ip = socket.htonl(
            struct.unpack("I", socket.inet_aton(socket.gethostbyname(host)))[0]
        )

        pid = os.getpid()

        self.pack_string(host.encode())
        self.pack_uint(ip)
        self.pack_uint(program)
        self.pack_uint(version)
        self.pack_uint(procnumber)
        self.pack_uint(port)
        self.pack_uint(pid)

    # adoGetAsync
    def pack_nameparamfiltercallback(self, args):
        """pack callback and the list of ADO names, parameters, properties and filter"""
        names, server, tid, ppmIndex = args
        self.pack_callback(server, 10)
        self.pack_nameparam((names, ppmIndex), tid)
        self.pack_uint(0)  # filter

    # adoGetNoBlock
    def pack_nameparamcallback(self, args):
        """pack callback and the list of ADO names, parameters and properties"""
        names, server, tid, ppmIndex = args
        self.pack_callback(server, 11)
        self.pack_nameparam((names, ppmIndex), tid)

    # adoSetNoBlock
    def pack_nameparamcallbackdata(self, args):
        """pack callback and the list of ADO names, parameters, properties and data"""
        names_values, server, tid, ppmIndex = args
        self.pack_callback(server, 12)
        self.pack_nameparamdata((names_values, ppmIndex), tid)

    def pack_controlcallback(self, args):
        server, tid = args
        self.pack_uint(0)
        self.pack_uint(tid)  # transaction ID
        self.pack_uint(1)  # nprop
        self.pack_callback(server, 10)


class ADOUnpacker(rpc.Unpacker):
    def __init__(self, arg):
        rpc.Unpacker.__init__(self, arg)
        # assign unpack function to each XDTYPE
        self.XDTYPE_unpack: Dict[str, Callable[[], Any]] = dict(
            CharType=self.unpack_int,
            UCharType=self.unpack_uint,
            ShortType=self.unpack_int,
            UShortType=self.unpack_uint,
            LongType=self.unpack_int,
            ULongType=self.unpack_uint,
            FloatType=self.unpack_float,
            DoubleType=self.unpack_double,
            StringType=self.unpack_string,
            BlobType=self.unpack_bytes,
            IntType=self.unpack_int,
            UIntType=self.unpack_uint,
        )

    def unpack_meta(self):
        self.unpack_uint()
        self.unpack_uint()  # tid
        noOfProp = self.unpack_uint()
        meta = []
        for x in range(0, noOfProp):
            features = self.unpack_uint()
            adoparameter = self.unpack_string().decode()
            adoproperty = self.unpack_string().decode()
            dtype = InverseXDTYPE[self.unpack_enum()]
            count = self.unpack_uint()
            ppmSize = self.unpack_int()
            # print adoparameter, adoproperty, dtype, count, ppmSize, features
            # add to list
            meta.append(
                ADOMetaData(adoparameter, adoproperty, dtype, count, ppmSize, features)
            )
        return meta

    def unpack_data(self):
        self.unpack_uint()
        tid = self.unpack_uint() & 0xFFFFFF
        noOfProp = self.unpack_uint()
        summary = self.unpack_int()
        istatus = []
        for ip in range(0, noOfProp):
            istatus.append(self.unpack_int())
        dtype = []
        count = []
        for ip in range(0, noOfProp):
            if istatus[ip]:
                d, c = 0, 0  # because dtype, count is used in next for loop
            else:
                d = self.unpack_enum()
                c = self.unpack_uint()
            dtype.append(d)
            count.append(c)
        # print(tid, noOfProp, summary, istatus, dtype, count)
        data: List = []
        for ip in range(0, noOfProp):
            if istatus[ip]:
                continue
            ctype = InverseXDTYPE[dtype[ip]]
            # print dtype[ ip ], ctype, count[ ip ]
            try:
                func = self.XDTYPE_unpack[ctype]
            except KeyError:  # 'VoidType'
                data.append(None)  # VoidType will end up here
                continue
            if ctype == "BlobType":
                # was d = self.unpack_bytes()
                # data.append( struct.unpack( str(len(d)) + 'b', d ) ) # b = signed char
                data.append(bytearray(self.unpack_bytes()))
            elif ctype == "StringType":
                data.append([self.unpack_string().decode(errors="surrogateescape")])
            elif count[ip]:
                data.append(self.unpack_farray(count[ip], func))
            else:
                data.append(self.unpack_array(func))
        # print "prop count =", noOfProp, "summary =", summary, "status =", istatus, \
        #       "type =", ctype, "count =", count, "data =", data, "tid =", tid
        return data, tid, summary, istatus

    def unpack_status(self):
        self.unpack_uint()
        tid = self.unpack_uint()
        # print hex(tid) # 0xC0000000L
        noOfProp = self.unpack_uint()
        summary = self.unpack_int()
        istatus = []
        for ip in range(0, noOfProp):
            istatus.append(self.unpack_int())
        return summary, tid, istatus


ADOMetaData = collections.namedtuple(
    "ADOMetaData", "parameter, property, type, count, ppmSize, features"
)


class ADOClient(rpc.TCPClient):
    packer: ADOPacker
    unpacker: ADOUnpacker

    def __init__(self, host, prog, vers):
        if prog <= 0xFFFF:
            rpc.RawTCPClient.__init__(self, host, prog, vers, prog)
        else:
            rpc.TCPClient.__init__(self, host, prog, vers)
        self.lock = threading.Lock()

    def mkcred(self):
        # Overridden to use UNIX credentials
        # if self.cred is None:
        #    self.cred = (AUTH_NULL, make_auth_null())
        self.cred = (rpc.AUTH_UNIX, rpc.make_auth_unix_default())
        # print(f'DBG:cns3.mkcred: {self.cred}')
        return self.cred

    def addpackers(self):
        self.packer = ADOPacker()
        self.unpacker = ADOUnpacker(b"")

    # adoMetaData
    def call_4(self, arg):
        with self.lock:
            return self.make_call(
                4, arg, self.packer.pack_name, self.unpacker.unpack_meta
            )

    # adoGet
    def call_2(self, *arg):
        with self.lock:
            return self.make_call(
                2, arg, self.packer.pack_nameparam, self.unpacker.unpack_data
            )

    # adoSet
    def call_1(self, *arg):
        with self.lock:
            return self.make_call(
                1, arg, self.packer.pack_nameparamdata, self.unpacker.unpack_status
            )

    # adoGetAsync
    def call_3(self, *arg):
        with self.lock:
            return self.make_call(
                3,
                arg,
                self.packer.pack_nameparamfiltercallback,
                self.unpacker.unpack_status,
            )


class ADOClientNR(rpc.TCPClient):
    """class similar to adoClient class, but for calls which return no data"""

    packer: ADOPacker
    unpacker: ADOUnpacker

    def __init__(self, host, prog, vers):
        if prog <= 0xFFFF:
            rpc.RawTCPClient.__init__(self, host, prog, vers, prog)
        else:
            rpc.TCPClient.__init__(self, host, prog, vers)
        self.lock = threading.Lock()

    def addpackers(self):
        self.packer = ADOPacker()
        self.unpacker = ADOUnpacker(b"")

    # adoGetNoBlock
    def call_5(self, *arg):
        with self.lock:
            return self.make_call(5, arg, self.packer.pack_nameparamcallback, None)

    # adoSetNoBlock
    def call_16(self, *arg):
        with self.lock:
            return self.make_call(16, arg, self.packer.pack_nameparamcallbackdata, None)

    # adoStopAsync
    def call_7(self, *arg):
        with self.lock:
            return self.make_call(7, arg, self.packer.pack_controlcallback, None)

    # overridden to not expect any return value
    def do_call(self):
        call = self.packer.get_buf()
        rpc.sendrecord(self.sock, call)
        self.unpacker.reset(b"")


def _findClient(CClass, ado):
    """Return existing CClass (= adoClient or adoClientNR) instance or create new one."""
    with _clients_lock:
        try:
            c = _clients[(ado.server, ado.program, ado.version, CClass)]
        except KeyError:
            try:
                c = CClass(ado.server, ado.program, ado.version)
            except (socket.error, RuntimeError) as msg:
                # socket.error: (111, 'Connection refused')
                # socket.timeout: timed out
                # RuntimeError: program not registered
                return None, RhicError.COULD_NOT_CREATE_ADOIF_CLIENT
            c.addpackers()
            # print "added client", ado.server, ado.program, ado.version
            _clients[(ado.server, ado.program, ado.version, CClass)] = c
        return c, RhicError.SUCCESS


def _removeClient(CClass, ado):
    """Remove client from global dict of clients."""
    with _clients_lock:
        del _clients[(ado.server, ado.program, ado.version, CClass)]


def _removeClientObject(c):
    """Remove client from global dict of clients."""
    with _clients_lock:
        for k, v in _clients.items():
            if v == c:
                del _clients[k]
                return


def _getNextTid(how_many):
    global _globaltid
    with _globaltid_lock:
        nexttid = _globaltid
        _globaltid += how_many
        return nexttid


class AsyncServerState(Enum):
    DISCONNECTED = 0
    CONNECTED = 1
    NEEDS_RECONNECT = 2
    WAIT_RECONNECT = 3
    UNKNOWN = 4


@dataclass
class AsyncServer:
    key: Hashable
    sock: socket.socket
    last_timestamp: datetime
    callback: Callable

    # RPC fields
    prog: int
    vers: int

    # Defaults
    hb_count: int = 0
    last_retry: Optional[datetime] = None
    clients: List = field(default_factory=list)
    tids_expected: Set = field(default_factory=set)
    tids_received: Set = field(default_factory=set)
    state: AsyncServerState = AsyncServerState.UNKNOWN

    @property
    def host(self):
        host, _ = self.sock.getsockname()
        return host

    @property
    def port(self):
        _, port = self.sock.getsockname()
        return port

    def update_state(self) -> AsyncServerState:
        if (len(self.tids_expected) > 0 and len(self.tids_received) > 0 and len(self.clients) == 0) or (
            (datetime.now() - self.last_timestamp)
            > timedelta(seconds=NO_ACTIVITY_TIMEOUT)
        ):
            # We:
            # - Expect some TIDs
            # - Have received at least 1 of those TIDs
            # - Have no servers connected
            # so, we need to try to reconnect to the server
            ready_reconnect = self.last_retry is None or (
                datetime.now() - self.last_retry
            ) > timedelta(seconds=HB_FREQ)
            if ready_reconnect:
                new_state = AsyncServerState.NEEDS_RECONNECT
            else:
                new_state = AsyncServerState.WAIT_RECONNECT
        elif ((len(self.tids_expected) == 0 or len(self.tids_received) == 0) and len(self.clients) == 0):
            # We:
            # - Expect no TIDs nor have received any TIDs
            # - Have no clients connected
            # so, we expect no servers to be connected 
            new_state = AsyncServerState.DISCONNECTED
        elif len(self.clients) > 0:
            # We:
            # - Have at least 1 server connected
            # so, we should get deliveries if available
            new_state = AsyncServerState.CONNECTED
        else:
            new_state = AsyncServerState.UNKNOWN

        if self.state != new_state:
            logging.info(f"Transitioning {self} from {self.state} to {new_state}")

        self.state = new_state
        return self.state

    def __str__(self) -> str:
        return str(self.key)

    def __hash__(self) -> int:
        return hash(self.key)


class AsyncReceiver(rpc.Server):
    """async server class -- procs 10 and 11 receive the data and do not reply,
    proc 12 receives status and does not reply"""

    packer: rpc.Packer
    unpacker: ADOUnpacker

    _global = None

    @classmethod
    def global_inst(cls):
        if cls._global is None:
            cls._global = AsyncReceiver()
            cls._global.background()

        return cls._global

    def __init__(self):
        self.host = ""  # Should normally be '' for default interface
        self.prog = 0x20000000 + os.getpid()
        self.vers = 1
        self.port = 0  # Should normally be 0 for random port

        self.addpackers()

        self.logger = logging.getLogger(self.__class__.__name__)
        self.tids = {}
        self.inform = 0
        self.thread = None
        self.timer_thread = None
        self.queue_thread = None
        self.wait = DefaultSelector()
        self.current_server = None
        self.data_queue = Queue() # type: ignore

        self.key_server_map: Dict[Hashable, AsyncServer] = {}
        self.server_server_map: Dict[socket.socket, AsyncServer] = {}
        self.client_server_map: Dict[socket.socket, AsyncServer] = {}
        self.tid_server_map: Dict[int, AsyncServer] = {}
        self.server_known_status: Dict[AsyncServer, AsyncServerState] = {}

    def get_server(self, key):
        return self.key_server_map.get(key)

    def make_server(self, key, callback):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.listen(64)

        server = AsyncServer(key, sock, datetime.now(), callback, self.prog, self.vers)

        self.key_server_map[key] = server
        self.server_server_map[sock] = server

        self.wait.register(sock, EVENT_READ)

        return server

    def start(self):
        """No longer necessary due to new socket structure, kept for compatibility"""
        pass

    def loop(self):
        """Internal helper function which waits on data and maybe deliver it."""
        run = True
        if self.timer_thread is None:
            self.timer_thread = threading.Thread(target=self.process_timers, daemon=True)
            self.timer_thread.start()
            
        while run:
            try:
                run = self.process_one()
            except Exception as exc:
                self.logger.exception("Uncaught exception", exc_info=exc)


        self.thread = None

    def background(self):
        """Wait for async data in dedicated thread and deliver them through callback in that thread"""
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def process_one(self):
        """Check state of sockets and read data if any. Exit when not more TIDs to serve."""
        try:
            event_list = self.wait.select(1.0)
        except KeyboardInterrupt:
            print("Keyboard interrupt received, exiting")
            return False

        for key, event in event_list:
            sock: socket.socket = key.fileobj  # type: ignore

            if sock in self.server_server_map:
                # new connection
                client, _ = sock.accept()

                server = self.server_server_map[sock]
                server.clients.append(client)

                self.client_server_map[client] = server

                self.wait.register(client, EVENT_READ)

                server.update_state()
            elif event & EVENT_READ:
                # new data
                self.current_server = self.client_server_map[sock]
                self.current_server.update_state()
                try:
                    self.session(sock)
                    self.current_server.last_timestamp = datetime.now()
                    self.current_server.hb_count += 1
                finally:
                    self.current_server = None

            else:
                self.cleanup(sock)

        return True

    def session(self, sock):
        """Read data from socket."""
        try:
            call = rpc.recvrecord(sock)
        except EOFError:
            # it is OK if socket has no data to read
            self.cleanup(sock)
            return
        except socket.error as exc:
            # self.logger.warn("socket error during read: %s", exc)
            self.cleanup(sock)
            return

        reply = self.handle(call)
        if reply is not None:
            try:
                rpc.sendrecord(sock, reply)
            except socket.error as exc:
                self.logger.warn("socket error during write: %s", exc)
                self.cleanup(sock)

    def cleanup(self, client: socket.socket):
        """Removed fd from list of fds to check up on."""
        self.logger.info("Cleaned up %s (server for %s)", client, self.client_server_map[client])

        # Remove client sockets from watchlist
        self.wait.unregister(client)
        client.close()

        # Do server cleanup if necessary
        server = self.client_server_map[client]
        server.clients.remove(client)
        del self.client_server_map[client]

        if not server.clients and not server.tids_expected:
            # Server has no more active clients,
            # destroy the server
            self.logger.info("Cleaned up server %s", server)
            self.wait.unregister(server.sock)
            server.sock.close()

            # Delete state
            del self.key_server_map[server.key]
            del self.server_server_map[server.sock]

    def addpackers(self):
        self.packer = rpc.Packer()
        self.unpacker = ADOUnpacker("")

    def returnNothing(self):
        self.turn_around()

        self.packer.get_buf = lambda: None  # type: ignore
        self.packer.reset()

    def handle_0(self):
        """Handle NULL message."""
        self.packer.get_buf = self.packer.get_buffer  # type: ignore
        self.turn_around()
        # this should occur every 200 seconds
        self.logger.debug(
            "Got heartbeat from %s at %s", self.current_server, datetime.now()
        )

    def handle_10(self):
        """Receives async data."""
        data, tid, summarystatus, istatus = self.unpacker.unpack_data()
        self.returnNothing()
        if self.current_server:
            self.current_server.tids_received.add(tid)

        try:
            requests, ppmIndex = self.tids[tid]
            args = [
                (data, tid, requests, istatus, ppmIndex),
                (data, tid, requests, ppmIndex),
                (data, tid, requests),
            ]
            # Try argument types to user function, most specific signature first
            for arg in args:
                try:
                    self.proc(arg)
                    break
                except ValueError as ex:  # ValueError: too many values to unpack
                    if str(ex).startswith("too many values to unpack"):
                        continue
                    else:
                        raise
        except KeyError:
            self.logger.warn("asyncReceiver: async tid = %d is unknown", tid)

    def handle_11(self):
        """Receives non-blocking get data."""
        data, tid, status, istatus = self.unpacker.unpack_data()
        if status != 0:
            if any(istatus):  # Return True if any element of the iterable is true.
                if len(istatus) == 1:
                    status = istatus[0]
                else:
                    status = istatus
        self.returnNothing()
        try:
            requests, ppmIndex = self.tids[tid]
            self.proc((data, tid, requests, status, ppmIndex))
            del self.tids[tid]  # not need for this tid
            del self.tid_server_map[tid]  # not need for this tid
        except KeyError:
            self.logger.warn(
                "asyncReceiver: non-blocking get tid = % d is unknown", tid
            )

    def handle_12(self):
        """Receives non-blocking set data."""
        status, tid, istatus = self.unpacker.unpack_status()
        self.returnNothing()
        try:
            requests, ppmIndex = self.tids[tid]
            self.proc((status, tid, requests, ppmIndex))
            del self.tids[tid]  # not need for this tid
            del self.tid_server_map[tid]  # not need for this tid
        except KeyError:
            self.logger.warn("non-blocking set tid = %d is unknown", tid)

    def proc(self, arg, server=None):
        if self.queue_thread is None:
            self.queue_thread = threading.Thread(target=self.process_queue, daemon=True)
            self.queue_thread.start()
            self.logger.info("Created queue processor thread")
        
        if server is None:
            server = self.current_server

        self.data_queue.put((server, arg))

    def process_queue(self):
        while True:
            server, arg = self.data_queue.get()
            server.callback(arg)

    def process_timers(self):
        self.logger.info("Timer thread created")

        while True:
            # Process timers no faster than once every 5 seconds
            self.logger.debug("Processing timers")
            server_server_map = self.server_server_map.copy()

            for server in server_server_map.values():
                if server not in self.server_known_status:
                    self.server_known_status[server] = server.state

                if server.update_state() == AsyncServerState.NEEDS_RECONNECT:
                    self.logger.info("Server needs reconnection: %s (state %s)", server, server.state)
                    self.rerequest(server)
                self.server_known_status[server] = server.state
            time.sleep(5.0)

    def handle_disconnect(self, server, status, tid, requests, ppmIndex):
        try:
            requests, ppmIndex = self.tids[tid]
            # Try argument types to user function, most specific signature first
            try:
                self.proc(({}, tid, requests, [status] * len(requests), ppmIndex), server=server)
            except ValueError as ex:  # ValueError: too many values to unpack
                if str(ex).startswith("too many values to unpack"):
                    self.logger.info("Received %s from %s", status, server)
                    return
                else:
                    raise
        except KeyError:
            self.logger.warn("asyncReceiver: async tid = %d is unknown", tid)

    def rerequest(self, server: AsyncServer):
        notify = self.server_known_status[server] not in (
            AsyncServerState.NEEDS_RECONNECT,
            AsyncServerState.WAIT_RECONNECT,
        )
        try:
            for tid in server.tids_expected.copy():
                requests, ppmIndex = self.tids[tid]
                if notify:
                    self.handle_disconnect(server, RhicError.IO_DISCONNECTED, tid, requests, ppmIndex)

                _, status = adoHB(requests[0][0])
                if status != RhicError.SUCCESS:
                    self.logger.info("Server is down: %s", server)
                    server.last_retry = datetime.now()
                else:
                    tid, status = adoGetAsync(
                        list=requests,
                        server=server,
                        ppmIndex=ppmIndex,
                        tid=tid,
                        callback=server.callback,
                    )
                    if any(st == RhicError.SUCCESS for st in status):
                        self.logger.info(
                            "Server is back up, re-request success: %s", server
                        )
                        self.handle_disconnect(server, RhicError.IO_RECONNECTED, tid, requests, ppmIndex)
                        server.last_retry = None
                        server.last_timestamp = datetime.now()
                    else:
                        server.last_retry = datetime.now()
        finally:
            pass

def adoMetaData(ado, timeout=DEFAULT_TIMEOUT, cache=True):
    """Get metadata for ADO."""
    if ado.adoClass in _metadata_dict and cache:
        return _metadata_dict[ado.adoClass], 0

    c, st = _findClient(ADOClient, ado)
    if st != 0:
        return None, st

    c.set_timeout(timeout)  # Set the timeout for the client

    try:
        reply = c.call_4(ado.genericName)
    except socket.timeout:
        _removeClientObject(c)
        return None, RhicError.TIMEDOUT
    except (socket.error, RuntimeError):
        _removeClientObject(c)
        return None, RhicError.CANTRECV

    if not reply:
        return None, RhicError.ADOIF_ADO_NOT_FOUND

    _metadata_dict[ado.adoClass] = dict(
        ((desc.parameter, desc.property), desc) for desc in reply
    )
    return _metadata_dict[ado.adoClass], RhicError.SUCCESS


def adoGet(*ado_param_prop, ppmIndex=0, list=None, timeout=DEFAULT_TIMEOUT):
    """Get data from specified ADOs, parameters and properties.
    This function is called as: adoGet( ado, parameter, property )
    or as: adoGet( list = [(ado1, parameter1, property1),
                           (ado2, parameter2, property2), ...] )."""
    if list:
        names = list
    else:
        if len(ado_param_prop) != 3:
            raise TypeError(
                "adoGet() takes exactly 3 arguments ({0} given)".format(
                    len(ado_param_prop)
                )
            )
        names = [ado_param_prop]

    ado = names[0][0]  # names is list of tuples
    c, st = _findClient(ADOClient, ado)
    if st != 0:
        return None, [st] * len(names)

    c.set_timeout(timeout)
    names2 = []
    for i in range(len(names)):
        ado, adoparameter, adoproperty = names[i]
        names2.append((ado.genericName, adoparameter, adoproperty))

    try:
        reply, tid, status, istatus = c.call_2(names2, ppmIndex)  # tid not used
    except socket.timeout:
        _removeClientObject(c)
        return None, [RhicError.TIMEDOUT] * len(names)
    except (socket.error, EOFError):
        # socket.timeout: timed out
        _removeClientObject(c)
        return None, [RhicError.ADO_FAILED] * len(names)

    return reply, [RhicError(s) for s in istatus]

list_type = list
def adoSet(*ado_param_prop_value, ppmIndex=0, list=None, timeout=DEFAULT_TIMEOUT):
    """Set parameters and properties of specified ADOs.
    This function is called as: adoSet( ado, parameter, property, value )
    or as: adoSet( list = [(ado1, parameter1, property1, value1),
                           (ado2, parameter2, property2, value2), ...] )."""
    start_time = time.time_ns()
    if list:
        names = list
    else:
        if len(ado_param_prop_value) != 4:
            raise TypeError(
                "adoSet() takes exactly 4 arguments ({0} given)".format(
                    len(ado_param_prop_value)
                )
            )
        names = [ado_param_prop_value]
    ado = names[0][0]  # names is list of tuples
    c, st = _findClient(ADOClient, ado)
    if st != 0:
        return None, [st] * len(names)

    c.set_timeout(timeout)
    names2 = []
    names3 = []
    istatus = [0] * len(names)
    istatus_idx = list_type(range(len(names)))
    diff = 0
    for i in range(len(names)):
        ado, adoparameter, adoproperty, value = names[i]
        ## try to add another parameter
        try:
            dtype = _metadata_dict[ado.adoClass][(adoparameter, adoproperty)]
            if dtype.type == "StringType":
                names[i] = (ado, adoparameter, adoproperty, str(value).encode())
            elif dtype.type == "BlobType":
                # self.pack_bytes( struct.pack( str(len(value)) + 'B', *map(int, value) ) ) # b = signed char
                names[i] = (ado, adoparameter, adoproperty, bytes(value))
            else:
                try:
                    func = c.packer.XDTYPE_pack[dtype.type]
                    convfunc = int if dtype.type not in ("FloatType", "DoubleType") else float
                    if dtype.count == 1:
                        names[i] = (ado, adoparameter, adoproperty, func(convfunc(value)))
                    else:
                        names[i] = (ado, adoparameter, adoproperty, list_type(map(convfunc, value)))
                except KeyError: #VoidType
                    names[i] = (ado, adoparameter, adoproperty, value)
                    pass

            names3.append(
                    (
                        ado.genericName,
                        adoparameter,
                        adoproperty,
                        dtype.type,
                        dtype.count,
                        value,
                        ado.systemName,
                    )
                )

        except ValueError as e:
            istatus[i - diff] = int(RhicError.ADOIF_CANNOT_CONVERT_DATA_TYPE)
            # names.pop(i - diff)
            istatus_idx.pop(i - diff)
            # convert values to required type
            names3.append(
                (
                    ado.genericName,
                    adoparameter,
                    adoproperty,
                    dtype.type,
                    dtype.count,
                    "<" + str(RhicError.ADOIF_CANNOT_CONVERT_DATA_TYPE) + ">",
                    ado.systemName,
                )
            )
            diff += 1
            continue
        except KeyError:
            # return None, [RhicError.ADOIF_PROPERTY_ID_NOT_FOUND] * len(names)
            istatus[i - diff] = int(RhicError.ADOIF_PROPERTY_ID_NOT_FOUND)
            # names.pop(i - diff)
            istatus_idx.pop(i - diff)
            # Set dtype.type to None
            # Set dtype.count to 1
            # Because dtype isn't actually set!
            names3.append(
                (
                    ado.genericName,
                    adoparameter,
                    adoproperty,
                    # dtype.type,
                    None,
                    # dtype.count,
                    1,
                    "<" + str(RhicError.ADOIF_PROPERTY_ID_NOT_FOUND) + ">",
                    ado.systemName,
                )
            )
            diff += 1
            continue

        # convert values to required type
        names2.append(
            (
                ado.genericName,
                adoparameter,
                adoproperty,
                dtype.type,
                dtype.count,
                value,
                ado.systemName,
            )
        )

    try:
        status, tid, istatus_call = c.call_1(names2, ppmIndex)  # tid not used
        for st, idx in zip(istatus_call, istatus_idx):
            istatus[idx] = st

        end_time = time.time_ns()
        elapsed_time = round((end_time-start_time)*1e-6, 3)
        # this is only for storing the values (names3 holds ALL values even if they were not set)
        setHistory.store(names3, ppmIndex, istatus, elapsed_time)
    except socket.timeout:
        _removeClientObject(c)
        error_data = [(t[0], t[1], t[2], t[3], t[4], "<"+str(RhicError.TIMEDOUT)+">", t[6]) for t in names3]
        end_time = time.time_ns()
        elapsed_time = round((end_time-start_time)*1e-6, 3)
        # end time and add error message for set value
        setHistory.store(error_data, ppmIndex, [int(RhicError.TIMEDOUT)]* len(names), elapsed_time)
        return None, [RhicError.TIMEDOUT] * len(names)
    except (socket.error, EOFError):
        _removeClientObject(c)
        error_data = [(t[0], t[1], t[2], t[3], t[4], "<"+str(RhicError.CANTRECV)+">", t[6]) for t in names3]
        end_time = time.time_ns()
        elapsed_time = round((end_time-start_time)*1e-6, 3)
        # end time and add error message for set value
        setHistory.store(error_data, ppmIndex, [int(RhicError.CANTRECV)]* len(names), elapsed_time)
        return None, [RhicError.CANTRECV] * len(names)
    # except (TypeError, ValueError):
    #     return None, [RhicError.ADOIF_CANNOT_CONVERT_DATA_TYPE] * len(names)

    return None, [RhicError(s) for s in istatus]


def adoHB(ado):
    """Call procedure 0"""
    c, st = _findClient(ADOClient, ado)
    if st != 0:
        return False, st

    try:
        with c.lock:
            c.call_0()
            return True, RhicError.SUCCESS
    except (socket.error, EOFError):
        _removeClient(ADOClient, ado)
        return False, RhicError.CANTRECV


def adoGetAsync(
    *ado_param_prop, ppmIndex=0, server=None, tid=0, list=None, callback=None
):
    """Register to asynchronously receive updates of specified parameters and properties
    of specified ados. This function is called as: adoGetAsync( ado, parameter, property )
    or as: adoGetAsync( list = [(ado1, parameter1, property1),
                                (ado2, parameter2, property2), ...] )."""

    logger = logging.getLogger("adoGetAsync")
    if callback is None:
        raise ValueError("Callback cannot be None")

    if list:
        names = list
    else:
        if len(ado_param_prop) != 3:
            raise ValueError(
                "adoGetAsync() takes exactly 3 arguments ({0} given)".format(
                    len(ado_param_prop)
                )
            )
        names = [ado_param_prop]
    ado = names[0][0]  # names is list of tuples

    c, st = _findClient(ADOClient, ado)
    if st != 0:
        return None, [st] * len(names)

    names2 = []
    for i in range(len(names)):
        ado, adoparameter, adoproperty = names[i]
        names2.append((ado.genericName, adoparameter, adoproperty))

    if tid <= 0:
        tid = _getNextTid(len(names))

    server_key = (c.host, c.prog, c.vers)
    receiver = AsyncReceiver.global_inst()
    if server is None:
        # Get an existing server?
        server = receiver.get_server(server_key)

    if server is None:
        # Make one if none exists
        logger.debug(f"Making server for {server_key}")
        server = receiver.make_server(server_key, callback)

    receiver.tid_server_map[tid] = server

    try:
        status, returnedtid, istatus = c.call_3(
            names2, server, tid, ppmIndex
        )  # returnedtid not used
    except (socket.error, EOFError):
        _removeClientObject(c)
        return None, [RhicError.CANTRECV] * len(names)

    # print 'call returned', status, istatus
    if status == 0:
        # copy of names[] in case caller changes it later
        for i in range(len(names)):
            ado, adoparameter, adoproperty = names[i]
            names2[i] = ado, adoparameter, adoproperty
        # race condition, data might arrive before tids is set FIX
        receiver.tids[tid] = (names2, ppmIndex)
        server.tids_expected.add(tid)

    return tid, [RhicError(s) for s in istatus]


def adoStopAsync(server=None, tid=0):
    """Stop asynchronous updates with specified transaction ID."""
    # if tid is 0, remove all tids of this server
    if server is None:
        server = AsyncReceiver.global_inst()

    if tid == 0:
        for tid in server.tid_server_map.copy():
            adoStopAsync(server, tid)
    else:
        try:
            requests, ppmIndex = server.tids.pop(tid)
            async_server = server.tid_server_map.pop(tid)
            async_server.tids_expected.remove(tid)
            ado = requests[0][0]
        except KeyError:
            return None, RhicError.IO_CANNOT_CANCEL_ASYNC

        c, st = _findClient(ADOClientNR, ado)
        if st != 0:
            return None, st

        try:
            reply = c.call_7(async_server, tid)  # always returns None
        except (socket.error, EOFError):
            _removeClientObject(c)
            return None, RhicError.CANTRECV

        return None, RhicError.SUCCESS


def adoGetNoBlock(*ado_param_prop, ppmIndex=0, server=None, list=None, callback=None):
    """Get data from specified ados, parameters and properties without blocking.
    This function is called as: adoGetNoBlock( ado, parameter, property )
    or as: adoGetNoBlock( list = [(ado1, parameter1, property1),
                                  (ado2, parameter2, property2), ...] )."""

    logger = logging.getLogger("adoGetNoBlock")
    if list:
        names = list
    else:
        if len(ado_param_prop) != 3:
            raise ValueError(
                "adoGetNoBlock() takes exactly 3 arguments ({0} given)".format(
                    len(ado_param_prop)
                )
            )
        names = [ado_param_prop]

    ado = names[0][0]  # names is list of tuples
    c, st = _findClient(ADOClientNR, ado)
    if st != 0:
        return None, st

    names2 = []
    for i in range(len(names)):
        ado, adoparameter, adoproperty = names[i]
        names2.append((ado.genericName, adoparameter, adoproperty))
    tid = _getNextTid(len(names))

    server_key = (c.host, c.prog, c.vers)
    receiver = AsyncReceiver.global_inst()
    if server is None:
        # Get an existing server?
        server = receiver.get_server(server_key)

    if server is None:
        # Make one if none exists
        logger.debug(f"Making server for {server_key}")
        server = receiver.make_server(server_key, callback)

    receiver.tid_server_map[tid] = server

    try:
        reply = c.call_5(names2, server, tid, ppmIndex)  # always returns None
    except (socket.error, EOFError):
        _removeClientObject(c)
        return None, RhicError.CANTRECV

    if reply == None:
        for i in range(len(names)):
            ado, adoparameter, adoproperty = names[i]
            names2[i] = ado, adoparameter, adoproperty
        server.tids_expected[tid] = (names2, ppmIndex)

    return tid, RhicError.SUCCESS


def adoSetNoBlock(
    *ado_param_prop_value, ppmIndex=0, server=None, list=None, callback=None
):
    """Set parameters and properties of specified ados without blocking.
    This function is called as: adoSetNoBlock( ado, parameter, property, value )
    or as: adoSetNoBlock( list = [(ado1, parameter1, property1, value1),
                                  (ado2, parameter2, property2, value2), ...] )."""

    start_time = time.time_ns()
    logger = logging.getLogger("adoSetNoBlock")
    if list:
        names = list
    else:
        if len(ado_param_prop_value) != 4:
            raise ValueError(
                "adoSetNoBlock() takes exactly 4 arguments ({0} given)".format(
                    len(ado_param_prop_value)
                )
            )
        names = [ado_param_prop_value]
    ado = names[0][0]  # names is list of tuples
    c, st = _findClient(ADOClientNR, ado)
    if st != 0:
        return None, RhicError(st)

    names2 = []
    for i in range(len(names)):
        ado, adoparameter, adoproperty, value = names[i]
        try:
            dtype = _metadata_dict[ado.adoClass][(adoparameter, adoproperty)]
        except KeyError:
            return None, RhicError.ADOIF_PROPERTY_ID_NOT_FOUND

        names2.append(
            (
                ado.genericName,
                adoparameter,
                adoproperty,
                dtype.type,
                dtype.count,
                value,
                ado.systemName,
            )
        )
    tid = _getNextTid(len(names))

    server_key = (c.host, c.prog, c.vers)
    receiver = AsyncReceiver.global_inst()
    if server is None:
        # Get an existing server?
        server = receiver.get_server(server_key)

    if server is None:
        # Make one if none exists
        logger.debug(f"Making server for {server_key}")
        server = receiver.make_server(server_key, callback)

    receiver.tid_server_map[tid] = server

    try:
        reply = c.call_16(names2, server, tid, ppmIndex)  # always returns None
        end_time = time.time_ns()
        elapsed_time = round((end_time-start_time)*1e-6, 3)
        setHistory.store(names2, ppmIndex, 0, elapsed_time)
    except (socket.error, EOFError):
        _removeClientObject(c)
        names3 = [(t[0], t[1], t[2], t[3], t[4], "<"+str(RhicError.CANTRECV)+">", t[6]) for t in names2]
        end_time = time.time_ns()
        elapsed_time = round((end_time-start_time)*1e-6, 3)
        setHistory.store(names3, ppmIndex, int(RhicError.CANTRECV), elapsed_time)
        return None, RhicError.CANTRECV
    except (TypeError, ValueError):
        # TypeError: int() argument must be a string or a number, not 'list'
        # ValueError: invalid literal for int() with base 10: 'x'
        names3 = [(t[0], t[1], t[2], t[3], t[4], "<"+str(RhicError.ADOIF_CANNOT_CONVERT_DATA_TYPE)+">", t[6]) for t in names2]
        status = int(RhicError.ADOIF_CANNOT_CONVERT_DATA_TYPE)
        end_time = time.time_ns()
        elapsed_time = round((end_time-start_time)*1e-6, 3)
        # end time and add error message for set valu
        setHistory.store(names3, ppmIndex, status, elapsed_time)
        return None, RhicError.ADOIF_CANNOT_CONVERT_DATA_TYPE

    if reply == None:
        namesC = []  # copy of names[] in case caller changes it later
        for i in range(len(names)):
            ado, adoparameter, adoproperty, value = names[i]
            namesC.append((ado, adoparameter, adoproperty))
        # race condition, data might arrive before tids is set FIX
        server.tids_expected[tid] = (namesC, ppmIndex)

    return tid, RhicError.SUCCESS


# Helper function to return the string representation of a feature_bit value
def feature_str(feature_bits) -> str:
    fd = {
        "READABLE": "R",
        "WRITABLE": "W",
        "DISCRETE": "D",
        "ARCHIVABLE": "A",
        "EDITABLE": "E",
        "CONFIGURATION": "C",
        "SAVABLE": "S",
        "DIAGNOSTIC": "I",
    }
    features = []
    for name in fd:
        feature = Feature[name]
        if feature_bits & feature:
            features.append(name.title())
    return ", ".join(features)


# Helper function to return category name - this support was replaced by feature bits but
# is included for convenience and backwards compatibility but should not be needed in general
def category_for_features(feature_bits) -> str:
    if feature_bits & Feature.CONFIGURATION:
        return "configData"
    elif feature_bits & Feature.DIAGNOSTIC:
        return "diagData"
    elif (
        (feature_bits & Feature.DISCRETE)
        and (feature_bits & Feature.WRITABLE)
        and (feature_bits & Feature.READABLE)
    ):
        return "discSetting"
    elif (feature_bits & Feature.WRITABLE) and (
        feature_bits & Feature.READABLE
    ):
        return "contSetting"
    elif (feature_bits & Feature.DISCRETE) and (
        feature_bits & Feature.READABLE
    ):
        return "discMeas"
    elif feature_bits & Feature.READABLE:
        return "contMeas"
    elif (feature_bits & Feature.DISCRETE) and (
        feature_bits & Feature.WRITABLE
    ):
        return "discAction"
    elif feature_bits & Feature.WRITABLE:
        return "contAction"
    else:
        return "unknownCategory"
