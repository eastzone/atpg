'''
    <Loads Stanford backbone network into appropriate objects (e.g. emulated_tf)>
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
    
Created on Aug 13, 2011

@author: Peyman Kazemian
'''
from headerspace.tf import *
from headerspace.hs import *
from headerspace.nu_smv_generator import *
from utils.emulated_tf import *
from config_parser.helper import dotted_ip_to_int
from config_parser.cisco_router_parser import ciscoRouter
from config_parser.helper import compose_standard_rules

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

def load_stanford_backbone_ntf():
    '''
    Loads Stanford backbone network transfer functions into an emulated_tf object with 3 layers.
    '''
    emul_tf = emulated_tf(3)
    emul_tf.set_fwd_engine_stage(1)
    for rtr_name in rtr_names:
        f = TF(1)
        f.load_object_from_file("work/tf_stanford_backbone/%s.tf"%rtr_name)
        f.activate_hash_table([15,14])
        emul_tf.append_tf(f)
    emul_tf.length = f.length
    return emul_tf

def load_stanford_backbone_ttf():
    '''
    Loads Stanford backbone topology transfer functions into a transfer function object
    '''
    f = TF(1)
    f.load_object_from_file("work/tf_stanford_backbone/backbone_topology.tf")
    return f
    
def load_stanford_ip_fwd_ntf():
    '''
    Loads IP forwarding part of Stanford backbone network transfer functions into an emulated_tf object with 1 layer.
    '''
    emul_tf = emulated_tf(1)
    emul_tf.set_fwd_engine_stage(0)
    emul_tf.output_port_const = 0
    for rtr_name in rtr_names:
        f = TF(1)
        f.load_object_from_file("work/tf_simple_stanford_backbone/%s.tf"%rtr_name)
        #f.activate_hash_table([3,2])
        emul_tf.append_tf(f)
    emul_tf.length = f.length
    return emul_tf

def load_stanford_ip_fwd_ttf():
    '''
    Loads Stanford backbone topology transfer functions into a transfer function object.
    this should be used together with load_stanford_ip_fwd_ntf.
    '''
    f = TF(1)
    f.load_object_from_file("work/tf_simple_stanford_backbone/backbone_topology.tf")
    return f

def load_port_to_id_map(path):
    '''
    load the map from port ID to name of box-port name.
    '''
    f = open("%s/port_map.txt"%path,'r')
    id_to_name = {}
    map = {}
    rtr = ""
    cs = ciscoRouter(1)
    for line in f:
        if line.startswith("$"):
            rtr = line[1:].strip()
            map[rtr] = {}
        elif line != "":
            tokens = line.strip().split(":")
            map[rtr][tokens[0]] = int(tokens[1])
            id_to_name[tokens[1]] = "%s-%s"%(rtr,tokens[0])
            out_port = int(tokens[1]) + cs.PORT_TYPE_MULTIPLIER * cs.OUTPUT_PORT_TYPE_CONST
            id_to_name["%s"%out_port] = "%s-%s"%(rtr,tokens[0])
    return (map,id_to_name)
    
def load_stanford_backbone_port_to_id_map():
    return load_port_to_id_map("work/tf_stanford_backbone")
    
def load_replicated_stanford_network(replicate,path):
    '''
    Load the transfer functions created by generate_augmented_stanford_backbone_tf.py
    '''
    ttf = TF(1)
    ttf.load_object_from_file("%s/backbone_topology.tf"%path)
    (name_to_id,id_to_name) = load_port_to_id_map(path)
    emul_tf = emulated_tf(3)
    for i in range(replicate):
        for rtr_name in rtr_names:
            f = TF(1)
            f.load_object_from_file("%s/%s%d.tf"%(path,rtr_name,i+1))
            #f.activate_hash_table([15,14])
            emul_tf.append_tf(f)
    f = TF(1)
    f.load_object_from_file("%s/root.tf"%(path))
    f.activate_hash_table([15,14])
    emul_tf.append_tf(f)
    return (emul_tf,ttf,name_to_id,id_to_name)
    
            
