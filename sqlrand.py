#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# sqlrand.py generates random numbers and stores them in an SQL database.

import syslog, traceback
import os, sys, time, math, commands
from libdaemon import Daemon

DEBUG = False
IS_SYSTEMD = os.path.isfile('/bin/journalctl')

class MyDaemon(Daemon):
	def run(self):
		sampleptr = 0
		samples = 5
		datapoints = 10
		data = range(samples)

		sampleTime = 12
		cycleTime = samples * sampleTime
		# sync to whole minute
		waitTime = (cycleTime + sampleTime) - (time.time() % cycleTime)
		if DEBUG:
			print "NOT waiting {0} s.".format(waitTime)
		else:
			time.sleep(waitTime)
		while True:
			try:
				startTime = time.time()

				result = do_work()
				if DEBUG:print result
				data[sampleptr] = result

				# report sample average
				sampleptr = sampleptr + 1
				if (sampleptr == samples):
					if DEBUG:print data
					somma = sum(data[:])
					averages = somma / samples
					if DEBUG:print averages
					do_report(averages)
					do_repsql(averages)
					sampleptr = 0

				waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
				if (waitTime > 0):
					if DEBUG:print "Waiting {0} s".format(waitTime)
					time.sleep(waitTime)
			except Exception as e:
				if DEBUG:
					print("Unexpected error:")
					print e.message
				syslog.syslog(e.__doc__)
				syslog_trace(traceback.format_exc())
				raise

def syslog_trace(trace):
	'''Log a python stack trace to syslog'''
	log_lines = trace.split('\n')
	for line in log_lines:
		if len(line):
			syslog.syslog(line)

def do_work():
	# Read the CPU temperature
	with open("/dev/random", 'rb') as file:
		r = [ord(x) for x in file.read(10)]

	return sum(r)

def do_repsql(result):
	# Get the time and date in human-readable form and UN*X-epoch...
	outDate = commands.getoutput("date '+%F %H:%M:%S'")
	if DEBUG:print "Sending {0} {1}".format(outDate, result)

def do_report(result):
	# Get the time and date in human-readable form and UN*X-epoch...
	outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")
	flock = '/tmp/raspdiagd/sr.lock'
	lock(flock)
	f = file('/tmp/raspdiagd/sqlrand.csv.txt', 'a')
	f.write('{0}, {1}\n'.format(outDate, float(result)) )
	f.close()
	unlock(flock)

def lock(fname):
	open(fname, 'a').close()

def unlock(fname):
	if os.path.isfile(fname):
		os.remove(fname)

if __name__ == "__main__":
	daemon = MyDaemon('/tmp/raspdiagd/sr.pid')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'stop' == sys.argv[1]:
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		elif 'foreground' == sys.argv[1]:
			# assist with debugging.
			print "Debug-mode started. Use <Ctrl>+C to stop."
			DEBUG = True
			if DEBUG:
				logtext = "Daemon logging is ON"
				syslog.syslog(syslog.LOG_DEBUG, logtext)
			daemon.run()
		else:
			print "Unknown command"
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart|foreground" % sys.argv[0]
		sys.exit(2)
