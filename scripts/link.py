#!/usr/bin/python
import sqlite3, time, random

DATABASE_FILE = "../atpg/work/i2-100-edge.sqlite"

rule_lists = []
query = "SELECT rules FROM test_packets_globally_compressed"
conn = sqlite3.connect(DATABASE_FILE, 6000)
rows = conn.execute(query)
for row in rows:
    rule_lists.append(row[0].split())
conn.close()

st = time.time()
    
rule_ids_set = set()
for rule_list in rule_lists:
    for rule in rule_list:
        if rule.startswith("link"):
            rule_ids_set.add(rule)
    
start_packets = len(rule_lists)
result_rule_lists = []
while(len(rule_ids_set) > 0):
    lucky_index = random.randint(0, len(rule_lists)-1)
    rule_list = rule_lists[lucky_index]
    
    for r in rule_list:
        new = False
        if r.startswith("link"):
            if r in rule_ids_set:
                new = True 
                result_rule_lists.append(rule_list)
        
            # Rules that have been hit already
            if new: 
                for r2 in rule_list:
                    if r2.startswith("link"):
                        if r2 in rule_ids_set:
                            rule_ids_set.remove(r2)
                del rule_lists[lucky_index]                
                break
    
end_packets = len(result_rule_lists)
    
en = time.time()
print "Compression: Start=%d, End=%d, Ratio=%f, Time=%f" % (start_packets, end_packets, float(end_packets)/start_packets, en-st)
