#!/usr/bin/python2 -t
# Al Marusic

#Send data to Set History Server.

from __future__ import division, print_function

import atexit
import getpass
import os
import pwd
import queue
import socket
import sys
import threading
import time
import xml.etree.ElementTree as ET

from cad_env import get_screenlock_user

MAX_IN_QUEUE = 100000  # the maximum # of records before new storage is rejected
# MAX_IN_QUEUE = 2 # for test
POLL_PERIOD = 10  # how often thread becomes active = 10 secs

debug = False
dataqueue = None
thread = None
storageOff = False
stop_flag = threading.Event()


# create thread, put messages into queue, periodically send data from it to set history server

def get_fullname_adquery(login: str):
    import subprocess as subp
    proc = subp.run(["adquery", "user", "-p", login], stdout=subp.PIPE, stderr=subp.DEVNULL, text=True)
    if proc.returncode != 0:
        return "Unknown"
    return proc.stdout

def usage():
    print(__doc__)
    print("setHistory.py   show | send | store | storemany")
    print()


def main(args):
    global debug

    if len(args) > 0 and args[0] == "-v":
        args.pop(0)
        debug = True

    debug = True
    data = [
        (
            "testgeneric",
            "testparameter",
            "value",
            "StringType",
            1,
            "TESTVALUE",
            "testsystem",
        ),
        ("testgeneric", "testIntparameter", "value", "IntType", 1, 55, "testsystem"),
        (
            "testgeneric",
            "testIntArrayparameter",
            "value",
            "IntType",
            5,
            [1, 2, 3, 4, 5],
            "testsystem",
        ),
    ]
    if len(args) > 0 and args[0] == "show":
        x = createXML([(data, 0, time.time())])
        #print(x)
        return
    if len(args) > 0 and args[0] == "send":
        args.pop(0)
        s = openConnection()
        x = createXML([(data, 0, time.time())])
        sendMessage(s, x)
        return
    if len(args) > 0 and args[0] == "store":
        args.pop(0)
        #print(data)
        store(data, 0)
        return
    if len(args) > 0 and args[0] == "storemany":
        args.pop(0)
        for level in range(3):
            datan = [
                (d[0] + str(level + 1),) + d[1:-1] + (d[-1] + str(level + 1),)
                for d in data
            ]
            store(datan, 0)
        return
    usage()
    return 1


def createXML(data_list):
    root = ET.Element("accessLog")
    root.attrib["version"] = "1.4"

    context = ET.SubElement(root, "context")
    context.attrib["login"] = about.login
    context.attrib["user"] = about.user
    context.attrib["procId"] = str(about.procId)
    context.attrib["procName"] = about.procName
    context.attrib["machine"] = about.machine
    context.tail = "\n"

    # tostring() does:
    # text = text.replace("&", "&amp;")
    # text = text.replace("<", "&lt;")
    # text = text.replace(">", "&gt;")
    # ignoring the status and set time
    stat_index = 0
    for names_values, ppmIndex, ctime, stat, sTime in data_list:
        ppmUser = ppmIndex + 1
        for d in names_values:
            # from cns.py: ado.genericName, adoparameter, adoproperty, dtype.type, dtype.count, value, ado.systemName
            generic_name, aparameter, aproperty, atype, count, value, system_name = d
            if system_name == generic_name:
                generic_name = ""  # if system name == generic name, do not send generic
            # system_name is required
            aparam_prop = (
                aparameter if aproperty == "value" else aparameter + ":" + aproperty
            )
            dtype = paramType.get(atype, "unknown")
            record = ET.SubElement(root, "setRecord")
            record.attrib["ppmUser"] = str(ppmUser)
            record.attrib["type"] = dtype
            record.attrib["time"] = str(ctime)
            record.tail = "\n"
            ET.SubElement(record, "generic").text = generic_name
            ET.SubElement(record, "system").text = system_name
            ET.SubElement(record, "property").text = aparam_prop
            # fix for arrays
            if count != 1:
                str_value = "[" + " ".join([str(v) for v in value]) + "]"
            elif dtype != "void":
                str_value = str(value)
            else:
                str_value = ""
            ET.SubElement(record, "value").text = str_value
            if len(stat) > 1 and len(stat) > stat_index:
                ET.SubElement(record, "status").text = str(stat[stat_index])
                stat_index+=1
            else:
                ET.SubElement(record, "status").text = str(stat[0])
            ET.SubElement(record, "set_time").text = str(sTime)

    try:
        x = ET.tostring(root, encoding="UTF-8", method="xml")
    except TypeError as ex:
        print(ex)
        print("input:", names_values, ppmIndex, ctime)
        return None
    return x


