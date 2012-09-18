"""This module generate C++ code for OpenFlow structs.

(C) Copyright Stanford University
Date May 2010
Created by ykk
"""
import pylibopenflow.cppize as cppize
import pylibopenflow.of.pythonize as ofcpyize
from pylibopenflow.config import *

class cppizer(cppize.cppizer):
    """Class that put C++ wrapper around C structures
    
    Date May 2010
    Created by ykk
    """
    def __init__(self, ofmsg):
        ofrules =  ofcpyize.rules(ofmsg)
        cppize.cppizer.__init__(self, ofmsg, ofrules)
        ##Reference to OpenFlow message class
        self.__ofmsg = ofmsg

