#! /usr/bin/env python
import DataMover
import SCPMover 
import IperfMover
import NetcatMover
import CondorTools
import ChirpTools 
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

chirp = ChirpTools.ChirpInfo("placement")

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
	chirp.ulog("writerecord", logmessage)

## *****************************
## Actually performn the placement 
## *****************************
def performPlacement(inputFile,outputFile):
	iperf = IperfMover.Iperf()
	iperfChirp = ChirpTools.ChirpInfo("iperf")
	scp = SCPMover.SCPMover()
	scpChirp = ChirpTools.ChirpInfo("scp")
	
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
