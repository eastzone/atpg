#set xlabel "Time"
set ylabel "Failures/Minute" font "Helvetica,8"
set nokey
set terminal pdf size 4,4
set output "date_aggregate.pdf"
set multiplot layout 2, 1

set xdata time
set timefmt "%s"
set format x "%b %d\n%H:%M"
set xrange ["1349186100":"1349210000"]
set title "Failures with All-pairs ping"
plot "data/gnuplot.data" using 1:2 with impulses
set title "Failures with ATPG's link cover suite"
plot "data/gnuplot_filtered.data" using 1:2 with impulses

