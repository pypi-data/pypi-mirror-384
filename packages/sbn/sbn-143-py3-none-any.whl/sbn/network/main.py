# This file is placed in the Public Domain.


import json
import logging
import os
import os.path
import sys
import time


from ..clients import Client
from ..command import Commands, command, scanner, table
from ..methods import parse
from ..handler import Event
from ..objects import update
from ..package import NAME, Mods
from ..package import getmod, inits, md5sum, modules, setdirs, sums
from ..utility import level, spl
from ..workdir import Workdir, moddir, pidfile, pidname, setwd


CHECKSUM = ""


"config"


class Config:

    debug = False
    default = "irc,mdl,rss"
    gets = {}
    index = None
    init  = ""
    level = "warn"
    mod = ""
    opts = ""
    otxt = ""
    sets = {}
    verbose = False
    version = 153
    wdr = ""


"clients"


class CLI(Client):

    def __init__(self):
        Client.__init__(self)
        self.register("command", command)

    def raw(self, txt):
        out(txt.encode('utf-8', 'replace').decode("utf-8"))


class Console(CLI):

    def callback(self, event):
        if not event.txt:
            return
        super().callback(event)
        event.wait()

    def poll(self):
        evt = Event()
        evt.txt = input("> ")
        evt.type = "command"
        return evt


"scripts"


def background():
    daemon("-v" in sys.argv)
    privileges()
    boot(False)
    pidfile(pidname(NAME))
    inits(spl(Config.init or Config.default))
    forever()


def console():
    import readline # noqa: F401
    boot()
    for _mod, thr in inits(spl(Config.init)):
        if "w" in Config.opts:
            thr.join(30.0)
    csl = Console()
    csl.start()
    forever()


def control():
    if len(sys.argv) == 1:
        return
    boot()
    Commands.add(md5)
    Commands.add(srv)
    Commands.add(tbl)
    csl = CLI()
    evt = Event()
    evt.orig = repr(csl)
    evt.type = "command"
    evt.txt = Config.otxt
    command(evt)
    evt.wait()


def service():
    privileges()
    boot(False)
    pidfile(pidname(NAME))
    banner()
    inits(spl(Config.init or Config.default))
    forever()


def boot(doparse=True):
    if doparse:
        parse(Config, " ".join(sys.argv[1:]))
        update(Config, Config.sets, empty=False)
        Workdir.wdr = Config.wdr
    level(Config.level)
    setwd(NAME)
    if "m" in Config.opts:
        Mods.dir("mods", "mods")
    if "n" in Config.opts:
        Mods.dir("network")
    setdirs("n" in Config.opts, "m" in Config.opts)
    if "v" in Config.opts:
        banner()
    if "a" in Config.opts:
        Config.init = ",".join(modules())
    sums(CHECKSUM)
    table(CHECKSUM)
    Commands.add(cmd)
    Commands.add(ver)
    logging.info("workdir is %s", Workdir.wdr)


"commands"


def cmd(event):
    event.reply(",".join(sorted(Commands.names)))


def md5(event):
    tbl = getmod("tbl")
    if tbl:
        event.reply(md5sum(tbl.__file__))
    else:
        event.reply("table is not there.")


def srv(event):
    import getpass
    name = getpass.getuser()
    event.reply(TXT % (NAME.upper(), name, name, name, NAME))


def tbl(event):
    Commands.names = {}
    scanner()
    event.reply("# This file is placed in the Public Domain.")
    event.reply("")
    event.reply("")
    event.reply('"lookup tables"')
    event.reply("")
    event.reply("")
    event.reply(f"NAMES = {json.dumps(Commands.names, indent=4, sort_keys=True)}")
    event.reply("")
    event.reply("")
    event.reply("MD5 = {")
    for module in scanner():
        event.reply(f'    "{module.__name__.split(".")[-1]}": "{md5sum(module.__file__)}",')
    event.reply("}")


def ver(event):
    event.reply(f"{NAME.upper()} {Config.version}")


"utilities"


def banner():
    tme = time.ctime(time.time()).replace("  ", " ")
    out("%s %s since %s (%s)" % (NAME.upper(), Config.version, tme, Config.level.upper()))


def check(txt):
    args = sys.argv[1:]
    for arg in args:
        if not arg.startswith("-"):
            continue
        for char in txt:
            if char in arg:
                return True
    return False


def daemon(verbose=False):
    pid = os.fork()
    if pid != 0:
        os._exit(0)
    os.setsid()
    pid2 = os.fork()
    if pid2 != 0:
        os._exit(0)
    if not verbose:
        with open('/dev/null', 'r', encoding="utf-8") as sis:
            os.dup2(sis.fileno(), sys.stdin.fileno())
        with open('/dev/null', 'a+', encoding="utf-8") as sos:
            os.dup2(sos.fileno(), sys.stdout.fileno())
        with open('/dev/null', 'a+', encoding="utf-8") as ses:
            os.dup2(ses.fileno(), sys.stderr.fileno())
    os.umask(0)
    os.chdir("/")
    os.nice(10)


def forever():
    while True:
        try:
            time.sleep(0.1)
        except (KeyboardInterrupt, EOFError):
            break


def out(txt):
    print(txt)
    sys.stdout.flush()


def privileges():
    import getpass
    import pwd
    pwnam2 = pwd.getpwnam(getpass.getuser())
    os.setgid(pwnam2.pw_gid)
    os.setuid(pwnam2.pw_uid)


"runtime"


def wrapped(func):
    try:
        func()
    except (KeyboardInterrupt, EOFError):
        out("")


def wrap(func):
    import termios
    old = None
    try:
        old = termios.tcgetattr(sys.stdin.fileno())
    except termios.error:
        pass
    try:
        wrapped(func)
    finally:
        if old:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old)


def main():
    if check("c"):
        wrap(console)
    elif check("d"):
        background()
    elif check("s"):
        wrapped(service)
    else:
        wrapped(control)


TXT = """[Unit]
Description=%s
After=network-online.target

[Service]
Type=simple
User=%s
Group=%s
ExecStart=/home/%s/.local/bin/%s -s

[Install]
WantedBy=multi-user.target"""


if __name__ == "__main__":
    main()
