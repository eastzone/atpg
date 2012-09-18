'''
    <IP star example in Headerspace paper>
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
    
    @Author: Peyman Kazemian
'''
from headerspace.hs import *
from headerspace.tf import TF
from headerspace.applications import *
from config_parser.helper import *
import random
from time import time, clock


NUM_MBOX = 2
format = {}
format["ip_src_pos"] = 0
format["ip_dst_pos"] = 4
format["ip_sender_pos"] = 8
format["stack_size_pos"] = 12
format["stack_pos"] = 13
format["ip_src_len"] = 4
format["ip_dst_len"] = 4
format["ip_sender_len"] = 4
format["stack_size_len"] = 1
format["stack_len"] = 4*5
format["length"] = 33

def make_TTF(num_mbox):
    TTF = TF(format["length"]*2)
    rule = {}
    rule["in_ports"] = [0]
    rule["out_ports"] = [1]
    TTF.add_link_rule(rule)
    rule["in_ports"] = [1]
    rule["out_ports"] = [0]
    TTF.add_link_rule(rule)
    rule["in_ports"] = [2]
    rule["out_ports"] = [3]
    TTF.add_link_rule(rule)
    rule["in_ports"] = [3]
    rule["out_ports"] = [2]
    TTF.add_link_rule(rule)
    rule["in_ports"] = [5]
    rule["out_ports"] = [4]
    TTF.add_link_rule(rule)
    rule["in_ports"] = [4]
    rule["out_ports"] = [5]
    TTF.add_link_rule(rule)
    rule["in_ports"] = [6]
    rule["out_ports"] = [7]
    TTF.add_link_rule(rule)
    rule["in_ports"] = [7]
    rule["out_ports"] = [6]
    TTF.add_link_rule(rule)
    rule["in_ports"] = [8]
    rule["out_ports"] = [9]
    TTF.add_link_rule(rule)
    rule["in_ports"] = [9]
    rule["out_ports"] = [8]
    TTF.add_link_rule(rule)
    rule["in_ports"] = [10]
    rule["out_ports"] = [11]
    TTF.add_link_rule(rule)
    rule["in_ports"] = [11]
    rule["out_ports"] = [10]
    TTF.add_link_rule(rule)
    rule["in_ports"] = [12]
    rule["out_ports"] = [13]
    TTF.add_link_rule(rule)
    rule["in_ports"] = [13]
    rule["out_ports"] = [12]
    TTF.add_link_rule(rule)
    for i in range(num_mbox):
        rule["in_ports"] = [14 + i*4]
        rule["out_ports"] = [15 + i*4]
        TTF.add_link_rule(rule)
        rule["in_ports"] = [15 + i*4]
        rule["out_ports"] = [14 + i*4]
        TTF.add_link_rule(rule)
        rule["in_ports"] = [16 + i*4]
        rule["out_ports"] = [17 + i*4]
        TTF.add_link_rule(rule)
        rule["in_ports"] = [17 + i*4]
        rule["out_ports"] = [16 + i*4]
        TTF.add_link_rule(rule)
        
    return TTF

def set_field(arr, field, value, right_mask):
    b_array = int_to_byte_array(value,8*format["%s_len"%field])
    start_pos = 2*format["%s_pos"%field]
    for i in range(2*format["%s_len"%field]):
        if right_mask <= 4*i:
            arr[start_pos + i] = b_array[i]
        elif (right_mask > 4*i and right_mask < 4*i + 4):
            shft = right_mask % 4;
            rm = (0xff << 2*shft) & 0xff
            lm = ~rm & 0xff
            arr[start_pos + i] = (b_array[i] & rm) | (arr[start_pos + i] & lm) 
            
def set_stack_field(arr,index,value,right_mask):
    b_array = int_to_byte_array(value,32)
    start_pos = 2*format["stack_pos"] + index * 4 * 2
    for i in range(8):
        if right_mask <= 4*i:
            arr[start_pos + i] = b_array[i]
        elif (right_mask > 4*i and right_mask < 4*i + 4):
            shft = right_mask % 4;
            rm = (0xff << 2*shft) & 0xff
            lm = ~rm & 0xff
            arr[start_pos + i] = (b_array[i] & rm) | (arr[start_pos + i] & lm) 

