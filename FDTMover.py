import os
import time
import socket
import sys
import signal
import hashlib
import pwd
import tempfile
import TimedExec
from IDPLException import *
from DataMover import *

class FDTMover(DataMover):
	def __init__(self, workDir=None):
		super(FDTMover,self).__init__()
		self.JAVA = 'java'
		self.FDTJAR = 'fdt.jar'
		
		self.setExe(self.JAVA)
		self.setOutputHandler(self.fdtout)
		self.setErrHandler(self.fdterr)
		self.rawData = None
		self.transferredKB=0
		self.serverDir = workDir
		self.user = None
		self.hostkey = None
		self.userkey = None
		self.userkeypub = None
		self.inputFile = None  # source file on client
		self.outputFile = None # dest file on server
		self.addRequirement("SubAttrs");

	def fdtout(self,pid,str):
		""" stdout handler when running fdt under TimedExec """
		message = "%s(%d): %s" % (socket.getfqdn(),pid,str)
		sys.stdout.write(message)
		host = socket.getfqdn()

	def fdterr(self,pid,str):
		""" stderr handler when running sshd under TimedExec """
		sys.stderr.write("%d#: %s" %(pid,str))
		if str.find("bind failed") != -1:
			raise PortInUseException("fdt", self.port)

	def getUser(self):
		return self.user

	def setUser(self,nuser):
		self.user = nuser

	def client(self,server,port=5001):
		args = ["-jar", self.FDTJAR, "-noupdates" ]
		args.extend(["-p", str(port)])
		args.extend(["-c", server, self.inputFile])
		args.extend(["-d","."])
		self.setArgs(args)
		print "client: " , args
		self.run()

	def server(self):
		args = ["-jar", self.FDTJAR, "-S", "-noupdates" ]
		# put the server in debug mode to accept only one incoming connection
		self.setArgs(args)
		self.setPortRange(5001,5010)
		print "server: " , args
		self.run()

class FDTMover6(FDTMover):
	def __init__(self, workDir=None):
		super(FDTMover6,self).__init__()
		self.setV6Test = True
# vim: ts=4:sw=4:
