'''
    <Slicing experiment in Header Space paper>
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
    
Created on Sep 26, 2011

@author: Peyman Kazemian
'''
from headerspace.hs import *
from headerspace.tf import *
from headerspace.slice import *
from config_parser.cisco_router_parser import ciscoRouter
from config_parser.helper import *
from time import time
import math
import random

cs = ciscoRouter(1)
rtr_port_const = 100

rtr_ids =   {"bbra_rtr":100,
             "bbrb_rtr":200,
             "boza_rtr":300,
             "bozb_rtr":400,
             "coza_rtr":500,
             "cozb_rtr":600,
             "goza_rtr":700,
             "gozb_rtr":800,
             "poza_rtr":900,
             "pozb_rtr":1000,
             "roza_rtr":1100,
             "rozb_rtr":1200,
             "soza_rtr":1300,
             "sozb_rtr":1400,
             "yoza_rtr":1500,
             "yozb_rtr":1600,
             }

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

port_ids = {"bbra_rtr":{"te7/1":1,"te6/3":2,"te7/2":3,"te6/1":4,"te1/4":5,"te1/3":6,"te7/3":7},
            "bbrb_rtr":{"te7/1":1,"te7/4":2,"te1/1":3,"te6/3":4,"te1/3":5,"te7/2":6,"te6/1":7},
            "boza_rtr":{"te2/1":1,"te3/1":2,"te2/3":3},
            "bozb_rtr":{"te2/1":1,"te3/1":2,"te2/3":3},
            "coza_rtr":{"te2/1":1,"te3/1":2,"te2/3":3},
            "cozb_rtr":{"te2/1":1,"te3/1":2,"te2/3":3},
            "goza_rtr":{"te2/1":1,"te3/1":2,"te2/3":3},
            "gozb_rtr":{"te2/1":1,"te3/1":2,"te2/3":3},
            "poza_rtr":{"te2/1":1,"te3/1":2,"te2/3":3},
            "pozb_rtr":{"te2/1":1,"te3/1":2,"te2/3":3},
            "roza_rtr":{"te2/1":1,"te3/1":2,"te2/3":3},
            "rozb_rtr":{"te2/1":1,"te3/1":2,"te2/3":3},
            "soza_rtr":{"te2/1":1,"te3/1":2,"te2/3":3},
            "sozb_rtr":{"te2/1":1,"te3/1":2,"te2/3":3},
            "yoza_rtr":{"te1/1":1,"te1/2":2,"te1/3":3, "te7/1":4},
            "yozb_rtr":{"te1/1":1,"te1/2":2,"te1/3":3, "te2/1":4},
            }

def generate_random_slice_hs(num_wc,base_ip,range_ip,max_right_subnet):
    hs = headerspace(cs.HS_FORMAT()["length"]*2)
    tcp_ports = [7,21,23,80,530,None,None,None,None,None]
    for i in range(num_wc/2):
        rand_ip = base_ip + random.randrange(0,range_ip)
        rand_subnet = random.randrange(0,max_right_subnet)
        all_x = byte_array_get_all_x(cs.HS_FORMAT()["length"]*2)
        cs.set_field(all_x, "ip_src", rand_ip, rand_subnet)
        cs.set_field(all_x, "ip_dst", rand_ip, rand_subnet)
        rand_tcp_port = random.choice(tcp_ports)
        if rand_tcp_port != None:
            cs.set_field(all_x, "transport_src", rand_tcp_port, 0)
            cs.set_field(all_x, "transport_dst", rand_tcp_port, 0)
        hs.add_hs(all_x)

    return hs