def make_byte_array_ip_star_hdr(num_stack,stack_ip_list,stack_subnet_list,ip_src,ip_src_subnet,ip_dst,ip_dst_subnet):
    hdr = byte_array_get_all_x(2*format["length"])
    if num_stack != None:
        set_field(hdr,"stack_size",len(stack_ip_list),0)
    set_field(hdr,"ip_src",ip_src,32-ip_src_subnet)
    set_field(hdr,"ip_dst",ip_dst,32-ip_dst_subnet)
    for i in range(len(stack_ip_list)):
        set_stack_field(hdr,i,stack_ip_list[i],32-stack_subnet_list[i])
    return hdr


def make_mbox_match(ip_dst, ip_dst_subnet, in_port):
    ip_match = make_byte_array_ip_star_hdr(None,[],[],0,0,ip_dst,ip_dst_subnet)
    hs_len = format["length"] * 2
    def mbox_match(hs,port):
        '''
        match function for a middle box
        '''
        if port == in_port:
            new_hs = hs.copy()
            new_hs.intersect(ip_match)
            if new_hs.count() > 0:
                return [new_hs]
        return []
        
    return mbox_match

def make_mbox_inv_match(ip_src, ip_src_subnet, out_port):
    ip_match = make_byte_array_ip_star_hdr(None,[],[],ip_src,ip_src_subnet,0,0)
    hs_len = format["length"] * 2
    def mbox_inv_match(hs,port):
        if port == out_port:
            new_hs = hs.copy()
            new_hs.intersect(ip_match)
            if new_hs.count() > 0:
                return [new_hs]
        return []
        
    return mbox_inv_match
 
def make_mbox_tf():
    def mbox_tf(hs,port):
        '''
        transfer function for  a middle box - replace ip src and dst
        '''
        cpy_hs = hs.copy()
        for elem in cpy_hs.hs_list:
            for i in range(8):
                tmp = elem[i]
                elem[i] = elem[i+8]
                elem[i+8] = tmp
        for elem in cpy_hs.hs_diff:
            for i in range(8):
                tmp = elem[i]
                elem[i] = elem[i+8]
                elem[i+8] = tmp
        return [(cpy_hs,[port])]
    
    return mbox_tf


def make_IP_str_match(_in_ports):
    in_ports = list(_in_ports)
    def IP_str_match(hs,port):
        if port in in_ports:
            return [hs.copy()]
        else:
            return []
    
    return IP_str_match

def make_IP_str_transform(ip_dst, ip_dst_subnet, _out_ports):     
    out_ports = list(_out_ports)
    hs_len = format["length"] * 2
    ip_match = make_byte_array_ip_star_hdr(None,[],[],0,0,ip_dst,ip_dst_subnet)
    def IP_str_transform(hs,port):
        if hs.count() == 0:
            return []
        num_stack = byte_to_int(hs.hs_list[0][format["stack_size_pos"]*2])
        cpy_hs = hs.copy() 
        elem_list = []
        elem_list.extend(cpy_hs.hs_list)
        elem_list.extend(cpy_hs.hs_diff)
        for elem in elem_list:
            b_tmp = elem[2*format["stack_pos"]:2*format["stack_pos"]+8]
            
            # copy sender Ip to src Ip and dst ip to last stack position
            for i in range(8):
                elem[i+2*format["ip_src_pos"]] = elem[i+2*format["ip_sender_pos"]]
                elem[i+2*format["stack_pos"]+8*num_stack-8] = elem[i+2*format["ip_dst_pos"]]
                
            # copy dst from stack and shift stack by one
            for i in range(8):
                elem[2*format["ip_dst_pos"]+i] = elem[2*format["stack_pos"]+i]
                for j in range(num_stack-1):
                    elem[2*format["stack_pos"]+i+j*8] = elem[2*format["stack_pos"]+i+j*8+8]
            for i in range(8):
                elem[2*format["stack_pos"]+num_stack*8-8+i] = b_tmp[i]

        cpy_hs.intersect(ip_match)
        if cpy_hs.count() > 0:
            return [(cpy_hs,out_ports)]
        else:
            return []
    
    return IP_str_transform

def make_IP_str_inv_match(out_ports, ip_dst, ip_dst_subnet):
    ip_match = make_byte_array_ip_star_hdr(None,[],[],0,0,ip_dst,ip_dst_subnet)
    hs_len = format["length"] * 2
    def IP_str_inv_match(hs,port):
        if port in out_ports:
            new_hs = hs.copy()
            new_hs.intersect(ip_match)
            if new_hs.count() > 0:
                return [new_hs]
        return []
    
    return IP_str_inv_match
                

