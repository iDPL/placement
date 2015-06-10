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
def performPlacement(inputFile, outputFile):


	movers = [ ("iperf", IperfMover.Iperf(), ChirpTools.ChirpInfo("iperf")), 
				("scp", SCPMover.SCPMover(), ChirpTools.ChirpInfo("scp"))]
	
	for name,pMover,pChirp in movers:
		if int(os.environ['_CONDOR_PROCNO']) == 0:
			iam = "client"
			try:
				# Set up the client
				pChirp.clearUserkey()
				pMover.clientSetup()
				# Get the pubkey and chirp it (only chirps if the mover
				# explicitly defines key file during clientSetup() ) 
				pChirp.postUserkey(pMover.getUserPubKeyFile())
				pMover.setTimeout(clientTimeout)

				if pMover.isFileTransfer():
					pMover.setInputfile(inputFile)
					md5 = "'%s'" % pMover.md5(inputFile)
					transferred = os.path.getsize(inputFile)

				# Time the client (iperf)
				pChirp.ulog(iam,"start")
				(host,port) = pChirp.getHostPort()
#				# Get the subordinate attributed after the server has been set up
				if pMover.needSubAttrs():
					pMover.setUser(pChirp.getUser())
					pMover.setOutputfile(pChirp.getOutputfile())

				## Finally, perform the actual placemen
				tstart = time.time()
				pMover.client(host,port)
				tend = time.time()

				if pMover.isFileTransfer(): 
					# get the server's MD5 Calculation and Compare
					xmd5 = pChirp.getMD5()
					ok = 1 if md5 == xmd5 else 0
				else:
					ok = 1   # no file to check MD5sum  
					transferred = pMover.transferred

				writeRecord(name,socket.getfqdn(),host,tstart,tend,1,tend-tstart,
					int(transferred))

				# Finish (client)
				pChirp.ulog(iam,"end")
			except IDPLException,e:
				pChirp.ulog(iam,"error %s" % e.message)

				print "Client had Exception: " + e.message
		else:
			iam = "server"
			try:
				# Set up the Server
				pChirp.ulog(iam,"start")
				pMover.serverSetup()
				if pMover.needPubKey():
					# read the public key of the connecting user
					pMover.setAuthorizedKey(pChirp.getUserkey())

				pMover.setOutputFile(outputFile)

				if pMover.needSubAttrs():
					## set up some Chirped Attrs, that won't be read by
					# client until server sets up 
					pChirp.clearMD5()
					pChirp.postOutputfile(outputFile)
					pChirp.postUser(pwd.getpwuid(os.geteuid()).pw_name)

				pMover.setTimeout(serverTimeout)
				pMover.setPortReporter(pChirp.postPort)
				# Run it
				pMover.server()
				if pMover.isFileTransfer():
					# post md5
					pChirp.postMD5(pMover.md5(outputFile))

				# Finish
				pChirp.ulog(iam,"end")
			except IDPLException, e:
				pChirp.ulog(iam,"error %s" % e.message)
				print "Server had Exception: " + e.message
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
