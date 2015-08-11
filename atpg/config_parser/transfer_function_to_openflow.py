'''
    <Converts transfer function object to a set of equivalent OpenFlow rules -- Part of HSA Library>
Created on Mar 27, 2012

@author: Peyman Kazemian
'''

from headerspace.hs import *
from headerspace.tf import *
from config_parser.cisco_router_parser import *
import json

from httplib import HTTPMessage

class OpenFlow_Rule_Generator(object):
    
    def __init__(self,tf,hs_format):
        '''
        hs_format could have the following fields:
        POSITION FIELDS: mac_src_pos, mac_dst_pos, vlan_pos, ip_src_pos, ip_dst_pos, ip_proto_pos, transport_src_pos, transport_dst_pos
        LENGTH FIELDS: mac_src_len, mac_dst_len, vlan_len, ip_src_len, ip_dst_len, ip_proto_len, transport_src_len, transport_dst_len
        '''
        self.hs_format = hs_format
        self.tf = tf
    
    def parse_non_wc_field(self,field,right_wc):
        '''
        right_wc can be True for IP fields and False for non-IP fields. It indicates wther thsi field should be treated
        as a right-hand masked field or not.
        '''
        
        wildcards = []
        if right_wc:
            found_right_wc = -1
            values = []
        else:
            found_right_wc = 0
            values = [0]
        for i in range (len(field)):
            for j in range (4):
                next_bit = (field[i] >> (2*j)) & 0x03
                if right_wc and found_right_wc == -1 and next_bit != 0x03:
                    # detect when we have scanned all right wildcarded bits
                    found_right_wc = j + i*4
                    values.append(0)
                new_values = []
                for value in values:
                    #if (next_bit == 0x02 or next_bit == 0x03) and found_right_wc != -1:
                    #    new_values.append(value + 2**(j + i*4))
                    #if (next_bit == 0x01 or next_bit == 0x03) and found_right_wc != -1:
                    #    new_values.append(value)
                    if next_bit == 0x02 and found_right_wc != -1:
                        new_values.append(value + 2**(j + i*4))
                    elif next_bit == 0x01 and found_right_wc != -1:
                        new_values.append(value)
                    elif next_bit == 0x03 and found_right_wc != -1:
                        # HACK: to avoid explosion of OF rules, we treat non-right side wildcards 
                        # on IP addresses or wildcard bits on non-IP addresses as 0
                        new_values.append(value)
                        
                values = new_values 
        return [values[0],found_right_wc]
    
    def find_new_field(self,field_match,field_mask,field_rewrite):
        '''
        finds out the new value for this field. If it is unknown (i.e. there are wildcard bits in it)
        it returns None.
        '''
        all_masked = True
        for i in range (len(field_mask)):
            if (field_mask[i] != 0xaa):
                all_masked = False
        if (all_masked):
            return None
        
        new_byte_array = byte_array_or(byte_array_and(field_match,field_mask),field_rewrite)
        value = 0
        for i in range (len(new_byte_array)):
            for j in range (4):
                next_bit = (new_byte_array[i] >> (2*j)) & 0x03
                if next_bit == 0x03:
                    print "ERROR: Unexpected rewrite action. Ignored. %s - %s - %s - %s"%(byte_array_to_hs_string(field_match),byte_array_to_hs_string(field_mask),byte_array_to_hs_string(field_rewrite),byte_array_to_hs_string(new_byte_array))
                    return None
                elif next_bit == 0x02:
                    value = value + 2**(4*i+j)
        return value
    
    def parse_rule(self,rule):
        '''
        Parses a single rule and generate openflow entry for that rule.
        the resulting openflow entry will have this format:
        FIEDL_wc: if the field is not wildcarded (0) or wildcarded (1) for IP fields, this a number between 0-32
        counting number of wildcarded bits from right
        FIELD_match: the match value for this field, after applying appropriate wildcard.
        FIELD_new: in case of a rewrite action, the new field value to be rewritten.
        '''
        fields = ["mac_src", "mac_dst", "vlan", "ip_src", "ip_dst", "ip_proto", "transport_src", "transport_dst"]
        openflow_entry = {}
        for field in fields:
            if "%s_pos"%field not in self.hs_format.keys():
                continue
            
            position = self.hs_format["%s_pos"%field]
            len = self.hs_format["%s_len"%field]
            wildcarded = True
            field_match = bytearray()
            field_mask = bytearray()
            field_rewrite = bytearray()
            for i in range(2*len):
                field_match.append(rule["match"][position*2+i])
                if rule["mask"] != None:
                    field_mask.append(rule["mask"][position*2+i])
                    field_rewrite.append(rule["rewrite"][position*2+i])
                if rule["match"][position*2+i] != 0xff:
                    wildcarded = False

            if wildcarded:
                if field == "ip_src" or field == "ip_dst":
                    openflow_entry["%s_wc"%field] = 32
                else:
                    openflow_entry["%s_wc"%field] = 1
                #openflow_entry["%s_match"%field] = [0]
                openflow_entry["%s_match"%field] = 0
            else:
                if field == "ip_src" or field == "ip_dst":
                    parsed = self.parse_non_wc_field(field_match, True)
                else:
                    parsed = self.parse_non_wc_field(field_match, False)
                openflow_entry["%s_wc"%field] = parsed[1]
                openflow_entry["%s_match"%field] = parsed[0]
                
            if (rule["mask"] != None):
                openflow_entry["%s_new"%field] = self.find_new_field(field_match,field_mask,field_rewrite)
            else:
                openflow_entry["%s_new"%field] = None
                
            openflow_entry["in_ports"] = rule["in_ports"]
            openflow_entry["out_ports"] = rule["out_ports"]
        
        return openflow_entry
    
    def generate_of_rules(self,filename):
        f = open("../utils/stanford_openflow_rules/%s"%filename,'w')
        rules = []
        for rule in self.tf.rules:
            of_rule = self.parse_rule(rule)
            rules.append(of_rule)
            
        f.write("{\"rules\":")
        f.write(json.dumps(rules))
        f.write("}")
        f.close()
            

def main():
    f = TF(1)
    f.load_object_from_file("../utils/tf_stanford_backbone/bbra_rtr.tf")
    OFG = OpenFlow_Rule_Generator(f,ciscoRouter(1).HS_FORMAT())
    OFG.generate_of_rules("bbra_rtr.of")
    
if __name__ == "__main__":
    main()