def make_IP_str_inv_transform(_in_ports):
    in_ports = list(_in_ports)
    def IP_str_inv_transform(hs,port):
        cpy_hs = hs.copy()     
        num_stack = byte_to_int(hs.hs_list[0][format["stack_size_pos"]*2])
        elem_list = []
        elem_list.extend(cpy_hs.hs_list)
        elem_list.extend(cpy_hs.hs_diff)
        for elem in elem_list:
            b_tmp = elem[2*format["ip_dst_pos"]:2*format["ip_dst_pos"]+8]
            for i in range(8):
                elem[2*format["ip_src_pos"]+i] = 0xff
                for j in reversed(range(num_stack-1)):
                    elem[format["stack_pos"]*2+8*j+i+8] = elem[format["stack_pos"]*2+8*j+i]
                elem[2*format["stack_pos"]+i] = b_tmp[i]
                elem[format["ip_dst_pos"]*2+i] = elem[format["stack_pos"]*2+8*num_stack+i-8]   
                         
        return [(cpy_hs,in_ports)]
    
    return IP_str_inv_transform 


def make_NTF(num_mbox):
    line_counter = 1
    num_stack = num_mbox + 1
    NTF = TF(format["length"])
    
    m_addr = [dotted_ip_to_int("10.1.1.1"),
              dotted_ip_to_int("10.1.2.2"),
              dotted_ip_to_int("10.1.3.3"),
              dotted_ip_to_int("10.1.4.4"),
              dotted_ip_to_int("10.1.5.5"),]
    m_subnet = [dotted_ip_to_int("10.1.1.0"),
              dotted_ip_to_int("10.1.2.0"),
              dotted_ip_to_int("10.1.3.0"),
              dotted_ip_to_int("10.1.4.0"),
              dotted_ip_to_int("10.1.5.0"),]
    
    sender_addr = dotted_ip_to_int("10.1.10.1")
    receiver_addr = dotted_ip_to_int("10.1.20.1")
    network_subnet = dotted_ip_to_int("10.1.0.0")
    
    # rules for R1
    for i in range(num_mbox):
        ip_match = make_byte_array_ip_star_hdr(None,[],[],0,0,m_addr[i],32)
        rule = TF.create_standard_rule([1,7], ip_match, [2], None, None, "sample.txt", [line_counter])
        NTF.add_fwd_rule(rule)
        line_counter += 1
        
    ip_match = make_byte_array_ip_star_hdr(None,[],[],0,0,receiver_addr,32)
    rule = TF.create_standard_rule([1,2], ip_match, [7], None, None, "sample.txt", [line_counter])
    NTF.add_fwd_rule(rule)
    line_counter += 1
    ip_match = make_byte_array_ip_star_hdr(None,[],[],0,0,sender_addr,32)
    rule = TF.create_standard_rule([2,7], ip_match, [1], None, None, "sample.txt", [line_counter])
    NTF.add_fwd_rule(rule)
    line_counter += 1
    
    # Add rule for R2:
    all_ip_star_ingress_ports = []
    for i in range(num_mbox):
        ip_match = make_byte_array_ip_star_hdr(None,[],[],0,0,m_addr[i],32)
        rule = TF.create_standard_rule([3,4], ip_match, [14+4*i], None, None, "sample.txt", [line_counter])
        NTF.add_fwd_rule(rule)
        line_counter += 1
        all_ip_star_ingress_ports.append(14+4*i)
    
    for i in range(num_mbox):
        rule = TF.create_custom_rule(make_IP_str_match(all_ip_star_ingress_ports), 
                                     make_IP_str_transform(m_addr[i], 32, [all_ip_star_ingress_ports[i]]), 
                                     make_IP_str_inv_match([all_ip_star_ingress_ports[i]], m_addr[i], 32), 
                                     make_IP_str_inv_transform(all_ip_star_ingress_ports), 
                                     "sample.txt", [line_counter])
        NTF.add_custom_rule(rule)
        line_counter += 1
    rule = TF.create_custom_rule(make_IP_str_match(all_ip_star_ingress_ports), 
                                 make_IP_str_transform(sender_addr, 32, [4]), 
                                 make_IP_str_inv_match([4], sender_addr, 32), 
                                 make_IP_str_inv_transform(all_ip_star_ingress_ports), 
                                 "sample.txt", [line_counter])
    NTF.add_custom_rule(rule)
    line_counter += 1
    rule = TF.create_custom_rule(make_IP_str_match(all_ip_star_ingress_ports), 
                                 make_IP_str_transform(receiver_addr, 32, [3]), 
                                 make_IP_str_inv_match([3], receiver_addr, 32), 
                                 make_IP_str_inv_transform(all_ip_star_ingress_ports), 
                                 "sample.txt", [line_counter])
    NTF.add_custom_rule(rule)
    line_counter += 1
        
    
    # add rule for R3:
    ip_match = make_byte_array_ip_star_hdr(None,[],[],0,0,receiver_addr,32)
    rule = TF.create_standard_rule([5,6], ip_match, [8], None, None, "sample.txt", [line_counter])
    NTF.add_fwd_rule(rule)
    line_counter += 1
    ip_match = make_byte_array_ip_star_hdr(None,[],[],0,0,sender_addr,32)
    rule = TF.create_standard_rule([5], ip_match, [6], None, None, "sample.txt", [line_counter])
    NTF.add_fwd_rule(rule)
    line_counter += 1    
    rule = TF.create_custom_rule(make_IP_str_match([8]), 
                                 make_IP_str_transform(receiver_addr, 32, [8]), 
                                 make_IP_str_inv_match([8], receiver_addr, 32), 
                                 make_IP_str_inv_transform([8]), 
                                 "sample.txt", [line_counter])
    NTF.add_custom_rule(rule)
    line_counter += 1
    rule = TF.create_custom_rule(make_IP_str_match([8]), 
                                 make_IP_str_transform(sender_addr, 32, [6]), 
                                 make_IP_str_inv_match([6], sender_addr, 32), 
                                 make_IP_str_inv_transform([8]), 
                                 "sample.txt", [line_counter])
    NTF.add_custom_rule(rule)
    line_counter += 1
    
    for i in range(num_mbox):
        rule = TF.create_custom_rule(make_IP_str_match([8]), 
                                     make_IP_str_transform(m_addr[i], 32, [5]), 
                                     make_IP_str_inv_match([5], m_addr[i], 32), 
                                     make_IP_str_inv_transform([8]), 
                                     "sample.txt", [line_counter])
        NTF.add_custom_rule(rule)
        line_counter += 1
        ip_match = make_byte_array_ip_star_hdr(None,[],[],0,0,m_addr[i],32)
        rule = TF.create_standard_rule([6], ip_match, [5], None, None, "sample.txt", [line_counter])
        NTF.add_fwd_rule(rule)
        line_counter += 1 
        
    
    # add rule for R4,R5,R8,R9,...
    for i in range(num_mbox):
        ip_match = make_byte_array_ip_star_hdr(None,[],[],0,0,m_subnet[i],24)
        rule = TF.create_standard_rule([15 + 4*i], ip_match, [16 + 4*i], None, None, "sample.txt", [line_counter])
        NTF.add_fwd_rule(rule)
        line_counter += 1 
        ip_match = make_byte_array_ip_star_hdr(None,[],[],0,0,network_subnet,18)
        rule = TF.create_standard_rule([16 + 4*i], ip_match, [15 + 4*i], None, None, "sample.txt", [line_counter])
        NTF.add_fwd_rule(rule)
        line_counter += 1 
        
    # add rule for R6
    ip_match = make_byte_array_ip_star_hdr(None,[],[],0,0,receiver_addr,32)
    rule = TF.create_standard_rule([9], ip_match, [10], None, None, "sample.txt", [line_counter])
    NTF.add_fwd_rule(rule)
    line_counter += 1 
    ip_match = make_byte_array_ip_star_hdr(None,[],[],0,0,network_subnet,16)
    rule = TF.create_standard_rule([10], ip_match, [9], None, None, "sample.txt", [line_counter])
    NTF.add_fwd_rule(rule)
    line_counter += 1 
    
    # add rule for R7
    rule = TF.create_custom_rule(make_IP_str_match([11]), 
                                 make_IP_str_transform(receiver_addr, 32, [12]), 
                                 make_IP_str_inv_match([12], receiver_addr, 32), 
                                 make_IP_str_inv_transform([11]), 
                                 "sample.txt", [line_counter])
    NTF.add_custom_rule(rule)
    line_counter += 1
    rule = TF.create_custom_rule(make_IP_str_match([11]), 
                                 make_IP_str_transform(network_subnet, 21, [11]), 
                                 make_IP_str_inv_match([11], network_subnet, 21), 
                                 make_IP_str_inv_transform([11]), 
                                 "sample.txt", [line_counter])
    NTF.add_custom_rule(rule)
    line_counter += 1
    
    # rule for middle boxes:
    for i in range(num_mbox):
        rule = TF.create_custom_rule(make_mbox_match(m_addr[i], 32, 17+4*i), 
                                     make_mbox_tf(), 
                                     make_mbox_inv_match(m_addr[i], 32, 17+4*i), 
                                     make_mbox_tf(), 
                                     "sample.txt", [line_counter])
        NTF.add_custom_rule(rule)
        line_counter += 1
        
    return NTF


