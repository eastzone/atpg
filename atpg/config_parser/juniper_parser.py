'''
    <Juniper IOS parser. Generates Transfer Function Objects -- Part of Hassel>
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

Created on Mar 11, 2012

@author: James Hongyi Zeng
'''

from helper import *
from headerspace.tf import *
from headerspace.hs import *
from xml.etree.ElementTree import ElementTree
import re

class juniperRouter(object):
    '''
    classdocs
    '''
    PORT_ID_MULTIPLIER = 1
    INTERMEDIATE_PORT_TYPE_CONST = 1
    OUTPUT_PORT_TYPE_CONST = 2
    PORT_TYPE_MULTIPLIER = 10000
    SWITCH_ID_MULTIPLIER = 100000
    
    def __init__(self, switch_id):
        '''
        Constructor
        '''
        # for each acl number has a list of acl dictionary entries
        self.acl = {}
        # for each vlan holds the list of ports in its spanning tree
        self.vlan_ports = {}
        # for each port/vlan hold the ip address and subnet pair that is configured on it.
        self.port_subnets = {}
        # forwarding table
        self.fwd_table = []
        # arp and mac table
        self.arp_table = {}
        self.mac_table = {}
        # for each interface, we have (access-list#, in/out, file, line)
        self.acl_iface = {}
        # list of vlans configured on this switch
        self.config_vlans = []
        # list of ports configured on this switch
        self.config_ports = set()
        self.switch_id = switch_id
        self.port_to_id = {}
        self.hs_format = self.HS_FORMAT()
        self.replaced_vlan = 0
        
        # map ae-bundle name into the real logical interface
        self.ae_bundles = {}
        
    def set_replaced_vlan(self,vlan):
        self.replaced_vlan = vlan
        
    @staticmethod
    def HS_FORMAT():
        format = {}
        format["vlan_pos"] = 4
#        format["ip_src_pos"] = 2
        format["ip_dst_pos"] = 0
#        format["ip_proto_pos"] = 10
#        format["tcp_src_pos"] = 11
#        format["tcp_dst_pos"] = 13
#        format["tcp_ctrl_pos"] = 15
        format["vlan_len"] = 2
#        format["ip_src_len"] = 4
        format["ip_dst_len"] = 4
