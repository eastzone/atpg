'''
    <Run reachability test on replicated Stanford Network>
Created on Aug 14, 2011

@author: Peyman Kazemian
'''
from utils.load_stanford_backbone import *
from config_parser.cisco_router_parser import ciscoRouter
from headerspace.hs import *
from headerspace.applications import *
from time import time, clock


(ntf,ttf,port_map,port_reverse_map) = load_replicated_stanford_network(16,"16xtf_stanford_backbone")
cs = ciscoRouter(1)
output_port_addition = cs.PORT_TYPE_MULTIPLIER * cs.OUTPUT_PORT_TYPE_CONST

#add_internet(ntf,ttf,port_map,cs,[("171.64.0.0",14),("128.12.0.0",16)])

all_x = byte_array_get_all_x(ntf.length)
#cs.set_field(all_x, "ip_dst", dotted_ip_to_int("172.0.0.0"), 21)
#cs.set_field(all_x, "vlan", 92, 0)
test_pkt = headerspace(ntf.length)
test_pkt.add_hs(all_x)

src_port_id = port_map["bbra_rtr1"]["te6/3"]
dst_port_ids = [port_map["roza_rtr10"]["te3/3"]+output_port_addition]

st = time()
paths = find_reachability(ntf,ttf,src_port_id,dst_port_ids,test_pkt)
en = time()
print_loops(paths, port_reverse_map)
print len(paths)


print en-st
