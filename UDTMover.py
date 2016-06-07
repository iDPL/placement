import os
import time
import socket
import sys
import signal
import hashlib
import TimedExec
from IDPLException import *
from DataMover import *


class UDTMover(DataMover):
	""" UDT-based Data Mover """
	def __init__(self):
		super(UDTMover,self).__init__()
		self.setExe('./udtxfer')
		self.setOutputHandler(self.udtout)
		self.setErrHandler(self.udterr)
		self.oFile = None	
		self.transferred=0

	def setInputFile(self,fname):
		sys.stdout.write("UDT::setInputFile called with %s\n" % fname)
		super(UDTMover,self).setInputFile(fname)

	def setOutputFile(self,fname):
		sys.stdout.write("UDT::setOutputFile called with %s\n" % fname)
		super(UDTMover,self).setOutputFile(fname)

	def udtout(self,pid,str):
		""" stdout handler when running udtxfer under TimedExec """
		message = "%s(%d): %s" % (socket.getfqdn(),pid,str)
		sys.stdout.write(str)

	def udterr(self,pid,str):
		""" stderr handler when running udtxfer under TimedExec """
		sys.stdout.write("%d#: %s" %(pid,str))
		raise PortInUseException("udt", self.port)

	def client(self,server,port=20660):
		self.setArgs(["-c", "%s" % server,"-p", "%d" % int(port), "-f", "%s" % self.outputFile])
		sys.stdout.write("About to run udt client\n")
		self.run()

	def server(self):
		self.setArgs(["-s", "-f", "%s" % self.inputFile])
		#self.setArgs(["-s", "-f", "/home/gthain/mesh/placement/1G"])
		self.setPortArg("-p")
		self.setPortRange(20660,20670)
		sys.stdout.write("About to run udt server\n")
		self.run()
		sys.stdout.write("Done running udt server\n")

# vim: ts=4:sw=4:
