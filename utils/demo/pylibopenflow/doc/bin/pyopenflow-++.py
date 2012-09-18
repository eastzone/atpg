#!/usr/bin/env python
"""This script generate C++ wrapper for
for each data structure in openflow.h.

(C) Copyright Stanford University
Author ykk
Date April 2010
"""
import sys
import getopt
import pylibopenflow.output as output
import pylibopenflow.openflow as openflow
import pylibopenflow.of.ppize as ofppize

def usage():
    """Display usage
    """
    print "Usage "+sys.argv[0]+" <options> output_file\n"+\
          "Options:\n"+\
          "-h/--help\n\tPrint this usage guide\n"+\
          "-i/--input\n\tSpecify input header file\n"+\
          "-t/--headertemplate\n\tSpecify template for header file\n"+\
          "-c/--codetemplate\n\tSpecify template for code file\n"+\
          ""
          
#Parse options and arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "hi:c:t:",
                               ["help","input=",
                                "codetemplate=","headertemplate="])
except getopt.GetoptError:
    usage()
    sys.exit(2)

#Check there is only output file
if not (len(args) == 1):
    usage()
    sys.exit(2)

#Parse options
##Input
headerfile=None
##H Template file
htemplatefile="include/openflow-pack.template.hh"
##C Template file
ctemplatefile="include/openflow-pack.template.cc"
for opt,arg in opts:
    if (opt in ("-h","--help")):
        usage()
        sys.exit(0)
    elif (opt in ("-i","--input")):
        headerfile=arg
    elif (opt in ("-x","--codetemplate")):
        ctemplatefile=arg
    elif (opt in ("-t","--headertemplate")):
        htemplatefile=arg
    else:
        print "Unhandled option:"+opt
        sys.exit(2)

#Generate Python code
ofmsg = openflow.messages(headerfile)
cppizer = ofppize.cppizer(ofmsg)

hfileRef = open(args[0]+".hh", "w")
cfileRef = open(args[0]+".cc", "w")
for x in cppizer.hcode(args[0], htemplatefile):
    hfileRef.write(x+"\n")
for x in cppizer.ccode(ctemplatefile, None,
                       ["#include \""+args[0]+".hh\""]):
    cfileRef.write(x+"\n")
hfileRef.write("\n")
cfileRef.write("\n")
cfileRef.close()
hfileRef.close()