#        format["ip_proto_len"] = 1
#        format["tcp_src_len"] = 2
#        format["tcp_dst_len"] = 2
#        format["tcp_ctrl_len"] = 1
        format["length"] = 6
        return format
    
    def wc_to_parsed_string(self, byte_arr):
        fields = ["vlan","ip_src","ip_dst","ip_proto","tcp_src","tcp_dst","tcp_ctrl"]
        out_string = ""
        for field in fields:
            offset = self.hs_format["%s_pos"%field]
            len = self.hs_format["%s_len"%field]
            ba = bytearray()
            for i in range(0,len):
                ba.append(byte_arr[offset+i])
            out_string = "%s%s:%s, "%(out_string, field, byte_array_to_hs_string(ba))
        return out_string
            
    def set_field(self, arr, field, value, right_mask):
        '''
        Sets the field in byte array arr to value.
        @arr: the bytearray to set the field bits to value.
        @field: 'vlan', 'ip_src', 'ip_dst', 'ip_proto', 'tcp_src', 'tcp_dst', 'tcp_ctrl'
        @value: an integer number, of the width equal to field's width
        @right_mask: number of bits, from right that should be ignored when written to field.
        e.g. to have a /24 ip address, set mask to 8.
        '''
        b_array = int_to_byte_array(value,8*self.hs_format["%s_len"%field])
        start_pos = 2*self.hs_format["%s_pos"%field]
        for i in range(2*self.hs_format["%s_len"%field]):
            if right_mask <= 4*i:
                arr[start_pos + i] = b_array[i]
            elif (right_mask > 4*i and right_mask < 4*i + 4):
                shft = right_mask % 4;
                rm = (0xff << 2*shft) & 0xff
                lm = ~rm & 0xff
                arr[start_pos + i] = (b_array[i] & rm) | (arr[start_pos + i] & lm) 
        
    def set_switch_id(self, switch_id):
        self.switch_id = switch_id
        
    def get_switch_id(self):
        return self.switch_id
        
    def set_hs_format(self, hs_format):
        self.hs_format = hs_format
        
    @staticmethod
    def make_acl_dictionary_entry():
        entry = {}
        entry["action"] = True
        entry["src_ip"] = 0
        entry["src_ip_mask"] = 0xffffffff
        entry["dst_ip"] = 0
        entry["dst_ip_mask"] = 0xffffffff
        entry["ip_protocol"] = 0 # Note: this is used instead of any ip protocol
        entry["transport_src_begin"] = 0
        entry["transport_src_end"] = 0xffff
        entry["transport_dst_begin"] = 0
        entry["transport_dst_end"] = 0xffff
        entry["tcp_ctrl_begin"] = 0
        entry["tcp_ctrl_end"] = 0xff
        return entry
    
    def acl_dictionary_entry_to_bytearray(self,dic_entry):
        result = []
        result.append(byte_array_get_all_x(self.hs_format["length"]*2))
        if (dic_entry["ip_protocol"] != 0):
            self.set_field(result[0], "ip_proto", dic_entry["ip_protocol"], 0)
        self.set_field(result[0], "ip_src", dic_entry["src_ip"], find_num_mask_bits_right_mak(dic_entry["src_ip_mask"]))
        self.set_field(result[0], "ip_dst", dic_entry["dst_ip"], find_num_mask_bits_right_mak(dic_entry["dst_ip_mask"]))
        tp_src_matches = range_to_wildcard(dic_entry["transport_src_begin"],dic_entry["transport_src_end"],16)
        tmp = []
        for tp_src_match in tp_src_matches:
            b = bytearray(result[0])
            self.set_field(b, "tcp_src", tp_src_match[0], tp_src_match[1])
            tmp.append(b)
        result = tmp
        tp_dst_matches = range_to_wildcard(dic_entry["transport_dst_begin"],dic_entry["transport_dst_end"],16)
        tmp = []
        for tp_dst_match in tp_dst_matches:     
            for r in result:
                b = bytearray(r)
                self.set_field(b, "tcp_dst", tp_dst_match[0], tp_dst_match[1])
                tmp.append(b)
        result = tmp
        tp_ctrl_matches = range_to_wildcard(dic_entry["tcp_ctrl_begin"],dic_entry["tcp_ctrl_end"],8)
        tmp = []
        for tp_ctrl_matche in tp_ctrl_matches:     
            for r in result:
                b = bytearray(r)
                self.set_field(b, "tcp_ctrl", tp_ctrl_matche[0], tp_ctrl_matche[1])
                tmp.append(b)
        result = tmp
        return result
    
    @staticmethod
    def acl_dictionary_entry_to_string(entry):
        output = ""
        if entry["action"]:
            output = "permit "
        else:
            output = "deny "
        output = output + "ip protocol: %d -- src ip: %s -- src ip mask: %s -- src transport port: %d-%d -- dst ip: %s -- dst ip mask: %s -- dst transport port: %d-%d"%(entry["ip_protocol"],
        int_to_dotted_ip(entry["src_ip"]),int_to_dotted_ip(entry["src_ip_mask"]),entry["transport_src_begin"],entry["transport_src_end"],
        int_to_dotted_ip(entry["dst_ip"]),int_to_dotted_ip(entry["dst_ip_mask"]),entry["transport_dst_begin"],entry["transport_dst_end"],
         )
        return output;
            
    
    @staticmethod
    def get_protocol_number(proto_name):
        dict = {"ah":51, "eigrp":88, "esp":50, "gre":47, "icmp":1, "igmp":2, "igrp":9,
                "ip": 0, "ipinip":94, "nos":4, "ospf":89, "tcp":6, "udp":17}
        if proto_name in dict.keys():
            return dict[proto_name]
        else:
            try:
                num = int(proto_name)
                return num
            except Exception as e:
                return None
        
    @staticmethod
    def get_udp_port_number(port_name):
        dict = {"biff": 512, "bootpc":68, "bootps":69, "discard":9, "domain":53, "dnsix":90,
                "echo":7, "mobile-ip":434, "nameserver":42, "netbios-dgm":137, "netbios-ns":138,
                "ntp":123, "rip":520, "snmp":161, "snmptrap":162, "sunrpc":111, "syslog":514,
                "tacacs-ds":49, "talk":517, "tftp":69, "time":37, "who":513, "xdmcp":177}
        if port_name in dict.keys():
            return dict[port_name]
        else:
            try:
                num = int(port_name)
                return num
            except Exception as e:
                return None
        
    @staticmethod
    def get_tcp_port_number(port_name):
        dict = {"bgp":179, "chargen":19, "daytime":13, "discard":9, "domain":53, "echo":7,
                "finger":79, "ftp":21, "ftp-data":20, "gopher":70, "hostname":101,
                "irc":194, "klogin":543, "kshell":544, "lpd":515, "nntp":119, "pop2":109,
                "pop3":110, "smtp":25, "sunrpc":111, "syslog":514, "tacacs-ds":65, "talk":517,
                "telnet":23, "time": 37, "uucp":540, "whois":43, "www":80}
        if port_name in dict.keys():
            return dict[port_name]
        else:
            try:
                num = int(port_name)
                return num
            except Exception as e:
                return None
            
    @staticmethod
    def get_transport_port_number(port):
        try:
            num = int(port)
            return num
        except Exception as e:
            return None
        
    @staticmethod
    def get_ethernet_port_name(port):
        result = ""
        reminder = ""
        if port.lower().startswith("tengigabitethernet"):
            result = "te"
            reminder = port[len("tengigabitethernet"):]
        elif port.lower().startswith("gigabitethernet"):
            result = "gi"
            reminder = port[len("gigabitethernet"):]
        elif port.lower().startswith("fastethernet"):
            result = "fa"
            reminder = port[len("fastethernet"):]
        else:
            result = port
        return "%s%s"%(result, reminder)
                
    def parse_access_list_entry(self, entry, line_counter):
        
        def parse_ip(lst):
            result = {}
            if lst[0].lower() == "any":
                result["ip"] = 0
                result["ip_mask"] = 0xffffffff
                lst.pop(0)
            elif lst[0].lower() == "host":
                result["ip"] = dotted_ip_to_int(lst[1])
                result["ip_mask"] = 0
                lst.pop(0)
                lst.pop(0)
            elif is_ip_address(lst[0]):
                result["ip"] = dotted_ip_to_int(lst[0])
                if len(lst) > 1 and is_ip_address(lst[1]):
                    result["ip_mask"] = dotted_ip_to_int(lst[1])
                    lst.pop(0)
                    lst.pop(0)
                else:
                    result["ip_mask"] = 0
                    lst.pop(0)
            return result
        
        def parse_port(lst, proto):
            result = {}
            proto_reader = None
            
            if proto == 6:
                proto_reader = self.get_tcp_port_number
            elif proto == 17:
                proto_reader = self.get_udp_port_number
            else:
                proto_reader = self.get_transport_port_number
                
            if lst[0] == "eq":
                lst.pop(0)
                p = proto_reader(lst.pop(0))
                if p != None:
                    result["port_begin"] = p
                    result["port_end"] = p
            elif lst[0] == "gt":
                lst.pop(0)
                p = proto_reader(lst.pop(0))
                if p != None:
                    result["port_begin"] = p + 1
                    result["port_end"] = 0xffff
            elif lst[0] == "range":
                lst.pop(0)
                p1 = proto_reader(lst.pop(0))
                p2 = proto_reader(lst.pop(0))
                if p1 != None and p2 != None:
                    result["port_begin"] = p1
                    result["port_end"] = p2
                    
            return result
        
        tokens = entry.split()
        tokens.pop(0)
        acl_number = tokens.pop(0)
        acl_number_int = int(acl_number)
        
        action = tokens.pop(0)
        if action.lower() == "permit" or action.lower() == "deny":
            if not acl_number in self.acl.keys():
                self.acl[acl_number] = []
            
            new_entry = self.make_acl_dictionary_entry()
            new_entry["action"] = (action.lower() == "permit")
            
            # standard access-list entry
            if acl_number_int < 100:
                new_entry["ip_protocol"] = 0
                new_ip = parse_ip(tokens)
                if (len(new_ip.keys()) > 0):
                    new_entry["src_ip"] = new_ip["ip"]
                    new_entry["src_ip_mask"] = new_ip["ip_mask"]
                    self.acl[acl_number].append(new_entry)
                    #print self.acl_dictionary_entry_to_string(new_entry)
                    return True
                else:
                    return False
            
            # extended access-list entry
            else:
                if self.get_protocol_number(tokens[0]) != None:
                    new_entry["ip_protocol"] = self.get_protocol_number(self.get_protocol_number(tokens.pop(0)))
                elif is_ip_address(tokens[0]):
                    new_entry["ip_protocol"] = 0
                else:
                    return False

                # src ip address and ip mask
                new_ip = parse_ip(tokens)
                if (len(new_ip.keys()) > 0):
                    new_entry["src_ip"] = new_ip["ip"]
                    new_entry["src_ip_mask"] = new_ip["ip_mask"]

                # src transport port number
                if len(tokens) > 0:
                    new_ports = parse_port(tokens, new_entry["ip_protocol"])
                    if len(new_ports.keys()) > 0:
                        new_entry["transport_src_begin"] = new_ports["port_begin"]
                        new_entry["transport_src_end"] = new_ports["port_end"]
                    
                # dst ip address and ip mask    
                if len(tokens) > 0:
                    new_ip = parse_ip(tokens)
                    if (len(new_ip.keys()) > 0):
                        new_entry["dst_ip"] = new_ip["ip"]
                        new_entry["dst_ip_mask"] = new_ip["ip_mask"]
                        
                # dst transport port number
                if len(tokens) > 0:
                    new_ports = parse_port(tokens, new_entry["ip_protocol"])
                    if len(new_ports.keys()) > 0:
                        new_entry["transport_dst_begin"] = new_ports["port_begin"]
                        new_entry["transport_dst_end"] = new_ports["port_end"]
                        
                # tcp control bits
                if len(tokens) > 0:
                    t = tokens.pop(0)
                    if t == "established":
                        new_entry["tcp_ctrl_begin"] = 0x80
                        new_entry["tcp_ctrl_end"] = 0xff
                        
                new_entry["line"] = [line_counter];
                self.acl[acl_number].append(new_entry)
                #print self.acl_dictionary_entry_to_string(new_entry)
                return True
   
    def generate_port_ids(self, additional_ports):
        '''
        looks at all the ports that has FWD mode for any vlan
        or appear as forwarding port of a forwarding rule, and assign a unique ID
        to them based on switch_id and a random port id.
        addition_ports will also be considered and assigned a unqie ID. This is for
        ports that exist on the switch but are not part of any vlan or output of 
        forwarding rules.
        '''
        print "=== Generating port IDs ==="
        s = set(additional_ports)
        for elem in self.config_ports:
            s.add(elem)
        suffix = 1
        for p in s:
            id = self.switch_id * self.SWITCH_ID_MULTIPLIER + suffix * self.PORT_ID_MULTIPLIER
            self.port_to_id[p] = id
            suffix += 1
        #print self.port_to_id
        print "=== DONE generating port IDs ==="
        
    def get_port_id(self,port_name):
        if port_name in self.port_to_id.keys():
            return self.port_to_id[port_name]
        else:
            return None
        
    def optimize_forwarding_table(self):
        print "=== Compressing forwarding table ==="
        print " * Originally has %d ip fwd entries * "%len(self.fwd_table)

        n = compress_ip_list(self.fwd_table)
        print " * After compression has %d ip fwd entries * "%len(n)
        self.fwd_table = n

        '''
        for elem in n:
            str = "%s/%d: action: %s compressing: "%(int_to_dotted_ip(elem[0]) , elem[1], elem[2])
            for e in elem[3]:
                str = str + int_to_dotted_ip(e[0]) + "/%d, "%e[1]
            print str
        '''
        print "=== DONE forwarding table compression ==="
        
    def generate_transfer_function(self, tf): 
        '''
        After calling read_config_file(), read_spanning_tree_file() and read_route_file(), 
        generate_port_ids(), and optionally optimize_forwarding_table(),
        this method may be called to generate transfer function rules corresponding to this box.
        The rules will be added to transfer function tf passed to the function.
        ''' 
        print "=== Generating Transfer Function ==="
        # generate the input part of tranfer function from in_port to fwd_port
        # and output part from intermedite ports to output ports
        print " * Generating ACL transfer function * " 
        for acl in self.acl_iface.keys():
            if acl not in self.acl.keys():
                continue
            for acl_instance in self.acl_iface[acl]:
                file_name = acl_instance[3]
                specified_ports = []
                vlan = acl_instance[2]
                if acl_instance[0].startswith("vlan"):
                    for p in self.vlan_ports[acl_instance[0]]:
                        specified_ports.append(self.port_to_id[p])
                else:
                    specified_ports = [self.port_to_id(acl_instance[0])]
                for acl_dic_entry in self.acl[acl]:
                    matches = self.acl_dictionary_entry_to_bytearray(acl_dic_entry)
                    lines = acl_instance[4]
                    lines.extend(acl_dic_entry["line"])
                    # in acl entry
                    if acl_instance[1] == "in":
                        in_ports = specified_ports
                        out_ports = []
                        if (acl_dic_entry["action"]):
                            out_ports = [self.switch_id * self.SWITCH_ID_MULTIPLIER]
                        for match in matches:
                            self.set_field(match, "vlan", vlan, 0)
                            next_rule = TF.create_standard_rule(in_ports, match, out_ports, None, None, file_name, lines)
                            tf.add_fwd_rule(next_rule)
                    # out acl entry
                    else:
                        for match in matches:
                            self.set_field(match, "vlan", vlan, 0)
                            if (not acl_dic_entry["action"]):
                                out_ports = []
                                in_ports = []
                                for port in specified_ports:
                                    in_ports.append(port+self.PORT_TYPE_MULTIPLIER * self.INTERMEDIATE_PORT_TYPE_CONST)
                                next_rule = TF.create_standard_rule(in_ports, match, out_ports, None, None, file_name, lines)
                                tf.add_fwd_rule(next_rule)
                            else:
                                for port in specified_ports:
                                    in_ports = [port+self.PORT_TYPE_MULTIPLIER * self.INTERMEDIATE_PORT_TYPE_CONST]
                                    out_ports = [port+self.PORT_TYPE_MULTIPLIER * self.OUTPUT_PORT_TYPE_CONST]
                                    next_rule = TF.create_standard_rule(in_ports, match, out_ports, None, None, file_name, lines)
                                    tf.add_fwd_rule(next_rule)
        
        # default rule for all vlans configured on this switch and un-vlan-tagged ports
        intermediate_port = [self.switch_id * self.SWITCH_ID_MULTIPLIER]
        for cnf_vlan in self.config_vlans:
            if self.vlan_ports.has_key("vlan%d"%cnf_vlan):
                match = byte_array_get_all_x(self.hs_format["length"]*2)
                self.set_field(match, "vlan", cnf_vlan, 0)
                all_in_ports = []
                for port in self.vlan_ports["vlan%d"%cnf_vlan]:
                    all_in_ports.append(self.port_to_id[port])
                def_rule = TF.create_standard_rule(all_in_ports, match, intermediate_port, None, None, "", [])
                tf.add_fwd_rule(def_rule)
        # ... un-vlan-tagged port
        all_in_ports = []
        for port in self.port_to_id.keys():
            if port != "self":
                all_in_ports.append(self.port_to_id[port])
#        match = byte_array_get_all_x(self.hs_format["length"]*2)
#        self.set_field(match, "vlan", 0, 0)
#        def_rule = TF.create_standard_rule(all_in_ports, match, intermediate_port, None, None, "", [])
#        tf.add_fwd_rule(def_rule) 
        
        # default rule from intermediate port to outut port
        match = byte_array_get_all_x(self.hs_format["length"]*2)
        for port_id in all_in_ports:
            before_out_port = [port_id+self.PORT_TYPE_MULTIPLIER * self.INTERMEDIATE_PORT_TYPE_CONST]
            after_out_port = [port_id+self.PORT_TYPE_MULTIPLIER * self.OUTPUT_PORT_TYPE_CONST]
            def_rule = TF.create_standard_rule(before_out_port, match, after_out_port , None, None, "", [])
            # James: No default output ACL
            #tf.add_fwd_rule(def_rule)
        
        ##################################
#        print " * Generating VLAN forwarding transfer function... * "
#        # generate VLAN forwarding entries
#        for vlan_num in self.port_subnets.keys():
#            #James: if VLAN has only one port, don't worry about forwarding!
#            vlan = int(vlan_num)
#            if "vlan%d"%vlan in self.vlan_ports.keys():
#                if(len(self.vlan_ports["vlan%d"%vlan]) == 1):
#                    #print "Found orphant VLAN %s on port %s" %(vlan_num, self.vlan_ports["vlan%d"%int(vlan_num)])
#                    continue
#            #end of James' magic :P
#            for (ip_addr,subnet_mask,file_name,lines,port) in self.port_subnets[vlan_num]:
#                match = byte_array_get_all_x(self.hs_format["length"]*2)
#                in_port = [self.switch_id * self.SWITCH_ID_MULTIPLIER]
#                vlan = int(vlan_num)
#                out_ports = []
#                if ip_addr == None:
#                    self.set_field(match, "vlan", vlan, 0)
#                else:
#                    self.set_field(match, "ip_dst", ip_addr, subnet_mask)
#                    self.set_field(match, "vlan", vlan, 0)
#                if not port.startswith("vlan"):
#                    out_ports.append(self.port_to_id[port]+self.PORT_TYPE_MULTIPLIER * self.INTERMEDIATE_PORT_TYPE_CONST)
#                elif "vlan%d"%vlan in self.vlan_ports.keys():
#                    port_list = self.vlan_ports["vlan%d"%vlan]
#                    for p in port_list:
#                        out_ports.append(self.port_to_id[p]+self.PORT_TYPE_MULTIPLIER * self.INTERMEDIATE_PORT_TYPE_CONST)
#                tf_rule = TF.create_standard_rule(in_port, match, out_ports, None, None,file_name,lines)
#                tf.add_fwd_rule(tf_rule)
                   
        ###################################
        print " * Generating IP forwarding transfer function... * "  
        self.fwd_table.sort(key=lambda fwd_rule: fwd_rule[1], reverse=True)
   
        # generate the forwarding part of transfer fucntion, from the fwd_prt, to pre-output ports
        for subnet in range(32,-1,-1):
            
            while [] in self.fwd_table:
                self.fwd_table.remove([])
            
            for fwd_rule in self.fwd_table:
                index = self.fwd_table.index(fwd_rule)
                
                if fwd_rule[1] != subnet:
                    break
                
                else:
                    
                    #in -ports and match bytearray
                    match = byte_array_get_all_x(self.hs_format["length"]*2)
                    self.set_field(match, "ip_dst", int(fwd_rule[0]), 32-subnet)
                    in_port = [self.switch_id * self.SWITCH_ID_MULTIPLIER]
                    # mask, rewrite 
                    mask = byte_array_get_all_one(self.hs_format["length"]*2)
                    rewrite = byte_array_get_all_zero(self.hs_format["length"]*2)
                    # find out the file-line it represents:
                    lines = []
                    file_name = ""
                    if len(fwd_rule) == 4:
                        for c_rule in fwd_rule[3]:
                            file_name = c_rule[3]
                            lines.extend(c_rule[4])
                    else:
                        file_name = fwd_rule[3]
                        lines.extend(fwd_rule[4])
                    # set up out_ports
                    out_ports = []
                    
                    # fwd_rule[2] is a list, thanks to LAG
                    for output_port in fwd_rule[2]:
                        vlan = 0
                        m = re.split('\.',output_port)
                        # drop rules:
                        if output_port == "self":
                            self_rule = TF.create_standard_rule(in_port,match,[],None,None,file_name,lines)
                            tf.add_fwd_rule(self_rule)
                        # non drop rules
                        else:
                            # sub-ports: port.vlan
                            if len(m) > 1:
                                if m[0] in self.port_to_id.keys():
                                    out_ports.append(self.port_to_id[m[0]]+self.PORT_TYPE_MULTIPLIER * self.OUTPUT_PORT_TYPE_CONST)
                                    vlan = int(m[1])
                                else:
                                    print "ERROR: unrecognized port %s"%m[0]
                                    return -1
                            # vlan outputs
                            elif output_port.startswith('vlan'):
                                if output_port in self.vlan_ports.keys():
                                    port_list = self.vlan_ports[output_port]
                                    for p in port_list:
                                        out_ports.append(self.port_to_id[p]+self.PORT_TYPE_MULTIPLIER * self.OUTPUT_PORT_TYPE_CONST)
                                    vlan = int(output_port[4:])
                                else:
                                    print "ERROR: unrecognized vlan %s"%output_port
                                    return -1
                            # physical ports - no vlan taging
                            else:
                                if output_port in self.port_to_id.keys():
                                    out_ports.append(self.port_to_id[output_port] + self.PORT_TYPE_MULTIPLIER * self.OUTPUT_PORT_TYPE_CONST)
                                    vlan = 0
                                else:
                                    print "ERROR: unrecognized port %s"%output_port
                                    return -1
                        
                        # now set the fields
                        self.set_field(mask, 'vlan', 0, 0)
                        self.set_field(rewrite, 'vlan', vlan, 0)
                        tf_rule = TF.create_standard_rule(in_port, match, out_ports, mask, rewrite,file_name,lines)
                        tf.add_rewrite_rule_no_influence(tf_rule) 
                
                self.fwd_table[index] = []
                #Invalidate fwd_rule      
        print "=== Successfully Generated Transfer function ==="
        #print tf
        return 0    
    
    def read_route_file(self, file_path):
        print "=== Reading Juniper Router FIB File ==="
        f = open(file_path,'r')
        line_counter = 0

        while True:
            # Garbage in the front
            line = f.next()
            line_counter += 1
            if line.startswith("Destination"):
                while True:
                    line = f.next()
                    line_counter += 1
                    tokens = line.split()
                    if len(tokens) == 6 and tokens[3]=="indr":
                        ip_subnet = dotted_subnet_to_int(tokens[0])
                        # Interface in the next line
                        line = f.next()
                        line_counter += 1
                        port = line.split()[-1]
                        
                        if port in self.ae_bundles.keys():
                            ports_new = self.ae_bundles[port]
                            self.fwd_table.append([ip_subnet[0],ip_subnet[1],ports_new,port+file_path,[line_counter]])
                        else:
                            self.fwd_table.append([ip_subnet[0],ip_subnet[1],[port],file_path,[line_counter]])
                    elif len(tokens) == 8:
                        ip_subnet = dotted_subnet_to_int(tokens[0])
                        port = tokens[-1]
                        if port in self.ae_bundles.keys():
                            ports_new = self.ae_bundles[port]
                            self.fwd_table.append([ip_subnet[0],ip_subnet[1],ports_new,port+file_path,[line_counter]])
                        else:
                            self.fwd_table.append([ip_subnet[0],ip_subnet[1],[port],file_path,[line_counter]])
                    elif line.startswith("Destination"):
                        # Don't parse other tables
                        f.close()
                        return

    def read_config_file(self, file_path, router_name, ns = "{http://xml.juniper.net/junos/10.4R9/junos-interface}"):
        print "=== Reading Juniper Router Interface File ==="       
        tree = ElementTree(file=file_path)
        
        routers = tree.findall("router")
        for router in routers:
            if router.get("name") != router_name:
                continue
            physical_interfaces = router.findall("{0}interface-information/{0}physical-interface".format(ns))
            
            for physical_interface in physical_interfaces:
                physical_interface_name = physical_interface.find("{0}name".format(ns)).text
                physical_interface_name = physical_interface_name.replace(":","-")
                if physical_interface_name.startswith("ae"):
                    # Aggregated interface. We don't need to record it here
                    continue
                
                logical_interfaces = physical_interface.findall("{0}logical-interface".format(ns))
                
                if logical_interfaces != []:
                    # The port is up
                    self.config_ports.add(physical_interface_name)
                
                for logical_interface in logical_interfaces:
                    logical_interface_name = logical_interface.find("{0}name".format(ns)).text
                    logical_interface_name = logical_interface_name.replace(":","-")
                    
                    addresses = logical_interface.findall("{0}address-family".format(ns))
                    
                    for address in addresses:
                        address_family = address.find("{0}address-family-name".format(ns)).text
                        
                        if address_family == "aenet":
                            # This is part of an aggregate ethernet
                            ae_bundle_name = address.find("{0}ae-bundle-name".format(ns)).text
                            # Record the real interface name
                            # James: Hack for now to reduce the run-time. we don't need to multicast...
                            self.ae_bundles[ae_bundle_name] = [logical_interface_name]
                            #if ae_bundle_name not in self.ae_bundles.keys():
                            #    self.ae_bundles[ae_bundle_name] = [logical_interface_name]
                            #else:
                            #    self.ae_bundles[ae_bundle_name].append(logical_interface_name)
                        elif address_family != "inet":
                            # Only process IPv4 Port
                            continue
                    
                        vlan = int(re.split('\.',logical_interface_name)[1])
                        
                        if vlan >= 0 and vlan < 4096:   
                            if vlan not in self.config_vlans:
                                self.config_vlans.append(vlan)
                            
                            if not "vlan%d"%vlan in self.vlan_ports.keys():
                                self.vlan_ports["vlan%d"%vlan] = []
                                
                            self.vlan_ports["vlan%d"%vlan].append(physical_interface_name)  
                            
                            if "%d"%vlan not in self.port_subnets.keys():
                                self.port_subnets["%d"%vlan] = []  
                                
                            ip_address = address.find("{0}interface-address/{0}ifa-local".format(ns))        
                            subnet_address = address.find("{0}interface-address/{0}ifa-destination".format(ns))
                                
                            if ip_address==None or subnet_address==None:
                                continue
                               
                            
                            ip_int = dotted_ip_to_int(ip_address.text)
                            subnet_mask = re.split("/", subnet_address.text)
                            if len(subnet_mask) == 1:
                                mask_int = 32
                            else:
                                mask_int = int(subnet_mask[1])
                            self.port_subnets["%d"%vlan].append((ip_int, 32-mask_int, file_path, [], physical_interface_name))           
