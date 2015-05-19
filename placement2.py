#! /usr/bin/env python
import DataMover
import CondorTools
from IDPLException import *
import os
import sys
import signal
import socket
import time
import getopt
import subprocess

##### Configurables
clientTimeout = 120
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
		self.md5Attr = "%sMD5" % prefix
		self.host = socket.getfqdn()
	def postPort(self,port):
		self.chirp.setJobAttr(self.jobAttr, "'%s %d'" % (self.host, port))
	def clearPort(self):
		self.chirp.setJobAttr(self.jobAttr, None)

	def postMD5(self,md5):
		self.chirp.setJobAttr(self.md5Attr, "'%s'" % md5)
	def clearMD5(self):
		self.chirp.setJobAttr(self.md5Attr, None)
	def getMD5(self):
		interval = 5
		maxtries = 12 
		md5 = chirp.getJobAttrWait(self.md5Attr,None,interval, maxtries)
		return md5

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
## Actually performn the placement 
## *****************************
def performPlacement(inputFile,outputFile):
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
			netcat.setInputFile(inputFile)
			md5 = "'%s'" % netcat.md5(inputFile)
			# Time the client (netcat)
			netcatChirp.ulog(iam,"start")
			(host,port) = netcatChirp.getHostPort()
			tstart = time.time()
			netcat.client(host,port)
			tend = time.time()
			transferred = os.path.getsize(inputFile)
			xmd5 = netcatChirp.getMD5()
			ok = 1 if md5 == xmd5 else 0
			writeRecord("netcat",socket.getfqdn(),host,tstart,tend,ok,
				tend-tstart,int(transferred))
			# Finish (netcat)
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
			netcat.setOutputFile(outputFile)
			netcat.setTimeout(serverTimeout)
			netcat.setPortReporter(netcatChirp.postPort)
			netcatChirp.clearMD5()
			# Run it
			netcat.server()
			# post md5
			netcatChirp.postMD5(netcat.md5(outputFile))
			# Finish
			netcatChirp.ulog(iam,"end")
		except IDPLException, e:
			netcatChirp.ulog(iam,"error %s" % e.message)
			print "Server had Exception: " + e.message
		finally:
			netcatChirp.clearPort()	
	
## *****************************
## main routine
## *****************************

def main(argv):
	inputfile = ''
	outputfile = ''
	try:
		opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
	except getopt.GetoptError:
		print 'placement2.py -i <inputfile> -o <outputfile>'
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print 'placement2.py -i <inputfile> -o <outputfile>'
			sys.exit()
		elif opt in ("-i", "--ifile"):
			inputfile = arg
		elif opt in ("-o", "--ofile"):
			outputfile = arg
	print 'Input file is:', inputfile
	print 'Output file is:', outputfile
	performPlacement(inputfile,outputfile)


if __name__ == "__main__":
	main(sys.argv[1:])
		
# vim: ts=4:sw=4:tw=78
