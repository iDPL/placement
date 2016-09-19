import TimedExec
from IDPLException import *
import os
import time
import socket
import sys
import signal
import hashlib

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
		self.portReporter = Reporter().noReport
		self.inputFile = None
		self.outputFile = None
		self.tstart=time.time()
		self.tend=time.time()
		self.delta = -1
		self.transferred = 0
		self.moverArgs = None
		## List of Strings that are "requirements" for a particular dataMover
		self.requirements=[]
		self.addRequirement("FileTransfer")

		## add v6 addresses for v4 names, used when performing a IPv6 test
		self.v6Names = { \
			'idpl.elab.cnic.cn':'2400:dd01:1011:1:92b1:1cff:fe0c:740d', \
			'mickey.buaa.edu.cn':'2001:da8:203:d406:16da:e9ff:fef9:b68f', \
			'komatsu.chtc.wisc.edu':'2607:f388:107c:502::c', \
			'flashio-osg.calit2.optiputer.net':'2607:f720:1700:31d::61', \
			'mongo.mayer.optiputer.net':'2607:f720:1700:1b32::6', \
			'murpa.rocksclusters.org':'2607:f720:1400:1410:d267:e5ff:fe13:108f' }
		# default tests to v4
		self.v6Test = False


	## Various Getters including abstract ones
	def getPortRange(self,low,high):
		return (self.lowPort, self.highPort)

	def getUserPubKeyFile(self):
		"""Overridden by movers that need a public key"""
		return None 
	def getTimers(self):
		""" return the timers from the run """
		## delta may have been extracted from tool output, see IperfMover
		if self.delta < 0:
			self.delta=self.tend - self.tstart
		return(self.tstart,self.tend, self.delta)

	def isV6Test(self):
		return self.v6Test

	##  Various Setters
	def setPortRange(self,low,high):
		self.lowPort = low
		self.highPort = high

	def setPortArg(self,portArg):
		self.portArg = portArg 

	def setExe(self, executable):
		self.exe = executable

	def setArgs(self,args):
		self.args = args 

	def setMoverArgs(self,moverargs):
			"""This is an abstract method. Specific Movers should Override"""
			pass

	def setOutputHandler(self,stdout=None):
		self.stdoutHandler = stdout

	def setErrHandler(self,stderr=None):
		self.stderrHandler = stderr 

	def setInputFile(self,fname):
		"""Set the name of the InputFile (for reading)"""
		self.inputFile = fname

	def setOutputFile(self,fname):
		"""Set the name of the OutputFile (for writing)"""
		self.outputFile = fname

	def setPortReporter(self,reporter):
		""" enable the port actually used by the server to be reported """
		self.portReporter = reporter

	def setTimeout(self,timeout):
		self.timeout = timeout

	def setV6Test(self,flag):
		self.v6Test = flag

	## End of Setters

	def md5(self,fname):
		"""Open the file fname, read it and calc md5sum"""
		buflen = 65536
		hash = hashlib.md5()
		with open(fname,'r',buflen) as f:
			buf = f.read(buflen)
			while len(buf) > 0:
				hash.update(buf)
				buf = f.read(buflen)
		return hash.hexdigest()

	
	def clientSetup(self):
		"""Generic Client Setup prior to Movement"""
		pass
	def serverSetup(self):
		"""Generic  Server Setup prior to Movement"""


	## Methods to determine requirements of a particular Mover
	def hasRequirement(self,req):
		return (req in self.requirements)

	def addRequirement(self,req):
		if not self.hasRequirement(req):
			self.requirements.append(req)
	
	def deleteRequirement(self,req):
		while self.hasRequirement(req):
			self.requirements.remove(req)

	def run(self):

		if self.hasRequirement("FileTransfer") and self.inputFile is not None:
			iFile = file(self.inputFile,'r')
		else:
			iFile = None

		if self.lowPort is None or self.highPort is None:
			targs=[self.exe]
			targs.extend(self.args)
			self.tstart=time.time()
			resultcode,output,err=TimedExec.runTimedCmd(self.timeout,
				targs, indata=iFile,
				outhandler=self.stdoutHandler, 
				errhandler=self.stderrHandler)
			self.tend=time.time()
			if resultcode < 0:
				sys.stdout.write("Result code: %d\n" % resultcode)
				if iFile is not None:
					iFile.close()
				raise TimeOutException(self.exe)	
		else:
			for self.port in range(self.lowPort,self.highPort):
				try:
					targs=[self.exe]
					targs.extend(self.args)
					targs.extend([self.portArg, "%d" % int(self.port)]),
					## in 2 seconds call the portReporter to indicate
					## which port is being used. If specific mover has
					## an error within 2 seconds, assumed that port is in use.
					## Then next port is tried.
					rd = TimedExec.RunDelayed(2,self.portReporter,self.port)
					rd.run()
					self.tstart=time.time()
					resultcode,output,err=TimedExec.runTimedCmd(self.timeout,
						targs, indata=iFile,
						outhandler=self.stdoutHandler, 
						errhandler=self.stderrHandler)
					self.tend=time.time()
					rd.join()
					if resultcode < 0:
						sys.stdout.write("Result code: %d\n" % resultcode)
						raise TimeOutException(self.exe)	
					break
				except PortInUseException,e:
					## Cancel the portReporter
					rd.cancel()
					sys.stderr.write(e.message + "\n")
					rd.join()

			if iFile is not None:
				iFile.close()


class Reporter(object):
	""" Empty portReport. Nothing is printed """
	def noReport(self, port):
		pass

class PrintReporter(object):
	""" print the port to stdout """
	def doReport(self, port):
		print port	

# vim: ts=4:sw=4:
