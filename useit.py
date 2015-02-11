#!/usr/bin/env python
import TimedExec 
import sys


#This is used to create new subprocess and it will return output as well as error 
resultcode,output,err=TimedExec.runTimedCmd(30,["/usr/bin/iperf","-s"])
sys.stdout.write("Result code: %d\n" % resultcode)
print "==== Command stdout ==="
for line in output:
	sys.stdout.write(line)
print "=======Command Stderr===="
for line in err:
	sys.stdout.write(line)
# vim: ts=4:sw=4:tw=78
