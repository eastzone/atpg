'''
    <Slice Class-- Part of HSA Library>
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
    
Created on Jan 26, 2011

@author: Peyman Kazemian
'''

from headerspace.tf import TF

class Slice(object):
    '''
    classdocs
    '''
    def __init__(self, length):
        '''
        Constructor
        '''
        self.length = length
        self.reservations = []
        self.port_to_reservation = {}
        
    def get_port_reservation(self,port):
        if "%s"%port in self.port_to_reservation:
            return self.port_to_reservation["%s"%port]
        else:
            return []

    def set_hs_reservation(self, ports, hs):
        '''
        set hs reservation on @port to new_hs
        NOTE: hs.hs_list MUST have only one wildcard expression
        '''
        if hs.length != self.length:
            return None
        hs_copy = hs.copy()
        port_list = list(ports)
        self.reservations.append((port_list,hs_copy))
        for port in ports:
            if "%s"%port not in self.port_to_reservation.keys():
                self.port_to_reservation["%s"%port] = []
            self.port_to_reservation["%s"%port].append(hs)
    
    def intersect(self,other_slice):
        result = Slice(self.length)
        for (port_list1,hs1) in other_slice.reservations:
            for (port_list2,hs2) in self.reservations:
                port_isect = [p for p in port_list1 if p in port_list2]
                if len(port_isect) > 0:
                    ihs = hs1.copy_intersect(hs2)
                    if ihs.count() > 0:
                        result.set_hs_reservation(port_isect, ihs) 
                    
        return result
    
    def __str__(self):
        result = ""
        for (p, hs) in self.reservations:
            result = result + "Port: %s - Header Space:\n %s\n"%(p,hs)
        return result


        