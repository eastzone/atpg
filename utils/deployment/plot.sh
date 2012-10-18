#!/bin/bash
./link_cover.py
./date_aggregate.py data/output.csv data/gnuplot.data
./date_aggregate.py data/output_filtered.csv data/gnuplot_filtered.data
gnuplot gnuplot/date_aggregate.plt
evince date_aggregate.pdf

