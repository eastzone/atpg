'''
    <Generates a set of transfer functions, only modeling IP forwarding behavior of Stanford Network>
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
    
Created on May 29, 2012

@author: Peyman Kazemian
'''
import sys, os
sys.path.append("../")

from config_parser.helper import *
from headerspace.tf import *
from headerspace.hs import *
from config_parser.cisco_router_parser import *
import re

format = {}
format["ip_dst_pos"] = 0
format["ip_dst_len"] = 4
format["length"] = 4

rtr_names = [("bbra_rtr",0),
             ("bbrb_rtr",0),
             ("boza_rtr",0),
             ("bozb_rtr",0),
             ("coza_rtr",580),
             ("cozb_rtr",580),
             ("goza_rtr",0),
             ("gozb_rtr",0),
             ("poza_rtr",0),
             ("pozb_rtr",0),
             ("roza_rtr",0),
             ("rozb_rtr",0),
             ("soza_rtr",580),
             ("sozb_rtr",580),
             ("yoza_rtr",0),
             ("yozb_rtr",0),
             ]

def generate_fwd_table_tf(cisco_parser,tf):
    print " * Generating IP forwarding transfer function... * "  
    # generate the forwarding part of transfer fucntion, from the fwd_prt, to pre-output ports
    for subnet in range(32,-1,-1):
        for fwd_rule in cisco_parser.fwd_table:
            if fwd_rule[1] == subnet:
                #in -ports and match bytearray
                match = byte_array_get_all_x(cisco_parser.hs_format["length"]*2)
                cisco_parser.set_field(match, "ip_dst", int(fwd_rule[0]), 32-subnet)
                in_ports = []
                for p in cisco_parser.port_to_id.keys():                    
                    in_ports.append(cisco_parser.port_to_id[p])
                # find out the file-line it represents:
                lines = []
                file_name = ""
                if len(fwd_rule) == 4:
                    for c_rule in fwd_rule[3]:
                        file_name = c_rule[3]
                        lines.extend(c_rule[4])
                else:
                    file_name = fwd_rule[3]
                    lines.extend(fwd_rule[4])
                # set up out_ports
                out_ports = []
                vlan = 0
                m = re.split('\.',fwd_rule[2])
                # drop rules:
                if fwd_rule[2] == "self":
                    self_rule = TF.create_standard_rule(in_ports,match,[],None,None,file_name,lines)
                    tf.add_fwd_rule(self_rule)
                # non drop rules
                else:
                    # sub-ports: port.vlan
                    if len(m) > 1:
                        if m[0] in cisco_parser.port_to_id.keys():
                            out_ports.append(cisco_parser.port_to_id[m[0]])
                            vlan = int(m[1])
                        else:
                            print "ERROR: unrecognized port %s"%m[0]
                            return -1
                    # vlan outputs
                    elif fwd_rule[2].startswith('vlan'):
                        if fwd_rule[2] in cisco_parser.vlan_ports.keys():
                            port_list = cisco_parser.vlan_ports[fwd_rule[2]]
                            for p in port_list:
                                if p in cisco_parser.port_to_id.keys():
                                    out_ports.append(cisco_parser.port_to_id[p])
                            vlan = int(fwd_rule[2][4:])
                        else:
                            print "ERROR: unrecognized vlan %s"%fwd_rule[2]
                            return -1
                    # physical ports - no vlan taging
                    else:
                        if fwd_rule[2] in cisco_parser.port_to_id.keys():
                            out_ports.append(cisco_parser.port_to_id[fwd_rule[2]])
                            vlan = 0
                        else:
                            print "ERROR: unrecognized port %s"%fwd_rule[2]
                            return -1

                    tf_rule = TF.create_standard_rule(in_ports, match, out_ports, None, None,file_name,lines)
                    tf.add_fwd_rule(tf_rule) 
                        
    print "=== Successfully Generated Transfer function ==="
    return 0     

id = 1
cs_list = {}

WORK_DIR = "../work/tf_simple_stanford_backbone/"
if not os.path.exists(WORK_DIR):
    os.makedirs(WORK_DIR)

