'''
    <Generate OpenFlow rules to emulate behavior of Stanford Network>
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
    
Created on Mar 31, 2012

@author: Peyman Kazemian
'''
from config_parser.transfer_function_to_openflow import OpenFlow_Rule_Generator
from config_parser.cisco_router_parser import ciscoRouter
from headerspace.tf import TF

format = {}
format["ip_dst_pos"] = 0
format["ip_dst_len"] = 4
format["length"] = 4

rtr_names = ["bbra_rtr",
             "bbrb_rtr",
             "boza_rtr",
             "bozb_rtr",
             "coza_rtr",
             "cozb_rtr",
             "goza_rtr",
             "gozb_rtr",
             "poza_rtr",
             "pozb_rtr",
             "roza_rtr",
             "rozb_rtr",
             "soza_rtr",
             "sozb_rtr",
             "yoza_rtr",
             "yozb_rtr",
             ]

for rtr_name in rtr_names:
    f = TF(1)
    f.load_object_from_file("../work/tf_simple_stanford_backbone/%s.tf"%rtr_name)
    #OFG = OpenFlow_Rule_Generator(f,ciscoRouter(1).HS_FORMAT())
    OFG = OpenFlow_Rule_Generator(f,format)
    OFG.generate_of_rules("%s.of"%rtr_name)
