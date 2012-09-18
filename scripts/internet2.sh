#!/bin/bash
PROJECTPATH=../atpg/

cd ${PROJECTPATH}
./atpg_internet2.py -p 10 -f i2-10.sqlite > ${PROJECTPATH}/work/i2-10.txt
./atpg_internet2.py -p 40 -f i2-40.sqlite > ${PROJECTPATH}/work/i2-40.txt
./atpg_internet2.py -p 70 -f i2-70.sqlite > ${PROJECTPATH}/work/i2-70.txt
./atpg_internet2.py -p 100 -f i2-100.sqlite > ${PROJECTPATH}/work/i2-100.txt
./atpg_internet2.py -p 100 -f i2-100-edge.sqlite > ${PROJECTPATH}/work/i2-100-edge.txt
