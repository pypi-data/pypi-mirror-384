# This file is placed in the Public Domain.


"show modules"


from ..package import modules


def mod(event):
    event.reply(",".join(modules()))
