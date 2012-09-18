#!/usr/bin/env python
import sys, argparse, threading, time, math, random, json, os
import SimpleHTTPServer, SocketServer, Queue

import pylibopenflow.openflow as openflow
import pylibopenflow.output as output
import pylibopenflow.of.msg as of_msg
import pylibopenflow.of.simu as of_simu

from pinpoint import Pinpointer

class StanfordTopo:
    "Topology for Stanford backbone"

    PORT_ID_MULTIPLIER = 1
    INTERMEDIATE_PORT_TYPE_CONST = 1
    OUTPUT_PORT_TYPE_CONST = 2
    PORT_TYPE_MULTIPLIER = 10000
    SWITCH_ID_MULTIPLIER = 100000
    
    DUMMY_SWITCH_BASE = 1000
    
    PORT_MAP_FILENAME = "data/stanford/port_map.txt"
    TOPO_FILENAME = "data/stanford/backbone_topology.tf"
    
    dummy_switches = set()

    def __init__( self ):
        # Read topology info
        self.switch_id_to_name = {}
        self.ports = self.load_ports(self.PORT_MAP_FILENAME)        
        self.links = self.load_topology(self.TOPO_FILENAME)
        self.switches = self.ports.keys()
        self.switch_name_to_errors = {}
        self.link_id_to_errors = {}
            
    def load_ports(self, filename):
        ports = {}
        f = open(filename, 'r')
        for line in f:
            if line.startswith("$"):
                switch_name = line[1:].strip()
                stored = False
            elif not line.startswith("$") and line != "":
                tokens = line.strip().split(":")
                port_flat = int(tokens[1])
                
                dpid = port_flat / self.SWITCH_ID_MULTIPLIER
                port = port_flat % self.PORT_TYPE_MULTIPLIER
                
                if dpid not in ports.keys():
                    ports[dpid] = set()
                if port not in ports[dpid]:
                    ports[dpid].add(port)  
                if not stored:
                    self.switch_id_to_name[dpid] = switch_name
                    stored = True          
        f.close()
        return ports
        
    def load_topology(self, filename):
        links = set()
        f = open(filename, 'r')
        for line in f:
            if line.startswith("link"):
                tokens = line.split('$')
                src_port_flat = int(tokens[1].strip('[]').split(', ')[0])
                dst_port_flat = int(tokens[7].strip('[]').split(', ')[0])
                link_id = tokens[-2]
                links.add((src_port_flat, dst_port_flat, link_id))
        f.close()
        return links
        
    def dump_json(self, filename):
        topo = StanfordTopo()
        nodes = []
        links = []
        
        for (src_port, dst_port, link_id) in topo.links:
            if link_id not in self.link_id_to_errors.keys():
                self.link_id_to_errors[link_id] = False
            if self.link_id_to_errors[link_id]:
                links.append({"source": src_port / topo.SWITCH_ID_MULTIPLIER - 1, 
                  "target":dst_port / topo.SWITCH_ID_MULTIPLIER - 1,
                  "value": 1,
                  "problems": 1,
                  "name" : link_id
                  })                     
            else: 
                links.append({"source": src_port / topo.SWITCH_ID_MULTIPLIER - 1, 
                  "target":dst_port / topo.SWITCH_ID_MULTIPLIER - 1,
                  "value": 1,
                  "name" : link_id
                  }) 
                    
        for index in xrange(0, len(topo.switch_id_to_name.keys())):
            switch_name = topo.switch_id_to_name[index+1]
            if switch_name not in self.switch_name_to_errors.keys():
                self.switch_name_to_errors[switch_name] = []
            
            if switch_name.startswith("bbr"):
                group = 0
            else:
                group = 1
           
            if not self.switch_name_to_errors[switch_name] == []:
                problems = self.switch_name_to_errors[switch_name]
                json_string = "$".join(problems)
                json_string.replace('\r','')
                json_string.replace('\n','')
                
                nodes.append({"name":switch_name,"group":group, "problems":json_string} )
            else:
                nodes.append({"name":switch_name,"group":group} )
        
        json_object = {"nodes":nodes,"links":links}
        f = open(filename,'w')
        json.dump(json_object, f)
        f.close

    def inject_errors(self, error_rules):
        # error_rules is a set of error rule ids
        p = Pinpointer()
        for rule in error_rules:
            tokens = rule.split("_")
            if rule not in self.switch_name_to_errors["_".join(tokens[0:2])]:
                self.switch_name_to_errors["_".join(tokens[0:2])].extend(p.get_config_lines(rule))

    def remove_errors(self, error_rules):
        p = Pinpointer()
        for rule in error_rules:
            tokens = rule.split("_")
            lines = p.get_config_lines(rule)
            for line in lines:
                try:
                    self.switch_name_to_errors["_".join(tokens[0:2])].remove(line)
                except:
                    pass
                
    def inject_link_errors(self, error_rules):
        for rule in error_rules:
            self.link_id_to_errors[rule] = True
    
    def remove_link_errors(self, error_rules):
        for rule in error_rules:
            try:
                self.link_id_to_errors[rule] = False
            except:
                pass
                
    def clear_errors(self):
        for switch in self.switch_name_to_errors.keys():
            self.switch_name_to_errors[switch] = []
        for link_id in self.link_id_to_errors.keys():
            self.link_id_to_errors[link_id] = False
        

class DemoHTTPHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/web/data"):
            last_time = os.path.getmtime('.' + self.path)
            elapse = time.time() - last_time
            if elapse > 5:
                self.send_response(304)
                return
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
        
    def do_POST(self):
        if self.path.startswith("/web/inject"):
            self.do_inject_external()
        elif self.path.startswith("/web/reset"):
            self.do_reset_external()
        elif self.path.startswith("/web/detect"):
            self.do_detect_external()
        self.send_response(200)  
    def do_inject_external(self):
        pass
    def do_reset_external(self):
        pass
    def do_detect_external(self):
        pass

class TCPServer(SocketServer.TCPServer): 
     allow_reuse_address = True 

class Application:
    CONTROLLER_DPID = 0xCAFECAFE
    
    def main(self):
        # Start the periodic call in the GUI to check if the queue contains
        # anything 
        try:   
            while True:
                self.processOF()
                self.processError()
                time.sleep(1)
        except KeyboardInterrupt:
            # Stop Thread 1
            self.running = False
            
            # Stop Thread 3
            self.httpd.shutdown()
            
            return -1      

    def __init__(self, controller='localhost', port=6633):
        self.controller = controller
        self.port = port
        self.received_packet_count = 0
        self.topology_real = StanfordTopo()
        self.topology_discovered = StanfordTopo()
        self.pinpointer = Pinpointer()
        
        # Content: String!
        self.queue_GUI_to_OF = Queue.Queue()
        # Contnet: OF message!
        self.queue_OF_to_GUI = Queue.Queue()
        
        self.running = True
    	
    	# Thread 1: OF thread
    	self.thread1 = threading.Thread(target=self.connectToController)
        #self.thread1.start()
        
        # Thread 2: Connect to run pinpointer
        self.errors = []
        self.test_packets = []
        self.queue_pinpoint_to_GUI = Queue.Queue()
        self.thread2 = None
        
        # Thread 3: WebServer
        DemoHTTPHandler.do_inject_external = self.do_inject
        DemoHTTPHandler.do_reset_external = self.do_reset
        DemoHTTPHandler.do_detect_external = self.do_detect
        self.httpd = TCPServer(("", 8000), DemoHTTPHandler)
        self.thread3 = threading.Thread(target=self.httpd.serve_forever)
        self.thread3.start()
        
        self.draw_callback(None)
        
    def do_inject(self):
        self.inject_callback(None) 
        
    def do_reset(self):
        self.topology_real.clear_errors()
        self.topology_discovered.clear_errors()
        self.topology_real.dump_json("web/data/data.json")
        self.topology_discovered.dump_json("web/data/dataDiscovered.json")
    
    def do_detect(self):
        if self.errors != []:
            self.thread2 = threading.Thread(target=self.pinpoint, args=(self.test_packets, self.errors))
            self.thread2.start()
            self.errors = []
        else:
            # Touch!
            self.topology_discovered.dump_json("web/data/dataDiscovered.json")
        
    def submit_callback(self, widget, entry):
        packet = entry.get_text()
        self.send_packet(packet)
   
    def draw_callback(self, widget):
        self.topology_real.dump_json("web/data/data.json")
        self.topology_discovered.dump_json("web/data/dataDiscovered.json")
    
    def inject_callback(self, widget):
        self.topology_real.clear_errors()
        self.topology_discovered.clear_errors()
        test_packets, errors = self.pinpointer.generate_test_case(1)
        self.errors = errors
        self.test_packets = test_packets
        link_errors = []
        device_errors = []
        for error in errors:
            if error.startswith("_"):
                link_errors.append(error)
            else:
                device_errors.append(error)
        self.topology_real.inject_errors(device_errors)
        self.topology_real.inject_link_errors(link_errors)
        self.topology_real.dump_json("web/data/data.json")
        
        #self.thread2 = threading.Thread(target=self.pinpoint, args=(test_packets, errors))
        #self.thread2.start()
                
    def send_packet(self, packet="Hello, World!\n"):
        self.queue_GUI_to_OF.put(packet)

    def processOF(self):        
        while not self.queue_OF_to_GUI.empty():
            msg = self.queue_OF_to_GUI.get()
            self.msgCallback(msg)
        if not self.running:
            sys.exit(1)
        return True

    def processError(self):     
        if self.queue_pinpoint_to_GUI.empty():
            return True
        
        link_errors = []
        device_errors = []
        
        errors = self.queue_pinpoint_to_GUI.get()
        for error in errors:
            if error.startswith("_"):
                link_errors.append(error)
            else:
                device_errors.append(error)
        self.topology_discovered.inject_errors(device_errors)
        self.topology_discovered.inject_link_errors(link_errors)
        self.topology_discovered.dump_json("web/data/dataDiscovered.json")
        return True
    
    def connectToController(self):   
        #Connect to controller
        ofmsg = openflow.messages()
        ofparser = of_msg.parser(ofmsg)
        ofsw = of_simu.switch(ofmsg, self.controller, self.port,
                              dpid=self.CONTROLLER_DPID,
                              parser=ofparser)
        ofsw.send_hello()
        
        while self.running:
            msg = ofsw.connection.msgreceive(blocking=False)
            # OF to GUI
            if msg != None:
                ofsw.receive_openflow(msg)
                self.queue_OF_to_GUI.put(msg)
            # GUI to OF
            while not self.queue_GUI_to_OF.empty():
                packet = self.queue_GUI_to_OF.get()
                ofsw.send_packet(inport=0, packet=packet)
            time.sleep(0.1)
            
    def pinpoint(self, test_packets, errors):
        errors = self.pinpointer.pin_point_test ( test_packets, errors ) 
        print "Fuck!!"   
        self.queue_pinpoint_to_GUI.put(errors)    
    

def main():
    parser = argparse.ArgumentParser(description='Python backend to communicate with Beacon', epilog="Report any bugs to hyzeng@stanford.edu")
    parser.add_argument('--controller', '-c', dest='controller', default="localhost")
    parser.add_argument('--port', '-p', dest='port', default=6633)
    parser.add_argument('--verbose', '-v', dest='verbose', action='count')
    args = parser.parse_args()
    
    port = args.port
    controller = args.controller
    if args.verbose == None:
        output.set_mode("INFO")
    else:
        output.set_mode("DBG")
    
    # Main Loop here 
    app = Application(controller=controller, port=port)
    app.main()

if __name__ == '__main__':
    main()
