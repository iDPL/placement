import TimedExec
from IDPLException import *
import os
import time
import socket
import sys
import signal


timeoutDefault = 30
portArgDefault = "-p"
class DataMover(object):
	def __init__(self,timeout=timeoutDefault):
		self.timeout = timeout
		self.lowPort = None 
		self.highPort = None 
		self.exe = ""
		self.args = []
		self.portArg = portArgDefault
		self.port = 0

	def setPortRange(self,low,high):
		self.lowPort = low
		self.highPort = high
	
	def getPortRange(self,low,high):
		return (self.lowPort, self.highPort)

	def setPortArg(self,portArg):
		self.portArg = portArg 

	def setExe(self, executable):
		self.exe = executable

	def setArgs(self,args):
		self.args = args 

	def setOutputHandler(self,stdout=None, stderr=None):
		self.stdoutHandler = stdout 
		self.stderrHandler = stderr 

	def run(self):
		if self.lowPort is None or self.highPort is None:
			targs=[self.exe]
			targs.extend(self.args)
			resultcode,output,err=TimedExec.runTimedCmd(self.timeout,
				targs,self.stdoutHandler, self.stderrHandler)
			if resultcode < 0:
				sys.stdout.write("Result code: %d\n" % resultcode)
				raise TimeOutException(self.exe)	
		else:
			for self.port in range(self.lowPort,self.highPort):
				try:
					targs=[self.exe]
					targs.extend(self.args)
					targs.extend([self.portArg, "%d" % int(self.port)]),
					resultcode,output,err=TimedExec.runTimedCmd(self.timeout,
						targs, self.stdoutHandler, self.stderrHandler)
					if resultcode < 0:
						sys.stdout.write("Result code: %d\n" % resultcode)
						raise TimeOutException(self.exe)	
					break
				except PortInUseException,e:
					sys.stderr.write(e.message)


class IperfMover(DataMover):

	def __init__(self):
		super(IperfMover,self).__init__()
		iperfExe = '/usr/bin/iperf'
		if not os.path.exists(iperfExe):
			iperfExe = '/opt/iperf/bin/iperf'
		self.setExe(iperfExe)
		self.setOutputHandler(self.iperfout,self.iperferr)
	
	def iperfout(self,pid,str):
		""" stdout handler when running iperf under TimedExec """
		global transferredKB
		message = "%s(%d): %s" % (socket.getfqdn(),pid,str)
		sys.stdout.write(message)
		host = socket.getfqdn()
		try:
			if str.find("its/sec") != -1:
				transferredKB = str.split()[-4]
				msg = " ".join(str.split()[-2:])
				# chirp.ulog("%s: iperf %s" % (host, msg))
				os.kill(pid,signal.SIGTERM)
			if str.find("listening") != -1:
				listenport = int(str.split()[-1])
				# chirp.setJobAttr("IperfServer","'%s %d'" % (host, listenport))
		except IDPLException,e:
			sys.stderr.write(e.message)

	def iperferr(self,pid,str):
		""" stderr handler when running iperf under TimedExec """
		sys.stdout.write("%d#: %s" %(pid,str))
		raise PortInUseException("iperf", self.port)

	def client(self,server,port=5001):
		self.setArgs(["-c","%s" % server,"-p","%d" % int(port)])
		self.run()

	def server(self):
		self.setArgs(["-s"])
		self.setPortRange(5001,5010)
		self.run()


# vim: ts=4:sw=4:
