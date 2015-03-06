#! /usr/bin/env python
import CondorTools
import TimedExec
from IDPLException import *
import os
import sys
import signal
import socket

##### Configurables
### IPERF ####
### iperf ports
iperfPortLow = 5001
iperfPortHigh = 5010
iperfPort = iperfPortLow

iperfExe = '/usr/bin/iperf'
if not os.path.exists(iperfExe):
	iperfExe = '/opt/iperf/bin/iperf'

clientTimeout = 30
serverTimeout = 120
##############

#### Chirp Setup
chirp = CondorTools.CondorChirp()

def iperfout(pid,str):
	""" stdout handler when running iperf under TimedExec """
	message = "%s(%d): %s" % (socket.getfqdn(),pid,str)
	sys.stdout.write(message)
	host = socket.getfqdn()
	try:
		if str.find("its/sec") != -1:
			os.kill(pid,signal.SIGTERM)
		if str.find("listening") != -1:
			listenport = int(str.split()[-1])
			chirp.setJobAttr("IperfServer","'%s %d'" % (host, listenport))
	except e:
		print e 

def iperferr(pid,str):
	""" stderr handler when running iperf under TimedExec """
	sys.stdout.write("%d#: %s" %(pid,str))
	raise PortInUseException("iperf", iperfPort)

# This is used to create new subprocess and it will return output 
# as well as error 


def iperfServer():
	for iperfPort in range(iperfPortLow,iperfPortHigh):
		try:
			resultcode,output,err=TimedExec.runTimedCmd(serverTimeout,[iperfExe,
					"-s", "-p", "%d" % iperfPort ],iperfout, iperferr)

			if resultcode < 0:
				sys.stdout.write("Result code: %d\n" % resultcode)
				raise TimeOutException("iperf")	
			break
		except PortInUseException,e:
			sys.stderr.write("%s reported port %d is in use\n" %(e.source, e.port))
		
def iperfClient():
	interval = 5
	maxtries = 12*3
	serverInfo = chirp.getJobAttrWait("IperfServer",None,interval, maxtries)
	host,port = serverInfo.strip("'").split()
	resultcode,output,err=TimedExec.runTimedCmd(clientTimeout,[iperfExe,
					"-c", host, "-p", "%d" % int(port) ],iperfout, iperferr)


## *****************************
## main routine
## *****************************

if int(os.environ['_CONDOR_PROCNO']) == 0:
	iperfClient()
else:
	chirp.setJobAttr("IperfServer", None)
	iperfServer()
	chirp.setJobAttr("IperfServer", None)

#if int(os.environ['_CONDOR_PROCNO']) == 0:
#	try:
#		iperfClient()
#	except Exception,e:
#		print "Client had Exception: ", e
#else:
#	try:
#		chirp.setJobAttr("IperfServer", None)
#		iperfServer()
#	except Exception,e:
#		print "Server had Exception: ", e
#		chirp.setJobAttr("IperfServer", None)
		
# vim: ts=4:sw=4:tw=78
