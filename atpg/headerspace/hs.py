'''
    <Headerspace Class -- Part of HSA Library>
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

from math import ceil
from operator import xor

def byte_array_intersect(a1, a2):
    '''
    a1 n a2.
    '''
    if len(a1) != len(a2):
        return []
    result = bytearray()
    for i in range(len(a1)):
        result.append(a1[i] & a2[i])
    for b in result:
        if (b & 0x03 == 0) or (b & 0x0c == 0) or (b & 0x30 == 0) or (b & 0xc0 == 0):
            return []
    return result

def byte_array_complement(a):
    '''
    a'
    '''
    result = []
    length = len(a)
    for i in range(length):
        for j in range(4):
            if (a[i] >> 2*j) & 0x03 == 0x01:
                all_x = byte_array_get_all_x(length)
                all_x[i] = ((0xFE << 2*j) & 0xff) | ((0xFF >> (8 - 2*j)) & 0xff)
                result.append(all_x)
            elif (a[i] >> 2*j) & 0x03 == 0x02:
                all_x = byte_array_get_all_x(length)
                all_x[i] = ((0xFD << 2*j) & 0xff) | ((0xFF >> (8 - 2*j)) & 0xff)
                result.append(all_x)
    return result

def byte_array_difference(a,b):
    ''''
    a - b = a n b'
    '''
    diff = []
    b_complement = byte_array_complement(b)
    for b_array in b_complement:
        isect = byte_array_intersect(a,b_complement)
        if isect != []:
            diff.append(isect)
    return diff

def byte_array_equal(a1,a2):
    '''
    checks if a1=a2.
    '''
    r = a1.__eq__(a2)
    return r

def byte_array_list_contained_in(list_a,list_b):
    result = True
    for a in list_a:
        this_result = False
        for b in list_b:
            if byte_array_equal(a,b):
                this_result = True
                break
        if this_result == False:
            result = False
            break
    return result

def byte_array_subset(a,b):
    '''
    checks if a is subset of b.
    doesn't work if a is empty
    '''
    for i in range(len(a)):
        cmp = a[i] ^ b[i]
        if cmp != 0 and cmp & b[i] != cmp:
            return False
    return True

def byte_array_and(b1, b2):
    '''
    perform 'and' operation when b1 and b2 can have wildcard bits
    '''
    b_out = bytearray()
    for i in range(len(b1)):
        tmp = (b1[i] & b2[i] & 0xaa) | ((b1[i] | b2[i]) & 0x55)
        b_out.append(tmp);
    return b_out

def byte_array_or(b1, b2):
    '''
    perform 'or' operation when b1 and b2 can have wildcard bits
    '''
    b_out = bytearray()
    for i in range(len(b1)):
        tmp = (b1[i] & b2[i] & 0x55) | ((b1[i] | b2[i]) & 0xaa)
        b_out.append(tmp);
    return b_out

def byte_array_not(b):
    '''
    perform 'or' operation when b1 and b2 can have wildcard bits
    '''
    b_out = bytearray()
    for i in range(len(b)):
        tmp = ((b[i] << 1) & 0xaa) | ((b[i] >> 1) & 0x55)
        b_out.append(tmp);
    return b_out

def byte_array_wildcard_to_mask_match_strings(byte_array):
    if byte_array == None:
        return "None"
    str_mask = ""
    str_match = ""
    for b in byte_array:
        for i in range(4):
            b_shift = b >> (i * 2)
            next_bit = b_shift & 0x03
            if (next_bit == 0x01):
                str_mask = "1" + str_mask
                str_match = "0" + str_match
            elif (next_bit == 0x02):
                str_mask = "1" + str_mask
                str_match = "1" + str_match
            elif (next_bit == 0x03):
                str_mask = "0" + str_mask
                str_match = "0" + str_match
            else:
                str_mask = "0" + str_mask
                str_match = "1" + str_match
    return [str_mask,str_match]

def byte_array_to_hs_string(byte_array):
    if byte_array == None:
        return "None"
    str = ""
    for b in byte_array:
        for i in range(4):
            b_shift = b >> (i * 2)
            next_bit = b_shift & 0x03
            if (next_bit == 0x01):
                str = "0" + str
            elif (next_bit == 0x02):
                str = "1" + str
            elif (next_bit == 0x03):
                str = "x" + str
            else:
                str = "z" + str
    return str

def byte_has_no_x(b):
    for i in range(4):
        b_shift = b >> (i * 2)
        next_bit = b_shift & 0x03
        if (next_bit == 0x03 or next_bit == 0):
            return False
    return True

def byte_to_int(b):
    val = 0
    for i in range(4):
        b_shift = b >> (i * 2)
        next_bit = b_shift & 0x03
        if (next_bit == 0x02):
            val = val + 2**i
        elif (next_bit != 0x01):
            return None
    return val

def byte_array_to_pretty_hs_string(byte_array):
    if byte_array == None:
        return "None"
    str = ""
    ln = len(byte_array)
    cntr = -1
    pretty_flag = False
    for b in byte_array:
        cntr += 1
        if (cntr % 2 == 0 and cntr+1 < len):
            if (byte_has_no_x(byte_array[cntr]) and byte_has_no_x(byte_array[cntr+1])):               
                pretty_flag = True
                val = byte_to_int(byte_array[cntr]) + byte_to_int(byte_array[cntr+1])*16
                if cntr > 0:
                    str = "D%d,%s"%(val,str)
                else:
                    str = "D%d%s"%(val,str)
                continue
        elif (pretty_flag):
            pretty_flag = False
            continue
        
        if (cntr % 2 == 0 and cntr > 0):
            str = "," + str
        for i in range(4):
            b_shift = b >> (i * 2)
            next_bit = b_shift & 0x03
            if (next_bit == 0x01):
                str = "0" + str
            elif (next_bit == 0x02):
                str = "1" + str
            elif (next_bit == 0x03):
                str = "x" + str
            else:
                str = "z" + str
        
    return str

def hs_string_to_byte_array(str):
    if str == None:
        return None
    if str == "None":
        return None
    strlen = len(str)
    ln = int(ceil(strlen / 4.0))
    br = bytearray()
    for j in range(ln):
        substr = str[max(0,strlen-4*j-4):strlen-4*j]
        next_byte = 0
        sublen = len(substr)
        for i in range(4):
            if i > sublen-1:
                next_byte = next_byte | (0x03 << 2*i)
            elif (substr[i] == 'X' or substr[i] == 'x'):
                next_byte = next_byte | (0x03 << 2*(sublen-i-1))
            elif (substr[i] == '1'):
                next_byte = next_byte | (0x02 << 2*(sublen-i-1))
            elif (substr[i] == '0'):
                next_byte = next_byte | (0x01 << 2*(sublen-i-1))
            elif (substr[i] == 'Z' or substr[i] == 'z'):
                next_byte = next_byte | (0x00 << 2*(sublen-i-1))   
        br.append(next_byte)
    return br

def int_to_byte_array(int_value, len):
    '''
    reads len bits from int_value and converts it to a bytearray of len ceil(len/4).
    Note: len should be a multiple of 4.
    '''
    ln = int(ceil(len/4.0))
    br = bytearray()
    for j in range(ln):
        nible = (int_value >> 4*j) & 0xf
        next_byte = 0
        for i in range(4):
            if (nible >> i) & 0x1 == 0:
                next_byte = next_byte | (0x01 << 2*i)
            if (nible >> i) & 0x1 == 1:
                next_byte = next_byte | (0x02 << 2*i)
        br.append(next_byte)
    return br

def byte_array_get_all_x(length):
    b = bytearray()
    for i in range(length):
        b.append(0xFF)
    return b
        
def byte_array_get_all_one(length):
    b = bytearray()
    for i in range(length):
        b.append(0xaa)
    return b
        
def byte_array_get_all_zero(length):
    b = bytearray()
    for i in range(length):
        b.append(0x55)
    return b
        
def byte_array_set_bit(b_array,byte,bit,value):
    if byte>=len(b_array) | bit >= 4:
        return False
    else:
        b_array[byte] = (b_array[byte] & ~(0x3 << bit*2) | (value << bit*2))
        return True
        
def byte_array_get_bit(b_array,byte,bit):
    if byte>=len(b_array) | bit >= 4:
        return 0x04;
    else:
        return (b_array[byte] >> 2*bit) & 0x03;
        
def byte_array_set_bytes(b_array, byte, value, num_bytes):
    if byte+num_bytes>len(b_array):
        return False
    else:
        for i in range(num_bytes):
            b_array[byte+i] = (value >> i*8) & 0xff
        return True

class headerspace(object):
    '''
    A headerspace object keeps a set of header space regions. it can be union of
    [0,1,x,z] expressions. It can also keep a list of headerspaces to be subtracted
    from this object. The subtraction can be done lazily.
    It also enables normal set operations on header space.
    '''
    
    def __init__(self, length):
        '''
        Constructor
        length is two times the length of packet headers in bytes.
        '''
        self.hs_list = []
        self.hs_diff = []
        # list of (tf,rule_id,port) that has been lazy evaluated
        self.lazy_rule_ids = []
        # list of (tf,rule_id,port) that has been evaluated on this headerspace
        self.applied_rule_ids = []
        self.length = length
        
    def add_hs(self, value):
        '''
        adds value to the list of headerspaces, hs_list
        @value: bytearray of lenght self.length or another headerspace objects
        @return: True if successful, False otherwise
        '''
        if value.__class__ == bytearray:
            if len(value) != self.length:
                return False
            else:
                self.hs_list.append(bytearray(value))
                return True
        elif value.__class__ == headerspace:
            if value.length != self.length:
                return False
            else:
                for elem in value.hs_list:
                    self.hs_list.append(bytearray(elem))
                for elem in value.hs_diff:
                    self.hs_diff.append(bytearray(elem))
                return True
            
    def add_hs_list(self, values):
        '''
        adds values to the list of headerspaces, hs_list
        @values: list of bytearray of lenght self.length or other headerspace objects
        @return: True
        '''
        for value in values:
            if value.__class__ == bytearray:
                if len(value) == self.length:
                    self.hs_list.append(bytearray(value))
            elif value.__class__ == headerspace:
                if value.length == self.length:
                    for elem in value.hs_list:
                        self.hs_list.append(bytearray(elem))
                    for elem in value.hs_diff:
                        self.hs_diff.append(bytearray(elem))
        return True
    
    def diff_hs(self, value):
        '''
        lazily subtract value from this headerspace
        @value: bytearray of lenght self.length
        @return: True if successful, False otherwise
        '''
        if value.__class__ == bytearray:
            if len(value) != self.length:
                return False
            else:
                self.hs_diff.append(bytearray(value))
                return True
        else:
            return False
    
    def diff_hs_list(self, values):
        '''
        lazily subtract values from this headerspace
        @values: list of bytearray of lenght self.length
        @return: True
        '''
        for value in values:
            if value.__class__ == bytearray:
                if len(value) == self.length:
                    self.hs_diff.append(bytearray(value))
        return True
            
    def count(self):
        '''
        returns count of number of elements in hs_list
        '''
        return len(self.hs_list)
    
    def count_dif(self):
        '''
        returns count of number of elements in hs_dif
        '''
        return len(self.hs_diff)
    
    def copy(self):
        '''
        create a deep copy of itself
        '''
        deep_copy = headerspace(self.length)
        for elem in self.hs_list:
            deep_copy.hs_list.append(bytearray(elem))
        for elem in self.hs_diff:
            deep_copy.hs_diff.append(bytearray(elem))
        for (ntf,rule_id,port) in self.applied_rule_ids:
            deep_copy.applied_rule_ids.append((ntf,rule_id,port))
        for (ntf,rule_id,port) in self.lazy_rule_ids:
            deep_copy.lazy_rule_ids.append((ntf,rule_id,port))
        return deep_copy
    
    def to_string(self):
        '''
        represent a [0,1,x,z] string showing the header space.
        ''' 
        strings = []
        diffs = []
        for hs in self.hs_list:
            new_expression = byte_array_to_pretty_hs_string(hs)
            strings.append(new_expression)
        for hs in self.hs_diff:
            new_expression = byte_array_to_pretty_hs_string(hs)
            diffs.append(new_expression)
            
        union1 = ""
        union2 = ""
        for str in strings:
            union1 = union1 + " U\n" + str
        if len(union1) > 0:
            union1 = union1[3:]
        for str in diffs:
            union2 = union2 + " U\n" + str
        if len(union2) > 0:
            union2 = union2[3:]
            union1 = "(%s) \n-\n(%s)"%(union1,union2)
   
        return union1
        
    def intersect(self, other_hs):
        '''
        intersect itself with other_hs if the header lengths are equal.
        The result will be saved in the caller instance itself.
        @other_fs: @type headerspace or bytearray: the other headerspace to intersect with
        @return: @type Boolean: True if successful, False if an error happens
        '''
        if other_hs.__class__ == headerspace:
            new_hs_list = []
            if self.length != other_hs.length:
                return False
            for hs1 in self.hs_list:
                for hs2 in other_hs.hs_list:
                    isect = byte_array_intersect(hs1, hs2)
                    if len(isect) > 0:
                        new_hs_list.append(isect)
            self.hs_list = new_hs_list
            for hs in other_hs.hs_diff:
                self.hs_diff.append(hs)
            return True
        elif other_hs.__class__ == bytearray:
            new_hs_list = []
            if self.length != len(other_hs):
                return False
            for hs1 in self.hs_list:
                isect = byte_array_intersect(hs1, other_hs)
                if len(isect) > 0:
                    new_hs_list.append(isect)
            self.hs_list = new_hs_list
            return True
            
    def copy_intersect(self, other_hs):
        cpy = self.copy()
        cpy.intersect(other_hs)
        return cpy
    
    def complement(self):
        '''
        find the complement of header space pieces saved in hs_list
        and saves it back to itself
        '''
        # if empty, make it all x
        if len(self.hs_list) == 0:
            self.hs_list.append(byte_array_get_all_x(self.length))
            self.hs_diff = []
        else:
            c_hs_list = []
            # create on hs object per union element in self.hs_list
            for elem in self.hs_list:
                c_set = byte_array_complement(elem)
                tmp = headerspace(self.length)
                tmp.add_hs_list(c_set)
                c_hs_list.append(tmp)
            
            result = c_hs_list[0]
            for i in range(1,len(c_hs_list)):
                result.intersect(c_hs_list[i])
            
            self.hs_list = list(result.hs_list)
            # add hs_diff to results:
            for hs in self.hs_diff:
                self.hs_list.append(hs)
            self.hs_diff = []
                
    def copy_complement(self):
        cpy = self.copy()
        cpy.complement()
        return cpy
    
    def minus(self, other_fs):
        '''
        computes self - other_fs. note that the hs_diff will be intact
        '''
        cpy = other_fs.copy_complement()
        self.intersect(cpy)
        self.compress()
        
    def copy_minus(self, other_fs):
        cpy = self.copy()
        cpy.minus(other_fs)
        return cpy
        
    def self_diff(self):
        '''
        computes hs_list - hs_diff and saves all the result in hs_list.
        '''
        if len(self.hs_diff) == 0:
            return
        temp = headerspace(self.length)
        temp.add_hs_list(self.hs_diff)
        self.hs_diff = []
        self.minus(temp)
        
    def is_subset_of(self, other_fs):
        '''
        checks if self is a subset of other_hs
        '''
        cpy = self.copy()
        cpy.minus(other_fs)
        cpy.self_diff()
        if len(cpy.hs_list) > 0:
            return False
        else:
            return True
    
    def compress(self):
        ''''
        TODO: Compress function need to consider more cases 
        Warning: depreciated
        '''
        pop_index = []
        for i in range(len(self.hs_list)):
            for j in range(i+1,len(self.hs_list)):
                if byte_array_equal(self.hs_list[i], self.hs_list[j]):
                    pop_index.append(i)
                elif byte_array_subset(self.hs_list[i], self.hs_list[j]):
                    pop_index.append(i)
                elif byte_array_subset(self.hs_list[j], self.hs_list[i]):
                    pop_index.append(j)
                    
        new_hs_list = []
        for k in range(len(self.hs_list)):
            if k not in pop_index:
                new_hs_list.append(self.hs_list[k])
                
        self.hs_list = new_hs_list
            
    def clean_up(self):
        new_hs = []
        for h in self.hs_list:
            flag = False
            for dh in self.hs_diff:
                if byte_array_subset(h,dh):
                    flag = True
            if not flag:
                new_hs.append(h)
        if (len(new_hs)>0):
            self.hs_list = new_hs
            new_diff_hs = []
            for dh in self.hs_diff:
                for h in self.hs_list:
                    tmp = byte_array_intersect(h,dh)
                    if len(tmp) > 0:
                        new_diff_hs.append(tmp)
            self.hs_diff = new_diff_hs
        else:
            self.hs_list = []
            self.hs_diff = []
                
                    
    def add_lazy_tf_rule(self, ntf, rule_id,port):
        self.lazy_rule_ids.append((ntf,rule_id,port))
        
    def apply_lazy_tf_rule(self):
        result = [self.copy()]
        result[0].lazy_rule_ids = []
        for (ntf,rule_id,port) in self.lazy_rule_ids:
            temp = []
            for elemHS in result:
                temp.extend(ntf.T_rule(rule_id,elemHS,port))
            result = temp;
        return result
               
    def push_applied_tf_rule(self,ntf,rule_id,in_port):
        self.applied_rule_ids.append((ntf,rule_id,in_port))
        
    def pop_applied_tf_rule(self):
        return self.applied_rule_ids.pop()
        
    def __str__(self):
        return self.to_string()
        
    
