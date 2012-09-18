'''
    <Run Reachability test on IP forwarding part of Stanford Backbone Network>
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

ntf = load_stanford_ip_fwd_ntf()
ttf = load_stanford_ip_fwd_ttf()
(port_map,port_reverse_map) = load_port_to_id_map("tf_simple_stanford_backbone")


all_x = byte_array_get_all_x(ntf.length)
test_pkt = headerspace(ntf.length)
test_pkt.add_hs(all_x)

src_port_id = port_map["coza_rtr"]["te3/3"]
dst_port_ids = [port_map["yoza_rtr"]["te1/4"]]


loop_port_ids = [
                 port_map["bbra_rtr"]["te7/1"],
                 port_map["bbrb_rtr"]["te7/1"],
                 port_map["bbra_rtr"]["te6/3"],
                 port_map["bbrb_rtr"]["te7/4"],
                 port_map["bbra_rtr"]["te7/2"],
                 port_map["bbrb_rtr"]["te1/1"],
                 port_map["bbra_rtr"]["te6/1"],
                 port_map["bbrb_rtr"]["te6/3"],
                 port_map["bbra_rtr"]["te1/4"],
                 port_map["bbrb_rtr"]["te1/3"],
                 port_map["bbra_rtr"]["te1/3"],
                 port_map["bbrb_rtr"]["te7/2"],
                 port_map["bbra_rtr"]["te7/3"],
                 port_map["bbrb_rtr"]["te6/1"],
                 port_map["boza_rtr"]["te2/3"],
                 port_map["coza_rtr"]["te2/3"],
                 port_map["yozb_rtr"]["te1/3"],
                 port_map["yozb_rtr"]["te1/2"],
                 port_map["yoza_rtr"]["te1/1"],
                 port_map["yoza_rtr"]["te1/2"],
                 port_map["bozb_rtr"]["te2/3"],
                 port_map["cozb_rtr"]["te2/3"],
                 port_map["gozb_rtr"]["te2/3"],
                 port_map["pozb_rtr"]["te2/3"],
                 port_map["goza_rtr"]["te2/3"],
                 port_map["poza_rtr"]["te2/3"],
                 port_map["rozb_rtr"]["te2/3"],
                 port_map["sozb_rtr"]["te2/3"],
                 port_map["roza_rtr"]["te2/3"],
                 port_map["soza_rtr"]["te2/3"],
                 ]

st = time()
paths = find_reachability(ntf,ttf,src_port_id,dst_port_ids,test_pkt)
en = time()
print_loops(paths, port_reverse_map)
print len(paths)

print en-st
