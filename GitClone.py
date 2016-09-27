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
		self.gitAction='clone'
		self.deleteRequirement("FileTransfer")
		self.addRequirement("PathTransfer")
		self.addRequirement("PullSemantics")

	def setMoverArgs(self,moverargs):
		args=re.findall(r'gitclone:{(.*)}',moverargs)
		print "GitClone.setMoverArgs:", args
		# only support pull or clone
		for a in args:
			if a == 'pull' or a == 'clone':
				self.gitAction=a
		print self.gitAction
			
		
		
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
		# now create the arguments for git clone itself
		args = [self.gitAction,]
		ofile = self.outputFile.replace("'","")
		if self.isV6Test():
			server = self.v6Names[server]
		# Versions of git are broken in handling v6 literal addresses
		# [user@0000:1111::0] styled URL seems to work
		if self.isV6Test() and server.find(":") >= 0:
			remote="[%s@%s]:%s" % (self.user, server,self.inputFile)
		else:
			remote="%s@%s:%s" % (self.user, server,self.inputFile)

		if self.gitAction == 'clone':
			args.extend([remote])
			args.extend(["%s" % ofile])
		else:
			# This is a pull. chdir to the local repo, update the
			# remote origin url and then pull
			os.chdir(ofile)
			cmd = [self.GITexe,"config","remote.origin.url",remote]
			TimedExec.runTimedCmd(2,cmd)
			
		self.setArgs(args)
		print "client: " , args
		self.run()

class GitClone6(GitClone):
	def __init__(self, workDir=None):
		super(GitClone6,self).__init__(workDir)
		self.setV6Test(True)


# vim: ts=4:sw=4:
