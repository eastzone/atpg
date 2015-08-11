'''
    <Cisco IOS parser. Generates Transfer Function Objects -- Part of HSA Library>
Created on May 11, 2011

@author: Peyman Kazemian
@author: James Hongyi Zeng
'''
from helper import *
from headerspace.tf import *
from headerspace.hs import *
import re

class ciscoRouter(object):
    '''
    Cisco router parser.
    The generated transfer function will have three sub-layers: 
    1) from input port to fwd port: the packet will go through input acl, and vlan untag process
    2) from fwd port to pre-output port: the forwarding table will find output port. but the output
    filter has not been applied yet.
    3) from pre-output port to output port: this is where output acl filter is being done.
    So in order to see the ultimate faith of packet, we need to apply the tf.T() 3 consequative times.
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
        # for each access-list#, we have (interface, in/out, vlan, file, line)
        self.acl_iface = {}
        # list of vlans configured on this switch
        self.config_vlans = []
        # list of ports configured on this switch
        self.config_ports = set()
        #trunk or access mode of all physical ports
        self.vlan_mode = {}
        self.switch_id = switch_id
        self.port_to_id = {}
        self.hs_format = self.HS_FORMAT()
        self.replaced_vlan = 0
        self.def_vlan = 1
        
    def set_default_vlan(self,vlan):
        self.def_vlan = vlan
        
    def set_replaced_vlan(self,vlan):
        self.replaced_vlan = vlan
        
    @staticmethod
    def HS_FORMAT():
        format = {}
        format["vlan_pos"] = 0
        format["ip_src_pos"] = 2
        format["ip_dst_pos"] = 6
        format["ip_proto_pos"] = 10
        format["transport_src_pos"] = 11
        format["transport_dst_pos"] = 13
        format["transport_ctrl_pos"] = 15
        format["vlan_len"] = 2
        format["ip_src_len"] = 4
        format["ip_dst_len"] = 4
        format["ip_proto_len"] = 1
        format["transport_src_len"] = 2
        format["transport_dst_len"] = 2
        format["transport_ctrl_len"] = 1
        format["length"] = 16
        return format
    
    def wc_to_parsed_string(self, byte_arr):
        fields = ["vlan","ip_src","ip_dst","ip_proto","transport_src","transport_dst","transport_ctrl"]
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
        @field: 'vlan', 'ip_src', 'ip_dst', 'ip_proto', 'transport_src', 'transport_dst', 'transport_ctrl'
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
        
    def set_witch_id(self, switch_id):
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
        entry["transport_ctrl_begin"] = 0
        entry["transport_ctrl_end"] = 0xff
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
            self.set_field(b, "transport_src", tp_src_match[0], tp_src_match[1])
            tmp.append(b)
        result = tmp
        tp_dst_matches = range_to_wildcard(dic_entry["transport_dst_begin"],dic_entry["transport_dst_end"],16)
        tmp = []
        for tp_dst_match in tp_dst_matches:     
            for r in result:
                b = bytearray(r)
                self.set_field(b, "transport_dst", tp_dst_match[0], tp_dst_match[1])
                tmp.append(b)
        result = tmp
        tp_ctrl_matches = range_to_wildcard(dic_entry["transport_ctrl_begin"],dic_entry["transport_ctrl_end"],8)
        tmp = []
        for tp_ctrl_matche in tp_ctrl_matches:     
            for r in result:
                b = bytearray(r)
                self.set_field(b, "transport_ctrl", tp_ctrl_matche[0], tp_ctrl_matche[1])
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
    def get_transport_port_number(port_name):
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
                proto_reader = ciscoRouter.get_transport_port_number
            elif proto == 17:
                proto_reader = ciscoRouter.get_udp_port_number
            else:
                proto_reader = ciscoRouter.get_transport_port_number
                
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
                        
                # transport control bits
                if len(tokens) > 0:
                    t = tokens.pop(0)
                    if t == "established":
                        new_entry["transport_ctrl_begin"] = 0x80
                        new_entry["transport_ctrl_end"] = 0xff
                        
                new_entry["line"] = [line_counter];
                self.acl[acl_number].append(new_entry)
                #print self.acl_dictionary_entry_to_string(new_entry)
                return True
                
    def read_config_file(self, file_path):
        '''
        Reads in the CISCO router config file and extracts access list entries and the ports/vlans 
        they apply to. 
        '''
        print "=== Reading Cisco Router Config File ==="
        f = open(file_path,'r')
        last_iface = ""
        last_vlan = None
        line_counter = 0;
        for line in f:
            line = line.strip()
            # read an access-list line 
            if line.startswith("access-list"):
                self.parse_access_list_entry(line,line_counter)
            elif line.startswith("interface"):
                tokens = line.split()
                last_iface = ciscoRouter.get_ethernet_port_name(tokens[1].lower())
                if last_iface.startswith("vlan"):
                    last_vlan = int(last_iface[4:])
                    self.config_vlans.append(last_vlan)
                else:
                    parts = re.split('\.',last_iface)
                    if len(parts) > 1:
                        last_vlan = int(parts[1])
                        last_iface = parts[0]
                        self.config_vlans.append(last_vlan)
                        if not "vlan%d"%last_vlan in self.vlan_ports.keys():
                            self.vlan_ports["vlan%d"%last_vlan] = []
                        self.vlan_ports["vlan%d"%last_vlan].append(last_iface)
                    else:
                        last_vlan = None
                    self.config_ports.add(last_iface)
                if last_vlan != None and "%d"%last_vlan not in self.port_subnets.keys():
                    self.port_subnets["%d"%last_vlan] = []
            elif line.startswith("switchport mode"):
                tokens = line.split()
                vlan_mode = tokens[2]
                self.vlan_mode[last_iface] = vlan_mode
            elif line.startswith("ip access-group"):
                tokens = line.split()
                if not tokens[2] in self.acl_iface.keys():
                    self.acl_iface[tokens[2]] = []
                self.acl_iface[tokens[2]].append((last_iface,tokens[3],last_vlan,file_path,[line_counter]))
            elif line.startswith("no ip address"):
                if last_vlan != None:
                    self.port_subnets["%d"%last_vlan].append((None,None,file_path,[line_counter],last_iface))
            elif line.startswith("ip address"):
                tokens = line.split()
                if last_vlan != None:
                    ip_int = dotted_ip_to_int(tokens[2])
                    mask_int = find_num_mask_bits_left_mak(dotted_ip_to_int(tokens[3]))
                    self.port_subnets["%d"%last_vlan].append((ip_int, 32-mask_int, file_path, [line_counter], last_iface))
            elif line.startswith("shutdown") and last_vlan != None:
                self.config_vlans.remove(last_vlan)
                del self.port_subnets["%d"%last_vlan]
            line_counter = line_counter + 1
        f.close()
        #print self.port_subnets
        #print self.acl
        #print self.acl_iface
        print "=== DONE Reading Cisco Router Config File ==="
                
    def read_spanning_tree_file(self, file_path):
        '''
        Reads in, the CISCO router "sh spanning-tree" output and extracts the list of ports that
        are in FWD mode for each vlan.
        '''
        print "=== Reading Cisco Router Spanning Tree File ==="
        current_vlan = 0
        f = open(file_path,'r')
        for line in f:
            tokens = line.split()
            if len(tokens) == 0:
                continue
            if line.startswith("VLAN"):
                if len(tokens) == 1:
                    current_vlan = "vlan%d"%int(tokens[0][4:])
                    self.vlan_ports[current_vlan] = []
            elif (("FWD" in tokens) or ("fwd" in tokens)):
                self.vlan_ports[current_vlan].append(tokens[0].lower())
        f.close()
        #print self.vlan_ports
        print "=== DONE Reading Cisco Router Spanning Tree File ==="
        
    def read_arp_table_file(self, file_path):
        '''
        Reads in CISCO router arp table - sh arp
        '''
        print "=== Reading Cisco Router ARP Table File ==="
        f = open(file_path,'r')
        for line in f:
            tokens = line.split()
            if (len(tokens) >= 6 and tokens[4].lower() == "arpa"):
                self.arp_table[tokens[1]] = (tokens[3].lower(),tokens[5].lower())
        f.close()
        print "=== DONE Reading Cisco Router ARP Table File ==="
                    
    def read_mac_table_file(self, file_path):
        '''
        Reads in CISCO mac address table - sh mac-address-table
        '''
        print "=== Reading Cisco Mac Address Table File ==="
        f = open(file_path,'r')
        seen_star = False
        ports = []
        mac = ""
        for line in f:
            tokens = line.split()
            if (line.startswith("*")):
                if (seen_star):
                    self.mac_table[mac] = ports
                    ports = []
                mac = "vlan%s,%s"%(tokens[1],tokens[2])
                seen_star = True
                if (len(tokens) >= 7):
                    ports.extend(tokens[6].split(","))
            elif (seen_star):
                ports.extend(tokens[0].split(","))
        self.mac_table[mac] = ports
        print "=== DONE Reading Cisco Mac Address Table File ==="
                    
    def read_route_file(self, file_path):
        '''
        Reads in the CISCO router "sh ip cef" output and extracts the forwarding table entries.
        '''            
        print "=== Reading Cisco Router IP CEF File ==="
        f = open(file_path,'r')
        port = ""
        line_counter = 0;
        for line in f:
            tokens = line.split()
            if len(tokens) == 0:
                continue
            if is_ip_subnet(tokens[0]):
                ip_subnet = dotted_subnet_to_int(tokens[0])
                if len(tokens) > 2:
                    port = ciscoRouter.get_ethernet_port_name(tokens[2])
                    # next hop is a vlan, but also we know the ip adress. in this case we should find out which vlan port has that ip address
                    if port.lower().startswith("vlan") and is_ip_address(tokens[1]):
                        # look up next hop IP address in arp table to find the mac address and output port
                        if (tokens[1] in self.arp_table.keys()):
                            (mac,vln) = self.arp_table[tokens[1]]
                            # if next hop output port is a vlan, look it up in mac table
                            if vln.startswith("vlan"):
                                vm_key = "%s,%s"%(vln,mac)
                                # if mac-address-table for that vlan has the mac address, find out the port
                                if vm_key in self.mac_table.keys():
                                    resolved_port = self.mac_table[vm_key][0]
                                    vlan_num = int(vln[4:])
                                    port = "%s.%d"%(ciscoRouter.get_ethernet_port_name(resolved_port),vlan_num)
                            # if next hop output port is not vlan, use it       
                            else:
                                port = ciscoRouter.get_ethernet_port_name(vln)
                    # next hop is an attached vlan  
                    elif port.lower().startswith("vlan"):
                        vlan = int(port[4:])
                    else:
                        parts = re.split('\.',port)
                        if len(parts) > 1 and self.replaced_vlan != 0:
                            port = "%s.%d"%(parts[0],self.replaced_vlan)
                            vlan = self.replaced_vlan
                        elif len(parts) > 1:
                            vlan = int(parts[1])
                else:
                    port = "self"
                    
                if port.lower().startswith("loopback") or port.lower().startswith("null") or tokens[1].lower().startswith("drop"):
                    port = "self"
                    
                    
                self.fwd_table.append([ip_subnet[0],ip_subnet[1],port.lower(),file_path,[line_counter]])
            line_counter = line_counter + 1
        f.close()
        #print self.fwd_table
        print "=== DONE Reading Cisco Router IP CEF File ==="
    
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
        for vlan in self.vlan_ports.keys():
            for elem in self.vlan_ports[vlan]:
                s.add(elem)
        suffix = 1
        for p in s:
            id = self.switch_id * self.SWITCH_ID_MULTIPLIER + suffix * self.PORT_ID_MULTIPLIER
            self.port_to_id[p] = id
            suffix += 1
        #print self.port_to_id
        print "=== DONE generating port IDs ==="
        
    def generate_port_ids_only_for_output_ports(self):
        s = set()
        for fwd_rule in self.fwd_table:
            m = re.split('\.',fwd_rule[2])
            if len(m) > 1:
                s.add(m[0])
            elif fwd_rule[2].startswith('vlan'):
                if fwd_rule[2] in self.vlan_ports.keys():
                    port_list = self.vlan_ports[fwd_rule[2]]
                    for p in port_list:
                        s.add(p)
            elif fwd_rule[2] != "self":
                s.add(fwd_rule[2])
            suffix = 1
        for p in s:
            id = self.switch_id * self.SWITCH_ID_MULTIPLIER + suffix * self.PORT_ID_MULTIPLIER
            self.port_to_id[p] = id
            suffix += 1

        
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
        # and output part from intermedite port s to output ports
        print " * Generating ACL transfer function * " 
        for acl in self.acl_iface.keys():
            if acl not in self.acl.keys():
                continue
            for acl_instance in self.acl_iface[acl]:
                file_name = acl_instance[3]
                specified_ports = []
                access_ports = []
                vlan = acl_instance[2]
                if acl_instance[0].startswith("vlan"):
                    for p in self.vlan_ports[acl_instance[0]]:
                        specified_ports.append(self.port_to_id[p])
                        if p in self.vlan_mode.keys() and self.vlan_mode[p] == "access":
                            access_ports.append(self.port_to_id[p])
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
                            # IN ACL for VLAN tagged packets going to trunk or access ports
                            self.set_field(match, "vlan", vlan, 0)
                            next_rule = TF.create_standard_rule(in_ports, match, out_ports, None, None, file_name, lines)
                            tf.add_fwd_rule(next_rule)
                            # IN ACL for un-vlan tagged packets going to access ports. If there is any access port, 
                            # we should accept untagged packets, and tag them with the corresponding VLAN tag.
                            if (len(access_ports) > 0):
                                self.set_field(match, "vlan", 0, 0)
                                mask = byte_array_get_all_one(self.hs_format["length"]*2)
                                rewrite = byte_array_get_all_zero(self.hs_format["length"]*2)
                                self.set_field(mask, 'vlan', 0, 0)
                                self.set_field(rewrite, 'vlan', vlan, 0)
                                next_rule = TF.create_standard_rule(access_ports, match, out_ports, mask, rewrite, file_name, lines)
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
                                    if port in access_ports:
                                        # If sending out from an access port, strip the VLAN tag
                                        mask = byte_array_get_all_one(self.hs_format["length"]*2)
                                        rewrite = byte_array_get_all_zero(self.hs_format["length"]*2)
                                        self.set_field(mask, 'vlan', 0, 0)
                                        self.set_field(rewrite, 'vlan', 0, 0)
                                        next_rule = TF.create_standard_rule(in_ports, match, out_ports, mask, rewrite, file_name, lines)
                                    else:
                                        next_rule = TF.create_standard_rule(in_ports, match, out_ports, None, None, file_name, lines)
                                    tf.add_fwd_rule(next_rule)
        
        # default rule for all vlans configured on this switch and un-vlan-tagged ports
        intermediate_port = [self.switch_id * self.SWITCH_ID_MULTIPLIER]
        vlan_ports = set()
        trunk_ports = set()
        for vlan_name in self.vlan_ports.keys():
            cnf_vlan = int(vlan_name[4:])
            if self.vlan_ports.has_key("vlan%d"%cnf_vlan):
                match = byte_array_get_all_x(self.hs_format["length"]*2)
                self.set_field(match, "vlan", cnf_vlan, 0)
                all_in_ports = []
                access_ports = []
                for port in self.vlan_ports["vlan%d"%cnf_vlan]:
                    all_in_ports.append(self.port_to_id[port])
                    vlan_ports.add(self.port_to_id[port])
                    if port in self.vlan_mode.keys() and self.vlan_mode[port] == "access":
                        access_ports.append(self.port_to_id[port])
                    else:
                        trunk_ports.add(self.port_to_id[port])
                # default rule for vlan tagged packets arriving on access and trunk port   
                def_rule = TF.create_standard_rule(all_in_ports, match, intermediate_port, None, None, "", [])
                tf.add_fwd_rule(def_rule)
                # default rule for un-vlan tagged packets received on access port
                if (len(access_ports) > 0):
                    match = byte_array_get_all_x(self.hs_format["length"]*2)
                    self.set_field(match, "vlan", 0, 0)
                    mask = byte_array_get_all_one(self.hs_format["length"]*2)
                    rewrite = byte_array_get_all_zero(self.hs_format["length"]*2)
                    self.set_field(mask, 'vlan', 0, 0)
                    self.set_field(rewrite, 'vlan', cnf_vlan, 0)
                    def_rule = TF.create_standard_rule(access_ports, match, intermediate_port, mask, rewrite, "", [])
                    tf.add_fwd_rule(def_rule)
                
                #default rules for outgoing packets
                for port_id in all_in_ports:
                    match = byte_array_get_all_x(self.hs_format["length"]*2)
                    mask = byte_array_get_all_one(self.hs_format["length"]*2)
                    rewrite = byte_array_get_all_zero(self.hs_format["length"]*2)
                    before_out_port = [port_id+self.PORT_TYPE_MULTIPLIER * self.INTERMEDIATE_PORT_TYPE_CONST]
                    after_out_port = [port_id+self.PORT_TYPE_MULTIPLIER * self.OUTPUT_PORT_TYPE_CONST]
                    # default rule for vlan tagged packets leaving access ports
                    if port_id in access_ports:
                        self.set_field(match, "vlan", cnf_vlan, 0)
                        self.set_field(mask, 'vlan', 0, 0)
                        self.set_field(rewrite, 'vlan', 0, 0)
                        def_rule = TF.create_standard_rule(before_out_port, match, after_out_port , mask, rewrite, "", [])
                        tf.add_rewrite_rule(def_rule)
                    # default rule for vlan tagged packets leaving trunk ports
                    else:
                        self.set_field(match, "vlan", cnf_vlan, 0)
                        def_rule = TF.create_standard_rule(before_out_port, match, after_out_port , None, None, "", [])
                        tf.add_fwd_rule(def_rule)
                
        #defult rule for unvaln-tagged packets received on an trunk port 
        if (len(trunk_ports) > 0):
            match = byte_array_get_all_x(self.hs_format["length"]*2)
            self.set_field(match, "vlan", 0, 0)
            mask = byte_array_get_all_one(self.hs_format["length"]*2)
            rewrite = byte_array_get_all_zero(self.hs_format["length"]*2)
            self.set_field(mask, 'vlan', 0, 0)
            self.set_field(rewrite, 'vlan', self.def_vlan, 0)
            def_rule = TF.create_standard_rule(list(trunk_ports), match, intermediate_port, mask, rewrite, "", [])
            tf.add_fwd_rule(def_rule)
                
        # ... un-vlan-tagged port
        all_in_ports = []
        for port in self.port_to_id.keys():
            if port != "self":
                all_in_ports.append(self.port_to_id[port])
        for port in vlan_ports:
            all_in_ports.remove(port)
            
        # default rule for un-tagged packets from input port to forwarding engine
        if (len(all_in_ports) > 0):
            match = byte_array_get_all_x(self.hs_format["length"]*2)
            self.set_field(match, "vlan", 0, 0)
            def_rule = TF.create_standard_rule(all_in_ports, match, intermediate_port, None, None, "", [])
            tf.add_fwd_rule(def_rule) 
        
        # default rule for un-tagged packets from intermediate port to outut port
        match = byte_array_get_all_x(self.hs_format["length"]*2)
        for port_id in all_in_ports:
            before_out_port = [port_id+self.PORT_TYPE_MULTIPLIER * self.INTERMEDIATE_PORT_TYPE_CONST]
            after_out_port = [port_id+self.PORT_TYPE_MULTIPLIER * self.OUTPUT_PORT_TYPE_CONST]
            def_rule = TF.create_standard_rule(before_out_port, match, after_out_port , None, None, "", [])
            tf.add_fwd_rule(def_rule)
        
        ##################################
        print " * Generating VLAN forwarding transfer function... * "
        # generate VLAN forwarding entries
        for vlan_num in self.port_subnets.keys():
            for (ip_addr,subnet_mask,file_name,lines,port) in self.port_subnets[vlan_num]:
                match = byte_array_get_all_x(self.hs_format["length"]*2)
                in_port = [self.switch_id * self.SWITCH_ID_MULTIPLIER]
                vlan = int(vlan_num)
                out_ports = []
                if ip_addr == None:
                    self.set_field(match, "vlan", vlan, 0)
                else:
                    self.set_field(match, "ip_dst", ip_addr, subnet_mask)
                    self.set_field(match, "vlan", vlan, 0)
                if not port.startswith("vlan"):
                    out_ports.append(self.port_to_id[port]+self.PORT_TYPE_MULTIPLIER * self.INTERMEDIATE_PORT_TYPE_CONST)
                elif "vlan%d"%vlan in self.vlan_ports.keys():
                    port_list = self.vlan_ports["vlan%d"%vlan]
                    for p in port_list:
                        out_ports.append(self.port_to_id[p]+self.PORT_TYPE_MULTIPLIER * self.INTERMEDIATE_PORT_TYPE_CONST)
                tf_rule = TF.create_standard_rule(in_port, match, out_ports, None, None,file_name,lines)
                tf.add_fwd_rule(tf_rule)
                   
        ###################################
        print " * Generating IP forwarding transfer function... * "  
        # generate the forwarding part of transfer fucntion, from the fwd_prt, to pre-output ports
        for subnet in range(32,-1,-1):
            for fwd_rule in self.fwd_table:
                if fwd_rule[1] == subnet:
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
                    vlan = 0
                    m = re.split('\.',fwd_rule[2])
                    # drop rules:
                    if fwd_rule[2] == "self":
                        self_rule = TF.create_standard_rule(in_port,match,[],None,None,file_name,lines)
                        tf.add_fwd_rule(self_rule)
                    # non drop rules
                    else:
                        # sub-ports: port.vlan
                        if len(m) > 1:
                            if m[0] in self.port_to_id.keys():
                                out_ports.append(self.port_to_id[m[0]]+self.PORT_TYPE_MULTIPLIER * self.INTERMEDIATE_PORT_TYPE_CONST)
                                vlan = int(m[1])
                            else:
                                print "ERROR: unrecognized port %s"%m[0]
                                return -1
                        # vlan outputs
                        elif fwd_rule[2].startswith('vlan'):
                            if fwd_rule[2] in self.vlan_ports.keys():
                                port_list = self.vlan_ports[fwd_rule[2]]
                                for p in port_list:
                                    out_ports.append(self.port_to_id[p]+self.PORT_TYPE_MULTIPLIER * self.INTERMEDIATE_PORT_TYPE_CONST)
                                vlan = int(fwd_rule[2][4:])
                            else:
                                print "ERROR: unrecognized vlan %s"%fwd_rule[2]
                                return -1
                        # physical ports - no vlan taging
                        else:
                            if fwd_rule[2] in self.port_to_id.keys():
                                out_ports.append(self.port_to_id[fwd_rule[2]] + self.PORT_TYPE_MULTIPLIER * self.INTERMEDIATE_PORT_TYPE_CONST)
                                vlan = 0
                            else:
                                print "ERROR: unrecognized port %s"%fwd_rule[2]
                                return -1
                        # now set the fields
                        self.set_field(mask, 'vlan', 0, 0)
                        self.set_field(rewrite, 'vlan', vlan, 0)
                        tf_rule = TF.create_standard_rule(in_port, match, out_ports, mask, rewrite,file_name,lines)
                        tf.add_rewrite_rule(tf_rule) 
                        
        print "=== Successfully Generated Transfer function ==="
        #print tf
        return 0
    
 
        
        