def add_internet(ntf,ttf,port_map,cs,campus_ip_list):
    '''
    Campus IP list is a list of (ip address,subnet mask) for each IP subnet on campus
    '''
    s = TF(cs.HS_FORMAT()["length"]*2)
    s.set_prefix_id("internet")
    for entry in campus_ip_list:
        match = byte_array_get_all_x(cs.HS_FORMAT()["length"]*2)
        cs.set_field(match,'ip_dst',dotted_ip_to_int(entry[0]),32-entry[1])
        rule = TF.create_standard_rule([0], match, [0], None, None, "", [])
        s.add_fwd_rule(rule)
    ntf.append_tf(s)
    
    bbra_internet_port1 = port_map["bbra_rtr"]["te1/1"]
    bbra_internet_port2 = port_map["bbra_rtr"]["te7/4"]
    bbrb_internet_port1 = port_map["bbrb_rtr"]["te1/4"]
    bbrb_internet_port2 = port_map["bbrb_rtr"]["te7/3"]
    rule = TF.create_standard_rule([bbra_internet_port1], None,[0], None, None, "", [])
    ttf.add_link_rule(rule)
    rule = TF.create_standard_rule([bbra_internet_port2], None,[0], None, None, "", [])
    ttf.add_link_rule(rule)
    rule = TF.create_standard_rule([bbrb_internet_port1], None,[0], None, None, "", [])
    ttf.add_link_rule(rule)
    rule = TF.create_standard_rule([bbrb_internet_port2], None,[0], None, None, "", [])
    ttf.add_link_rule(rule)
    rule = TF.create_standard_rule([0], None,[bbra_internet_port1], None, None, "", [])
    ttf.add_link_rule(rule)
    rule = TF.create_standard_rule([0], None,[bbra_internet_port2], None, None, "", [])
    ttf.add_link_rule(rule)
    rule = TF.create_standard_rule([0], None,[bbrb_internet_port1], None, None, "", [])
    ttf.add_link_rule(rule)
    rule = TF.create_standard_rule([0], None,[bbrb_internet_port2], None, None, "", [])
    ttf.add_link_rule(rule)
    
def get_end_ports(name_to_id,index):

    linked_ports = [("bbra_rtr","te7/3"),
                    ("bbra_rtr","te7/2"),
                    ("bbra_rtr","te7/1"),
                    ("bbra_rtr","te1/3"),
                    ("bbra_rtr","te1/4"),
                    ("bbra_rtr","te6/1"),
                    ("bbra_rtr","te6/3"),
                    
                    ("bbrb_rtr","te7/1"),
                    ("bbrb_rtr","te7/2"),
                    ("bbrb_rtr","te7/4"),
                    ("bbrb_rtr","te6/3"),
                    ("bbrb_rtr","te6/1"),
                    ("bbrb_rtr","te1/1"),
                    ("bbrb_rtr","te1/3"),
                    
                    ("boza_rtr","te2/1"),
                    ("boza_rtr","te3/1"),
                    ("boza_rtr","te2/3"),
                    ("bozb_rtr","te2/3"),
                    ("bozb_rtr","te2/1"),
                    ("bozb_rtr","te3/1"),
                    
                    ("coza_rtr","te3/1"),
                    ("coza_rtr","te2/1"),
                    ("coza_rtr","te2/3"),
                    ("cozb_rtr","te2/3"),
                    ("cozb_rtr","te2/1"),
                    ("cozb_rtr","te3/1"),
                    
                    ("goza_rtr","te2/1"),
                    ("goza_rtr","te3/1"),
                    ("goza_rtr","te2/3"),
                    ("gozb_rtr","te2/3"),
                    ("gozb_rtr","te2/1"),
                    ("gozb_rtr","te3/1"),
                    
                    ("poza_rtr","te2/1"),
                    ("poza_rtr","te3/1"),
                    ("poza_rtr","te2/3"),
                    ("pozb_rtr","te2/3"),
                    ("pozb_rtr","te2/1"),
                    ("pozb_rtr","te3/1"),
                    
                    ("roza_rtr","te3/1"),
                    ("roza_rtr","te2/1"),
                    ("roza_rtr","te2/3"),
                    ("rozb_rtr","te2/3"),
                    ("rozb_rtr","te2/1"),
                    ("rozb_rtr","te3/1"),
                    
                    ("soza_rtr","te2/1"),
                    ("soza_rtr","te3/1"),
                    ("soza_rtr","te2/3"),
                    ("sozb_rtr","te2/3"),
                    ("sozb_rtr","te3/1"),
                    ("sozb_rtr","te2/1"),
                    
                    ("yoza_rtr","te7/1"),
                    ("yoza_rtr","te1/3"),
                    ("yoza_rtr","te1/1"),
                    ("yoza_rtr","te1/2"),
                    ("yozb_rtr","te1/2"),
                    ("yozb_rtr","te1/3"),
                    ("yozb_rtr","te2/1"),
                    ("yozb_rtr","te1/1"),

            ]
        
    
    end_ports = []
    cs = ciscoRouter(1)
    for rtr_name in rtr_names:
        mod_rtr_name = "%s%s"%(rtr_name,index)
        for rtr_port in name_to_id[mod_rtr_name]:
            if (rtr_name,rtr_port) not in linked_ports:
                end_ports.append(name_to_id[mod_rtr_name][rtr_port] + cs.PORT_TYPE_MULTIPLIER * cs.OUTPUT_PORT_TYPE_CONST)
                
    return end_ports
        