def expand_NTF(NTF, num_rules):
    port_groups = [[1,2,7,101,102,103,104,105,106,107],
                   [3,4,14,18,201,202,203,204,205],
                   [5,6,8,301,302,303,304,305,306,307],
                   [9,10,401,402,403,404,405,406,407,408]]
    per_port_rules = num_rules/4
    for j in range(4):
        for i in range(per_port_rules):
            first = random.randrange(32,255)
            second = random.randrange(1,255)
            ip_addr = dotted_ip_to_int("10.1.%d.%d"%(first,second))
            subnet = random.randrange(27,32)
            ip_match = make_byte_array_ip_star_hdr(None,[],[],0,0,ip_addr,subnet)
            in_port = random.choice(port_groups[j])
            out_port = random.choice(port_groups[j])
            rule = TF.create_standard_rule([in_port], ip_match, [out_port], None, None, "dummy", [])
            NTF.add_fwd_rule(rule)
            

reverse_map = {"0":"SRC","1":"R1-1","2":"R1-2","7":"R1-3",
               "3":"R2-1","4":"R2-2",
               "5":"R3-1","6":"R3-2","8":"R3-3",
               "9":"R6-1","10":"R6-2",
               "11":"R7-1","12":"R7-2","13":"DST",
               "14":"R2-3","15":"R4-1","16":"R4-2","17":"M1",
               "18":"R2-4","19":"R5-1","20":"R5-2","21":"M2",
               "22":"R2-5","23":"R6-1","24":"R6-2","25":"M3",
               "26":"R2-6","27":"R7-1","28":"R7-2","29":"M4",}


