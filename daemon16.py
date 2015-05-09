#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon16.py reports various UPS variables.

import os, sys, time, math, commands
from libdaemon import Daemon

class MyDaemon(Daemon):
	def run(self):
		sampleptr = 0
		samples = 6
		datapoints = 5
		data = [[None]*datapoints for _ in range(samples)]

		sampleTime = 10
		cycleTime = samples * sampleTime
		# sync to whole minute
		waitTime = (cycleTime + sampleTime) - (time.time() % cycleTime)
		time.sleep(waitTime)
		while True:
			startTime = time.time()

			result = do_work().split(',')
			data[sampleptr] = map(float, result)

			sampleptr = sampleptr + 1
			if (sampleptr == samples):
				somma = map(sum,zip(*data))
				averages = [format(s / samples, '.3f') for s in somma]
				do_report(averages)
				sampleptr = 0

			waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
			if (waitTime > 0):
				time.sleep(waitTime)

def do_work():
	# 5 datapoints gathered here
	upsc = commands.getoutput("upsc ups@localhost").splitlines()
	for element in range(0, len(upsc) - 1):
		var = upsc[element].split(': ')
		if (var[0] == 'input.voltage'):
			ups0 = float(var[1])
		if (var[0] == 'battery.voltage'):
			ups1 = float(var[1])
		if (var[0] == 'battery.charge'):
			ups2 = float(var[1])
		if (var[0] == 'ups.load'):
			ups3 = float(var[1])
		if (var[0] == 'battery.runtime'):
			ups4 = float(var[1])

	return '{0}, {1}, {2}, {3} ,{4}'.format(ups0, ups1, ups2, ups3, ups4)

def do_report(result):
	# Get the time and date in human-readable form and UN*X-epoch...
	outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")

	result = ', '.join(map(str, result))
	flock = '/tmp/raspdiagd-16.lock'
	lock(flock)
	f = file('/tmp/16-aux-ups.csv', 'a')
	f.write('{0}, {1}\n'.format(outDate, result) )
	f.close()
	unlock(flock)
	return

def lock(fname):
	open(fname, 'a').close()

def unlock(fname):
	if os.path.isfile(fname):
		os.remove(fname)

if __name__ == "__main__":
	daemon = MyDaemon('/tmp/raspdiagd-16.pid')
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
			daemon.run()
		else:
			print "Unknown command"
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart|foreground" % sys.argv[0]
		sys.exit(2)
