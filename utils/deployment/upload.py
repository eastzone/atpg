#!/usr/bin/python
import sqlite3
DATABASE = 'result/result.sqlite'

start_date = 1008
end_date = 1010
conn = sqlite3.connect(DATABASE)
conn.execute('CREATE TABLE IF NOT EXISTS ping_result (time REAL, source TEXT, destination TEXT, latency REAL)')

sources = []
hosts_file = open("hosts.txt")
for line in hosts_file:
    if line[0] != '#':
        sources.append(line.split('.')[0])
hosts_file.close()
        
for date in range(start_date, end_date):
    for source in sources:
        source_file = open("result/%d/report_%d_%s.txt" % (date, date, source))
        for line in source_file:
            query = 'INSERT INTO ping_result VALUES (?, ?, ?, ?)'
            (time, destination, latency) = line.split()
            if latency == "+Inf":
                latency = "999999"
            conn.execute(query, (time, source, destination, latency))
        source_file.close()
        conn.commit()

conn.commit()
conn.close()

