#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon12.py measures the CPU load.

import os, sys, time, math, commands
from libdaemon import Daemon

DEBUG = False

class MyDaemon(Daemon):
	def run(self):
		sampleptr = 0
		samples = 5
		datapoints = 11
		data = [[None]*datapoints for _ in range(samples)]

		sampleTime = 12
		cycleTime = samples * sampleTime
		# sync to whole minute
		waitTime = (cycleTime + sampleTime) - (time.time() % cycleTime)
		if DEBUG:
			print "NOT waiting {0} s.".format(waitTime)
		else:
			time.sleep(waitTime)
		while True:
			startTime = time.time()

			result = do_work().split(',')

			data[sampleptr] = map(float, result)
			# report sample average
			sampleptr = sampleptr + 1
			if (sampleptr == samples):
				somma = map(sum,zip(*data))
				# not all entries should be float
				# 0.37, 0.18, 0.17, 4, 143, 32147, 3, 4, 93, 0, 0
				averages = [format(s / samples, '.3f') for s in somma]
				averages[3]=int(data[sampleptr-1][3])
				averages[4]=int(data[sampleptr-1][4])
				averages[5]=int(data[sampleptr-1][5])
				do_report(averages)
				sampleptr = 0

			waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
			if (waitTime > 0):
				if DEBUG:print "Waiting {0} s".format(waitTime)
				time.sleep(waitTime)

def do_work():
	# 6 datapoints gathered here
	outHistLoad = commands.getoutput("cat /proc/loadavg").replace(" ",", ").replace("/",", ")

	# 5 datapoints gathered here
	outCpu = commands.getoutput("vmstat 1 2").splitlines()[3].split()
	outCpuUS = outCpu[12]
	outCpuSY = outCpu[13]
	outCpuID = outCpu[14]
	outCpuWA = outCpu[15]
	outCpuST = 0

	return '{0}, {1}, {2}, {3}, {4}, {5}'.format(outHistLoad, outCpuUS, outCpuSY, outCpuID, outCpuWA, outCpuST)

def do_report(result):
	# Get the time and date in human-readable form and UN*X-epoch...
	outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")
	result = ', '.join(map(str, result))
	flock = '/tmp/raspdiagd-12.lock'
	lock(flock)
	f = file('/tmp/12-load-cpu.csv', 'a')
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
	daemon = MyDaemon('/tmp/raspdiagd-12.pid')
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
			daemon.run()
		else:
			print "Unknown command"
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart|foreground" % sys.argv[0]
		sys.exit(2)
