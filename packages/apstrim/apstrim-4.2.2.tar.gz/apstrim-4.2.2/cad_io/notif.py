#!/usr/bin/env python3
# Al Marusic

"""Python module for sending messages to notif server."""
import socket
from enum import IntEnum

from cad_io.cns import cnslookup

# AS: comment the following line for local testing
from . import rpc as rpc

__version__ = "1.07"
__author__ = "Al Marusic"


def usage():
    print(__doc__)
    print("Usage:   notif.py [-r|-a] message")


NOTIFY_EMERGENCY = 8
NOTIFY_ALERT = 7
NOTIFY_CRITICAL = 6
NOTIFY_ERROR = 5
NOTIFY_WARNING = 4
# messages with notif levels 4 to 8 get turned into alarms
NOTIFY_NOTICE = 3
NOTIFY_INFO = 2
NOTIFY_DEBUG = 1
NOTIFY_OK = 0

class NotifCategory(IntEnum):
    """Notif categories."""
    EMERGENCY = NOTIFY_EMERGENCY
    ALERT = NOTIFY_ALERT
    CRITICAL = NOTIFY_CRITICAL
    ERROR = NOTIFY_ERROR
    WARNING = NOTIFY_WARNING
    NOTICE = NOTIFY_NOTICE
    INFO = NOTIFY_INFO
    DEBUG = NOTIFY_DEBUG
    OK = NOTIFY_OK

SERVERS = [
    "RHICNotifServer",
    "AGSNotifServer",
    "TestNotifServer",
]

_SERVER_CACHE = {}

origin = "notif.py"


class notifPacker(rpc.Packer):
    def pack_message(self, args):
        category, topic, message = args
        self.pack_int(0)
        self.pack_string(origin.encode())  # host
        self.pack_string(b"python")  # task
        self.pack_int(0)  # task ID
        self.pack_int(category)  # category
        self.pack_int(0)  # 0
        self.pack_string(topic.encode())
        self.pack_string(message.encode())


class NotifClient(rpc.TCPClient):
    packer: notifPacker

    def addpackers(self):
        self.packer = notifPacker()
        self.unpacker = rpc.Unpacker("")

    # do not wait for reply
    def do_call(self):
        call = self.packer.get_buf()
        rpc.sendrecord(self.sock, call)

    def call_10(self, arg):
        return self.make_call(10, arg, self.packer.pack_message, None)

def send(server, topic, message, category=NOTIFY_OK):
    if server in SERVERS:
        if server not in _SERVER_CACHE:
            cns = cnslookup(server)
            _SERVER_CACHE[server] = (cns.value, cns.longA)
        host, prog = _SERVER_CACHE[server]
    else:
        try:
            host, prog = server
        except ValueError:
            raise ValueError("Server must either be NotifServer name, or tuple of (host, prog).")

    try:
        c = NotifClient(host, prog, 1)  # calls connect, which "timeout: timed out"
        # or "RuntimeError: program not registered"
        c.addpackers()
        # topic is ADO:ado:parameter for ADO alarms
        reply = c.call_10((category, topic, message))
    except (socket.error, EOFError, RuntimeError) as msg:
        return msg
    return reply


class notifUnpacker(rpc.Unpacker):
    def unpack_stat(self):
        self.unpack_int()
        o = self.unpack_string()
        t = self.unpack_string()
        self.unpack_int()
        self.unpack_int()
        self.unpack_int()
        to = self.unpack_string()
        if len(o) > 0 or len(t) > 0 or len(to) > 0:
            print("non-empty fields:", o, t, to)
        message = self.unpack_string().decode()
        return message


class StatClient(rpc.TCPClient):
    unpacker: notifUnpacker

    def addpackers(self):
        self.packer = rpc.Packer()
        self.unpacker = notifUnpacker("")

    def call_me(self, proc):
        return self.make_call(proc, None, None, self.unpacker.unpack_stat)


def statRequest(server, option="stat"):
    """Send various requests no notif server."""
    # 3 = write and return stat
    # 5 = test
    # 4 = reconfigure
    # 2 = terminate
    if server in SERVERS:
        if server not in _SERVER_CACHE:
            cns = cnslookup(server)
            _SERVER_CACHE[server] = (cns.value, cns.longA)
        host, prog = _SERVER_CACHE[server]
    else:
        try:
            host, prog = server
        except ValueError:
            raise ValueError("Server must either be NotifServer name, or tuple of (host, prog).")

    options = dict(stat=3, test=5, terminate=2, reconfigure=4)
    proc = options.get(option, 3)
    # print(options, option, proc)
    try:
        c = StatClient(host, prog, 1)  # calls connect, which "timeout: timed out"
        # or "RuntimeError: program not registered"
        c.addpackers()
        reply = c.call_me(proc)
    except (socket.error, EOFError, RuntimeError) as msg:
        return msg
    return reply


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Send message to notif server.")
    parser.add_argument("-s", "--server", default="TestNotifServer", help="Notif server name.", choices=SERVERS)
    parser.add_argument("-t", "--topic", default="Test", help="Topic.")
    parser.add_argument("-c", "--category", default=NotifCategory.OK.name, help="Notif level of message.", choices=[e.name for e in NotifCategory])
    parser.add_argument("message", help="Message.")


    args = parser.parse_args()
    server = args.server
    topic = args.topic
    category = NotifCategory[args.category]
    message = args.message

    if message.startswith("HB:"):
        st = send(server, "HB", message[3:], category=NOTIFY_WARNING)
    elif message.startswith("::stat::"):
        print(statRequest(server))
        exit(0)
    elif message.startswith("::test::"):
        print(statRequest(server, "test"))
        exit(0)
    elif message.startswith("::stop::"):
        # print(statRequest(host, program, "reconfigure"))
        print(statRequest(server, "terminate"))
        exit(0)
    else:
        st = send(server, topic, message, category=category)

    if st is not None:
        print(
            'ERROR: "{0}" while sending message to {1}'.format(
                st, server
            )
        )
        exit(10)
