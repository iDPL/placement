#! /usr/bin/env python
import DataMover
import SCPMover 
import CondorTools
from IDPLException import *
import os
import sys
import signal
import socket
import time
import getopt
import subprocess
import getpass
import pwd

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
		self.OutfileAttr = "%sOutfile" % prefix
		self.UserkeyAttr = "%sUserkey" % prefix
		self.UserAttr = "%sUser" % prefix
		self.host = socket.getfqdn()

	## Generic logging
	def ulog(self, who, message):
		logMessage = "%s(%s) %s:%s" % (self.host,self.prefix,who,message)
		self.chirp.ulog(logMessage)
	
	# MD5 Attributes
	def postMD5(self,md5):
		self.chirp.setJobAttr(self.md5Attr, "'%s'" % md5)

	def clearMD5(self):
		self.chirp.setJobAttr(self.md5Attr, None)
	def getMD5(self):
		interval = 5
		maxtries = 12 
		md5 = chirp.getJobAttrWait(self.md5Attr,None,interval, maxtries)
		return md5

	# Port Attributes
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

	## The attributes are written before server is declared ready
	## Never explicitly cleared
	# Outputfile (for SCP)
	def postOutputfile(self,outfile):
		if not os.path.isabs(outfile):
			outfile = os.path.join(os.getcwd(),outfile)
		self.chirp.setJobAttr(self.OutfileAttr, "'%s'" % outfile)

	def getOutputfile(self):
		return self.chirp.getJobAttr(self.OutfileAttr)

	# Userkey (For SCP)
	# Use Chirp for the client to send the public key
	def postUserkey(self,keyfile):
		f = open(keyfile,"r")
		key = "'%s'" % f.readline().strip()
		print "key is '%s'" % key
		f.close()
		self.chirp.setJobAttr(self.UserkeyAttr, key)

	def getUserkey(self):
		interval = 5
		maxtries = 12*3
		# trim off the beginning/ending '
		return chirp.getJobAttrWait(self.UserkeyAttr,None,interval, maxtries)[1:-1]

	def clearUserkey(self):
		self.chirp.setJobAttr(self.UserkeyAttr, None)

	# Localuser (for SCP)
	def postUser(self,user):
		self.chirp.setJobAttr(self.UserAttr, "'%s'" % user)

	def getUser(self):
		return self.chirp.getJobAttr(self.UserAttr)


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
	scp = SCPMover.SCPMover()
	scpChirp = ChirpMover("scp")
	
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
	
		#####   SCP TEST
		try:
			# Set up the client
			scpChirp.clearUserkey()
			scp.clientSetup()
			# Get the pubkey and chirp it
			scpChirp.postUserkey(scp.getUserPubKeyFile())
			scp.setTimeout(clientTimeout)
			scp.setInputfile(inputFile)
			md5 = "'%s'" % scp.md5(inputFile)

			# Get chirped attributes, first one is available only when server
			# is up and running.  
			(host,port) = scpChirp.getHostPort()
			# Get the subordinate attributed after the server has been set up
			scp.setUser(scpChirp.getUser())
			scp.setOutputfile(scpChirp.getOutputfile())
		
			# Time the client (scp)
			scpChirp.ulog(iam,"start")
			# Do the transfer
			tstart = time.time()
			scp.client(host,port)
			tend = time.time()
			transferred = os.path.getsize(inputFile)
			
			# get the server's MD5 Calculation and Compare
			xmd5 = scpChirp.getMD5()
			ok = 1 if md5 == xmd5 else 0
			writeRecord("scp",socket.getfqdn(),host,tstart,tend,ok,
				tend-tstart,int(transferred))
			# Finish (scp)
			scpChirp.ulog(iam,"end")

		except IDPLException,e:
			scpChirp.ulog(iam,"error %s" % e.message)
			print "Client had Exception: " + e.message
		finally:
			scpChirp.clearUserkey()
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
	
		#####   SCP TEST
		try:
			# Set up the Server prior to running it
			scp.serverSetup()

			# read the public key of the connecting user
			scp.setAuthorizedKey(scpChirp.getUserkey())
			scp.setOutputFile(outputFile)
			scp.setTimeout(serverTimeout)
			scp.setPortReporter(scpChirp.postPort)

			## set up some Chirped Attrs, that won't be read by
			# client until server sets up 
			scpChirp.clearMD5()
			scpChirp.postOutputfile(outputFile)
			print "server getpass.getuser():", getpass.getuser()
			print "server  pwd.getpwuid(os.geteuid()).pw_name", pwd.getpwuid(os.geteuid()).pw_name 
			print "server whoami:"
			os.system("whoami")
			print "==server whoami"
			scpChirp.postUser(pwd.getpwuid(os.geteuid()).pw_name)
	
			# Run it
			scp.server()
			# post md5
			scpChirp.postMD5(scp.md5(outputFile))
			# Finish
			scpChirp.ulog(iam,"end")
		except IDPLException, e:
			scpChirp.ulog(iam,"error %s" % e.message)
			print "Server had Exception: " + e.message
		finally:
			scpChirp.clearPort()	
	
## *****************************
## main routine
## *****************************

def main(argv):
	inputfile = ''
	outputfile = ''
	try:
		opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
	except getopt.GetoptError:
		print 'placement3.py -i <inputfile> -o <outputfile>'
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print 'placement3.py -i <inputfile> -o <outputfile>'
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
