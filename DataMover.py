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
		self.inputFile = None
		self.outputFile = None

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

	def setInputfile(self,fname):
		self.inputFile = fname

	def setOutputFile(self,fname):
		self.outputFile = fname

	def run(self):

		if self.inputFile is not None:
			iFile = file(self.inputFile,'r')
		else:
			iFile = None

		if self.lowPort is None or self.highPort is None:
			targs=[self.exe]
			targs.extend(self.args)
			resultcode,output,err=TimedExec.runTimedCmd(self.timeout,
				targs, indata=iFile,
				outhandler=self.stdoutHandler, 
				errhandler=self.stderrHandler)
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
					rd = TimedExec.RunDelayed(2,chirpPort().dRun,self.port)
					rd.run()
					resultcode,output,err=TimedExec.runTimedCmd(self.timeout,
						targs, indata=iFile,
						outhandler=self.stdoutHandler, 
						errhandler=self.stderrHandler)
					if resultcode < 0:
						sys.stdout.write("Result code: %d\n" % resultcode)
						raise TimeOutException(self.exe)	
					break
				except PortInUseException,e:
					sys.stderr.write(e.message)
					rd.cancel()
					rd.join()

			if iFile is not None:
				iFile.close()


class Iperf(DataMover):

	def __init__(self):
		super(Iperf,self).__init__()
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

class Netcat(DataMover):
	""" Netcat-based Data Mover """
	def __init__(self):
		super(Netcat,self).__init__()
		self.setExe('/usr/bin/nc')
		self.setOutputHandler(self.netcatout,self.netcaterr)
		self.oFile = None	

	def setOutputFile(self,fname):
		super(Netcat,self).setOutputFile(fname)
		self.oFile = file(self.outputFile,"w")	

	def netcatout(self,pid,str):
		""" stdout handler when running netcat under TimedExec """
		message = "%s(%d): %s" % (socket.getfqdn(),pid,str)
		if self.oFile is not None:
			self.oFile.write(str)
		else:
			sys.stdout.write(str)

	def netcaterr(self,pid,str):
		""" stderr handler when running iperf under TimedExec """
		sys.stdout.write("%d#: %s" %(pid,str))
		raise PortInUseException("netcat", self.port)

	def client(self,server,port=5001):
		self.setArgs(["%s" % server,"%d" % int(port)])
		self.run()
		if self.oFile is not None:
			self.oFile.close()

	def server(self):
		self.setPortArg("-l")
		self.setPortRange(5001,5010)
		self.run()

class chirpPort(object):
	def dRun(self, port):
			print "dRUN is being called with %d" % port 
			return TimedExec.runTimedCmd(1,["/bin/echo","%d" % port ])

# vim: ts=4:sw=4:
