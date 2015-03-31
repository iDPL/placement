#! /usr/bin/env python
import CondorTools
import TimedExec
from IDPLException import *
import os
import sys
import signal
import socket
import time

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
transferredKB = 0
tstart = 0.0
tend = 0.0

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

def iperfout(pid,str):
	""" stdout handler when running iperf under TimedExec """
	global transferredKB
	message = "%s(%d): %s" % (socket.getfqdn(),pid,str)
	sys.stdout.write(message)
	host = socket.getfqdn()
	try:
		if str.find("its/sec") != -1:
			transferredKB = str.split()[-4]
			msg = " ".join(str.split()[-2:])
			chirp.ulog("%s: iperf %s" % (host, msg))
			os.kill(pid,signal.SIGTERM)
		if str.find("listening") != -1:
			listenport = int(str.split()[-1])
			chirp.setJobAttr("IperfServer","'%s %d'" % (host, listenport))
	except IDPLException,e:
		sys.stderr.write(e.message)

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
			sys.stderr.write(e.message)
		
def iperfClient():
	interval = 5
	maxtries = 12*3
	serverInfo = chirp.getJobAttrWait("IperfServer",None,interval, maxtries)
	host,port = serverInfo.strip("'").split()
	tstart = time.time()
	resultcode,output,err=TimedExec.runTimedCmd(clientTimeout,[iperfExe,
					"-c", host,"-f","k","-p","%d" % int(port) ],iperfout, iperferr)
	tend = time.time()
	writeRecord("iperf",socket.getfqdn(),host,tstart,tend,1,tend-tstart,
			int(transferredKB))


## *****************************
## main routine
## *****************************
iam = socket.getfqdn()
logfcli = "%s: iperf client %s" 
logfsrv = "%s: iperf server %s" 
if int(os.environ['_CONDOR_PROCNO']) == 0:
	try:
		chirp.ulog(logfcli % (iam,"start"))
		iperfClient()
		chirp.ulog(logfcli % (iam,"end"))
	except Exception:
		chirp.ulog(logfcli % (iam,"error"))
		print "Client had Exception: "
else:
	try:
		chirp.ulog(logfsrv % (iam,"start"))
		chirp.setJobAttr("IperfServer", None)
		iperfServer()
		chirp.ulog(logfsrv % (iam,"end"))
		chirp.setJobAttr("IperfServer", None)
	except Exception:
		chirp.ulog(logfsrv % (iam,"error"))
		print "Server had Exception: "
		chirp.setJobAttr("IperfServer", None)

# vim: ts=4:sw=4:tw=78
