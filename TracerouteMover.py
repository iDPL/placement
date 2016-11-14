import TimedExec
import os
import time
import socket
import sys
import signal
import hashlib
import json
from IDPLException import *
from DataMover import *


class Traceroute(DataMover):

	def __init__(self):
		super(Traceroute,self).__init__()
		tracerouteExe = '/bin/traceroute'
		self.setExe(tracerouteExe)
		self.setOutputHandler(self.tracerouteout)
		self.setErrHandler(self.tracerouteerr)
		self.rawData = None
		self.transferred=0
		self.deleteRequirement("FileTransfer")
		self.addRequirement("NoPortsNeeded")
		self.isServer = False
		self.route = []
		self.allRoutes = []
	
	def clearRoute(self):
		self.route = []

	def tracerouteout(self,pid,str):
		""" stdout handler when running iperf under TimedExec """
		tstr = time.ctime()
		message = "%s(%d,%s): %s" % (socket.getfqdn(),pid,tstr,str)
		sys.stdout.write(message)
		if str.strip().startswith("trace"):
			return
		self.route.append(str.split())
		
	def tracerouteerr(self,pid,str):
		""" stderr handler when running iperf under TimedExec """
		sys.stderr.write("%d#: %s" %(pid,str))

	def exportRoute(self,host):
		exRt = {} 
		exRt['src'] = socket.getfqdn()
		exRt['dest'] = host
		exRt['v6'] = self.isV6Test()
		exRt['time'] =  time.time()
		exRt['path'] = self.route
		return json.dumps(exRt) 

	def client(self,server,port=None):
		self.setArgs(["-q","1","-n", "%s" % server])
		self.clearRoute()
		self.run()

	def server(self):
		self.setArgs(["-q","1","-n", "%s" % self.getSrc()])
		self.isServer = True
		self.clearRoute()
		self.run()

	def isFileTransfer(self):
		"""traceroute is memory to memory """
		return False 

class Traceroute6(Traceroute):
	def __init__(self):
		super(Traceroute6,self).__init__()
		self.setV6Test(True)

	def client(self,server,port=None):
		self.setArgs(["-q","1","-n", "-6", "%s" % self.v6Names[server]])
		self.run()

	def server(self):
		self.setArgs(["-q","1","-n", "-6", "%s" % self.v6Names[self.getSrc()]])
		self.isServer = True
		self.run()


# vim: ts=4:sw=4:
