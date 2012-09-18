#!/bin/bash
PROJECTPATH=../atpg/

cd ${PROJECTPATH}/
./atpg_stanford.py -p 10 -f stanford-10.sqlite > ${PROJECTPATH}/work/stanford-10.txt
./atpg_stanford.py -p 40 -f stanford-40.sqlite > ${PROJECTPATH}/work/stanford-40.txt
./atpg_stanford.py -p 70 -f stanford-70.sqlite > ${PROJECTPATH}/work/stanford-70.txt
./atpg_stanford.py -p 100 -f stanford-100.sqlite > ${PROJECTPATH}/work/stanford-100.txt
./atpg_stanford.py -p 100 -e -f stanford-100-edge.sqlite > ${PROJECTPATH}/work/stanford-100-edge.txt
