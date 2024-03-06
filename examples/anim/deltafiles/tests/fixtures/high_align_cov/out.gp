set terminal png tiny size 800,800
set output "out.png"
set size 1,1
set grid
unset key
set border 15
set tics scale 0
set xlabel "MGV_MGV-GENOME-0264574"
set ylabel "MGV_MGV-GENOME-0266457"
set format "%.0f"
set mouse format "%.0f"
set mouse mouseformat "[%.0f, %.0f]"
if(GPVAL_VERSION < 5) set mouse clipboardformat "[%.0f, %.0f]"
set xrange [1:39253]
set yrange [1:39594]
set style line 1  lt 1 lw 3 pt 6 ps 1
set style line 2  lt 3 lw 3 pt 6 ps 1
set style line 3  lt 2 lw 3 pt 6 ps 1
plot \
 "out.fplot" title "FWD" w lp ls 1, \
 "out.rplot" title "REV" w lp ls 2
