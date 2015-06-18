#!/bin/sh
# create subdirectory for output
subdir=$1
[ "X$subdir" == "X" ] && exit 0
[ ! -d $subdir ] && mkdir -p $subdir
[ ! -d $subdir/detail ] && mkdir  $subdir/detail
exit 0