sizes = [2,3,4]
expands = [1,20000,70000,100000,130000]
results = []
for size in sizes:
    result = []
    for expand in expands:
        my_NTF = make_NTF(size)
        my_TTF = make_TTF(size)
        print "BEGIN EXPANSION"
        expand_NTF(my_NTF,expand)
        print "END EXPANSION"
        all_x = byte_array_get_all_x(format["length"]*2)
        set_field(all_x, "stack_size", size+1, 0)
        test_pkt = headerspace(format["length"]*2)
        test_pkt.add_hs(all_x)
        loop_origins = []
        st = time()
        loops = detect_loop(my_NTF,my_TTF, [19], reverse_map,test_pkt)
        for loop in loops:
            loop_origins.append(find_loop_original_header(my_NTF,my_TTF,loop))
        en = time()
        print "$$$$$$$$ time is %d"%(en-st)
        for i in range(len(loops)):
            print "---------------------"
            print "PATH: %s"%loop_path_to_str(loops[i],reverse_map)
            print "ORIGINATED BY:"
            for h in loop_origins[i]:
                print h
        print len(loops)
        result.append(en-st)
    results.append(result)
print results

#[[0.028717994689941406, 0.073533058166503906, 0.15058493614196777, 0.2507789134979248, 1.2491989135742188, 4.9717040061950684], [0.17177915573120117, 0.44383811950683594, 0.96145200729370117, 1.7296581268310547, 11.418015956878662, 89.984761953353882]]
# [[1.126323938369751, 2.4239110946655273, 5.1174418926239014, 9.6081268787384033, 49.723267078399658, 244.03375601768494]]
    
#[[0.011652946472167969, 1.4100630283355713, 11.390981912612915, 38.584887981414795, 48.99320101737976], [0.05034279823303223, 3.907602071762085, 29.489521980285645, 88.87462592124939, 95.55689311027527], [0.2591121196746826, 12.661466836929321, 75.13316297531128, 169.5317587852478, 394.3256688117981]]
        
        
    
    