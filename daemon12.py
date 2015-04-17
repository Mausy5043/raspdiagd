#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon12.py measures the CPU load.

import sys, time, math, commands
from libdaemon import Daemon

class MyDaemon(Daemon):
	def run(self):
		sampleptr = 0
		sampleTime = 12
		samples = 5
		cycleTime = samples * sampleTime
		datapoints = 11
		data = [[None]*datapoints for _ in range(samples)]
		# sync to whole minute
		waitTime = (cycleTime + sampleTime) - (time.time() % cycleTime)
		time.sleep(waitTime)
		while True:
			startTime=time.time()

			data[sampleptr] = do_work().split(',')
			print data[sampleptr]

			# report sample average
			sampleptr = sampleptr + 1
			if (sampleptr == samples):
				do_report(sum(data[:]) / samples)
				sampleptr = 0

			waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
			while waitTime <= 0:
				waitTime = waitTime + sampleTime

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
	outCpuST = "NaN"

	outLoad = '{0}, {1}, {2}, {3}, {4}, {5}'.format(outHistLoad, outCpuUS, outCpuSY, outCpuID, outCpuWA, outCpuST)

	return outLoad

def do_report(Tc):
	# Get the time and date in human-readable form and UN*X-epoch...
	outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")

	f = file('/tmp/12-load-cpu.txt', 'a')
	f.write('{0}, {1}\n'.format(outDate, float(float(Tc)/1000)) )
	f.close()
	return

if __name__ == "__main__":
	daemon = MyDaemon('/tmp/raspdiagd-11.pid')
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
