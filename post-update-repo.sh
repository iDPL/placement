#!/bin/bash
# post-update-repo.sh  <logdir> <publishdir>
# Assumptions:
#        <logdir> -- git repository with checked out working copy
#        <publishdir> -- <publishdir>/<logdir>.git  - bare repo suitable for
#                                                     http-based git clone 
#
# return
#     -1   # normal return, but negative for DAGMAN retries
#     -2   # Other error 
LOGDIR=$1
PUBLISHDIR=$2
PUBLISHREPO=$PUBLISHDIR/$LOGDIR.git
if [ ! -d $LOGDIR -o ! -d $PUBLISHREPO ]; then
	exit -2
fi
pushd $LOGDIR
git add --all
git commit -m "Automatic update at `date`"
cd $PUBLISHREPO
git fetch
git update-server-info
popd
exit -1
