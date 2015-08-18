import TimedExec
import os
import time
import socket
import sys
import signal
import hashlib
from IDPLException import *
from DataMover import *


class Iperf(DataMover):

	def __init__(self):
		super(Iperf,self).__init__()
		iperfExe = '/usr/bin/iperf'
		if not os.path.exists(iperfExe):
			iperfExe = '/opt/iperf/bin/iperf'
		self.setExe(iperfExe)
		self.setOutputHandler(self.iperfout)
		self.setErrHandler(self.iperferr)
		self.rawData = None
		self.transferred=0
		self.deleteRequirement("FileTransfer")
		self.isServer = False
	
	def iperfout(self,pid,str):
		""" stdout handler when running iperf under TimedExec """
		tstr = time.ctime()
		message = "%s(%d,%s): %s" % (socket.getfqdn(),pid,tstr,str)
		sys.stdout.write(message)
		host = socket.getfqdn()
		try:
			## if transfer finished, record bytes sent
			## Then kill iperf (server)
			if str.find("its/sec") >= 0:
				self.transferred = str.split()[-4]
				self.rawData = " ".join(str.split()[-2:])
				interval=(str.split()[-6]).split('-')
				self.delta = float(interval[1])-float(interval[0])
				if self.isServer:
					os.kill(pid,signal.SIGTERM)
					sys.stdout.write("Killing pid %d\n" % pid)
		except IDPLException,e:
			sys.stderr.write(e.message)

	def iperferr(self,pid,str):
		""" stderr handler when running iperf under TimedExec """
		sys.stderr.write("%d#: %s" %(pid,str))
		if str.find("bind failed") != -1:
			raise PortInUseException("iperf", self.port)

	def client(self,server,port=5001):
		self.setArgs(["-c","%s" % server,"-p","%d" % int(port),"-f","k","-t","20"])
		self.run()

	def server(self):
		self.setArgs(["-s"])
		self.setPortRange(5001,5010)
		self.isServer = True
		self.run()

	def isFileTransfer(self):
		"""Iperf is memory to memory """
		return False 

class Iperf6(Iperf):
	def __init__(self):
		super(Iperf6,self).__init__()
		self.setV6Test(True)

	def client(self,server,port=5001):
		self.setArgs(["-V", "-c","%s" % self.v6Names[server],"-p","%d" % int(port),"-f","k"])
		self.run()

	def server(self):
		self.setArgs(["-V", "-s"])
		self.setPortRange(5001,5010)
		self.isServer = True
		self.run()


# vim: ts=4:sw=4:
