#!/bin/bash
# init-local-repos.sh  <logdir> <publishdir>
# Assumptions:
#        <logdir> -- git repository with checked out working copy
#        <publishdir> -- <publishdir>/<logdir>.git  - bare repo suitable for
#                                                     http-based git clone 
#
# return
#      0   # 
#     -2   # Other error 
# example:
# 	init-local-repos.sh ucsd2wisc /data/measurements/phil/mesh6
LOGDIR=$1
PUBLISHDIR=$2
PUBLISHREPO=$LOGDIR.git
if [ ! -d $LOGDIR ]; then
	exit -2
fi
if [ ! -d $PUBLISHDIR ]; then
	mkdir -p $PUBLISHDIR
	if [ $? -ne 0 ]; then
		echo "Could not create $PUBLISHDIR"
		exit -2;
	fi
fi
pushd $LOGDIR
git init
git add --all
git commit -m "Initialized on `date`"
FPLOGDIR=$(pwd)
cd $PUBLISHDIR
git clone --bare $FPLOGDIR $LOGDIR.git 
cd $LOGDIR.git
git config remote.origin.fetch "+*:*"
git update-server-info
popd
exit 0 
