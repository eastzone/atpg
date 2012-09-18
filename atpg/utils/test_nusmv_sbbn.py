'''
    <simple test>
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
    
Created on Jan 27, 2012

@author: Peyman Kazemian
'''
from headerspace.nu_smv_generator import *
from utils.load_stanford_backbone import *
from time import time

rtr_name = "yoza_rtr"
nusmv = NuSMV()
f = TF(1)
f.load_object_from_file("tf_stanford_backbone/%s.tf"%rtr_name)
(map,port_reverse_map) = load_stanford_backbone_port_to_id_map()
end_ports = []
for rtr_port in map[rtr_name]:
    end_ports.append(map[rtr_name][rtr_port]+20000)
nusmv.generate_nusmv_trans(f, end_ports)
nusmv.generate_nusmv_input()
src_port_id = map["yoza_rtr"]["te7/4"]
dst_port_id = map["yoza_rtr"]["te1/3"]+20000
st = time()
print nusmv.run_nusmv_reachability(src_port_id, dst_port_id)
en = time()