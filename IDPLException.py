# Exceptions generated in the IDPL
class PortInUseException(Exception):
	""" If a port is in use """
	def __init__(self,src,prt):
		self.source = src
		self.port = prt	

class TimeOutException(Exception):
	""" if a process timed out """
	def __init__(self,src):
		self.source = src

class CondorConfigValException(Exception):
	""" If we couldn't read a condor_config_val """
	def __init__(self,src):
		self.source = src
	
class CondorChirpGetException(Exception):
	""" If we couldn't get an Attribute """
	def __init__(self,src):
		self.source = src
	
class CondorChirpSetException(Exception):
	""" If we couldn't set an Attribute """
	def __init__(self,src):
		self.source = src
	
class CondorChirpUlogException(Exception):
	""" If we couldn't log a message Attribute """
	def __init__(self,src):
		self.source = src
	
