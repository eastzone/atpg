'''
    <Run reachability using NuSMV on replicated Stanford Network>

@author: peymankazemian
'''
from utils.load_stanford_backbone import *
from headerspace.nu_smv_generator import *
from time import time

net_dir = "16xtf_stanford_backbone"

(port_map,port_reverse_map) = load_port_to_id_map("16xtf_stanford_backbone")
src_port_id = port_map["bbra_rtr1"]["te6/3"]
dst_port_id = port_map["roza_rtr10"]["te3/3"]+20000
via_ports = [port_map["bbrb_rtr1"]["te6/3"],port_map["bbrb_rtr1"]["te6/3"]+20000]
nusmv = load_augmented_tf_to_nusmv(16,net_dir)
st = time()
#print nusmv.run_nusmv_one_path_via_ports_reachability(src_port_id, dst_port_id,via_ports)
print nusmv.run_nusmv_reachability(src_port_id, dst_port_id)
en = time()
print en-st