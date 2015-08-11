#!/usr/bin/env python
'''
    <ATPG for Internet2>

@author: James Hongyi Zeng
'''
from utils.load_internet2_backbone import *
from headerspace.applications import *
from headerspace.hs import *
from multiprocessing import Pool, cpu_count
from config_parser.juniper_parser import juniperRouter
import random, time, sqlite3, os, json, socket, struct
from argparse import ArgumentParser

ntf_global = ""
ttf_global = ""
src_port_ids_global = set()
dst_port_ids_global = set()

DATABASE_FILE = "work/internet2.sqlite"
TABLE_NETWORK_RULES = "network_rules"
TABLE_TOPOLOGY_RULES = "topology_rules"
TABLE_RESULT_RULES = "result_rules"
TABLE_TEST_PACKETS = "test_packets"
TABLE_TEST_PACKETS_GLOBALLY_COMPRESSED = "test_packets_globally_compressed"
TABLE_TEST_PACKETS_LOCALLY_COMPRESSED = "test_packets_locally_compressed"

TABLE_SCRATCHPAD = "scratch_pad"
CPU_COUNT = cpu_count()

port_reverse_map_global = {}
port_map_global = {}


def parse_non_wc_field(field, right_wc):
    '''
    right_wc can be True for IP fields and False for non-IP fields. It indicates whether this field should be treated
    as a right-hand masked field or not.
    '''
    values = []
    wildcards = []
    if right_wc:
        found_right_wc = -1
    else:
        found_right_wc = 0
    for i in range (len(field)):
        for j in range (4):
            next_bit = (field[i] >> (2 * j)) & 0x03
            if right_wc and found_right_wc == -1 and next_bit != 0x03:
                # detect when we have scanned all right wildcarded bits
                found_right_wc = j + i * 4 + 1
                values.append(0)
            new_values = []
            for value in values:
                if (next_bit == 0x02 or next_bit == 0x03) and found_right_wc != -1:
                    new_values.append(value + 2 ** (j + i * 4))
                if (next_bit == 0x01 or next_bit == 0x03) and found_right_wc != -1:
                    new_values.append(value)
            values = new_values
    
    return [values, found_right_wc]

def parse_normal_field(field, right_wc):
    '''
    right_wc can be True for IP fields and False for non-IP fields. It indicates whether this field should be treated
    as a right-hand masked field or not.
    '''
    values = [0]
    wildcards = []
    if right_wc:
        found_right_wc = -1
    else:
        found_right_wc = 0
    for i in range (len(field)):
        for j in range (4):
            next_bit = (field[i] >> (2 * j)) & 0x03
            if right_wc and found_right_wc == -1 and next_bit != 0x03:
                # detect when we have scanned all right wildcarded bits
                found_right_wc = j + i * 4 + 1
                values.append(0)
            new_values = []
            for value in values:
                if (next_bit == 0x02 or next_bit == 0x03) and found_right_wc != -1:
                    new_values.append(value + 2 ** (j + i * 4))
                if (next_bit == 0x01 or next_bit == 0x03) and found_right_wc != -1:
                    new_values.append(value)
            values = new_values
    
    return [values, found_right_wc]

def parse_hs(hs_format, hs):
    
    match = hs
    
    fields = ["mac_src", "mac_dst", "vlan", "ip_src", "ip_dst", "ip_proto", "transport_src", "transport_dst"]
    openflow_entry = {}
    for field in fields:
        if "%s_pos" % field not in hs_format.keys():
            continue
        
        position = hs_format["%s_pos" % field]
        len = hs_format["%s_len"%field]
        wildcarded = True
        field_match = bytearray()
        for i in range(2 * len):
            field_match.append(match[position * 2 + i])
            if match[position * 2 + i] != 0xff:
                wildcarded = False

        if wildcarded:
            if field == "ip_src" or field == "ip_dst":
                openflow_entry["%s_wc" % field] = 32
            else:
                openflow_entry["%s_wc" % field] = 1
            openflow_entry["%s_match" % field] = [0]
        else:
            if field == "ip_src" or field == "ip_dst":
                parsed = parse_non_wc_field(field_match, True)
                if parsed[0] != []:
                    parsed[0][0] = socket.inet_ntoa(struct.pack('!L',parsed[0][0]))
            else:
                parsed = parse_normal_field(field_match, False)
            openflow_entry["%s_wc" % field] = parsed[1]
            openflow_entry["%s_match" % field] = parsed[0]
    
    return openflow_entry

