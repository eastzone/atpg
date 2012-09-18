#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name = "pylibopenflow",
    version = "0.1",
    packages = find_packages(),
    
    scripts = ['bin/cstruct2py-get-struct.py',
               'bin/cstruct2py-query-cheader.py',
               'bin/pyopenflow-get-struct.py',
               'bin/pyopenflow-ping-controller.py',
               'bin/pyopenflow-pythonize.py',
               'bin/cstruct2py-pythonize.py',
               'bin/pyopenflow-dump.py',
               'bin/pyopenflow-load-controller.py',
               'bin/pyopenflow-++.py',
               'bin/pyopenflow-time-flowmod.py'],
    provides = ["pylibopenflow"],

    author = "KK Yap",
    author_email = "yapkokkiong@gmail.com",
    description = "This is an OpenFlow parser, that generates C++ and Python OpenFlow files.",
    license = "OpenFlow License",
    keywords = "OpenFlow parser",
    url = "http://www.openflowswitch.org/wk/index.php/Pylibopenflow",
)