paramType = {
    "CharType": "char",
    "UCharType": "uchar",
    "ShortType": "short",
    "UShortType": "ushort",
    "LongType": "long",
    "ULongType": "ulong",
    "IntType": "int",
    "UIntType": "uint",
    "FloatType": "float",
    "DoubleType": "double",
    "StringType": "string",
    "VoidType": "void",
    "BlobType": "char",
}


class ID:
    def __init__(self):
        self.user = pwd.getpwuid(os.getuid()).pw_gecos
        self.procId = os.getpid()
        self.procName = sys.argv[0]
        self.machine = socket.gethostname()
        host_suffix = ".pbn.bnl.gov"
        if self.machine.endswith(host_suffix):
            self.machine = self.machine[0 : -len(host_suffix)]
        # pwd.struct_passwd(pw_name='marusic', pw_passwd='x', pw_uid=1554, pw_gid=23, pw_gecos='Marusic, Aljosa', pw_dir='/home/cfsd/marusic', pw_shell='/bin/tcsh')
        # from /vobs/libs/utils/AppContext.cxx

    @property
    def login(self):
        login = getpass.getuser()
        screenlock = None
        if os.path.exists("/home/cfsd/sysadmin/bin/isGroup"):
            screenlock = get_screenlock_user()

        if screenlock is None:
            return login  # os.getlogin() requires controlling terminal
        else:
            return f"{login}({screenlock})"
    

about = ID()

def _startThread():
    global dataqueue, thread
    dataqueue = queue.Queue(maxsize=MAX_IN_QUEUE)

    thread = threading.Thread(target=_loop, daemon=True)
    # The entire Python program exits when no alive non-daemon threads are left.
    atexit.register(_exit_handler)
    thread.start()


def _loop():
    should_stop = False
    while not should_stop:
        should_stop = stop_flag.wait(POLL_PERIOD)

        data_list = []
        try:
            # read all from queue
            while True:
                data = dataqueue.get_nowait()
                data_list.append(data)
        except queue.Empty:
            pass

        if not data_list:
            continue

        # convert to XML
        x = createXML(data_list)
        if True:  # change to False for testing
            s = openConnection()
            if debug:
                print("sending...")
                print(x)
            sendMessage(s, x)  # closes socket
        elif debug:
            print("out:", x)

def _exit_handler():
    stop_flag.set()  # set internal flag to True
    if thread is not None:
        thread.join()


def store(names_values, ppmIndex, status, elapsed_time):
    if storageOff:
        return
    if debug:
        for adoname, paramname, propname, dtype, count, value, _, in names_values:
            print(
                "storing:",
                adoname,
                paramname,
                propname,
                dtype,
                count,
                value,
                type(value),
                status,
                elapsed_time,
            )
    if dataqueue is None:
        _startThread()
    try:
        dataqueue.put((names_values, ppmIndex, time.time(), status, elapsed_time), block=False)
    except queue.Full:
        print("data", names_values, ppmIndex, "not sent to set history server")

SETHIST_HOST = os.environ.get("SETHISTHOST", "csinject01.pbn.bnl.gov")
SETHIST_PORT = int(os.environ.get("SETHISTPORT", "8001"))

#: cnslookup setHistoryServer
#REGSERVER SETHISTORY XML-TCP setHistoryServer csinject01.pbn.bnl.gov 8001 1542647881
#: cnslookup setHistory-Backup
#REGSERVER SETHISTORY XML-TCP setHistory-Backup csrhic01.pbn.bnl.gov 8001 1542649103

#: echo $SETHISTHOST
#csinject01.pbn.bnl.gov
#: echo $SETHISTHOSTBACKUP
#csrhic01.pbn.bnl.gov

def openConnection():
    # host = "csinject01.pbn.bnl.gov"  # get from CNS or os.getenv FIX
    host = SETHIST_HOST
    port = SETHIST_PORT
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    return s


def sendMessage(s, message):
    s.sendall(message)
    s.shutdown(socket.SHUT_WR)
    time.sleep(0.2)
    s.close()


if __name__ == "__main__":
    # main( sys.argv[1:] ) HANGS
    sys.exit(main(sys.argv[1:]))