def find_reachability_test(NTF, TTF, in_port, out_ports, input_pkt):
    paths = []
    propagation = []
 
    p_node = {}
    p_node["hdr"] = input_pkt
    p_node["port"] = in_port
    p_node["visits"] = []
    #p_node["hs_history"] = []
    propagation.append(p_node)
    #loop_count = 0
    while len(propagation) > 0:
        #get the next node in propagation graph and apply it to NTF and TTF
        #print "Propagation has length: %d"%len(propagation)
        tmp_propagate = []
        for p_node in propagation:
            next_hp = NTF.T(p_node["hdr"], p_node["port"])
            for (next_h, next_ps) in next_hp:            
                for next_p in next_ps:
                    new_p_node = {}
                    new_p_node["hdr"] = next_h
                    new_p_node["port"] = next_p
                    new_p_node["visits"] = list(p_node["visits"])
                    new_p_node["visits"].append(p_node["port"])
                    #new_p_node["hs_history"] = list(p_node["hs_history"])
                  
                    # Reached an edge port
                    if next_p in out_ports:
                        paths.append(new_p_node)
                        
                    linked = TTF.T(next_h, next_p)
                    
                    for (linked_h, linked_ports) in linked:
                        for linked_p in linked_ports:
                            new_p_node = {}
                            new_p_node["hdr"] = linked_h
                            new_p_node["port"] = linked_p
                            new_p_node["visits"] = list(p_node["visits"])
                            new_p_node["visits"].append(p_node["port"])
                            #new_p_node["hs_history"] = list(p_node["hs_history"])
                            #new_p_node["hs_history"].append(p_node["hdr"])
                            if linked_p not in new_p_node["visits"]:
                                tmp_propagate.append(new_p_node)
                                
        propagation = tmp_propagate
                
    return paths

def print_paths_to_database(paths, reverse_map, table_name):
    # Timeout = 6000s
    
    insert_string = "INSERT INTO %s VALUES (?, ?, ?, ?, ?, ?, ?)" % table_name
    
    queries = []
    for p_node in paths:
        path_string = ""
        for port in p_node["visits"]:
            path_string += ("%d " % port)
        path_string += ("%d " % p_node["port"])
        port_count = len(p_node["visits"]) + 1
        
        rl_id = ""
        for (n, r, s) in p_node["hdr"].applied_rule_ids:
            rl_id += (r + " ")
        rule_count = len(p_node["hdr"].applied_rule_ids)
        
        input_port = p_node["visits"][0]
        output_port = p_node["port"]
        output_hs = p_node["hdr"].copy()
        applied_rule_ids = list(output_hs.applied_rule_ids)
        input_hs = trace_hs_back(applied_rule_ids, output_hs, output_port)[0]
        header_string = json.dumps(parse_hs(juniperRouter(1).hs_format, input_hs.hs_list[0]))
        
        #header_string = byte_array_to_pretty_hs_string(input_hs.hs_list[0])
        queries.append((header_string, input_port, output_port, path_string, port_count, rl_id, rule_count))
    
    conn = sqlite3.connect(DATABASE_FILE, 6000)
    for query in queries:    
        conn.execute(insert_string, query)
        
    conn.commit()
    conn.close()

def path_compress(paths):
    ''' Compress Paths using Greedy Algorithm
    An implementation based on Min-Set-Cover
    '''
    result_paths = []
    exercised_rules = set()
    random.shuffle(paths)
    for p_node in paths:
        new_rule = False
        for (n, r, s) in p_node["hdr"].applied_rule_ids:
            if r not in exercised_rules:
                new_rule = True
                break
        if new_rule:
            result_paths.append(p_node)
            for (n, r, s) in p_node["hdr"].applied_rule_ids:
                exercised_rules.add(r)
    
    return result_paths

def rule_lists_compress(rule_lists):   
    st = time.time()
    
    rule_ids_set = set()
    for rule_list in rule_lists:
        rule_ids_set |= set(rule_list)
    
    #print "Reachable Rules: %d" % len(rule_ids_set)
    start_packets = len(rule_lists)
    result_rule_lists = []
    while(len(rule_ids_set) > 0):
        lucky_index = random.randint(0, len(rule_lists)-1)
        rule_list = rule_lists[lucky_index]
        for r in rule_list:
            if r in rule_ids_set:
                result_rule_lists.append(rule_list)
        
                # Rules that have been hit already
                rule_ids_set -= set(rule_list)
                del rule_lists[lucky_index]                
                break
    
    end_packets = len(result_rule_lists)
    
    en = time.time()
    
    print "Global Compression: Start=%d, End=%d, Ratio=%f, Time=%f" % (start_packets, end_packets, float(end_packets)/start_packets, en-st)
    print_rule_lists_to_database(result_rule_lists, TABLE_SCRATCHPAD)

