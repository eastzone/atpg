#!/usr/bin/python
'''
    Description: A simple monitor to coordinate ping
    Author: James Hongyi Zeng (hyzeng_at_stanford.edu)
'''

import socket, time, json, subprocess
from ping import Ping
from argparse import ArgumentParser

UDP_PORT = 8888

def getMyIp():
    result = subprocess.check_output(['ifconfig'])
    results = result.split('\n')
    address = results[1].split()[1].lstrip('addr:')
    return address

class MonitorClient():
    def __init__(self, client_names, server_name, threshold = 500, period = 1, udp_port = UDP_PORT):
        self.client_names = client_names
        self.server_name = server_name
        self.socket = socket.socket( socket.AF_INET, socket.SOCK_DGRAM ) 
        self.ping_objects = {}
        self.period = period
        self.threshold = threshold
        self.udp_port = udp_port
        
        for hostname in self.client_names:
            self.ping_objects[hostname] = Ping(hostname, 10000, 60)
        
    def run(self):
        while True:
            for hostname in self.client_names:
                delay = self.ping_objects[hostname].do()
                if delay == None or delay > self.threshold:
                    self.report(hostname, time.time())     
            time.sleep(self.period)
    
    def report(self, hostname, timestamp):
        message = {}
        message['dst'] = hostname
        message['src'] = getMyIp()
        message['time'] = timestamp
        
        self.socket.sendto( json.dumps(message), (self.server_name, self.udp_port) )            
        
class MonitorServer():
    def __init__(self, client_names, udp_port = UDP_PORT):
        self.client_names = client_names
        self.udp_port = udp_port
        self.socket = socket.socket( socket.AF_INET, socket.SOCK_DGRAM ) 
        
    def run(self):
        self.socket.bind( ('0.0.0.0',self.udp_port) )
        while True:
            data, addr = self.socket.recvfrom( 1024 ) # buffer size is 1024 bytes
            print "received message:", data
        
def main():
    description = "Simple Ping monitor"
    parser = ArgumentParser(description=description)
    parser.add_argument("-s", dest="server_mode", action='store_true',
                      help="Server Mode")
    parser.add_argument("-n", dest="num_clients",type=int,
                      default=2,
                      help="Number of clients")
    args = parser.parse_args()
    
    client_names = ["10.0.0.%s" % x for x in range(1,args.num_clients+1)]
    if args.server_mode:
        server = MonitorServer(client_names)
        server.run()
    else:
        client = MonitorClient(client_names, '10.0.0.1')
        client.run()
     
    
if __name__ == '__main__':
    main()
    
