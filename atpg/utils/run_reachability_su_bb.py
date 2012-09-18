'''
    <Run reachability test on Stanford network>
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
    
Created on Aug 14, 2011

@author: Peyman Kazemian
'''
from utils.load_stanford_backbone import *
from config_parser.cisco_router_parser import ciscoRouter
from headerspace.hs import *
from headerspace.applications import *
from time import time, clock

ntf = load_stanford_backbone_ntf()
ttf = load_stanford_backbone_ttf()
(port_map,port_reverse_map) = load_stanford_backbone_port_to_id_map()
cs = ciscoRouter(1)
output_port_addition = cs.PORT_TYPE_MULTIPLIER * cs.OUTPUT_PORT_TYPE_CONST

#add_internet(ntf,ttf,port_map,cs,[("171.64.0.0",14),("128.12.0.0",16)])

all_x = byte_array_get_all_x(ntf.length)
#cs.set_field(all_x, "ip_dst", dotted_ip_to_int("172.0.0.0"), 21)
#cs.set_field(all_x, "vlan", 92, 0)
test_pkt = headerspace(ntf.length)
test_pkt.add_hs(all_x)

src_port_id = port_map["yoza_rtr"]["te1/4"]
dst_port_ids = [port_map["boza_rtr"]["te3/3"]+output_port_addition]

st = time()

paths = find_reachability(ntf,ttf,src_port_id,dst_port_ids,test_pkt)
en = time()
print_loops(paths, port_reverse_map)
print len(paths)

print en-st
