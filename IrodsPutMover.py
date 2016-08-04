import TimedExec
import os
import time
import socket
import sys
import signal
import hashlib
from IDPLException import *
from DataMover import *


class IrodsPutMover(DataMover):

	def __init__(self):
		super(IrodsPutMover,self).__init__()
		irodsExe = '/usr/bin/iput'
		if not os.path.exists(irodsExe):
			irodsExe = '/opt/irods/bin/iput'
		self.setExe(irodsExe)
		self.setOutputHandler(self.irodsout)
		self.setErrHandler(self.irodserr)
		self.rawData = None
		self.transferred=0
		self.deleteRequirement("FileTransfer")
		self.addRequirement("NoPortsNeeded")
		self.isServer = False
	
	def irodsout(self,pid,str):
		""" stdout handler when running irods under TimedExec """
		message = "%s(%d): %s" % (socket.getfqdn(),pid,str)
		sys.stdout.write(message)
		host = socket.getfqdn()

		try:
			## if transfer finished, record bytes sent
			## Then kill irods (server)
			if str.find("MB/s") != -1:
				# Field 1 is MBs as a float, need to floor() it
				self.transferred = 1024  * int(str.split()[1].split(".")[0])
				self.rawData = " ".join(str.split()[-2:])
				#interval=(str.split()[-6]).split('-')
				#self.delta = float(interval[1])-float(interval[0])
				self.delta = float(str.split()[4])
				if self.isServer:
					os.kill(pid,signal.SIGTERM)
					sys.stdout.write("Killing pid %d\n" % pid)
		except IDPLException,e:
			sys.stderr.write(e.message)

	def irodserr(self,pid,str):
		""" stderr handler when running irods under TimedExec """
		sys.stderr.write("%d#: %s" %(pid,str))
		if str.find("bind failed") != -1:
			raise PortInUseException("rods", self.port)

	def client(self,server,port=20650):
		#self.setArgs(["-c","%s" % server,"-p","%d" % int(port),"-f","k","-t","20"])
		self.setArgs(["-v","-f","-N", "1", "/home/idpl/100M"])
		self.run()

	def server(self):
		#self.setArgs(["-s"])
		#self.setArgs(["-v","-f","-N", "1", "test40MB"])
		self.setExe("/bin/sleep")
		self.setArgs(["90"])
		#self.setPortRange(20650,20660)
		self.setPortRange(None,None)
		self.isServer = True
		self.run()

	def isFileTransfer(self):
		"""Irods is memory to memory """
		return False 
# vim: ts=4:sw=4:
