#! /usr/bin/env python
import DataMover
import CondorTools
from IDPLException import *
import os
import sys
import signal
import socket
import time

##### Configurables
clientTimeout = 30
serverTimeout = 120
##############

#### Chirp Setup
chirp = CondorTools.CondorChirp()
transferredKB = 0
tstart = 0.0
tend = 0.0

class ChirpMover(object):
	""" Use Chirp jobAttrs to post host:port pairs """
	def __init__(self,prefix):
		self.prefix = prefix
		self.chirp = CondorTools.CondorChirp()
		self.jobAttr = "%sServer" % prefix
		self.host = socket.getfqdn()
	def postPort(self,port):
		self.chirp.setJobAttr(self.jobAttr, "'%s %d'" % (self.host, port))
	def clearPort(self):
		self.chirp.setJobAttr(self.jobAttr, None)
	def getHostPort(self):
		interval = 5
		maxtries = 12*3
		serverInfo = chirp.getJobAttrWait(self.jobAttr,None,interval, maxtries)
		host,port = serverInfo.strip("'").split()
		return (host,port)	
	def ulog(self, who, message):
		logMessage = "%s(%s) %s:%s" % (self.host,self.prefix,who,message)
		self.chirp.ulog(logMessage)
	

def writeRecord(tag, src,dest,start,end,md5_equal,duration,kbytes):
	##| source      | varchar(64)      | source node
	##| destination | varchar(64)      | destination node
	##| time_start  | timestamp        | start time
	##| time_end    | timestamp        | end time
	##| md5_equal   | tinyint(1)       | md5 validated
	##| duration    | int(10) unsigned | transfer time (time_end-time_start)
	logmessage = "%s,%s,%s" % (tag, src, dest)
	logmessage += ",%f,%f,%d,%f" % (start,end,md5_equal,duration)
	logmessage += ",%d" % (kbytes)
	chirp.ulog(logmessage)

## *****************************
## main routine
## *****************************
iperf = DataMover.Iperf()
iperfChirp = ChirpMover("iperf")
netcat = DataMover.Netcat()
netcatChirp = ChirpMover("netcat")

if int(os.environ['_CONDOR_PROCNO']) == 0:
	iam = "client"
	#####   IPERF TEST
	try:
		# Set up the client
		iperf.setTimeout(clientTimeout)
		# Time the client (iperf)
		iperfChirp.ulog(iam,"start")
		(host,port) = iperfChirp.getHostPort()
		tstart = time.time()
		iperf.client(host,port)
		tend = time.time()
		writeRecord("iperf",socket.getfqdn(),host,tstart,tend,1,tend-tstart,
			int(iperf.transferredKB))
		# Finish (iperf)
		iperfChirp.ulog(iam,"end")
	except IDPLException,e:
		iperfChirp.ulog(iam,"error %s" % e.message)
		print "Client had Exception: " + e.message

	#####   NETCAT TEST
	try:
		# Set up the client
		netcat.setTimeout(clientTimeout)
		netcat.setInputFile("DataMover.py")
		# Time the client (netcat)
		netcatChirp.ulog(iam,"start")
		(host,port) = netcatChirp.getHostPort()
		tstart = time.time()
		netcat.client(host,port)
		tend = time.time()
		transferred = os.path.getsize("DataMover.py")
		writeRecord("netcat",socket.getfqdn(),host,tstart,tend,1,tend-tstart,
			int(transferred))
		# Finish (iperf)
		netcatChirp.ulog(iam,"end")
	except IDPLException,e:
		netcatChirp.ulog(iam,"error %s" % e.message)
		print "Client had Exception: " + e.message
else:
	iam = "server"
	#####   IPERF TEST
	try:
		# Set up the Server
		iperfChirp.ulog(iam,"start")
		iperf.setTimeout(serverTimeout)
		iperf.setPortReporter(iperfChirp.postPort)
		# Run it
		iperf.server()
		# Finish
		iperfChirp.ulog(iam,"end")
	except IDPLException, e:
		iperfChirp.ulog(iam,"error %s" % e.message)
		print "Server had Exception: " + e.message
	finally:
		iperfChirp.clearPort()	

	#####   NETCAT TEST
	try:
		# Set up the Server
		netcat.setOutputFile("OutputReceived")
		netcat.setTimeout(serverTimeout)
		netcat.setPortReporter(netcatChirp.postPort)
		# Run it
		netcat.server()
		# Finish
		netcatChirp.ulog(iam,"end")
	except IDPLException, e:
		netcatChirp.ulog(iam,"error %s" % e.message)
		print "Server had Exception: " + e.message
	finally:
		netcatChirp.clearPort()	
		
# vim: ts=4:sw=4:tw=78
