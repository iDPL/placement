import os
import socket
import CondorTools

class ChirpInfo(object):
	""" Use Chirp jobAttrs to post host:port pairs """
	def __init__(self,prefix):
		self.prefix = prefix
		self.chirp = CondorTools.CondorChirp()
		self.jobAttr = "%sServer" % prefix
		self.md5Attr = "%sMD5" % prefix
		self.OutfileAttr = "%sOutfile" % prefix
		self.UserkeyAttr = "%sUserkey" % prefix
		self.UserAttr = "%sUser" % prefix
		self.host = socket.getfqdn()

	## Generic logging
	def ulog(self, who, message):
		logMessage = "%s(%s) %s:%s" % (self.host,self.prefix,who,message)
		self.chirp.ulog(logMessage)
	
	# MD5 Attributes
	def postMD5(self,md5):
		self.chirp.setJobAttr(self.md5Attr, "'%s'" % md5)

	def clearMD5(self):
		self.chirp.setJobAttr(self.md5Attr, None)
	def getMD5(self):
		interval = 5
		maxtries = 12 
		md5 = self.chirp.getJobAttrWait(self.md5Attr,None,interval, maxtries)
		return md5

	# Port Attributes
	def postPort(self,port):
		self.chirp.setJobAttr(self.jobAttr, "'%s %d'" % (self.host, port))
	def clearPort(self):
		self.chirp.setJobAttr(self.jobAttr, None)
	def getHostPort(self):
		interval = 5
		maxtries = 12*3
		serverInfo = self.chirp.getJobAttrWait(self.jobAttr,None,interval, maxtries)
		host,port = serverInfo.strip("'").split()
		return (host,port)	

	## The attributes are written before server is declared ready
	## Never explicitly cleared
	# Outputfile (for SCP)
	def postOutputfile(self,outfile):
		if not os.path.isabs(outfile):
			outfile = os.path.join(os.getcwd(),outfile)
		self.chirp.setJobAttr(self.OutfileAttr, "'%s'" % outfile)

	def getOutputfile(self):
		return self.chirp.getJobAttr(self.OutfileAttr)

	# Userkey (For SCP)
	# Use Chirp for the client to send the public key
	def postUserkey(self,keyfile):
		"""read the contents of a keyfile and post, unless keyfile is None"""
		if keyfile is None: return
		f = open(keyfile,"r")
		key = "'%s'" % f.readline().strip()
		print "key is '%s'" % key
		f.close()
		self.chirp.setJobAttr(self.UserkeyAttr, key)

	def getUserkey(self):
		interval = 5
		maxtries = 12*3
		# trim off the beginning/ending '
		return self.chirp.getJobAttrWait(self.UserkeyAttr,None,interval, maxtries)[1:-1]

	def clearUserkey(self):
		self.chirp.setJobAttr(self.UserkeyAttr, None)

	# Localuser (for SCP)
	def postUser(self,user):
		self.chirp.setJobAttr(self.UserAttr, "'%s'" % user)

	def getUser(self):
		return self.chirp.getJobAttr(self.UserAttr)

