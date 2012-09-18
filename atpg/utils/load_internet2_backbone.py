'''
    <Loads Stanford backbone network into appropriate objects (e.g. emulated_tf)>
    Copyright (C) 2012  Stanford University

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    
Created on March 12, 2012

@author: James Hongyi Zeng
'''
from headerspace.tf import *
from headerspace.hs import *
from utils.emulated_tf import *
from config_parser.helper import dotted_ip_to_int
from config_parser.juniper_parser import juniperRouter
from multiprocessing import Pool

rtr_names = ["atla",
             "chic",
             "hous",
             "kans",
             "losa",
             "newy32aoa",
             "salt",
             "seat",
             "wash"
             ]

def load_internet2_backbone_ntf():
    emul_tf = emulated_tf(2, False)
#    i = 0
    
#    for rtr_name in rtr_names:
#        f = TF(1)
#        f.load_object_from_file("work/Internet2/%s.tf"%rtr_name)
#        f.activate_hash_table([15,14])
#        emul_tf.append_tf(f)
#        i = i+1
        
    pool = Pool()
    result = pool.map_async(load_ntf, rtr_names)

    # Close
    pool.close()
    pool.join()
    
    tfs = result.get()
    
    for tf in tfs:
        emul_tf.append_tf(tf)
    
    return emul_tf

def load_ntf(rtr_name):
    f = TF(1)
    f.load_object_from_file("work/Internet2/%s.tf"%rtr_name)
    f.activate_exact_match_hash(range(5,8))
    return f

def load_internet2_backbone_ttf():
    f = TF(1)
    f.load_object_from_file("work/Internet2/backbone_topology.tf")
    return f

def load_internet2_backbone_port_to_id_map():
    f = open("work/Internet2/port_map.txt",'r')
    id_to_name = {}
    map = {}
    rtr = ""
    cs = juniperRouter(1)
    for line in f:
        if line.startswith("$"):
            rtr = line[1:].strip()
            map[rtr] = {}
        elif line != "":
            tokens = line.strip().split(":")
            map[rtr][tokens[0]] = int(tokens[-1])
            id_to_name[tokens[-1]] = "%s-%s"%(rtr,":".join(tokens[0:-1]))
            out_port = int(tokens[-1]) + cs.PORT_TYPE_MULTIPLIER * cs.OUTPUT_PORT_TYPE_CONST
            id_to_name["%s"%out_port] = "%s-%s"%(rtr,":".join(tokens[0:-1]))
    return (map,id_to_name)