def load_tf_to_nusmv():
    '''
    For Model Checking Project.
    Creates NuSMV file from transfer function objects of Stanford network.
    '''
    nusmv = NuSMV()
    cs = ciscoRouter(1)
    nusmv.set_output_port_offset(cs.PORT_TYPE_MULTIPLIER * cs.OUTPUT_PORT_TYPE_CONST)
    for rtr_name in rtr_names:
        f = TF(1)
        f.load_object_from_file("work/tf_stanford_backbone/%s.tf"%rtr_name)
        nusmv.generate_nusmv_trans(f, [])
    
    (port_map,port_reverse_map) = load_stanford_backbone_port_to_id_map()
    end_ports = get_end_ports(port_map,"")         
    f = TF(1)
    f.load_object_from_file("work/tf_stanford_backbone/backbone_topology.tf")
    nusmv.generate_nusmv_trans(f,end_ports)
    nusmv.generate_nusmv_input()
    
    return nusmv

def load_augmented_tf_to_nusmv(replication_factor,dir_path):
    '''
    For Model Checking Project.
    Creates NuSMV file from transfer function objects of replicated Stanford network.
    '''
    nusmv = NuSMV()
    cs = ciscoRouter(1)
    nusmv.set_output_port_offset(cs.PORT_TYPE_MULTIPLIER * cs.OUTPUT_PORT_TYPE_CONST)
    (port_map,port_reverse_map) = load_port_to_id_map(dir_path)
    end_ports = []
    for replicate in range(1,replication_factor+1):
        for rtr_name in rtr_names:
            f = TF(1)
            f.load_object_from_file("%s/%s%d.tf"%(dir_path,rtr_name,replicate))
            nusmv.generate_nusmv_trans(f, [])
        end_ports_subset = get_end_ports(port_map,"%d"%replicate)
        end_ports.extend(end_ports_subset)
      
    f = TF(1)
    f.load_object_from_file("%s/root.tf"%(dir_path))
    nusmv.generate_nusmv_trans(f, [])
        
    f = TF(1)
    f.load_object_from_file("%s/backbone_topology.tf"%dir_path)
    nusmv.generate_nusmv_trans(f,end_ports)
    nusmv.generate_nusmv_input()
    
    return nusmv

def generate_stanford_backbne_one_layer_tf():
    '''
    Tries to merge the 3 layers of transfer function into one layer.
    WARNING: the result will be huge.
    '''
    for rtr_name in rtr_names:
        f = TF(1)
        f.load_object_from_file("../work/tf_stanford_backbone/%s.tf"%rtr_name)
        stage1_rules = []
        stage2_rules = []
        stage3_rules = []
        stage1_2_rules = []
        for rule in f.rules:
            if (rule["in_ports"][0] % 100000) == 0:
                stage2_rules.append(rule)
            elif ((rule["in_ports"][0] % 100000)/ 10000) == 0:
                stage1_rules.append(rule)
            elif ((rule["in_ports"][0] % 100000)/ 10000) == 1:
                stage3_rules.append(rule)
        for stage2_rule in stage2_rules:
            for stage1_rule in stage1_rules:
                r = compose_standard_rules(stage1_rule,stage2_rule)
                if r != None:
                    stage1_2_rules.append(r)
        for stage3_rule in stage3_rules:
            for stage1_2_rule in stage1_2_rules:
                r = compose_standard_rules(stage3_rule,stage1_2_rule)
                if r != None:
                    if r["mask"] == None:
                        f.add_fwd_rule(r)
                    else:
                        f.add_rewrite_rule(r)
        f.save_object_to_file("../work/tf_stanford_backbone/%s_one_layer.tf"%rtr_name)
       
            
    