def generate_random_fwd_rule(slice_chunk,base_ip,range_ip,max_right_subnet):
    tcp_flags = [128,128,64,None,None,None,None,None]
    match = byte_array_get_all_x(cs.HS_FORMAT()["length"]*2)
    rand_ip = base_ip + random.randrange(0,range_ip)
    rand_subnet = random.randrange(0,max_right_subnet)
    cs.set_field(match, "ip_dst", rand_ip, rand_subnet)
    mask = byte_array_get_all_one(cs.HS_FORMAT()["length"]*2)
    rewrite = byte_array_get_all_zero(cs.HS_FORMAT()["length"]*2)
    #choose if rewrite tcp src port and IP src address (to simulate a NAT). p = 0.2
    rand_num = random.randrange(10)
    if (rand_num == 2 or rand_num == 3):
        rand_ip = base_ip + random.randrange(0,range_ip)
        rand_subnet = random.randrange(0,max_right_subnet)
        rand_tcp_src = random.randrange(1000,2000) 
        cs.set_field(mask, "ip_src", 0, rand_subnet)
        cs.set_field(rewrite, "ip_src", rand_ip, rand_subnet)
        cs.set_field(mask, "transport_src", 0, 0)
        cs.set_field(rewrite, "transport_src", rand_tcp_src, 0)
    # set tcp flags with p = 3/8:
    tcp_flag = random.choice(tcp_flags)
    if tcp_flag != None:
        cs.set_field(mask, "transport_ctrl", 0, 6)
        cs.set_field(rewrite, "transport_ctrl", tcp_flag, 6)
    
    #choose a box in slice at random, and choose one of its ports that belong to
    # the slice as input port and one other random port from the box as the output port
    box_list = set()
    slice_ports = {}
    for (box,prt) in slice_chunk:
        box_list.add(box)
        if box not in slice_ports.keys():
            slice_ports[box] = []
        slice_ports[box].append(rtr_ids[box] + port_ids[box][prt])
    box_list = list(box_list)
    rand_box = random.choice(box_list)
    input_port = random.choice(slice_ports[rand_box])
    
    rand_box_ports = port_ids[rand_box].keys()
    rand_out_port_name = random.choice(rand_box_ports)
    output_port = rtr_ids[rand_box] + port_ids[rand_box][rand_out_port_name]
    
    rule = TF.create_standard_rule([input_port], match, [output_port], mask, rewrite, "", [])
    return rule


tf = TF(cs.HS_FORMAT()["length"]*2)
for (from_router,from_port,to_router,to_port) in topology:
    from_cs = rtr_ids[from_router]
    from_port = port_ids[from_router][from_port]
    to_cs = rtr_ids[to_router]
    to_port = port_ids[to_router][to_port]
    rule = TF.create_standard_rule([from_cs+from_port], None,[to_cs+to_port], None, None, "", [])
    tf.add_link_rule(rule)
    rule = TF.create_standard_rule([to_cs+to_port], None,[from_cs+from_port], None, None, "", [])
    tf.add_link_rule(rule)


slice_chuncks = [
                 [("boza_rtr","te2/1"),("boza_rtr","te3/1"),("boza_rtr","te2/3"),("bbra_rtr","te1/4"),("bbrb_rtr","te1/3"),
                 ("bozb_rtr","te2/1"),("bozb_rtr","te3/1"),("bozb_rtr","te2/3"),("bbra_rtr","te1/3"),("bbrb_rtr","te6/3")],
                 [("coza_rtr","te2/1"),("coza_rtr","te3/1"),("coza_rtr","te2/3"),("bbra_rtr","te7/2"),("bbrb_rtr","te6/1"),
                 ("cozb_rtr","te2/1"),("cozb_rtr","te3/1"),("cozb_rtr","te2/3"),("bbra_rtr","te6/1"),("bbrb_rtr","te7/2")],
                 [("goza_rtr","te2/1"),("goza_rtr","te3/1"),("goza_rtr","te2/3"),("bbra_rtr","te7/3"),("bbrb_rtr","te1/1"),
                 ("gozb_rtr","te2/1"),("gozb_rtr","te3/1"),("gozb_rtr","te2/3"),("bbra_rtr","te6/1"),("bbrb_rtr","te7/2")],
                 [("poza_rtr","te2/1"),("poza_rtr","te3/1"),("poza_rtr","te2/3"),("bbra_rtr","te6/1"),("bbrb_rtr","te7/2"),
                 ("pozb_rtr","te2/1"),("pozb_rtr","te3/1"),("pozb_rtr","te2/3"),("bbra_rtr","te7/3"),("bbrb_rtr","te1/1")],
                 [("roza_rtr","te2/1"),("roza_rtr","te3/1"),("roza_rtr","te2/3"),("bbra_rtr","te1/3"),("bbrb_rtr","te6/3"),
                 ("rozb_rtr","te2/1"),("rozb_rtr","te3/1"),("rozb_rtr","te2/3"),("bbra_rtr","te1/4"),("bbrb_rtr","te1/3")],
                 [("soza_rtr","te2/1"),("soza_rtr","te3/1"),("soza_rtr","te2/3"),("bbra_rtr","te6/1"),("bbrb_rtr","te7/2"),
                 ("sozb_rtr","te2/1"),("sozb_rtr","te3/1"),("sozb_rtr","te2/3"),("bbra_rtr","te7/2"),("bbrb_rtr","te6/1")],
                 [("yoza_rtr","te1/1"),("yoza_rtr","te1/2"),("yoza_rtr","te1/3"),("yoza_rtr","te7/1"),("bbra_rtr","te6/3"),("bbrb_rtr","te7/4"),
                 ("yozb_rtr","te1/1"),("yozb_rtr","te1/2"),("yozb_rtr","te1/3"),("yozb_rtr","te2/1"),("bbra_rtr","te1/3"),("bbrb_rtr","te6/3")],
                 ]

 
