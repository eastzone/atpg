'''
    <Run reachability test on Internet2>
Created on Mar 11, 2012

@author: James Hongyi Zeng
'''
from utils.load_internet2_backbone import *
from config_parser.juniper_parser import juniperRouter
from headerspace.hs import *
from headerspace.applications import *
from time import time
#from multiprocessing import Pool

ntf_global = []
ttf_global = []
dst_port_ids_global = []

def find_reachability_multiprocess(in_port, input_pkt):
    paths = []
    propagation = []
 
    p_node = {}
    p_node["hdr"] = input_pkt
    p_node["port"] = in_port
    p_node["visits"] = []
    p_node["hs_history"] = []
    propagation.append(p_node)
    #loop_count = 0
    while len(propagation)>0:
        #get the next node in propagation graph and apply it to NTF and TTF
        print "Propagation has length: %d"%len(propagation)
        
        results = map(two_step, propagation)
        
        tmp_propagate = []
        for result in results:
            (local_propagation, local_paths) = result
            tmp_propagate.extend(local_propagation)
            paths.extend(local_paths)
        
        propagation = tmp_propagate
                
    return paths


def two_step (p_node):
    propagation = []
    paths = []
    
    next_hp = ntf_global.T(p_node["hdr"],p_node["port"])
    for (next_h,next_ps) in next_hp:    

        for next_p in next_ps:
            if next_p in dst_port_ids_global:
                reached = {}
                reached["hdr"] = next_h
                reached["port"] = next_p
                reached["visits"] = p_node["visits"]+[p_node["port"]]
                #reached["visits"] = list(p_node["visits"])
                #reached["visits"].append(p_node["port"])
                reached["hs_history"] = list(p_node["hs_history"])
                paths.append(reached)
            else:
                linked = ttf_global.T(next_h,next_p)
                for (linked_h,linked_ports) in linked:
                    for linked_p in linked_ports:
                        new_p_node = {}
                        new_p_node["hdr"] = linked_h
                        new_p_node["port"] = linked_p
                        new_p_node["visits"] = p_node["visits"]+[p_node["port"]]
                        #new_p_node["visits"].append(p_node["port"])
                        #new_p_node["visits"].append(next_p)
                        new_p_node["hs_history"] = list(p_node["hs_history"])
                        new_p_node["hs_history"].append(p_node["hdr"])
                        if linked_p in dst_port_ids_global:
                            paths.append(new_p_node)
                        elif linked_p in new_p_node["visits"]:
                            #loop_count += 1
                            pass
                            #print "WARNING: detected a loop - branch aborted: \nHeaderSpace: %s\n Visited Ports: %s\nLast Port %d "%(\
                            #    new_p_node["hdr"],new_p_node["visits"],new_p_node["port"])
                        else:
                            #tmp_propagate.append(new_p_node)
                            propagation.append(new_p_node)

    return (propagation, paths)
    

def main():
    global ntf_global
    global ttf_global
    global dst_port_ids_global 
    
    ntf_global = load_internet2_backbone_ntf()
    ttf_global = load_internet2_backbone_ttf()
    (port_map,port_reverse_map) = load_internet2_backbone_port_to_id_map()
    cs = juniperRouter(1)
    output_port_addition = cs.PORT_TYPE_MULTIPLIER * cs.OUTPUT_PORT_TYPE_CONST
    
    all_x = byte_array_get_all_x(ntf_global.length)
    
    #cs.set_field(all_x, "vlan", 32, 0)
    #cs.set_field(all_x, "ip_dst", dotted_ip_to_int("64.57.28.243"), 8)
    #cs.set_field(all_x, "ip_src", dotted_ip_to_int("172.27.76.233"), 0)
    #cs.set_field(all_x, "tcp_dst", 22, 0)
    #cs.set_field(all_x, "ip_proto", 6, 0)
    
    test_pkt = headerspace(ntf_global.length)
    test_pkt.add_hs(all_x)
    
    src_port_id = port_map["atla"]["xe-0/1/1"]
    dst_port_ids_global = [port_map["atla"]["xe-1/0/2"]+output_port_addition]

    st = time()
    paths = find_reachability_multiprocess(src_port_id,test_pkt)
    
    #paths = find_reachability(ntf_global, ttf_global, src_port_id, dst_port_ids_global, test_pkt)
    en = time()
    print_loops(paths, port_reverse_map)
    print len(paths)
    
    #loops = detect_loop(ntf,ttf,loop_port_ids,port_reverse_map,None,output_port_addition)
    #en = time()
    #print_loops(loops, port_reverse_map)
    #print len(loops)
    
    print en-st

if __name__ == "__main__":
    main()
