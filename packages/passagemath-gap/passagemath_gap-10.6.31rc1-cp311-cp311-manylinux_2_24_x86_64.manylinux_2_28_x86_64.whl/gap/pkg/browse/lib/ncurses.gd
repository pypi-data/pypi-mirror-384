#############################################################################
##
#W  ncurses.gd            GAP 4 package `Browse'                 Frank Lübeck
##
##  Note that the kernel has generated the record 'NCurses'.
##  

NCurses.CTRL := function(c) return CharInt(IntChar(c) mod 32); end;