def run_slice_isolation(repeat):
    primary_slice_sizes = [10,50,250,1000]
    num_slices = [10,100,500]
    results = []
    for primary_slice_size in primary_slice_sizes:
        result = []
        for num_slice in num_slices:
            repeat_results = []
            for i in range(repeat):
                other_slices = Slice(cs.HS_FORMAT()["length"]*2)
                primary_slice = Slice(cs.HS_FORMAT()["length"]*2)
                for i in range(num_slice+1):
                    random_slices = random.sample(slice_chuncks,2)
                    slice_port_ids = set()
                    for random_slice in random_slices:
                        for (rtr,prt) in random_slice:
                            slice_port_ids.add(port_ids[rtr][prt] + rtr_ids[rtr])
                    hs = generate_random_slice_hs(primary_slice_size,dotted_ip_to_int("171.64.0.0"),2**16-1,16)
                    if i == num_slice:
                        primary_slice.set_hs_reservation(list(slice_port_ids), hs)
                    else:
                        other_slices.set_hs_reservation(list(slice_port_ids),hs)
                st = time()
                isect = other_slices.intersect(primary_slice)
                en = time()
                repeat_results.append(en-st)
            #print "result: %s"%isect
            avg = sum(repeat_results)/repeat
            sum_sqr = 0
            for num in repeat_results:
                sum_sqr = (num-avg)**2
            std_dev = math.sqrt(sum_sqr)/repeat
            result.append((avg,std_dev))

        results.append(result)

    print results

def run_slice_leakage_test(repeat):
    primary_slice_sizes = [10,50,250,1000]
    num_slices = [10,100,500]
    results = []
    for primary_slice_size in primary_slice_sizes:
        result = []
        for num_slice in num_slices:
            repeat_results = []
            other_slices = Slice(cs.HS_FORMAT()["length"]*2)
            primary_slice = Slice(cs.HS_FORMAT()["length"]*2)
            for i in range(num_slice+1):
                random_slices = random.sample(slice_chuncks,2)
                slice_port_ids = set()
                for random_slice in random_slices:
                    for (rtr,prt) in random_slice:
                        slice_port_ids.add(port_ids[rtr][prt] + rtr_ids[rtr])
                hs = generate_random_slice_hs(primary_slice_size,dotted_ip_to_int("171.64.0.0"),2**16-1,16)
                if i == num_slice:
                    primary_slice.set_hs_reservation(list(slice_port_ids), hs)
                else:
                    other_slices.set_hs_reservation(list(slice_port_ids),hs)
            #Now that slices has been created, generate a random rule
            # and check if the rule causes any leakage problem
            repeat_results = []
            for i in range(repeat):
                slice_chunk = [item for sublist in random_slices for item in sublist]
                rule = generate_random_fwd_rule(slice_chunk,dotted_ip_to_int("171.64.0.0"),2**16-1,16)
                f = TF(cs.HS_FORMAT()["length"]*2)
                f.add_rewrite_rule(rule)
                transformed_slice = Slice(cs.HS_FORMAT()["length"]*2)
                st = time()
                in_port = rule["in_ports"][0]
                primary_hs_list = primary_slice.get_port_reservation(in_port)
                for primary_hs in primary_hs_list:
                    ohs = f.T(primary_hs,in_port)
                    for (hs,p_list) in ohs:
                        transformed_slice.set_hs_reservation(p_list, hs)
                leak = transformed_slice.intersect(other_slices)
                en = time()
                #print leak
                repeat_results.append(en-st)
            avg = sum(repeat_results)/repeat
            sum_sqr = 0
            for num in repeat_results:
                sum_sqr = (num-avg)**2
            std_dev = math.sqrt(sum_sqr)/repeat
            result.append((avg,std_dev))
            print result
            
        results.append(result)
        print results
                
#run_slice_isolation(5)
run_slice_leakage_test(50)