def find_test_packets(src_port_id):

    # Generate All-X packet
    all_x = byte_array_get_all_x(ntf_global.length)
    test_pkt = headerspace(ntf_global.length)
    test_pkt.add_hs(all_x)
       
    st = time.time()
    paths = find_reachability_test(ntf_global, ttf_global, src_port_id, dst_port_ids_global, test_pkt)
    en = time.time()
    
    print_paths_to_database(paths, port_reverse_map_global, TABLE_TEST_PACKETS)
    result_string = "Port:%d, Path No:%d, Time: %fs" % (src_port_id, len(paths), en - st)    
    print result_string

    # Compress
    st = time.time()
    paths = path_compress(paths)
    en = time.time()

    result_string = "Port:%d, Compressed Path No:%d, Time: %fs" % (src_port_id, len(paths), en - st)    
    print result_string
    
    print_paths_to_database(paths, port_reverse_map_global, TABLE_TEST_PACKETS_LOCALLY_COMPRESSED)

    return len(paths)

def chunks(l, n):
    """ Yield successive n chunks from l.
    """
    sub_list_length = len(l) / n        
    if sub_list_length == 0:
        sub_list_length = len(l)    
    return [l[i:i+sub_list_length] for i in range(0, len(l), sub_list_length)]

def merge_chunks(chunks):
    result = sum(chunks, [])
    return result

def print_rule_lists_to_database(result_rule_lists, table_name):
    conn = sqlite3.connect(DATABASE_FILE, 6000)
    query = "INSERT INTO %s VALUES (?, ?)" % table_name
   
    for rule_list in result_rule_lists:
        conn.execute(query, (" ".join(rule_list), len(rule_list)))
     
    conn.commit()    
    conn.close()
    
def read_rule_lists_from_database(table_name):
    result_rule_lists = []
    conn = sqlite3.connect(DATABASE_FILE, 6000)
    query = "SELECT rules FROM %s"  % TABLE_SCRATCHPAD
    rows = conn.execute(query)
    
    for row in rows:
        result_rule_lists.append(row[0].split())
    conn.close()
    return result_rule_lists

