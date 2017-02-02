import os
import time
import socket
import sys
import signal
import hashlib
import pwd
import tempfile
import TimedExec
import subprocess
import CondorTools
from IDPLException import *
from DataMover import *

class GridFTPMover(DataMover):
	def __init__(self, workDir=None):
		super(GridFTPMover,self).__init__()

		self.scratchDir = os.getcwd()

		os.environ["LD_LIBRARY_PATH"] = self.scratchDir + "/gridftp/usr/lib64/"

		self.setOutputHandler(self.gridftpout)
		self.setErrHandler(self.gridftperr)
		self.rawData = None
		self.transferredKB=0
		self.serverDir = workDir
		self.user = None
		self.hostkey = None
		self.userkey = None
		self.userkeypub = None
		self.inputFile = None  # source file on client
		self.outputFile = None # dest file on server
		self.addRequirement("NoPortsNeeded")
		
		#self.addRequirement("SubAttrs");
		print "Done with GridFTP init"

	def gridftpout(self,pid,str):
		""" stdout handler when running gridftp under TimedExec """
		message = "%s(%d): %s" % (socket.getfqdn(),pid,str)
		sys.stdout.write(message)
		host = socket.getfqdn()

	def gridftperr(self,pid,str):
		""" stderr handler when running gridftp under TimedExec """
		sys.stderr.write("%d#: %s" %(pid,str))
		if str.find("bind failed") != -1:
			raise PortInUseException("gridftp", self.port)

	def getUser(self):
		return self.user

	def setUser(self,nuser):
		self.user = nuser

	def client(self,server,port=20650):
		subprocess.call(["tar", "xzf", "gridftp-7.20-1.tar.gz"])
		self.setExe(self.scratchDir + "/gridftp/usr/bin/globus-url-copy")
		args = [self.inputFile, "ftp://" + server + ":20655/~/1G"]
		self.setArgs(args)
		print "About to run gridftp client: " , args
		self.run()

	def server(self):
		subprocess.call(["tar", "xzf", "gridftp-7.20-1.tar.gz"])
		chirp = CondorTools.CondorChirp()
		client = chirp.getJobAttrWait("DstHost",None,60, 1)[1:-1]

		self.setExe(self.scratchDir + "/gridftp/usr/sbin/globus-gridftp-server")
		args = ["-exec", self.scratchDir + "/gridftp/usr/sbin/globus-gridftp-server", "-1", "-p", "20655", "-aa", "-port-range", "20656,20660", "-home-dir", self.scratchDir, "-ipc-allow-from", client]
		self.setArgs(args)
		print "About to run gridftp server: " , args
		self.run()
		print "Done runnning gridftp server: " , args

# vim: ts=4:sw=4:
