'''
    <A class for generting NuSMV input from TF object -- Part of HSA Library>
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
    
Created on Dec 31, 2011

@author: Peyman Kazemian
'''
from headerspace.tf import TF
from headerspace.tf import *
import os

MODEL_CHECKER_PATH = "/Users/peymankazemian/NuSMV/nusmv/NuSMV"
TMP_FILE_PATH = "../tmp.smv"
PORT_VAR_LEN = 32
HDR_VAR_LEN = 32

class NuSMV(object):
    '''
    A class that generates NuSMV input file from transfer function
    NOTE1: port 0 is a special port that shouldn't be used
    NOTE2: first call generate_nusmv_trans to generate transition function for NuSMV
    input file. Then call generate_nusmv_input to complete the input.
    NOTE3: invalid_port is a port that doesn't appear anywhere in the transfer function.
    by default it is 1. If port 1 appears in the transfer function, change it to some 
    other unused port number. This port will be used when dropping the packet.
    '''
    def __init__(self):
        self.nusmv_trans = []
        self.invalid_port = 1
        self.length = 0
        self.out_port_offset = 0
        self.generated_nusmv_input = ""
        
    def set_invalid_port(self,invalid_port):
        self.invalid_port = invalid_port
    
    def set_output_port_offset(self,offset):
        self.out_port_offset = offset
    
    def flush(self):
        self.nusmv_trans = []
        self.generated_nusmv_input = ""
    
    def generate_nusmv_trans(self,tf,end_ports):
        l = tf.length * 4
        self.length = l
        num_parts = int(ceil(self.length / (HDR_VAR_LEN*1.0)))
        
        nusmv_rules = []
        for rule in tf.rules:
            nusmv_rule = ""
            for port in rule["in_ports"]:
                if nusmv_rule == "":
                    nusmv_rule = nusmv_rule + "(p = 0ud%d_%s"%(PORT_VAR_LEN,port)
                else:
                    nusmv_rule = nusmv_rule + " | p = 0ud%d_%s"%(PORT_VAR_LEN,port)
            nusmv_rule = nusmv_rule + ")"
            mask = byte_array_wildcard_to_mask_match_strings(rule["match"])[0]
            match = byte_array_wildcard_to_mask_match_strings(rule["match"])[1]
            
            if (rule["match"]):
                for i in range(num_parts):
                    s_range = i * HDR_VAR_LEN
                    if (self.length > i*HDR_VAR_LEN+HDR_VAR_LEN-1):
                        e_range = i*HDR_VAR_LEN+HDR_VAR_LEN-1
                        num_bits = HDR_VAR_LEN
                    else:
                        e_range = self.length - 1
                        num_bits = self.length - HDR_VAR_LEN*i
                    nusmv_rule = nusmv_rule + " & ((h%s & 0ub%s_%s) = 0ub%s_%s)"%(i,num_bits,mask[l-e_range:l-s_range],num_bits,match[l-e_range:l-s_range])
                
            
            if (rule["affected_by"]):
                for (aff_rule,aff_intersect,aff_ports) in rule["affected_by"]:
                    affected = ""
                    for aff_in_port in aff_ports:
                        if (affected == ""):
                            affected = "(p != 0ud%d_%s"%(PORT_VAR_LEN,aff_in_port)
                        else:
                            affected = affected + " & p != 0ud%d_%s"%(PORT_VAR_LEN,aff_in_port)
                    affected = affected + ")"
                    aff_mask = byte_array_wildcard_to_mask_match_strings(aff_intersect)[0]
                    aff_match = byte_array_wildcard_to_mask_match_strings(aff_intersect)[1]
                    for i in range(num_parts):
                        s_range = i * HDR_VAR_LEN
                        if (self.length > i*HDR_VAR_LEN+HDR_VAR_LEN-1):
                            e_range = i*HDR_VAR_LEN+HDR_VAR_LEN-1
                            num_bits = HDR_VAR_LEN
                        else:
                            e_range = self.length - 1
                            num_bits = self.length - HDR_VAR_LEN*i
                        affected = affected + " | ((h%s & 0ub%s_%s) != 0ub%s_%s)"%(i,num_bits,aff_mask[l-e_range:l-s_range],num_bits,aff_match[l-e_range:l-s_range])
                    nusmv_rule = nusmv_rule + " & (" + affected + ")"
                
            if (rule["mask"] != None and rule["rewrite"] != None):
                action_mask = byte_array_to_hs_string(rule["mask"])
                action_rewrite = byte_array_to_hs_string(rule["rewrite"])
                for i in range(num_parts):
                    s_range = i * HDR_VAR_LEN
                    if (self.length > i*HDR_VAR_LEN+HDR_VAR_LEN-1):
                        e_range = i*HDR_VAR_LEN+HDR_VAR_LEN-1
                        num_bits = HDR_VAR_LEN
                    else:
                        e_range = self.length - 1
                        num_bits = self.length - HDR_VAR_LEN*i
                    nusmv_rule = nusmv_rule + " & (next(h%s) = ((h%s & 0ub%s_%s) | 0ub%s_%s))"%\
                        (i,i,num_bits,action_mask[l-e_range:l-s_range],num_bits,action_rewrite[l-e_range:l-s_range])
            else:
                for i in range(num_parts):
                    nusmv_rule = nusmv_rule + " & (next(h%s) = h%s)"%(i,i)
    
            if (rule["action"] == "link"):
                nusmv_rule = nusmv_rule + " & (next(pin) = 0ud%d_%d)"%(PORT_VAR_LEN,rule["out_ports"][0]+self.out_port_offset)
            else:
                nusmv_rule = nusmv_rule + " & (next(p) != pin & next(pin) = pin)"
                
            if rule["out_ports"] != None and len(rule["out_ports"]) > 0:    
                for out_port in rule["out_ports"]:
                    nusmv_rule = nusmv_rule + " & (next(p) = 0ud%d_%s)"%(PORT_VAR_LEN,out_port)
            else:
                # don't include this rule. it is a drop.
                nusmv_rule = nusmv_rule + "& (next(p) = 0ud%d_%s)"%(PORT_VAR_LEN,self.invalid_port)
                
            nusmv_rules.append(nusmv_rule)
        
        for end_port in end_ports:
            nusmv_rule = "p = 0ud%d_%s & next(p) = 0ud%d_%s"%(PORT_VAR_LEN,end_port,PORT_VAR_LEN,end_port)
            nusmv_rules.append(nusmv_rule)
            
        nusmv_rules.append("p = 0ud%d_%s & next(p) = 0ud%d_%s"%(PORT_VAR_LEN,self.invalid_port,PORT_VAR_LEN,self.invalid_port))
            
        self.nusmv_trans.extend(nusmv_rules)
        
    def generate_nusmv_input(self):
        self.generated_nusmv_input = "MODULE main\n"
        self.generated_nusmv_input = self.generated_nusmv_input + "\n"
        self.generated_nusmv_input = self.generated_nusmv_input + "VAR\n"
        self.generated_nusmv_input = self.generated_nusmv_input + "p: unsigned word[%s];\n"%(PORT_VAR_LEN)
        self.generated_nusmv_input = self.generated_nusmv_input + "pin: unsigned word[%s];\n"%(PORT_VAR_LEN)
        num_parts = int(ceil(self.length / (HDR_VAR_LEN*1.0)))
        for i in range(num_parts):
            s_range = i * HDR_VAR_LEN
            if (self.length > i*HDR_VAR_LEN+HDR_VAR_LEN-1):
                e_range = i*HDR_VAR_LEN+HDR_VAR_LEN-1
                num_bits = HDR_VAR_LEN
            else:
                e_range = self.length - 1
                num_bits = self.length - HDR_VAR_LEN*i
            self.generated_nusmv_input = self.generated_nusmv_input + "h%s: unsigned word[%s];\n"%(i,num_bits)
        self.generated_nusmv_input = self.generated_nusmv_input + "\n"
        self.generated_nusmv_input = self.generated_nusmv_input + "INIT p = 0ud%d_0;\n"%PORT_VAR_LEN
        self.generated_nusmv_input = self.generated_nusmv_input + "INIT pin = 0ud%d_0;\n"%PORT_VAR_LEN
        
        num_init = num_parts
        for i in range(num_init):
            s_range = i * HDR_VAR_LEN
            if (self.length > i*HDR_VAR_LEN+HDR_VAR_LEN-1):
                e_range = i*HDR_VAR_LEN+HDR_VAR_LEN-1
                num_bits = HDR_VAR_LEN
            else:
                e_range = self.length - 1
                num_bits = self.length - HDR_VAR_LEN*i
            self.generated_nusmv_input = self.generated_nusmv_input + "INIT h%s = 0ub%d_0;\n"%(i,num_bits)
        
        self.generated_nusmv_input = self.generated_nusmv_input + "\n"
        self.generated_nusmv_input = self.generated_nusmv_input + "TRANS\n"
        
        trans = ""
        for nusmv_transition in self.nusmv_trans:
            if trans == "":
                trans = trans + "( %s )"%nusmv_transition
            else:
                trans = trans + " |\n( %s )"%nusmv_transition
        self.generated_nusmv_input = self.generated_nusmv_input + trans;
        
        #print self.generated_nusmv_input
        
    def execute_nusmv_file(self):    
        p = os.popen("%s %s"%(MODEL_CHECKER_PATH,TMP_FILE_PATH), "r")
        result = False
        while 1:
            line = p.readline()
            if not line:
                break
            if not (line.startswith("WARNING") or line.startswith("***")):
                print line
                if line.find("true") != -1:
                    result = True
            else:
                print line
        return result
    
    def run_nusmv_reachability(self,in_port,out_port):
        '''
        there exist a path from in_port to out_port
        '''
        f = open("%s"%TMP_FILE_PATH, 'w')
        f.write(self.generated_nusmv_input)
        f.write(" |\n( p = 0ud%d_0 & next(p) = 0ud%d_%s);\n"%(PORT_VAR_LEN,PORT_VAR_LEN,in_port))
        f.write("SPEC !EF (p = 0ud%d_%s);"%(PORT_VAR_LEN,out_port))
        f.close()
        return not self.execute_nusmv_file()
        
    def run_nusmv_one_path_via_ports_reachability(self,in_port,out_port,via_ports):
        '''
        at least one path from in_port to out_port passes through via_ports
        '''
        f = open("%s"%TMP_FILE_PATH, 'w')
        f.write(self.generated_nusmv_input)
        f.write(" |\n( p = 0ud%d_0 & next(p) = 0ud%d_%s & next(pin) = 0ud%d_%s);\n"%(PORT_VAR_LEN,PORT_VAR_LEN,in_port,PORT_VAR_LEN,in_port+self.out_port_offset))
        vias = ""
        for port in via_ports:
            if vias == "":
                vias = "(p = 0ud%d_%s"%(PORT_VAR_LEN,port)
            else:
                vias = vias + " | p = 0ud%d_%s"%(PORT_VAR_LEN,port)
        vias = vias + ")"
        #f.write("SPEC EF(%s & EF(p = 0ud%d_%s));"%(vias,PORT_VAR_LEN,out_port))
        f.write("SPEC AG(!%s | AG(!(p = 0ud%d_%s)));"%(vias,PORT_VAR_LEN,out_port))
        f.close()
        return not self.execute_nusmv_file()
    
    def run_nusmv_all_paths_via_ports_reachability(self,in_port,out_port,via_ports):
        '''
        all paths from in_port to out_port should pass through via_ports
        or there is no path between in_port and out_port.
        '''
        f = open("%s"%TMP_FILE_PATH, 'w')
        f.write(self.generated_nusmv_input)
        f.write(" |\n( p = 0ud%d_0 & next(p) = 0ud%d_%s);\n"%(PORT_VAR_LEN,PORT_VAR_LEN,in_port))
        vias = ""
        for port in via_ports:
            if vias == "":
                vias = "(p = 0ud%d_%s"%(PORT_VAR_LEN,port)
            else:
                vias = vias + " | p = 0ud%d_%s"%(PORT_VAR_LEN,port)
        vias = vias + ")"
        f.write("SPEC !E[!%s U (p = 0ud%d_%s)];"%(vias,PORT_VAR_LEN,out_port))
        f.close()
        return self.execute_nusmv_file()
