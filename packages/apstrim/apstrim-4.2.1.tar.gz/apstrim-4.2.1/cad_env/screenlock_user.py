import getpass
import os
import re
import subprocess as subp
from typing import Optional

SCREENLOCK_RE = re.compile(r"(\S+)\s+(\d+)")

_screenlock_last_read: int = 0
_screenlock_user: Optional[str] = None


def get_screenlock_user():
    global _screenlock_last_read
    global _screenlock_user

    username = getpass.getuser()
    proc = subp.run(
        ["/home/cfsd/sysadmin/bin/isGroup", "-q", username],
        text=True,
        stdout=subp.DEVNULL,
        stderr=subp.DEVNULL,
    )
    if proc.returncode != 0:
        _screenlock_last_read = 0
        _screenlock_user = None
        return None

    filename = "/tmp/ScreenLockFile"

    if not os.path.exists(filename):
        _screenlock_last_read = 0
        _screenlock_user = None
        return None

    stat = os.stat(filename)
    if stat.st_mtime <= _screenlock_last_read:
        # No update since last check
        return _screenlock_user

    with open(filename, "rt") as file:
        content = file.read()
        match = SCREENLOCK_RE.match(content)
        if match:
            username, _ = match.groups()
            _screenlock_last_read = stat.st_mtime
            _screenlock_user = username
        else:
            _screenlock_last_read = 0
            _screenlock_user = None
    return _screenlock_user
