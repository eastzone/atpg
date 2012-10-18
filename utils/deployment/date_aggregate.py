#!/usr/bin/python
import sys

in_file_name = sys.argv[1]
out_file_name = sys.argv[2]

granularity = 60
input_file = open(in_file_name)
epoch_dict = {}
for line in input_file:
    epoch_time = int(line.split('.')[0].strip('\"'))
    epoch_time_bucket = epoch_time / granularity
    if epoch_time_bucket not in epoch_dict.keys():
        epoch_dict[epoch_time_bucket] = 0
    epoch_dict[epoch_time_bucket] += 1
    
output_file = open(out_file_name, 'w')
keys = epoch_dict.keys()
# keys.sort()
# Stupid GNUPlot cannot handle localtime!!
for epoch_time_bucket in keys:
    output_file.write("%d %d\n" % (epoch_time_bucket * granularity - 3600 * 7, epoch_dict[epoch_time_bucket]))
output_file.close()
input_file.close()
