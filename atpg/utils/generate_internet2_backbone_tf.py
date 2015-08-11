'''
    <Generates all transfer functions for Internet2>
Created on Mar 11, 2012

@author: James Hongyi Zeng
'''
import sys, os
sys.path.append("../")

from config_parser.juniper_parser import *
from headerspace.tf import *
from time import time, clock

st = time()
output_path = "Internet2"
rtr_names = [("atla",0),
             ("chic",0),
             ("hous",0),
             ("kans",0),
             ("losa",0),
             ("newy32aoa",0),
             ("salt",0),
             ("seat",0),
             ("wash",0)
             ]

WORK_DIR = "../work/Internet2/"
if not os.path.exists(WORK_DIR):
    os.makedirs(WORK_DIR)

id = 1
cs_list = {}
for (rtr_name,vlan) in rtr_names:
    cs = juniperRouter(id)
    cs.set_replaced_vlan(vlan)
    tf = TF(cs.HS_FORMAT()["length"]*2)
    tf.set_prefix_id(rtr_name)
    cs.read_config_file("../data/Internet2/data/show_interfaces.xml", rtr_name)
    cs.read_route_file("../data/Internet2/data/%s-show_route_forwarding-table_table_default.xml"%rtr_name)
    cs.generate_port_ids([])
    cs.optimize_forwarding_table()
    cs.generate_transfer_function(tf)
    #print tf
    tf.save_object_to_file(WORK_DIR+"%s.tf"%rtr_name)
    id += 1
    cs_list[rtr_name] = cs
    
f = open(WORK_DIR+"port_map.txt",'w')
for rtr in cs_list.keys():
    cs = cs_list[rtr]
    f.write("$%s\n"%rtr)
    for p in cs.port_to_id.keys():
        f.write("%s:%s\n"%(p,cs.port_to_id[p]))
    
f.close()
    
topology = [("chic","xe-0/1/0","newy32aoa","xe-0/1/3"), #05667
            ("chic","xe-1/0/1","kans","xe-0/1/0"), #05568
            ("chic","xe-1/1/3","wash","xe-6/3/0"), #05250
            ("hous","xe-3/1/0","losa","ge-6/0/0"), #05559
            ("kans","ge-6/0/0","salt","ge-6/1/0"), #05138
            ("chic","xe-1/1/2","atla","xe-0/1/3"), #05638
            ("seat","xe-0/0/0","salt","xe-0/1/1"), #05565
            ("chic","xe-1/0/2","kans","xe-0/0/3"), #05781
            ("hous","xe-1/1/0","kans","xe-1/0/0"), #05560
            ("seat","xe-0/1/0","losa","xe-0/0/0"), #05564
            ("salt","xe-0/0/1","losa","xe-0/1/3"), #05571
            ("seat","xe-1/0/0","salt","xe-0/1/3"), #05573
            ("newy32aoa","et-3/0/0-0","wash","et-3/0/0-0"), #06126
            ("newy32aoa","et-3/0/0-1","wash","et-3/0/0-1"), #06126-2
            ("chic","xe-1/1/1","atla","xe-0/0/0"), #05419
            ("losa","xe-0/1/0","seat","xe-2/1/0"), #05572
            ("hous","xe-0/1/0","losa","ge-6/1/0"), #05581
            ("atla","xe-0/0/3","wash","xe-1/1/3"), #05251
            ("hous","xe-3/1/0","kans","ge-6/2/0"), #05561
            ("atla","ge-6/0/0","hous","xe-0/0/0"), #05423
            ("chic","xe-1/0/3","kans","xe-1/0/3"), #05976
            ("losa","xe-0/0/3","salt","xe-0/1/0"), #05563
            ("atla","ge-6/1/0","hous","xe-1/0/0"), #05562
            ("atla","xe-1/0/3","wash","xe-0/0/0"), #06366
            ("chic","xe-2/1/3","wash","xe-0/1/3"), #05637
            ("atla","xe-1/0/1","wash","xe-0/0/3"), #05133
            ("kans","xe-0/1/1","salt","ge-6/0/0"), #05566
            ("chic","xe-1/1/0","newy32aoa","xe-0/0/0"), #05239
            ]

tf = TF(cs.HS_FORMAT()["length"]*2)
# James: link ID should have prefix too.
tf.set_prefix_id("link")
for (from_router,from_port,to_router,to_port) in topology:
    from_cs = cs_list[from_router]
    to_cs = cs_list[to_router]
    rule = TF.create_standard_rule([from_cs.get_port_id(from_port) + from_cs.PORT_TYPE_MULTIPLIER * from_cs.OUTPUT_PORT_TYPE_CONST], None,[to_cs.get_port_id(to_port)], None, None, "", [])
    tf.add_link_rule(rule)
    rule = TF.create_standard_rule([to_cs.get_port_id(to_port) + to_cs.PORT_TYPE_MULTIPLIER * to_cs.OUTPUT_PORT_TYPE_CONST], None,[from_cs.get_port_id(from_port)], None, None, "", [])
    tf.add_link_rule(rule)
tf.save_object_to_file(WORK_DIR+"backbone_topology.tf")
en = time()
print en - st
    
