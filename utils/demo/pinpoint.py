#!/usr/bin/env python
'''
Pinpoint the problematic rule

@author: James Hongyi Zeng
'''
import sqlite3
import random
from argparse import ArgumentParser
from itertools import islice

DATABASE_FILE = "data/db2.sqlite"

class Pinpointer:
    hard_coded_index = 0

    def load_database(self):
        rules = set()
        test_packets = []
        
        query = "SELECT rules FROM test_packets_globally_compressed"
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute(query)
        
        for row in cursor:
            rules_tested = set(row[0].encode("ascii").split())
            for rule in rules_tested:
                rules.add(rule)
            test_packets.append(rules_tested)
        conn.close()
        return test_packets, rules

    def pin_point(self, passed_packets, failed_packets, answer):
        # James: Should not use answer directly!!!

        # Stage 1. Aggregate all passed/failed rules
        passed_rules = set()
        failed_rules = set()
        for packet in passed_packets:
            passed_rules |= packet
        for packet in failed_packets:
            failed_rules |= packet
        stage_1 = list(failed_rules - passed_rules)
        
        if len(stage_1) > 50:
            print "Stage 1 Too big. Return Stage 1 directly."
            return stage_1
        
        # Stage 2, Query the reserved packet
        passed_rules = set()
        failed_rules = set()
        
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        for rule in stage_1:
            query = " SELECT rules FROM test_packets_locally_compressed\n WHERE \n"
            query += " ".join([" rules LIKE", "\'%% %s %%\'\n" % rule])
            for rule_not in stage_1:
                if rule_not != rule:
                    query += " " + " ".join(["AND rules NOT like", "\'%%%s%%\'\n" % rule_not])

            query += " LIMIT 1 "    
            
            #print query
            cursor.execute(query)    
            for row in cursor:
                test_packet = set(row[0].encode("ascii").split())
                
                
                test_result = self.pass_or_fail(test_packet, answer)
                
                #print test_packet, test_result
                if test_result == True:
                    passed_rules.add(rule)
                else:
                    failed_rules.add(rule)
        
        conn.close()
        stage_2 = list(set(stage_1)-passed_rules)
        return stage_2

    # Map ONE failed rule to the configuration file
    # in addition, return n lines before and n lines after
    def get_config_lines( self, failed_rule, n=1):
        # Step 1, map rule to line and file
        step1 = {}
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        query = "SELECT file, line FROM network_rules WHERE rule LIKE " + "\'" + failed_rule + "\'";
        cursor.execute(query)
        for row in cursor:
            filename = row[0].encode("ascii")
            lines = map(int, row[1].encode("ascii").split())
        lines.sort()
        conn.close()
        
        # Step 2, replace file and line with actual contents
        if filename=='':
            return ['default'] * (2*n+1)
                
        result = []
        f = open('data/'+ filename, 'r')
        file_lines = f.readlines()
        f.close()
        
        for line in lines:
            
            contents = file_lines[line-n:line+n+1]
            
            new_contents = []
            line_no = line - n;
            for content in contents:                    
                new_contents.append( str(line_no) + ":" + content)
                line_no += 1
            result.extend(new_contents) 
                                   
        return result  

    def pass_or_fail(self, test_packet, answer):
        for rule in test_packet:
            if rule in answer:
                return False
        return True

    def pin_point_test ( self, test_packets, failed_rules ):
        
        print "Failed Rules:", failed_rules
        
        # Build the test case
        passed_packets = []
        failed_packets = []
        
        for packet in test_packets:
            for failed_rule in failed_rules:
                if failed_rule in packet:
                    failed_packets.append(packet)
                    break
                    
        for packet in test_packets:
            if packet not in failed_packets:
                passed_packets.append(packet)
                
        print "No. of passed packets:", len(passed_packets)
        print "No. of failed packets:", len(failed_packets)
        
        result = self.pin_point(passed_packets, failed_packets, failed_rules)
        
        print "Result:", result
        
        return result

    def generate_test_case( self, number_of_failures):
        test_packets, rules = self.load_database()    
        hard_coded_rules = [['bbra_rtr_507'], 
                            ['soza_rtr_365'], 
                            ['yozb_rtr_512'],
                            ['roza_rtr_39'],
                            ['sozb_rtr_399'],
                            ['pozb_rtr_47'],
                            ['coza_rtr_309'],
                           ]
        failed_rules = hard_coded_rules[self.hard_coded_index]
        print failed_rules
        self.hard_coded_index = (self.hard_coded_index + 1) % len(hard_coded_rules)
        
        #failed_rules = random.sample(rules, number_of_failures)
        #print failed_rules
        return test_packets, failed_rules
            

    def main(self):
        f = open("result.dat", "w")
        number_of_iterations = 1
        max_number_of_failures = 1
        for _ in xrange(0, number_of_iterations):
            number_of_failures = random.randint(1, max_number_of_failures)    
            test_packets, failed_rules = self.generate_test_case( number_of_failures)
            #failed_rules = ['_12']
            result_length = len(self.pin_point_test ( test_packets, failed_rules ))
            f.write("%d %f\n" % (number_of_failures, result_length) )
        f.close()
        #description = "Run fault localization algorithm"
        #parser = ArgumentParser(description=description)
        #parser.add_argument("integer", 
        #                  default=5,type=int,metavar='N',
        #                  help="Number of failures")
        #args = parser.parse_args()
        #number_of_failures = args.integer
        #result_length = pin_point_test ( number_of_failures )
 
if __name__ == "__main__":
    pinpointer = Pinpointer()
    pinpointer.main()
