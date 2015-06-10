import os
import time
import socket
import sys
import signal
import hashlib
import TimedExec
from IDPLException import *
from DataMover import *


class Netcat(DataMover):
	""" Netcat-based Data Mover """
	def __init__(self):
		super(Netcat,self).__init__()
		self.setExe('/usr/bin/nc')
		self.setOutputHandler(self.netcatout)
		self.setErrHandler(self.netcaterr)
		self.oFile = None	

	def setOutputFile(self,fname):
		super(Netcat,self).setOutputFile(fname)
		self.oFile = file(self.outputFile,"w")	
		self.setOutputHandler(self.oFile)

	def netcatout(self,pid,str):
		""" stdout handler when running netcat under TimedExec """
		message = "%s(%d): %s" % (socket.getfqdn(),pid,str)
		sys.stdout.write(str)

	def netcaterr(self,pid,str):
		""" stderr handler when running netcat under TimedExec """
		sys.stdout.write("%d#: %s" %(pid,str))
		raise PortInUseException("netcat", self.port)

	def client(self,server,port=5011):
		self.setArgs(["%s" % server,"%d" % int(port)])
		self.run()
		if self.oFile is not None:
			self.oFile.close()

	def server(self):
		self.setArgs(["-d"])
		self.setPortArg("-l")
		self.setPortRange(5011,5020)
		self.run()
		if self.oFile is not None:
			self.oFile.close()

# vim: ts=4:sw=4:
