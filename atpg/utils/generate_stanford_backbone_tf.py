'''
    <Generates all transfer functions for Stanford backbone network>
Created on Aug 10, 2011

@author: Peyman Kazemian
'''
import sys, os
sys.path.append("../")

from config_parser.cisco_router_parser import *
from headerspace.tf import *
from time import time, clock

st = time()
output_path = "tf_stanford_backbone"
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
id = 1
cs_list = {}

WORK_DIR = "../work/tf_stanford_backbone/"
if not os.path.exists(WORK_DIR):
    os.makedirs(WORK_DIR)

for (rtr_name,vlan) in rtr_names:
    cs = ciscoRouter(id)
    cs.set_replaced_vlan(vlan)
    tf = TF(cs.HS_FORMAT()["length"]*2)
    tf.set_prefix_id(rtr_name)
    cs.read_arp_table_file("../data/Stanford_backbone/%s_arp_table.txt"%rtr_name)
    cs.read_mac_table_file("../data/Stanford_backbone/%s_mac_table.txt"%rtr_name)
    cs.read_config_file("../data/Stanford_backbone/%s_config.txt"%rtr_name)
    cs.read_spanning_tree_file("../data/Stanford_backbone/%s_spanning_tree.txt"%rtr_name)
    cs.read_route_file("../data/Stanford_backbone/%s_route.txt"%rtr_name)
    cs.generate_port_ids([])
    #if rtr_name == "coza_rtr" or rtr_name == "cozb_rtr" or rtr_name == "soza_rtr" or rtr_name == "sozb_rtr" or rtr_name == "yoza_rtr" or rtr_name == "yozb_rtr":
    cs.optimize_forwarding_table()
    cs.generate_transfer_function(tf)
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

tf = TF(cs.HS_FORMAT()["length"]*2)
for (from_router,from_port,to_router,to_port) in topology:
    from_cs = cs_list[from_router]
    to_cs = cs_list[to_router]
    rule = TF.create_standard_rule([from_cs.get_port_id(from_port) + from_cs.PORT_TYPE_MULTIPLIER * from_cs.OUTPUT_PORT_TYPE_CONST], None,[to_cs.get_port_id(to_port)], None, None, "", [])
    tf.add_link_rule(rule)
    rule = TF.create_standard_rule([to_cs.get_port_id(to_port) + to_cs.PORT_TYPE_MULTIPLIER * to_cs.OUTPUT_PORT_TYPE_CONST], None,[from_cs.get_port_id(from_port)], None, None, "", [])
    tf.add_link_rule(rule)
tf.save_object_to_file(WORK_DIR+"/backbone_topology.tf")
en = time()
print en - st
    
