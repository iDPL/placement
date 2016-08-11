import TimedExec
import IDPLException
import os
import time

defaultTimeout = 2
class CondorChirp():
	def __init__(self):
		resultcode,out,err=TimedExec.runTimedCmd(defaultTimeout,
			["condor_config_val","LIBEXEC"])

		#print "CondorChirp out =", out
		#print "CondorChirp err =", err 
		if (resultcode < 0):
			raise IDPLExecption.CondorConfigValException("Chirp Init")
		else:
			self.executable=os.path.join(out[0].strip(),"condor_chirp")

	def getJobAttr(self,attr):
		""" condor chirp to get a job attribute """
		resultcode,out,err=TimedExec.runTimedCmd(defaultTimeout,
			[self.executable,"get_job_attr", attr])
		if resultcode != 0:
			raise IDPLException.CondorChirpGetException(attr)
		else:
			if out[0].strip().lower() == "undefined":
				return None
			else:
				return out[0].strip()
	
	def getJobAttrWait(self,attr,waitVal,interval,maxTries):
		""" condor chirp to get a job attribute. 
		wait for the value to be something other than waitVal """
		tries = 0
		rattr = self.getJobAttr(attr)
		while rattr == waitVal and tries < maxTries:
			tries += 1
			if tries >= maxTries:
				raise IDPLException.CondorChirpGetException(attr)
			time.sleep(interval)
			rattr = self.getJobAttr(attr)

		return rattr
		
	def setJobAttr(self,attr,val):
		""" condor chirp to set a job attribute
			if val == None, set it to 'UNDEFINED' """

		if val is None:
			val = "UNDEFINED"

		resultcode,out,err=TimedExec.runTimedCmd(defaultTimeout,
			[self.executable,"set_job_attr", attr, val])
		if resultcode != 0:
			raise IDPLException.CondorChirpSetException(attr + ":" + val)
		else:
			return out 
		

	def ulog(self,message):
		""" condor chirp to log a message """  

		resultcode,out,err=TimedExec.runTimedCmd(defaultTimeout,
			[self.executable,"ulog", "'%s'" % message])
		if resultcode != 0:
			raise IDPLException.CondorChirpUlogException(message)
		else:
			return out 
		
# vim: ts=4:sw=4:
