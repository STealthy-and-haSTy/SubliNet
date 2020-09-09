import imp
import sys


###----------------------------------------------------------------------------


def reload(prefix, modules=[""]):
    prefix = "SubliNet.%s." % prefix

    for module in modules:
        module = (prefix + module).rstrip(".")
        if module in sys.modules:
            imp.reload(sys.modules[module])


###----------------------------------------------------------------------------


reload("src")

from .src import *


# ###----------------------------------------------------------------------------


def plugin_loaded():
    utils.loaded()
    core.loaded()
    # core.log('Hi', panel=True)


def plugin_unloaded():
    core.unloaded()
    utils.unloaded()


###----------------------------------------------------------------------------
