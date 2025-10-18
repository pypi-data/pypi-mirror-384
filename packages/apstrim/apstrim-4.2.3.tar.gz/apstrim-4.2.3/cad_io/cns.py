#!/usr/bin/env python3
# Al Marusic

"""Implementation of ADO networking protocol.
"""

# __version__ = "3.43b"
__author__ = "Al Marusic"
__version__ = "v5.1.1 2023-05-18"  # Removed adoIf functions


"""
To get data about object from CNS:
> ~/bin/cns3.py wfgman.rhic
ADO wfgman wfgman.rhic acnlin9b 1000023 1 wfgman.rhic n/ 0

To get metadata of ADO:
> ~/bin/cns3.py wfgman.rhic -meta |& more
('version', 'value', 'StringType', 1, 0, 18)
('className', 'value', 'StringType', 1, 0, 18)
('commandBufferLength', 'desc', 'StringType', 1, 0, 18)
...

To get data from property:
> ~/bin/cns3.py wfgman.rhic fecName
wfgman.rhic fecName:value [['acnlin9b.pbn.bnl.gov']]

To set property:
> ~/bin/cns3.py wfgman.rhic debugD 0
wfgman.rhic debugD:value [[0]]

To asynchronously receive values of property:
> ~/bin/cns3.py wfg.b-dmain-ps readbackM -async 5
...

To get data from property without blocking:
> ~/bin/cns3.py wfg.b-dmain-ps readbackM -noblock
"""

import collections
import os
import threading
from typing import Optional

from . import rpc as rpc

CNSData = collections.namedtuple(
    "CNSData", "type, string2, entry, value, longA, longB, string3, string4, status"
)

EntryType = {
    "NO_VALUE": 0,
    "SERVER": 1,
    "ADO": 2,
    "ALIAS": 7,
    "MISC": 12,
    "CDEVDEVICE": 13,
    "REGSERVER": 14,
}
InverseEntryType = dict(zip(EntryType.values(), EntryType.keys()))


class CNSUnpacker(rpc.Unpacker):
    def unpack_generic(self):
        entryType = self.unpack_enum()
        entry = self.unpack_string().decode()
        value = self.unpack_string().decode()
        string2 = self.unpack_string().decode()
        longA = self.unpack_uint()
        longB = self.unpack_uint()
        status = self.unpack_uint()
        string3 = self.unpack_string().decode()
        string4 = self.unpack_string().decode()
        if entryType in InverseEntryType and entryType != 0 and status == 0:
            return CNSData(
                InverseEntryType[entryType],
                string2,
                entry,
                value,
                longA,
                longB,
                string3,
                string4,
                status,
            )
        else:
            return None


class CNSClient(rpc.TCPClient):
    """RPC object to access CNS."""

    packer: rpc.Packer
    unpacker: CNSUnpacker

    # _global: Optional["CNSClient"] = None

    def __init__(
        self,
        host=os.getenv("CNSHOST", "acnserver01.pbn.bnl.gov"),
        prog=0x36666666,
        vers=5,
    ):
        super().__init__(host, prog, vers)
        self.lock = threading.Lock()
        self.packer = rpc.Packer()
        self.unpacker = CNSUnpacker(b"")

    def lookup(self, name: str):
        with self.lock:
            reply = self.make_call(
                2,
                name.encode(),
                self.packer.pack_string,
                self.unpacker.unpack_generic,
            )
            return reply

    # @classmethod
    # def instance(cls):
    #     if cls._global is None:
    #         cls._global = cls()

    #     return cls._global


_primary_client: Optional[CNSClient] = None
_backup_client: Optional[CNSClient] = None  # CNSClient(host=os.getenv("CNSHOSTBACKUP"))


def cnslookup(name: str, backup: bool = False):
    """Lookup up name in CNS."""
    global _primary_client, _backup_client
    if backup:
        if _backup_client is None:
            _backup_client = CNSClient(host=os.getenv("CNSHOSTBACKUP"))
        client = _backup_client
    else:
        if _primary_client is None:
            _primary_client = CNSClient()
        client = _primary_client

    try:
        return client.lookup(name)
    except (IOError, EOFError): 
        if backup:
            _backup_client.close()
            _backup_client = None
            raise
        _primary_client.close()
        _primary_client = None
        return cnslookup(name, backup=True)


if __name__ == "__main__":
    import sys

    print(cnslookup(sys.argv[1]))
