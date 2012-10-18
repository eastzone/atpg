#!/usr/bin/python
'''
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
    
    Author: James Hongyi Zeng (hyzeng_at_stanford.edu)
'''

import socket, time, re, urllib2, logging
from subprocess import Popen, PIPE

class MonitorClient():
    def __init__(self, peer_url, period = 10, update_period = 60):
        self.peer_names = []
        self.ping_objects = {}
        self.period = period
        self.peer_url = peer_url
        
        self.update_period = update_period
        self.update_peer_names()     
        
    def run(self):
        reports = []
        last_time_update_url = time.time()
        
        while True:
            for hostname in self.peer_names:
                 #print hostname
                 try:
                     host_ip = socket.gethostbyname(hostname)
                 except:
                     host_ip = hostname
                 #print host_ip
                 ping = Popen(["ping", "-c", "1", "-w", "1", host_ip], stdout = PIPE)
                 matcher = re.search("min/avg/max/mdev = (\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)", ping.stdout.read())
                 if matcher:
                     result = matcher.group(1)
                 else:
                     result = "+Inf"
                 
                 report = "%f %s %s" % (time.time(), host_ip, result)
                 logging.debug(report)
                 reports.append(report)             
            
            # Have some rest!
            time.sleep(self.period)
            
            suffix = time.strftime('%m%d')
            report_file = open('report_%s.txt' % (suffix), 'a')
            for report in reports:
                report_file.write(report + '\n')
            report_file.close()
            reports = []
                
            if time.time() - last_time_update_url > self.update_period:
                self.update_peer_names()
                last_time_update_url = time.time()
                logging.info("Peer names updated")
                
                
    def update_peer_names(self):
        try:
            response = urllib2.urlopen(self.peer_url)
            self.peer_names = []
            for line in response:
                if line != "\n":
                    self.peer_names.append(line.rstrip())
        except:
            pass
        
def main():
    description = "ATPG reachability monitor"
    logging.basicConfig(level=logging.DEBUG)
    
    client = MonitorClient("http://dl.dropbox.com/u/10554311/peers.txt")
    client.run()
     
    
if __name__ == '__main__':
    main()
    