def main():  
    global src_port_ids_global
    global dst_port_ids_global
    global port_map_global
    global port_reverse_map_global
    global ntf_global
    global ttf_global
    global DATABASE_FILE
    
    parser = ArgumentParser(description="Generate Test Packets for Internet2")
    parser.add_argument("-p", dest="percentage", type=int,
                      default="100",
                      help="Percentage of test terminals")
    parser.add_argument("-f", dest="filename",
                      default="internet2.sqlite",
                      help="Filename of the database")
    parser.add_argument("-e", action="store_true",
                      default=False,
                      help="Edge port only")
    args = parser.parse_args()
    
    DATABASE_FILE = "work/%s" % args.filename
     
    cs = juniperRouter(1)
    output_port_addition = cs.PORT_TYPE_MULTIPLIER * cs.OUTPUT_PORT_TYPE_CONST
     
    # Load .tf files
    ntf_global = load_internet2_backbone_ntf()
    ttf_global = load_internet2_backbone_ttf()
    (port_map_global, port_reverse_map_global) = load_internet2_backbone_port_to_id_map()
    
    # Initialize the database
    if os.access(DATABASE_FILE, os.F_OK):
        os.remove(DATABASE_FILE)
    
    conn = sqlite3.connect(DATABASE_FILE)
    conn.execute('CREATE TABLE %s (rule TEXT, input_port TEXT, output_port TEXT, action TEXT, file TEXT, line TEXT)' % TABLE_NETWORK_RULES)
    conn.execute('CREATE TABLE %s (rule TEXT, input_port TEXT, output_port TEXT)' % TABLE_TOPOLOGY_RULES)
    conn.execute('CREATE TABLE %s (header TEXT, input_port INTEGER, output_port INTEGER, ports TEXT, no_of_ports INTEGER, rules TEXT, no_of_rules INTEGER)' % TABLE_TEST_PACKETS)
    conn.execute('CREATE TABLE %s (header TEXT, input_port INTEGER, output_port INTEGER, ports TEXT, no_of_ports INTEGER, rules TEXT, no_of_rules INTEGER)' % TABLE_TEST_PACKETS_LOCALLY_COMPRESSED)
    conn.execute('CREATE TABLE %s (rules TEXT, no_of_rules INTEGER)' % TABLE_TEST_PACKETS_GLOBALLY_COMPRESSED)
    conn.execute('CREATE TABLE %s (rule TEXT)' % TABLE_RESULT_RULES)

    rule_count = 0
    for tf in ntf_global.tf_list:
        rule_count += len(tf.rules)
        for rule in tf.rules:
            query = "INSERT INTO %s VALUES (?, ?, ?, ?, ?, ?)" % TABLE_NETWORK_RULES
            conn.execute(query, (rule['id'],' '.join(map(str, rule['in_ports'])), ' '.join(map(str, rule['out_ports'])), rule['action'], rule["file"], ' '.join(map(str, rule["line"]))))
    print "Total Rules: %d" % rule_count
    conn.commit()
    
    rule_count = len(ttf_global.rules) 
    for rule in ttf_global.rules:
        query = "INSERT INTO %s VALUES (?, ?, ?)" % TABLE_TOPOLOGY_RULES 
        conn.execute(query, (rule['id'],' '.join(map(str, rule['in_ports'])), ' '.join(map(str, rule['out_ports']))))  
    print "Total Links: %d" % rule_count
   
    # Generate all ports
    for rtr in port_map_global.keys():
        src_port_ids_global |= set(port_map_global[rtr].values())
    
    
    total_length = len(src_port_ids_global)
    if args.e == True:
        for rule in ttf_global.rules:
            if rule['out_ports'][0] in src_port_ids_global:
                src_port_ids_global.remove(rule['out_ports'][0])    
    
    new_length = len(src_port_ids_global)* args.percentage / 100
    src_port_ids_global = random.sample(src_port_ids_global, new_length)
    print "Total Length: %d" % total_length
    print "New Length: %d" % new_length
    
    for port in src_port_ids_global:
        port += output_port_addition
        dst_port_ids_global.add(port)
    
    #src_port_ids_global = [300013]
    #dst_port_ids_global = [320010]
    
    conn.commit()
    conn.close()
    
    # Run reachability
    start_time = time.time()
    
    pool = Pool()
    result = pool.map_async(find_test_packets, src_port_ids_global)

    # Close
    pool.close()
    pool.join()
    
    end_time = time.time()
    
    test_packet_count = result.get()
    total_paths = sum(test_packet_count)    
    print "========== Before Compression ========="
    print "Total Paths = %d" % total_paths
    print "Average packets per port = %f" % (float(total_paths) / len(src_port_ids_global))
    print "Total Time = %fs" % (end_time - start_time)
    
    #Global Compressing 
    start_time = time.time()
       
    conn = sqlite3.connect(DATABASE_FILE, 6000)    
    result_rule_lists = []
    query = "SELECT rules FROM %s"  % TABLE_TEST_PACKETS_LOCALLY_COMPRESSED
    rows = conn.execute(query)

    for row in rows:
        result_rule_lists.append(row[0].split())
    conn.close()
  
    chunk_size = 80000
    while(True):
        print "Start a new round!"
        conn = sqlite3.connect(DATABASE_FILE, 6000)
        conn.execute('DROP TABLE IF EXISTS %s' % TABLE_SCRATCHPAD)
        conn.execute('CREATE TABLE %s (rules TEXT, no_of_rules INTEGER)' % TABLE_SCRATCHPAD)
        conn.commit()    
        conn.close()
        
        start_len = len(result_rule_lists)
        print start_len
        
        pool = Pool()        
        no_of_chunks = len(result_rule_lists) / chunk_size + 1      
        rule_list_chunks = chunks(result_rule_lists, no_of_chunks)            
        result = pool.map_async(rule_lists_compress, rule_list_chunks)

        # Close
        pool.close()
        pool.join()
        result.get()
        
        print "End of this round."
        
        result_rule_lists = read_rule_lists_from_database(TABLE_SCRATCHPAD)
        
        end_len = len(result_rule_lists)
        if(float(end_len) / float(start_len) > 0.99):
            break

    end_time = time.time()
    
    query = "INSERT INTO %s VALUES (?, ?)" % TABLE_TEST_PACKETS_GLOBALLY_COMPRESSED
    query2 = "INSERT INTO %s VALUES (?)" % TABLE_RESULT_RULES
    
    total_paths = len(result_rule_lists)
    total_length = 0
    
    conn = sqlite3.connect(DATABASE_FILE, 6000)
    conn.execute('DROP TABLE IF EXISTS %s' % TABLE_TEST_PACKETS_GLOBALLY_COMPRESSED)
    conn.execute('CREATE TABLE %s (rules TEXT, no_of_rules INTEGER)' % TABLE_TEST_PACKETS_GLOBALLY_COMPRESSED)

    for rule_list in result_rule_lists:
        total_length += len(rule_list)
        conn.execute(query, (" ".join(rule_list), len(rule_list)))
        for rule in rule_list:
            conn.execute(query2, (rule,))
     
    conn.commit()    
    conn.close()
    
    print "========== After Compression ========="
    print "Total Paths = %d" % total_paths
    print "Average packets per port = %f" % (float(total_paths) / len(src_port_ids_global))
    print "Average length of rule list = %f" % (float(total_length) / total_paths)
    print "Total Time = %fs" % (end_time - start_time)
    
if __name__ == "__main__":
    main()
