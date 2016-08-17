import os
import time
import socket
import sys
import signal
import hashlib
import pwd
import tempfile
import stat
import TimedExec
from IDPLException import *
from DataMover import *
from SCPMover import *

GitSSH = """#!/bin/bash
ssh -o StrictHostKeyChecking=no -i %s -p %d $1 $2"""

class GitClone(SCPMover):
	def __init__(self, workDir=None):
		super(GitClone,self).__init__()
		self.GITexe = 'git' 
		self.deleteRequirement("FileTransfer")
		self.addRequirement("PathTransfer")
		self.addRequirement("PullSemantics")

	def client(self,server,port=5001):
		cwd = os.getcwd()
		self.setExe(self.GITexe)
		if self.user is None:
			self.user =  pwd.getpwuid(os.geteuid()).pw_name 
		## Create a script so that we can pass parameters to ssh for clone
		self.gitssh = tempfile.mkstemp(dir=cwd)
		f = os.fdopen(self.gitssh[0],'w')
		os.fchmod(self.gitssh[0],stat.S_IRWXU)
		f.write(GitSSH % (self.userkey, int(port)))
		f.close()
		# Tell git to use our wrapper script
		os.environ['GIT_SSH'] = self.gitssh[1]
		# if self.isV6Test():
		#	server = self.v6Names[server]
		#	if server.find(":") >= 0:
		#		server = "[%s]" % server 

		# now create the arguments for git clone itself
		args = ["clone",]
		args.extend(["%s@%s:%s" % (self.user, server,self.inputFile)])
		ofile = self.outputFile.replace("'","")
		args.extend(["%s" % ofile])
		self.setArgs(args)
		print "client: " , args
		self.run()

class GitClone6(GitClone):
	def __init__(self, workDir=None):
		super(GitClone6,self).__init__(workDir)
		self.setV6Test(True)


# vim: ts=4:sw=4:
