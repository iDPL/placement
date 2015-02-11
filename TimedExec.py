## This is small python class The will allow you 
## to run a command with a timeout.  It returns the subprocess 
## return code and output/err data from stdout/stderr
## Caveat Emptor
##         Don't use if very large volumes of output are expect
import subprocess
import signal
import os 
import threading
import errno
import sys
import select
from contextlib import contextmanager

class TimeoutThread(object):
	def __init__(self, seconds):
		self.seconds = seconds
		self.cond = threading.Condition()
		self.cancelled = False
		self.thread = threading.Thread(target=self._wait)

	def run(self):
		"""Begin the timeout."""
		self.thread.start()

	def _wait(self):
		with self.cond:
			self.cond.wait(self.seconds)

			if not self.cancelled:
				self.timed_out()

	def cancel(self):
		"""Cancel the timeout, if it hasn't yet occured."""
		with self.cond:
			self.cancelled = True
			self.cond.notify()
		self.thread.join()

	def timed_out(self):
		"""The timeout has expired."""
		raise NotImplementedError

class KillProcessThread(TimeoutThread):
	def __init__(self, seconds, pid):
		super(KillProcessThread, self).__init__(seconds)
		self.pid = pid

	def timed_out(self):
		try:
			#this is for linux you need to change it for windows
			os.kill(self.pid, signal.SIGKILL) 
		except OSError,e:
			# If the process is already gone, ignore the error.
			if e.errno not in (errno.EPERM, errno. ESRCH):
				raise e


@contextmanager
def processTimeout(seconds, pid):
	timeout = KillProcessThread(seconds, pid)
	timeout.run()
	try:
		yield
	finally:
		timeout.cancel()


def runTimedCmd(timeout, cmd):
	""" Run a command with a timeout.  returns it's output,error,and 
		returncode. stdin is None """

	## create the process
	proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

	outdata=[]
	errdata=[]
	## Output to monitor
	p_out = proc.stdout
	p_err = proc.stderr
	monitor = [p_out,p_err]

	## Grab data and append until process ends or times out
	with processTimeout(timeout, proc.pid):
		wantmore = True
		while wantmore:
			# Check if subprocess has already exited
			if proc.poll() is not None:
				break

			# See what's ready to be read 
			readable,writable,exceptional=select.select(monitor,[],monitor)

			for s in exceptional:
				wantmore = False

			for s in readable:
				line = s.readline()
				if s is p_out and len(line) > 0:
					outdata.append(line)
				if s is p_err and len(line) > 0:
					errdata.append(line)

	resultcode = proc.wait()

	## There is a race above where proc.poll() may indicate process
	## is finished, but errdata or outdata still has buffered data.
	## Grab it here
	for line in p_out.readlines():
		outdata.append(line)
	for line in p_err.readlines():
		errdata.append(line)

	return resultcode,outdata,errdata
