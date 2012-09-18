'''
    <Transfer function class -- Part of HSA Library>
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
    
Created on Jan 24, 2011

@author: Peyman Kazemian
'''

from headerspace.hs import *
from array import array
from headerspace.wildcard_dictionary import wildcard_dictionary

class TF(object):
    '''
    models a box transfer function, a network transfer function or a topology transfer function
    '''

    def __init__(self, length):
        '''
        Constructor
        length is two times the length of packet headers in bytes. (it is number of nibbles)
        '''
        self.length = length
        self.rules = []
        self.custom_rules = [] 
        self.lazy_eval_nibbles = []
        self.inport_to_rule = {}
        self.outport_to_rule = {}
        self.id_to_rule = {}
        self.next_id = 0
        self.prefix_id = ""
        self.lazy_eval_active = False
        self.send_on_receiving_port = False
        # TRIAL - won't be saved upon tf.save()
        self.hash_table_active = False
        self.hash_nibble_indices = []
        self.inport_to_hash_table = {}

        # James: Exact match hash
        self.exact_match_hash_active = False
        self.exact_match_hash = {}
        self.exact_match_indices = []
        
    def set_prefix_id(self,str_prefix):
        self.prefix_id = str_prefix
        
    def set_send_on_receiving_port(self, val):
        self.send_on_receiving_port = val
       
    def generate_next_id(self):
        self.next_id = self.next_id + 1
        return "%s_%d"%(self.prefix_id,self.next_id)
        
    def set_lazy_evaluate(self,list_of_nibbles):
        self.lazy_eval_nibbles = list_of_nibbles
        
    def activate_lazy_eval(self):
        self.lazy_eval_active = True
        
    def deactivate_lazy_eval(self):
        self.lazy_eval_active = False
        
    def activate_hash_table(self,nibble_indices):
        self.hash_table_active = True
        self.hash_nibble_indices = nibble_indices
        for key in self.inport_to_rule.keys():
            self.inport_to_hash_table[key] = wildcard_dictionary(4,50)
            for rule in self.inport_to_rule[key]:
                tmp = []
                for index in self.hash_nibble_indices:
                    tmp.append(rule["match"][index])
                self.inport_to_hash_table[key].add_entry(tmp,rule)
                
    def deactivate_hash_table(self):
        self.hash_table_active = False
    
            
    def activate_exact_match_hash(self, indices):
        self.exact_match_hash_active = True
        self.exact_match_indices = indices
        
        count = 0
        count1 = 0 
        for rule in self.rules:
            match = bytearray()
            match_key_string = ""
            for index in indices:
                match.append(rule["match"][index])      
            #print byte_array_to_hs_string(match)   
            #print byte_array_to_hs_string(rule["match"]) 
            #print rule['action'] 
            match_key_string = byte_array_to_hs_string(match)
            in_ports = rule["in_ports"]   
            
            if 'x' in match_key_string:
                match_key_string = "default"
                count += 1
            else:
                count1 += 1
                             
            for in_port in in_ports:
                if "%d"%in_port not in self.exact_match_hash.keys():
                    self.exact_match_hash["%d"%in_port] = {}
                if match_key_string not in self.exact_match_hash["%d"%in_port].keys():
                    self.exact_match_hash["%d"%in_port][match_key_string] = []
                self.exact_match_hash["%d"%in_port][match_key_string].append(rule)

        #print indices
        #print "Default Count", count
        #print "Normal Count", count1
        
    def deactivate_exact_match_hash(self):
        self.exact_match_hash_active = False
        self.exact_match_hash = {}
        
    def print_influences(self):
        '''
        For each rule, shows the list of higher priority rules that has an intersection with 
        the rule, and also the lower priority rules that has an intersection with the rule,
        in two separate lists.
        '''
        for rule in self.rules:
            print "%s Rule Match: %s,%s"%(rule["action"],byte_array_to_pretty_hs_string(rule["match"]),rule["in_ports"])
            print "Affected by:"
            for aff in rule["affected_by"]:
                print "%s: On Ports %s, Intersect= %s"%(byte_array_to_pretty_hs_string(aff[0]["match"]),aff[2],
                                                        byte_array_to_pretty_hs_string(aff[1]))
            print "Influence on:"
            for aff in rule["influence_on"]:
                print "%s"%(byte_array_to_pretty_hs_string(aff["match"]))
            print "-------------------"
            
    def to_string(self):
        strings = []
        for rule in self.rules:
            if (rule['action'] == 'rw'):
                match = byte_array_to_hs_string(rule['match'])
                mask = byte_array_to_hs_string(rule['mask'])
                rewrite = byte_array_to_hs_string(rule['rewrite'])
                string = "in_ports: %s, match: %s => ((h & %s) | %s, %s)" % (rule['in_ports'], \
                            match, mask, rewrite, rule['out_ports'])
                strings.append(string)
                
            if (rule['action'] == 'fwd'):
                match = byte_array_to_hs_string(rule['match'])
                string = "in_ports: %s, match: %s => (h , %s)" % (rule['in_ports'], \
                            match, rule['out_ports'])
                strings.append(string)
                
            if (rule['action'] == 'link'):
                string = "in_ports: %s => out_ports: %s" % (rule['in_ports'], \
                            rule['out_ports'])
                strings.append(string)
                
            if (rule['action'] == 'custom'):
                string = "match: %s , transform: %s" % (rule['match'].__name__, \
                            rule['transform'].__name__)
                strings.append(string)
                
        return strings
    
    def inv_to_string(self):
        strings = []
        for rule in self.rules:
            if (rule['action'] == 'rw'):
                inv_match = byte_array_to_hs_string(rule['inverse_match'])
                mask = byte_array_to_hs_string(rule['mask'])
                inv_rewrite = byte_array_to_hs_string(rule['inverse_rewrite'])
                string = "out_ports: %s match: %s => ((h & %s) | %s, %s)" % (rule['out_ports'], \
                            inv_match, mask, inv_rewrite, rule['in_ports'])
                strings.append(string)
            if (rule['action'] == 'fwd'):
                match = byte_array_to_hs_string(rule['match'])
                string = "out_ports: %s match: %s => (h , %s)" % (rule['out_ports'], \
                            match, rule['in_ports'])
                strings.append(string)
                
            if (rule['action'] == 'link'):
                string = "out_ports: %s => in_ports: %s)" % (rule['out_ports'], \
                            rule['in_ports'])
                strings.append(string)
        return strings
    
    @staticmethod
    def create_multirewrite_rule(in_ports, match, rules):
        '''
        creates a rule that if matches on in_ports, match, does all the actions
        in rules. the in_ports,matches in rules will be the same as in_ports, match 
        in the multi-rewrite rule.
        '''
        rule = {}
        rule["in_ports"] = in_ports
        if  match.__class__ == str:
            rule["match"] = hs_string_to_byte_array(match)
        elif match.__class__ == bytearray:
            rule["match"] = bytearray(match)
        else:
            rule["match"] = None
        rule["rules"] = rules
        rule["influence_on"] = []
        rule["affected_by"] = []
        return rule
            
    @staticmethod
    def create_custom_rule(match,transform,inv_match,inv_transform,file_name,lines):
        rule = {}
        rule["match"] = match
        rule["inv_match"] = inv_match
        rule["transform"] = transform
        rule["inv_transform"] = inv_transform
        if file_name != None:
            rule["file"] = file_name
        else:
            rule["file"] = ""
        rule["line"] = []
        rule["line"].extend(lines)
        rule["id"] = None
        return rule
            
    @staticmethod
    def create_standard_rule(in_ports, match, out_ports, mask, rewrite,file_name,lines):
        '''
        Create a rule using input arguments. Use None if an input is not applicable.
        '''
        rule = {}
        rule["in_ports"] = in_ports
        rule["out_ports"] = out_ports
        if  match.__class__ == str:
            rule["match"] = hs_string_to_byte_array(match)
        elif match.__class__ == bytearray:
            rule["match"] = bytearray(match)
        else:
            rule["match"] = None
            
        if  mask.__class__ == str:
            rule["mask"] = hs_string_to_byte_array(mask)
        elif mask.__class__ == bytearray:
            rule["mask"] = bytearray(mask)
        else:
            rule["mask"] = None
            
        if  rewrite.__class__ == str:
            rule["rewrite"] = hs_string_to_byte_array(rewrite)
        elif rewrite.__class__ == bytearray:
            rule["rewrite"] = bytearray(rewrite)
        else:
            rule["rewrite"] = None
            
        rule["influence_on"] = []
        rule["affected_by"] = []
        if file_name != None:
            rule["file"] = file_name
        else:
            rule["file"] = ""
        rule["line"] = []
        rule["line"].extend(lines)
        rule["id"] = None
        return rule
        
    @staticmethod
    def standard_rule_to_string(std_rule):
        string = ""
        string += "ID = %s, "%std_rule["id"]
        string += "in_ports = %s, "%std_rule["in_ports"]
        string += "match = %s, "%byte_array_to_hs_string(std_rule["match"])
        string += "mask = %s, "%byte_array_to_hs_string(std_rule["mask"])
        string += "rewrite = %s, "%byte_array_to_hs_string(std_rule["rewrite"])
        string += "out_ports = %s"%std_rule["out_ports"]
        return string
        
    def find_influences(self, priority):
        '''
        After inserting the new_rule, into self.rules, call this method to update the 
        rule dependencies.
        @priority: priority or position of the new rule in the table
        '''
        new_rule = self.rules[priority]
        for i in range(0,priority):
            if self.rules[i]["action"] == "rw" or self.rules[i]["action"] == "fwd":
                common_ports = [val for val in new_rule["in_ports"] if val in self.rules[i]["in_ports"]]
                intersect = byte_array_intersect(self.rules[i]["match"],new_rule["match"])
                if len(intersect) > 0 and len(common_ports) > 0:
                    new_rule["affected_by"].append((self.rules[i],intersect,common_ports))
                    self.rules[i]["influence_on"].append(self.rules[priority])
        for i in range(priority+1,len(self.rules)):
            if self.rules[i]["action"] == "rw" or self.rules[i]["action"] == "fwd":
                common_ports = [val for val in new_rule["in_ports"] if val in self.rules[i]["in_ports"]]
                intersect = byte_array_intersect(self.rules[i]["match"],new_rule["match"])
                if len(intersect) > 0 and len(common_ports) > 0:
                    new_rule["influence_on"].append(self.rules[i])
                    self.rules[i]["affected_by"].append((self.rules[priority],intersect,common_ports))
        
    def set_fast_lookup_pointers(self, priority):
        new_rule = self.rules[priority]
        in_ports = self.rules[priority]["in_ports"]
        out_ports = self.rules[priority]["out_ports"]
        for p in in_ports:
            port = "%d"%p
            if port not in self.inport_to_rule.keys():
                self.inport_to_rule[port] = []
            self.inport_to_rule[port].append(new_rule)
        for p in out_ports:
            port = "%d"%p
            if port not in self.outport_to_rule.keys():
                self.outport_to_rule[port] = []
            self.outport_to_rule[port].append(new_rule)
        self.id_to_rule[new_rule["id"]] = new_rule
        
    def add_rewrite_rule(self, rule, priority= -1):
        '''
        rule is a dictionary with following keys:
        * 'match': a bytearray of length self.length describing the header formats that
        match this rule.
        * 'in_ports': the list of input port numbers to match on
        * 'mask': a bytearray of length self.length that masks all the bits that won't 
        be rewritten
        * 'rewrite': a bytearray of length self.length that rewrites the desired bits.
        * 'out_ports': the list of output port numbers.
        '''
        extended_rule = rule.copy()
        extended_rule['match'] = bytearray(rule['match'])
        extended_rule['mask'] = bytearray(rule['mask'])
        # Mask rewrite
        extended_rule['rewrite'] = byte_array_and(byte_array_not(rule['mask']), rule['rewrite'])
        extended_rule['action'] = "rw"
        
        masked = byte_array_and(rule['match'], rule['mask'])
        rng = byte_array_or(masked, rule['rewrite'])
        extended_rule['inverse_match'] = rng
        extended_rule['inverse_rewrite'] = byte_array_and(byte_array_not(rule['mask']), rule['match'])
        extended_rule["id"] = self.generate_next_id()
        if (priority == -1 or priority >= len(self.rules)):
            self.rules.append(extended_rule)
            priority = len(self.rules) - 1
        else:
            self.rules.insert(priority, extended_rule)
            
        self.find_influences(priority)
        self.set_fast_lookup_pointers(priority)
        
        
    def add_fwd_rule(self, rule, priority=-1):
        '''
        * 'match': a bytearray of length self.length describing the header formats that
        match this rule.
        * 'in_ports': the list of input port numbers to match on
        * 'out_ports': the list of output port numbers.
        '''
        extended_rule = rule.copy()
        extended_rule['match'] = bytearray(rule['match'])
        extended_rule['action'] = "fwd"
        extended_rule['inverse_match'] = None
        extended_rule['inverse_rewrite'] = None
        extended_rule["id"] = self.generate_next_id()
        if (priority == -1 or priority >= len(self.rules)):
            self.rules.append(extended_rule)
            priority = len(self.rules) - 1
        else:
            self.rules.insert(priority, extended_rule)
            
        self.find_influences(priority)
        self.set_fast_lookup_pointers(priority)
        
    def add_link_rule(self, rule, priority = -1):
        '''
        This is useful for topology transfer fucntions
        * 'in_ports': the list of input port numbers to match on
        * 'out_port': the list of output port numbers.
        WARNING: Use link rule only in Topology Transfer Function. Don't mix it with other
        type of rules.
        '''
        extended_rule = rule.copy()
        extended_rule['action'] = "link"
        extended_rule['inverse_match'] = None
        extended_rule['inverse_rewrite'] = None
        extended_rule["id"] = self.generate_next_id()
        if (priority == -1):
            self.rules.append(extended_rule)
            priority = len(self.rules) - 1
        else:
            self.rules.insert(priority, extended_rule)
            
        self.set_fast_lookup_pointers(priority)
        
    def add_custom_rule(self, rule, priority=-1):
        '''
        Add a custom rule. You need to provide a function for finding math
        and a function for creating output header.
        rule should have the following entries:
        * 'match': a pointer to the function for finding if a packet match this rule.
        the function should accept (headerspace,in_port) as input and returns a list of 
        headerspace objects that match this rule
        * 'transform': a pointer to a function which outputs a list of (headerspace, list of out_ports)
        pairs as the output of the rule.
        * 'inv_match': a pointer to the function for finding if an output packet can be 
        generated by this rule. The function format is like "match'. 
        * 'inv_transform': a pointer to a function which outputs a list of (headerspace, 
        list of in_ports) pairs as the output of the inverse rule.
        WARNING: use custom rules in a transfer function with only custom rules. Interaction between
        custom rules and rewrite/fw rules is not defined.
        '''
        extended_rule = rule.copy()
        extended_rule['action'] = "custom"
        extended_rule["id"] = self.generate_next_id()
        if (priority == -1):
            self.rules.append(extended_rule)
            priority = len(self.rules) - 1
        else:
            self.rules.insert(priority, extended_rule)
        self.id_to_rule[extended_rule["id"]] = extended_rule
        self.custom_rules.append(self.rules[priority])
        
    def apply_rewrite_rule(self,rule,hs,port,applied_rules=None):
        mod_outports = list(rule["out_ports"])
        '''
        if (not self.send_on_receiving_port) and (port in mod_outports):
            mod_outports.remove(port)
        '''
        if len(mod_outports) == 0:
            return []
        
        new_hs = hs.copy_intersect(rule['match'])
        if new_hs.count() > 0 and port in rule["in_ports"]:
            for i in range(0,len(new_hs.hs_list)):
                barr = byte_array_or(byte_array_and(new_hs.hs_list[i],rule['mask']),rule['rewrite'])
                new_hs.hs_list[i] = barr
            for (r, h, in_ports) in rule["affected_by"]:
                if port in in_ports and (applied_rules == None or r["id"] in applied_rules):
                    new_hs.diff_hs(h)
            for i in range(0,len(new_hs.hs_diff)):
                barr = byte_array_or(byte_array_and(new_hs.hs_diff[i],rule['mask']),rule['rewrite'])
                new_hs.hs_diff[i] = barr
            new_hs.clean_up()
            if (new_hs.count() == 0):
                return []
            new_hs.push_applied_tf_rule(self,rule["id"],port)
            applied_rules.append(rule["id"])
            return [(new_hs,mod_outports)]
        else:
            return []
        
    def apply_fwd_rule(self,rule,hs,port,applied_rules=None):
        mod_outports = list(rule["out_ports"])
        '''
        if (not self.send_on_receiving_port) and (port in mod_outports):
            mod_outports.remove(port)
        '''
        if len(mod_outports) == 0:
            return []

        new_hs = hs.copy_intersect(rule['match'])
        if new_hs.count() > 0 and port in rule["in_ports"]:
            for (r, h, in_ports) in rule["affected_by"]:
                if port in in_ports and (applied_rules == None or r["id"] in applied_rules):
                    new_hs.diff_hs(h)
            new_hs.clean_up()
            if (new_hs.count() == 0):
                return []
            new_hs.push_applied_tf_rule(self,rule["id"],port)
            applied_rules.append(rule["id"])
            return [(new_hs,mod_outports)]
        else:
            return []
        
    def apply_link_rule(self,rule,hs,port):
        if port in rule["in_ports"]:
            ohs = hs.copy()
            ohs.push_applied_tf_rule(self,rule["id"],port)
            return [(ohs,list(rule['out_ports']))]
        else:
            return []
      
    def apply_custom_rule(self,rule,hs,port):
        result = []
        matches = rule["match"](hs,port)
        if len(matches) > 0:
            for match in matches:
                tmp_hp = rule["transform"](match,port)
                for (out_hs,out_ports) in tmp_hp:
                    if out_hs.count() > 0:
                        out_hs.push_applied_tf_rule(self,rule["id"],port)
                        result.append((out_hs,out_ports))
        return result
                        
    def T(self,hs,port):
        '''
        returns a list of (hs, list of output ports) as a result of applying transfer function.
        hs will have A-B format, where A is the intersection of hs and the rule's match struct
        and B will be union of match bytes of all the rules that influence on the matching rule.
        '''
        result = []
        applied_rules = []
        rule_set = []

        default_operation = False
        if self.exact_match_hash_active == True:
            # James: Implement a Longest Prefix Match below
            match = bytearray()
            for index in self.exact_match_indices:
                match.append(hs.hs_list[0][index]) 
                
            match_key_string = byte_array_to_hs_string(match)
            #for index in xrange(0, len(match_key_string)):
            #    bit = match_key_string[index]
            #    if bit == 'x':
            #        index = index -1
            #        break
            
            index = match_key_string.find('x')

            if index == 0:
                # All wildcard?
                default_operation = True
            elif index != -1:
                match_key_string = match_key_string[:index]
                
        else:
            default_operation = True
        
        if default_operation == False:
            #print match_key_string
            
            try:
                if len(match_key_string) == len(self.exact_match_indices) * 4:
                    # Full match
                    rule_set = self.exact_match_hash["%d"%port][match_key_string] + self.exact_match_hash["%d"%port]["default"]
                    #print "Exact", len(self.exact_match_hash["%d"%port][match_key_string])
                    #print "Default", len(self.exact_match_hash["%d"%port]["default"])
                else:
                    for key in self.exact_match_hash["%d"%port].keys():
                        if key.startswith(match_key_string):
                            rule_set += self.exact_match_hash["%d"%port][key]
                    rule_set += self.exact_match_hash["%d"%port]["default"]
                    #print "Wild %d vs %d" % (len(match_key_string), len(self.exact_match_indices) * 4)
                    #print len(rule_set)
            except KeyError:
                rule_set = self.exact_match_hash["%d"%port]["default"]
        else:
            #TODO: Hack! fix it    
            if self.inport_to_rule.has_key("%d"%port) and (not self.hash_table_active or len(hs.hs_list)>1):
                rule_set = self.inport_to_rule["%d"%port]
            elif self.hash_table_active and self.inport_to_hash_table.has_key("%d"%port):
                tmp = []
                for index in self.hash_nibble_indices:
                    tmp.append(hs.hs_list[0][index])
                rule_set = self.inport_to_hash_table["%d"%port].find_entry(tmp)
        
        #print "Size of rule_set is %d" % len(rule_set)
        #if len(rule_set) > 200:
        #    print port, default_operation, match_key_string, len(rule_set)
        
        for rule in rule_set:
            #check if this rule qualifies for lazy evaluation
            if (self.lazy_eval_active and self.is_qualified_for_lazy_eval(rule)):
                lazy_hs = hs.copy()
                lazy_hs.add_lazy_tf_rule(self,rule["id"],port)
                result.append(lazy_hs,rule["out_ports"])
            # link rule
            elif rule['action'] == "link":
                result.extend(self.apply_link_rule(rule, hs, port))
            # rewrite rule
            elif rule['action'] == "rw":
                result.extend(self.apply_rewrite_rule(rule, hs, port,applied_rules))
            # forward rule
            elif rule['action'] == "fwd":
                result.extend(self.apply_fwd_rule(rule, hs, port,applied_rules))
    
        # custom rules
        for rule in self.custom_rules:
            result.extend(self.apply_custom_rule(rule, hs, port))
       
        return result
                
    def T_rule(self,rule_id,hs,port):
        '''
        Apply rule with id = rule_id to (hs,port)
        Output is a list of [hs,list_of_out_ports].
        '''
        result = []
        if self.id_to_rule.has_key(rule_id):
            rule = self.id_to_rule[rule_id]
            if rule['action'] == "link":
                result = self.apply_link_rule(rule, hs, port)
            elif rule['action'] == "rw":
                result = self.apply_rewrite_rule(rule, hs, port)
            elif rule['action'] == "fwd":
                result = self.apply_fwd_rule(rule, hs, port)
            elif rule['action'] == "custom":
                result = self.apply_custom_rule(rule, hs, port)
                
        return result
        
    def apply_inv_link_rule(self,rule,hs,port):
        if (port in rule["out_ports"]):
            ihs = hs.copy()
            ihs.push_applied_tf_rule(self,rule["id"],port)
            return [(ihs,list(rule['in_ports']))]
        else:
            return []
        
    def apply_inv_rewrite_rule(self,rule,hs,port):
        result = []
        new_hs = hs.copy_intersect(rule['inverse_match'])
        if new_hs.count() > 0:
            for i in range(0,len(new_hs.hs_list)):
                barr = byte_array_or(byte_array_and(new_hs.hs_list[i],rule['mask']),rule['inverse_rewrite'])
                new_hs.hs_list[i] = barr
            for i in range(0,len(new_hs.hs_diff)):
                barr = byte_array_or(byte_array_and(new_hs.hs_diff[i],rule['mask']),rule['inverse_rewrite'])
                new_hs.hs_diff[i] = barr
            for p in rule["in_ports"]:
                next_hs = new_hs.copy()
                for (r, h, in_ports) in rule["affected_by"]:
                    if p in in_ports:
                        next_hs.diff_hs(h)
                next_hs.clean_up()
                if (next_hs.count() != 0):
                    next_hs.push_applied_tf_rule(self,rule["id"],port)
                    result.append((next_hs,[p]))
        return result
    
    def apply_inv_fwd_rule(self,rule,hs,port):
        result = []
        new_hs = hs.copy_intersect(rule['match'])
        if new_hs.count() > 0:
            for p in rule["in_ports"]:
                next_hs = new_hs.copy()
                for (r, h, in_ports) in rule["affected_by"]:
                    if p in in_ports:
                        next_hs.diff_hs(h)
                next_hs.clean_up()
                if (next_hs.count() != 0):
                    next_hs.push_applied_tf_rule(self,rule["id"],port)
                    result.append((next_hs,[p]))
        return result
                
    def apply_inv_custom_rule(self,rule,hs,port):
        result = []
        matches = rule["inv_match"](hs,port)
        for match in matches:
            tmp_hp = rule["inv_transform"](match,port)
            for (in_hs,in_ports) in tmp_hp:
                if in_hs.count() > 0:
                    in_hs.push_applied_tf_rule(self,rule["id"],port)
                    result.append((in_hs,in_ports))
        return result            
        
    def T_inv(self,hs,port):
        '''
        returns a list of (hs, list of in_ports) as possible inputs that can cause this (hs,port).
        The format of hs and returned headerspace object, is like T() method above. 
        '''
        result = []
        
        if self.outport_to_rule.has_key("%d"%port):
            for rule in self.outport_to_rule["%d"%port]:
                #check if rule qualifies for lazy eval
                if (self.lazy_eval_active and self.is_qualified_for_lazy_eval(rule)):
                    lazy_hs = hs.copy()
                    lazy_hs.add_lazy_tf_rule(self,rule["id"],port)
                    result.append(lazy_hs,rule["in_ports"])
                # link rule
                elif rule['action'] == "link":
                    result.extend(self.apply_inv_link_rule(rule, hs, port))
                # rewrite rule
                elif rule['action'] == "rw":
                    result.extend(self.apply_inv_rewrite_rule(rule, hs, port))
                # forward rules
                elif rule['action'] == "fwd":
                    result.extend(self.apply_inv_fwd_rule(rule, hs, port))
            
        # custom rules                
        for rule in self.custom_rules:
            result.extend(self.apply_inv_custom_rule(rule, hs, port))
                        
        return result
        
    def T_inv_rule(self,rule_id,hs,port):
        '''
        Apply rule with id = rule_id to (hs,port)
        Output is a list of [hs,list_of_out_ports].
        '''
        result = []
        if self.id_to_rule.has_key(rule_id):
            rule = self.id_to_rule[rule_id]
            if rule['action'] == "link":
                result = self.apply_inv_link_rule(rule, hs, port)
            elif rule['action'] == "rw":
                result = self.apply_inv_rewrite_rule(rule, hs, port)
            elif rule['action'] == "fwd":
                result = self.apply_inv_fwd_rule(rule, hs, port)
            elif rule['action'] == "custom":
                result = self.apply_inv_custom_rule(rule, hs, port)
                
        return result
        
    def is_qualified_for_lazy_eval(self,rule):
        '''
        This is a simple version of checking for lazy evaluation. 
        TODO: implement a more complex version that understand packet header rather than
        just looking at some bit positions
        '''
        if rule["action"] == "rw":
            no_rewrite_outside_lazy = True
            one_rewrite_inside_lazy = False
            for i in range(len(rule["mask"])):
                if i in self.lazy_eval_nibbles:
                    if rule["mask"][i] != 0xaa:
                        one_rewrite_inside_lazy = True
                else:
                    if rule["mask"][i] != 0xaa:
                        no_rewrite_outside_lazy = False
            return (no_rewrite_outside_lazy and one_rewrite_inside_lazy)
        else:
            return False

        
    def save_object_to_file(self, file):
        '''
        saves all the non-custom transfer function rules to a file
        '''
        print "=== Saving transfer function to file %s ==="%file
        f = open(file, 'w')
        f.write("%d$%s$%d$%d$%d$\n"%(self.length,self.prefix_id,self.next_id,self.lazy_eval_active,self.send_on_receiving_port))
        for nibble in self.lazy_eval_nibbles:
            f.write("%d$"%nibble)
        f.write("#\n")
        for rule in self.rules:
            f.write("%s$"%rule["action"])
            f.write("%s$"%rule["in_ports"])
            f.write("%s$"%byte_array_to_hs_string(rule["match"]))
            f.write("%s$"%byte_array_to_hs_string(rule["mask"]))
            f.write("%s$"%byte_array_to_hs_string(rule["rewrite"]))
            f.write("%s$"%byte_array_to_hs_string(rule["inverse_match"]))
            f.write("%s$"%byte_array_to_hs_string(rule["inverse_rewrite"]))
            f.write("%s$"%rule["out_ports"])
            f.write("#")
            for ra in rule["affected_by"]:
                f.write("%d;%s;%s#"%(self.rules.index(ra[0]),byte_array_to_hs_string(ra[1]),ra[2]))
            f.write("$")
            f.write("#")
            for io in rule["influence_on"]:
                f.write("%d#"%self.rules.index(io))
            f.write("$%s$"%rule["file"])
            for ln in rule["line"]:
                f.write("%d,"%ln)
            f.write("$%s$\n"%rule["id"])
        f.close()
        print "=== Transfer function saved to file %s ==="%file
        
    def load_object_from_file(self, file):
        '''
        load object from file, and replace the current object.
        '''
        print "=== Loading transfer function from file %s ==="%file
        f = open(file,'r')
        self.rules = []
        first_line = f.readline()
        tokens = first_line.split('$')
        self.length = int(tokens[0])
        self.prefix_id = tokens[1]
        self.next_id = int(tokens[2])
        if (int(tokens[3]) == 1):
            self.lazy_eval_active = True
        else:
            self.lazy_eval_active = False
        if (int(tokens[4]) == 1):
            self.send_on_receiving_port = True
        else:
            self.send_on_receiving_port = False
        second_line = f.readline()
        tokens = second_line.split('#')[0].split('$')
        for n in tokens:
            if n != "":
                self.lazy_eval_nibbles.append(int(n))
        for line in f:
            tokens = line.split('$')
            new_rule = {}
            # action
            new_rule["action"] = tokens[0]
            # in_ports
            in_p = tokens[1].strip('[]').split(', ')
            new_rule["in_ports"] = []
            for p in in_p:
                if p != "":
                    new_rule["in_ports"].append(int(p)) 
            # match
            match = hs_string_to_byte_array(tokens[2])
            new_rule["match"] = match
            # mask
            mask = hs_string_to_byte_array(tokens[3])
            new_rule["mask"] = mask
            # rewrite
            rewrite = hs_string_to_byte_array(tokens[4])
            new_rule["rewrite"] = rewrite
            # inverse_match
            inverse_match = hs_string_to_byte_array(tokens[5])
            new_rule["inverse_match"] = inverse_match
            # inverse_rewrite
            inverse_rewrite = hs_string_to_byte_array(tokens[6])
            new_rule["inverse_rewrite"] = inverse_rewrite
            # out_ports
            out_p = tokens[7].strip('[]').split(', ')
            new_rule["out_ports"] = []
            for p in out_p:
                if p != "":
                    new_rule["out_ports"].append(int(p)) 
            # affected by
            new_rule["affected_by"] = []
            affect_list = tokens[8].split('#')
            for affect in affect_list:
                if affect != "":
                    elems = affect.split(';')
                    aff_p = elems[2].strip('[]').split(', ')
                    prts = []
                    for p in aff_p:
                        if p != "":
                            prts.append(int(p)) 
                    new_affect = (int(elems[0]),hs_string_to_byte_array(elems[1]),prts)
                    new_rule["affected_by"].append(new_affect)
            # influence on
            new_rule["influence_on"] = []
            influence_list = tokens[9].split('#')
            for influence in influence_list:
                if influence != "":
                    new_rule["influence_on"].append(int(influence))
            new_rule["file"] = tokens[10]
            lns = tokens[11].split(',')
            new_rule["line"] = []
            for ln in lns:
                if ln != "":
                    new_rule["line"].append(int(ln))
            new_rule["id"] = tokens[12]
            # Save new rule
            self.rules.append(new_rule)

        f.close()
        # now replace index in affected_by and influence_on fields to the pointer to rules.
        for indx in range(len(self.rules)):
            rule = self.rules[indx]
            influences = []
            for idex in rule["influence_on"]:
                influences.append(self.rules[idex])
            rule["influence_on"] = influences
            affects = []
            for r in rule["affected_by"]:
                new_affect = (self.rules[r[0]],r[1],r[2])
                affects.append(new_affect)
            rule["affected_by"] = affects
            self.set_fast_lookup_pointers(indx)
            
        print "=== Transfer function loaded from file %s ==="%file
            
    def __str__(self):
        strs = self.to_string()
        result = ""
        for s in strs:
            result += "%s\n"%s
        return result
        
    def add_fwd_rule_no_influence(self, rule, priority=-1):
        '''
        * 'match': a bytearray of length self.length describing the header formats that
        match this rule.
        * 'in_ports': the list of input port numbers to match on
        * 'out_ports': the list of output port numbers.
        '''
        extended_rule = rule.copy()
        extended_rule['match'] = bytearray(rule['match'])
        extended_rule['action'] = "fwd"
        extended_rule['inverse_match'] = None
        extended_rule['inverse_rewrite'] = None
        extended_rule["id"] = self.generate_next_id()
        if (priority == -1 or priority >= len(self.rules)):
            self.rules.append(extended_rule)
            priority = len(self.rules) - 1
        else:
            self.rules.insert(priority, extended_rule)
            
        #self.find_influences(priority)
        self.set_fast_lookup_pointers(priority)
        
    def add_rewrite_rule_no_influence(self, rule, priority= -1):
        '''
        rule is a dictionary with following keys:
        * 'match': a bytearray of length self.length describing the header formats that
        match this rule.
        * 'in_ports': the list of input port numbers to match on
        * 'mask': a bytearray of length self.length that masks all the bits that won't 
        be rewritten
        * 'rewrite': a bytearray of length self.length that rewrites the desired bits.
        * 'out_ports': the list of output port numbers.
        '''
        extended_rule = rule.copy()
        extended_rule['match'] = bytearray(rule['match'])
        extended_rule['mask'] = bytearray(rule['mask'])
        # Mask rewrite
        extended_rule['rewrite'] = byte_array_and(byte_array_not(rule['mask']), rule['rewrite'])
        extended_rule['action'] = "rw"
        
        masked = byte_array_and(rule['match'], rule['mask'])
        rng = byte_array_or(masked, rule['rewrite'])
        extended_rule['inverse_match'] = rng
        extended_rule['inverse_rewrite'] = byte_array_and(byte_array_not(rule['mask']), rule['match'])
        extended_rule["id"] = self.generate_next_id()
        if (priority == -1 or priority >= len(self.rules)):
            self.rules.append(extended_rule)
            priority = len(self.rules) - 1
        else:
            self.rules.insert(priority, extended_rule)
            
        #self.find_influences(priority)
        self.set_fast_lookup_pointers(priority)
