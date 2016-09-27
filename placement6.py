#! /usr/bin/env python
import DataMover
import SCPMover 
import IperfMover
import IrodsMover
import IrodsPutMover
import NetcatMover
import FDTMover
import UDTMover
import CondorTools
import ChirpTools 
import GitClone
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

## Dictionary of Available Movers
AvailableMovers ={ 
    'fdt': ("Use Monalisa FDT IPv4",("fdt", FDTMover.FDTMover(), ChirpTools.ChirpInfo("fdt"))),
    'fdt6': ("Use Monalisa FDT IPv6",("fdt6", FDTMover.FDTMover6(), ChirpTools.ChirpInfo("fdt6"))),
    'gitclone': ("Use GIT and SSH to clone",("gitclone", GitClone.GitClone(), ChirpTools.ChirpInfo("gitclone"))),
    'gitclone6': ("Use GIT and SSH to clone IPv6",("gitclone6", GitClone.GitClone6(), ChirpTools.ChirpInfo("gitclone6"))),
	'iperf': ("Network test using iperf IPv4",("iperf", IperfMover.Iperf(), ChirpTools.ChirpInfo("iperf"))), 
    'iperf6':("Network test using iperf IPv6",("iperf6", IperfMover.Iperf6(), ChirpTools.ChirpInfo("iperf6"))), 
    'irods': ("Download data from Existing IRODs server",("irods", IrodsMover.IrodsMover(), ChirpTools.ChirpInfo("irods"))),
    'irodsput':("Put data to an Existing IRODs server", ("irodsput", IrodsPutMover.IrodsPutMover(), ChirpTools.ChirpInfo("irodsput"))),
    'scp': ("SCP to copy data from client to server",("scp", SCPMover.SCPMover(), ChirpTools.ChirpInfo("scp"))),
	'scp6': ("SCP using IPv6",("scp6", SCPMover.SCPMover6(), ChirpTools.ChirpInfo("scp6"))),
    'netcat': ("Raw Socket file copy from client to server", ("netcat", NetcatMover.Netcat(), ChirpTools.ChirpInfo("netcat"))),
	'netcat6':("Raw Socket file copy using IPv6", ("netcat6", NetcatMover.Netcat6(), ChirpTools.ChirpInfo("netcat6"))),
    'udt': ("UDT protocol to copy from client to server",  ("udt", UDTMover.UDTMover(), ChirpTools.ChirpInfo("udt")))
}
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

def isClient(procID, mover):
    # procID - processID
	# 		0 -  this  is the SRC in the submit file
    #       1 -  this  is the DST in the submit file 
	# Default: 
	#         procID == 0 is the "client", it will wait for the server to
	# 					setup and then push data to it. 
	#         procID == 1 is the "server" it will start up and wait for
	#         connections. Data will be PUSHED to the server
    #
    # PullSemantics:  if the mover has pull semantics then the notion of
    # client and server are reversed
	#         procID == 0 is the "server", it will start up and wait for
	#  					connections, data will be PULLED from it 
	#         procID == 1 is the "client" it will wait for the server to
	#					to setup and the pull data from it. 
    #		  
	if mover.hasRequirement("PullSemantics"):
		if  int(procID) != 0:
			return True
		return False 
	else: 
		if  int(procID) == 0:
			return True
		return False 
## *****************************
## Actually perform the placement 
## *****************************
def performPlacement(inputFile, outputFile, sequence=[],timeout=serverTimeout,
		moverargs=None):

	for testName in sequence: 
		try:
			name,pMover,pChirp = AvailableMovers[testName][1]
		except:
			# test not defined in set of available movers 
			chirp.ulog("startup","%s test is not defined in AvailableMovers" % testName) 
			continue
		pMover.setTimeout(timeout)
		pMover.setMoverArgs(moverargs)
		if isClient(os.environ['_CONDOR_PROCNO'],pMover):
			iam = "client"
			try:
				# Set up the client
				pChirp.clearUserkey() if pMover.hasRequirement("PubKey") else None 
				pMover.clientSetup()
				# Get the pubkey and chirp it (only chirps if the mover
				# explicitly defines key file during clientSetup() ) 
				pChirp.postUserkey(pMover.getUserPubKeyFile())
				pMover.setOutputFile(outputFile)
				if pMover.hasRequirement("PathTransfer"):
					pMover.setInputFile(inputFile)
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
			# pMover.setInputFile(inputFile)
			try:
				# Set up the Server
				pChirp.ulog(iam,"start")
				if pMover.hasRequirement("FileTransfer"):
					pMover.setOutputFile(outputFile)

				pMover.serverSetup()
				if pMover.hasRequirement("PubKey"):
					# read the public key of the connecting user
					pMover.setAuthorizedKey(pChirp.getUserkey())

				if pMover.hasRequirement("SubAttrs"):
					## set up some Chirped Attrs, that won't be read by
					# client until server sets up 
					pChirp.clearMD5()
					pChirp.postOutputfile(outputFile)
					pChirp.postUser(pwd.getpwuid(os.geteuid()).pw_name)

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

def usage(listMovers=False):
	print 'placement6.py [-l] [-s tstsequence ] [-a moverargs] [-t timeout] -i <inputfile> -o <outputfile>'
	if not listMovers:
		return
	print "Available Tests:"
	tsts = AvailableMovers.keys()
	tsts.sort()
	for tst in tsts:
		print "%-8s : %s" % (tst, AvailableMovers[tst][0])

def main(argv):
	inputfile = ''
	outputfile = ''
	sequence = ("iperf",)
	moverArgs = None
	timeout = serverTimeout 
	
	try:
		opts, args = getopt.getopt(argv,"lha:i:o:s:t:",
				["args=","ifile=","ofile=","timeout="])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			usage()
			sys.exit()
		elif opt in ("-i", "--ifile"):
			inputfile = arg
		elif opt in ("-o", "--ofile"):
			outputfile = arg
		elif opt in ("-s", "--sequence"):
			sequence = arg.split(',')
		elif opt in ("-t", "--timeout"):
			timeout = int(arg)
		elif opt in ("-a", "--args"):
			moverArgs = arg 
		elif opt in ("-l"):
			usage(listMovers=True)
			sys.exit(0)

	print 'Input file is:', inputfile
	print 'Output file is:', outputfile
	print 'Test Sequence is:', sequence
	performPlacement(inputfile,outputfile,sequence=sequence,timeout=timeout,moverargs=moverArgs)


if __name__ == "__main__":
	main(sys.argv[1:])
		
# vim: ts=4:sw=4:tw=78
