#! /usr/bin/env python
import DataMover
import SCPMover 
import IperfMover
import NetcatMover
import FDTMover
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
## Actually perform the placement 
## *****************************
def performPlacement(inputFile, outputFile):


	## This does a a)iperf, b)fdt, c) scp, d) netcat, e) iperf 
  	## sequence of tests.  remove any of the (,,) to remove a test 
	movers = [ ("iperf", IperfMover.Iperf(), ChirpTools.ChirpInfo("iperf")), 
				("fdt", FDTMover.FDTMover(), ChirpTools.ChirpInfo("fdt")),
				("scp", SCPMover.SCPMover(), ChirpTools.ChirpInfo("scp")),
				("netcat", NetcatMover.Netcat(),
						ChirpTools.ChirpInfo("netcat")),
				("iperf", IperfMover.Iperf(), ChirpTools.ChirpInfo("iperf")) ] 

	for name,pMover,pChirp in movers:
		if int(os.environ['_CONDOR_PROCNO']) == 0:
			iam = "client"
			try:
				# Set up the client
				pChirp.clearUserkey() if pMover.hasRequirement("PubKey") else None 
				pMover.clientSetup()
				# Get the pubkey and chirp it (only chirps if the mover
				# explicitly defines key file during clientSetup() ) 
				pChirp.postUserkey(pMover.getUserPubKeyFile())
				pMover.setTimeout(clientTimeout)

				if pMover.hasRequirement("FileTransfer"):
					pMover.setInputFile(inputFile)
					md5 = "'%s'" % pMover.md5(inputFile)
					transferred = os.path.getsize(inputFile)

				# Client Start 
				pChirp.ulog(iam,"start")
				if not pMover.hasRequirement("NoPortsNeeded"):
					(host,port) = pChirp.getHostPort()

				# Get the subordinate attributed after the
				# server has been set up
				if pMover.hasRequirement("SubAttrs"):
					pMover.setUser(pChirp.getUser())
					pMover.setOutputFile(pChirp.getOutputfile())

				## Finally, perform the actual placement
				pMover.client(host,port)

				if pMover.hasRequirement("FileTransfer"): 
					# get the server's MD5 Calculation and Compare
					xmd5 = pChirp.getMD5()
					ok = 1 if md5 == xmd5 else 0
				else:
					ok = 1   # no file to check MD5sum  
					transferred = pMover.transferred

				(tstart,tend,delta) = pMover.getTimers()
				writeRecord(name,socket.getfqdn(),host,tstart,tend,ok,delta,
					int(transferred))

				# Finish (client)
				pChirp.ulog(iam,"end")
			except IDPLException,e:
				pChirp.ulog(iam,"error %s" % e.message)
				print "Client had Exception: " + e.message
				break;
				
		else:
			iam = "server"
			try:
				# Set up the Server
				pChirp.ulog(iam,"start")
				pMover.serverSetup()
				if pMover.hasRequirement("PubKey"):
					# read the public key of the connecting user
					pMover.setAuthorizedKey(pChirp.getUserkey())

				pMover.setOutputFile(outputFile)

				if pMover.hasRequirement("SubAttrs"):
					## set up some Chirped Attrs, that won't be read by
					# client until server sets up 
					pChirp.clearMD5()
					pChirp.postOutputfile(outputFile)
					pChirp.postUser(pwd.getpwuid(os.geteuid()).pw_name)

				pMover.setTimeout(serverTimeout)
				pMover.setPortReporter(pChirp.postPort)
				# Run it
				pMover.server()
				if pMover.hasRequirement("FileTransfer"):
					# post md5
					pChirp.postMD5(pMover.md5(outputFile))

				# Finish
				pChirp.ulog(iam,"end")
			except IDPLException, e:
				pChirp.ulog(iam,"error %s" % e.message)
				print "Server had Exception: " + e.message
				break;  
			finally:
				pChirp.clearPort()	


## *****************************
## main routine
## *****************************

def main(argv):
	inputfile = ''
	outputfile = ''
	try:
		opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
	except getopt.GetoptError:
		print 'placement4.py -i <inputfile> -o <outputfile>'
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print 'placement4.py -i <inputfile> -o <outputfile>'
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
