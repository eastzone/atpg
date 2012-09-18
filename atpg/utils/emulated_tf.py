'''
    <emulates the functionality of multi-table boxes using one transfer function -- Part of HSA Library>
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
    
Created on Aug 14, 2011

@author: Peyman Kazemian
'''
from headerspace.hs import byte_array_list_contained_in

class emulated_tf(object):
    
    def __init__(self,n_reapet,duplicate_removal=True):
        self.switch_id_mul = 100000
        self.port_type_mul = 10000
        self.output_port_const = 2
        # list of transfer functions emulated by this class
        self.tf_list = []
        self.num_repeat = n_reapet
        # which stage of TF is FWD engine. starting from 0
        self.fwd_engine_stage = 1
        self.length = 0
        self.duplicate_removal = duplicate_removal
        
    def set_fwd_engine_stage(self,stage):
        self.fwd_engine_stage = stage
        
    def set_switch_id_multiplier(self,m):
        self.switch_id_mul = m
        
    def append_tf(self,tf):
        self.tf_list.append(tf)
        self.length = tf.length
        
    def insert_tf_at(self,tf,pos):
        self.tf_list.insert(pos, tf)
        
    def remove_duplicates(self,input_hs_list):
        #print "Start Removing Duplicates - len: %d"%len(input_hs_list)
        hs_buckets = {}
        to_be_removed = []
        for input_index in range(len(input_hs_list)):
            (cur_hs,cur_ports) = input_hs_list[input_index]
            bucket_name = "%s_%s"%(cur_hs.applied_rule_ids[len(cur_hs.applied_rule_ids) - self.fwd_engine_stage -1],cur_ports)
            if bucket_name not in hs_buckets.keys():
                hs_buckets[bucket_name] = [input_index]
            else:
                renew_bucket = []
                for i in hs_buckets[bucket_name]:
                    (prev_hs,prev_ports) = input_hs_list[i]
                    if byte_array_list_contained_in(prev_hs.hs_list,cur_hs.hs_list) and byte_array_list_contained_in(cur_hs.hs_diff,prev_hs.hs_diff):
                        to_be_removed.append(i)
                    else:
                        renew_bucket.append(i)
                renew_bucket.append(input_index)
                hs_buckets[bucket_name] = renew_bucket
                
        to_be_removed.sort(cmp=None, key=None, reverse=True)
        for i in to_be_removed:
            input_hs_list.pop(i)
        #print "Start Removing Duplicates - len: %d"%len(input_hs_list)
                
        
    def T(self,hs,port):
        sw_id = port / self.switch_id_mul - 1
        if sw_id >= len(self.tf_list):
            return []
        tf = self.tf_list[sw_id]
        phase = [(hs,[port])]
        for i in range(0,self.num_repeat):
            #print "we are in phase %d - input is %s at port %d"%(i,hs,port)
            tmp = []
            for (hs,port_list) in phase:
                for p in port_list:
                    tmp.extend(tf.T(hs,p))
            phase = tmp

        result = []
        for (h,ports) in phase:
            if port + self.output_port_const * self.port_type_mul in ports:
                ports.remove(port + self.output_port_const * self.port_type_mul)
            if (len(ports)>0):
                result.append((h,ports))
        if self.duplicate_removal:
            self.remove_duplicates(result)
        return result 
    
    def T_inv(self,hs,port):
        sw_id = port / self.switch_id_mul - 1
        if sw_id >= len(self.tf_list):
            return []
        tf = self.tf_list[sw_id]
        phase = [(hs,[port])]
        for i in range(0,self.num_repeat):
            tmp = []
            for (hs,port_list) in phase:
                for p in port_list:
                    tmp.extend(tf.T_inv(hs,p))
            phase = tmp
        return phase
    def sp(self):
        tf = self.tf_list[10]
        print "####################"
        print tf
        print "####################"
        
