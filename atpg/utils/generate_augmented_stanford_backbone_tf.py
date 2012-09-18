'''
    <Replicate Stanford backbone N times and connect them using a address translator box>
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
    
Created on Aug 10, 2011

@author: Peyman Kazemian
'''
from config_parser.cisco_router_parser import *
from headerspace.tf import *
from time import time, clock

replication_factor = 16
output_dir = "16xtf_stanford_backbone"
root_tf_id = 16*replication_factor + 1
start_ip_subnet = dotted_ip_to_int("171.64.0.0")
start_ip_mask = 14

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

id = 1
f = open("%s/port_map.txt"%output_dir,'w')
dummy_cs = ciscoRouter(1)
ttf = TF(dummy_cs.HS_FORMAT()["length"]*2)
ttf.set_prefix_id("topology")
root_tf = TF(dummy_cs.HS_FORMAT()["length"]*2)
root_tf.set_prefix_id("root_rtr")
root_tf_ports = []

for replicate in range(replication_factor):
    cs_list = {}
    for (rtr_name,vlan) in rtr_names:
        cs = ciscoRouter(id)
        cs.set_replaced_vlan(vlan)
        tf = TF(cs.HS_FORMAT()["length"]*2)
        tf.set_prefix_id(rtr_name)
        cs.read_arp_table_file("Stanford_backbone/%s_arp_table.txt"%rtr_name)
        cs.read_mac_table_file("Stanford_backbone/%s_mac_table.txt"%rtr_name)
        cs.read_config_file("Stanford_backbone/%s_config.txt"%rtr_name)
        cs.read_spanning_tree_file("Stanford_backbone/%s_spanning_tree.txt"%rtr_name)
        cs.read_route_file("Stanford_backbone/%s_route.txt"%rtr_name)
        cs.generate_port_ids([])
        #if rtr_name == "coza_rtr" or rtr_name == "cozb_rtr" or rtr_name == "soza_rtr" or rtr_name == "sozb_rtr" or rtr_name == "yoza_rtr" or rtr_name == "yozb_rtr":
        cs.optimize_forwarding_table()
        cs.generate_transfer_function(tf)
        #print tf
        tf.save_object_to_file("%s/%s%d.tf"%(output_dir,rtr_name,replicate+1))
        id += 1
        cs_list["%s%d"%(rtr_name,replicate+1)] = cs

    bbra_cs = cs_list["bbra_rtr%d"%(replicate+1)]
    ip_addr = start_ip_subnet + replicate * 2**18
    out_port = bbra_cs.get_port_id("te1/1")
    root_port = root_tf_id*dummy_cs.SWITCH_ID_MULTIPLIER + len(root_tf_ports) + 1
    root_tf_ports.append(root_port)
    
    #create the rule for root TF
    match = byte_array_get_all_x(dummy_cs.HS_FORMAT()["length"]*2)
    dummy_cs.set_field(match, "ip_dst", ip_addr, 32-start_ip_mask)
    mask = byte_array_get_all_one(dummy_cs.hs_format["length"]*2)
    dummy_cs.set_field(mask, "ip_dst", 0, 32-start_ip_mask)
    rewrite = byte_array_get_all_zero(dummy_cs.hs_format["length"]*2)
    dummy_cs.set_field(rewrite, "ip_dst", start_ip_subnet, 32-start_ip_mask)
    root_rule = TF.create_standard_rule([root_tf_id*dummy_cs.SWITCH_ID_MULTIPLIER], match, [out_port+ dummy_cs.PORT_TYPE_MULTIPLIER * dummy_cs.INTERMEDIATE_PORT_TYPE_CONST], mask, rewrite, "", [])
    root_tf.add_rewrite_rule(root_rule)
    
    #create the link rules connecting port te1/1 to root TF
    rule = TF.create_standard_rule([out_port + bbra_cs.PORT_TYPE_MULTIPLIER * bbra_cs.OUTPUT_PORT_TYPE_CONST], None,[root_port], None, None, "", [])
    ttf.add_link_rule(rule)
    rule = TF.create_standard_rule([root_port + bbra_cs.PORT_TYPE_MULTIPLIER * bbra_cs.OUTPUT_PORT_TYPE_CONST], None,[out_port], None, None, "", [])
    ttf.add_link_rule(rule)
    
    for rtr in cs_list.keys():
        cs = cs_list[rtr]
        f.write("$%s\n"%rtr)
        for p in cs.port_to_id.keys():
            f.write("%s:%s\n"%(p,cs.port_to_id[p]))

    for (from_router,from_port,to_router,to_port) in topology:
        from_cs = cs_list["%s%d"%(from_router,replicate+1)]
        to_cs = cs_list["%s%d"%(to_router,replicate+1)]
        rule = TF.create_standard_rule([from_cs.get_port_id(from_port) + from_cs.PORT_TYPE_MULTIPLIER * from_cs.OUTPUT_PORT_TYPE_CONST], None,[to_cs.get_port_id(to_port)], None, None, "", [])
        ttf.add_link_rule(rule)
        rule = TF.create_standard_rule([to_cs.get_port_id(to_port) + to_cs.PORT_TYPE_MULTIPLIER * to_cs.OUTPUT_PORT_TYPE_CONST], None,[from_cs.get_port_id(from_port)], None, None, "", [])
        ttf.add_link_rule(rule)

for port in root_tf_ports:
    r = TF.create_standard_rule([port], byte_array_get_all_x(dummy_cs.HS_FORMAT()["length"]*2),
                                 [root_tf_id*dummy_cs.SWITCH_ID_MULTIPLIER], 
                                 None, None, "", [])
    root_tf.add_fwd_rule(r)
    r = TF.create_standard_rule([port + dummy_cs.PORT_TYPE_MULTIPLIER * dummy_cs.INTERMEDIATE_PORT_TYPE_CONST], 
                                byte_array_get_all_x(dummy_cs.HS_FORMAT()["length"]*2),
                                [port + dummy_cs.PORT_TYPE_MULTIPLIER * dummy_cs.OUTPUT_PORT_TYPE_CONST], 
                                None, None, "", [])
    root_tf.add_fwd_rule(r)

ttf.save_object_to_file("%s/backbone_topology.tf"%output_dir)
root_tf.save_object_to_file("%s/root.tf"%output_dir)
en = time()
print en - st
f.close()
    