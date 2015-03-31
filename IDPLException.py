# Exceptions generated in the IDPL
class IDPLException(Exception):
	""" Generic Exception for IDPL """
	def __init__(self,subclass,src,msg):
		mtmp = "IDPLException.%s(%s):%s"
		self.message = mtmp % (type(subclass).__name__,src,msg)
		self.source = src

class PortInUseException(IDPLException):
	""" If a port is in use """
	def __init__(self,src,prt):
		super(PortInUseException,self).__init__(self,src,"%d" % prt)
		self.port = prt	

class TimeOutException(IDPLException):
	""" if a process timed out """
	def __init__(self,src):
		super(TimeOutException,self).__init__(self,src,"")

class CondorConfigValException(IDPLException):
	""" If we couldn't read a condor_config_val """
	def __init__(self,src):
		super(CondorConfigValException,self).__init__(self,src,"")
	
class CondorChirpGetException(IDPLException):
	""" If we couldn't get an Attribute """
	def __init__(self,src):
		super(CondorChirpGetException,self).__init__(self,src,"")
	
class CondorChirpSetException(IDPLException):
	""" If we couldn't set an Attribute """
	def __init__(self,src):
		super(CondorChirpSetException,self).__init__(self,src,"")
	
class CondorChirpUlogException(IDPLException):
	""" If we couldn't log a message Attribute """
	def __init__(self,src):
		super(CondorChirpUlogException,self).__init__(self,src,"")
	
# vim: ts=4:sw=4:tw=78
