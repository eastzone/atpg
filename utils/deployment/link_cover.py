#!/usr/bin/python
import networkx as nx
import time, random, copy

topology_file = open("data/topology.data")
G=nx.read_edgelist(topology_file)
topology_file.close()

#Only numbers are end terminals
end_terminals = [unicode(str(x)) for x in range(1, 100)]

links = G.edges()
shortest_paths = nx.shortest_path(G)

rule_lists = []
for source in end_terminals:
    for destination in end_terminals:
        try:
            if destination != source:
                rule_lists.append(shortest_paths[source][destination])
        except:
            pass

start_packets = len(rule_lists)
result_rule_lists = []

st = time.time()

# Remove end links
new_links = copy.deepcopy(links)
for link in links:
    (source, destination) = link
    if source in end_terminals or destination in end_terminals:
        new_links.remove(link)
links = new_links

# Min-Set-Cover
while len(links) > 0:

    lucky_index = random.randint(0, len(rule_lists)-1)
    lucky_path = rule_lists[lucky_index]
    
    # Break the path into links, excluding the end terminals
    for index in xrange(1, len(lucky_path)-2):
        new = False
        if (lucky_path[index],lucky_path[index+1]) in links:
            new = True 
            result_rule_lists.append(lucky_path)
            
        # Rules that have been hit already
        if new: 
            for index2 in xrange(1, len(lucky_path)-2):
                if (lucky_path[index],lucky_path[index+1]) in links:
                    links.remove((lucky_path[index],lucky_path[index+1]))
            break

end_packets = len(result_rule_lists)
    
en = time.time()
print "Compression: Start=%d, End=%d, Ratio=%f, Time=%f" % (start_packets, end_packets, float(end_packets)/start_packets, en-st)

# Now we start to filter CSV file to select ones that we're interested in.

# Step 1: Build "DNS"
hosts_file = open('data/hosts.txt')
ips_file = open('data/ips.txt')

ip_to_host_dict = {}
for ip in ips_file:
    host = hosts_file.readline().split('.')[0]
    ip_to_host_dict[ip.strip()] = host
    
hosts_file.close()
ips_file.close()

# Step 2: Build test pairs
test_pairs = []
for rule_list in result_rule_lists:
    test_pairs.append(("swan-ap%s"%rule_list[0], "swan-ap%s"%rule_list[-1]))

# Step 3: Filter
results_file = open('data/output.csv')
new_results_file = open('data/output_filtered.csv', 'w')
for line in results_file:
    components = line.split(',')
    source = components[1].strip('\"')
    try:
        destination = ip_to_host_dict[components[2].strip('\"')]
    except:
        continue
    if (source, destination) in test_pairs or (destination, source) in test_pairs:
        new_results_file.write(line)
    
results_file.close()
new_results_file.close()








