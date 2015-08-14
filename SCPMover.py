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

class SCPMover(DataMover):
	def __init__(self, workDir=None):
		super(SCPMover,self).__init__()
		self.SCPexe = '/usr/bin/scp'
		self.SSHDexe = '/usr/sbin/sshd'
		self.KEYGENexe = '/usr/bin/ssh-keygen'
		
		self.setExe(self.SSHDexe)
		self.setOutputHandler(self.sshout)
		self.setErrHandler(self.ssherr)
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
		self.addRequirement("PubKey");

	def sshout(self,pid,str):
		""" stdout handler when running sshd under TimedExec """
		message = "%s(%d): %s" % (socket.getfqdn(),pid,str)
		sys.stdout.write(message)
		host = socket.getfqdn()

	def ssherr(self,pid,str):
		""" stderr handler when running sshd under TimedExec """
		sys.stderr.write("%d#: %s" %(pid,str))
		if str.find("bind failed") != -1:
			raise PortInUseException("sshd", self.port)

	def setAuthorizedKey(self,key):
		"""Drop the authorized key into a secure temporary file"""
		if self.userkeypub is not None:
			os.unlink(self.userkeypub)
		fh,self.userkeypub = tempfile.mkstemp(dir=os.getcwd())
		os.write(fh,key)
		os.close(fh)

	def getUser(self):
		return self.user

	def setUser(self,nuser):
		self.user = nuser

	def getUserPubKeyFile(self):
		return self.userkeypub

	def clientSetup(self):
		# Set up a user key
		self.userkey,self.userkeypub = self.genkey("dsa") 

	def client(self,server,port=5001):
		self.setExe(self.SCPexe)
		if self.user is None:
			self.user =  pwd.getpwuid(os.geteuid()).pw_name 
		args = ["-o","StrictHostKeyChecking=no"]
		args.extend(["-i",self.userkey])
		args.extend(["-P","%d" % int(port)])
		if self.isV6Test():
			args.extend(["-6"])
			server = self.v6Names[server]
			if server.find(":") >= 0:
				server = "[%s]" % server 
		args.extend([self.inputFile, "%s@%s:%s" % 
			(self.user, server,self.outputFile)])
		self.setArgs(args)
		print "client: " , args
		self.run()

	def server(self):
		args = ["-o","AuthorizedKeysFile=%s" % self.userkeypub]
		if self.isV6Test():
			args.extend(["-6"])
		args.extend (["-o","StrictModes=no"])
		args.extend (["-o","UsePam=no"])
		args.extend (["-o","PermitRootLogin=no"])
		args.extend (["-o","PasswordAuthentication=no"])
		args.extend (["-o","PidFile=/dev/null"])
		args.extend(["-h",self.hostkey,"-D", "-e"])
		args.extend(["-f","/dev/null"])
		# put the server in debug mode to accept only one incoming connection
		args.extend(["-d"])
		self.setArgs(args)
		self.setPortRange(5001,5010)
		print "server: " , args
		self.run()

	def serverSetup(self):
		"""This is to setup the local ssh server"""
		if self.serverDir is None:
			self.serverDir = os.getcwd()
		if self.user is None:
			self.user =  pwd.getpwuid(os.geteuid()).pw_name 
		# Set up the host key
		self.hostkey,self.hostkeypub = self.genkey("rsa") 
			
	def genkey(self,bname,type="rsa"):
		"""generates host/user key in a temporary file"""
		cwd = os.getcwd()
		fh,key= tempfile.mkstemp(dir=cwd,text=True)
		os.close(fh)
		keypub = "%s.pub" % key 
		if os.path.isfile(key):
			os.unlink(key)
		if os.path.isfile(keypub):
			os.unlink(keypub)
		keygencmd = [self.KEYGENexe,"-q","-f",key,"-t", type, "-N", ""]
		opcode,out,err = TimedExec.runTimedCmd(5,keygencmd)
		if opcode != 0:
			print out
			print err
			raise SSHServerException("ssh-keygen",err)
		return (key,keypub)
		
class SCPMover6(SCPMover):
	def __init__(self, workDir=None):
		super(SCPMover6,self).__init__(workDir)
		self.setV6Test(True)


# vim: ts=4:sw=4:
