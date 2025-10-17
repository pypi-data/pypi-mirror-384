#########################################
# Code run when loading the pyfcg package #
#########################################

# Import all functionality into the pyfcg namespace
from pyfcg.fcg_go_bridge import *
from pyfcg.grammar import *
from pyfcg.agent import *
from pyfcg.cxn import *
from pyfcg.utils import *
from pyfcg.propbank import *
from pyfcg.resources import *
from pyfcg.web_interface import *

from . import agent, grammar, cxn, fcg_go_bridge, utils, propbank, resources

__all__ = [
    *agent.__all__,
    *cxn.__all__,
    *fcg_go_bridge.__all__,
    *grammar.__all__,
    *propbank.__all__,
    *utils.__all__,
    *resources.__all__,
]