for (rtr_name,vlan) in rtr_names:
    cs = ciscoRouter(id)
    cs.set_replaced_vlan(vlan)
    cs.set_hs_format(format)
    tf = TF(format["length"]*2)
    tf.set_prefix_id(rtr_name)
    cs.read_arp_table_file("../data/Stanford_backbone/%s_arp_table.txt"%rtr_name)
    cs.read_mac_table_file("../data/Stanford_backbone/%s_mac_table.txt"%rtr_name)
    cs.read_config_file("../data/Stanford_backbone/%s_config.txt"%rtr_name)
    cs.read_spanning_tree_file("../data/Stanford_backbone/%s_spanning_tree.txt"%rtr_name)
    cs.read_route_file("../data/Stanford_backbone/%s_route.txt"%rtr_name)
    #cs.generate_port_ids([])
    cs.generate_port_ids_only_for_output_ports()
    #if rtr_name == "coza_rtr" or rtr_name == "cozb_rtr" or rtr_name == "soza_rtr" or rtr_name == "sozb_rtr" or rtr_name == "yoza_rtr" or rtr_name == "yozb_rtr":
    cs.optimize_forwarding_table()
    generate_fwd_table_tf(cs,tf)
    #print tf
    tf.save_object_to_file(WORK_DIR+"/%s.tf"%rtr_name)
    id += 1
    cs_list[rtr_name] = cs
    
f = open(WORK_DIR+"/port_map.txt",'w')
for rtr in cs_list.keys():
    cs = cs_list[rtr]
    f.write("$%s\n"%rtr)
    for p in cs.port_to_id.keys():
        f.write("%s:%s\n"%(p,cs.port_to_id[p]))
    
f.close()
    
topology = [("bbra_rtr","te7/3","goza_rtr","te2/1"),
            ("bbra_rtr","te7/3","pozb_rtr","te3/1"),
            ("bbra_rtr","te1/3","bozb_rtr","te3/1"),
            ("bbra_rtr","te1/3","yozb_rtr","te2/1"),
            ("bbra_rtr","te1/3","roza_rtr","te2/1"),
            ("bbra_rtr","te1/4","boza_rtr","te2/1"),
            ("bbra_rtr","te1/4","rozb_rtr","te3/1"),
            ("bbra_rtr","te6/1","gozb_rtr","te3/1"),
            ("bbra_rtr","te6/1","cozb_rtr","te3/1"),
            ("bbra_rtr","te6/1","poza_rtr","te2/1"),
            ("bbra_rtr","te6/1","soza_rtr","te2/1"),
            ("bbra_rtr","te7/2","coza_rtr","te2/1"),
            ("bbra_rtr","te7/2","sozb_rtr","te3/1"),
            ("bbra_rtr","te6/3","yoza_rtr","te1/3"),
            ("bbra_rtr","te7/1","bbrb_rtr","te7/1"),
            ("bbrb_rtr","te7/4","yoza_rtr","te7/1"),
            ("bbrb_rtr","te1/1","goza_rtr","te3/1"),
            ("bbrb_rtr","te1/1","pozb_rtr","te2/1"),
            ("bbrb_rtr","te6/3","bozb_rtr","te2/1"),
            ("bbrb_rtr","te6/3","roza_rtr","te3/1"),
            ("bbrb_rtr","te6/3","yozb_rtr","te1/1"),
            ("bbrb_rtr","te1/3","boza_rtr","te3/1"),
            ("bbrb_rtr","te1/3","rozb_rtr","te2/1"),
            ("bbrb_rtr","te7/2","gozb_rtr","te2/1"),
            ("bbrb_rtr","te7/2","cozb_rtr","te2/1"),
            ("bbrb_rtr","te7/2","poza_rtr","te3/1"),
            ("bbrb_rtr","te7/2","soza_rtr","te3/1"),
            ("bbrb_rtr","te6/1","coza_rtr","te3/1"),
            ("bbrb_rtr","te6/1","sozb_rtr","te2/1"),
            ("boza_rtr","te2/3","bozb_rtr","te2/3"),
            ("coza_rtr","te2/3","cozb_rtr","te2/3"),
            ("goza_rtr","te2/3","gozb_rtr","te2/3"),
            ("poza_rtr","te2/3","pozb_rtr","te2/3"),
            ("roza_rtr","te2/3","rozb_rtr","te2/3"),
            ("soza_rtr","te2/3","sozb_rtr","te2/3"),
            ("yoza_rtr","te1/1","yozb_rtr","te1/3"),
            ("yoza_rtr","te1/2","yozb_rtr","te1/2"),
            ]

tf = TF(format["length"]*2)
for (from_router,from_port,to_router,to_port) in topology:
    from_cs = cs_list[from_router]
    to_cs = cs_list[to_router]
    rule = TF.create_standard_rule([from_cs.get_port_id(from_port)], None,[to_cs.get_port_id(to_port)], None, None, "", [])
    tf.add_link_rule(rule)
    rule = TF.create_standard_rule([to_cs.get_port_id(to_port)], None,[from_cs.get_port_id(from_port)], None, None, "", [])
    tf.add_link_rule(rule)
tf.save_object_to_file(WORK_DIR+"/backbone_topology.tf")

