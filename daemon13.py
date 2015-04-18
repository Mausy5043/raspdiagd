#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon13.py measures the network traffic.

import sys, time, math, commands
from libdaemon import Daemon

class MyDaemon(Daemon):
	def run(self):
		sampleptr = 0
		samples = 5
		datapoints = 6
		data = [[None]*datapoints for _ in range(samples)]

		sampleTime = 12
		cycleTime = samples * sampleTime
		# sync to whole minute
		waitTime = (cycleTime + sampleTime) - (time.time() % cycleTime)
		time.sleep(waitTime)
		while True:
			startTime=time.time()

			result = do_work().split(',')

			data[sampleptr] = map(int, result)
			# report sample average
			sampleptr = sampleptr + 1
			if (sampleptr == samples):
				somma = map(sum,zip(*data))
				print somma
				averages = [format(s / samples, '.3f') for s in somma]
				print averages
				#do_report(averages)
				sampleptr = 0

			waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
			while waitTime <= 0:
				waitTime = waitTime + sampleTime

			time.sleep(waitTime)

def do_work():
	# 6 datapoints gathered here
	# Network traffic
	wlIn = 0
	wlOut = 0
	etIn = 0
	etOut = 0
	loIn = 0
	loOut = 0

	list = commands.getoutput("cat /proc/net/dev").splitlines()
	for line in range(2,len(list)):
		device = list[line].split()[0]
		if device == "lo:":
			loIn = list[line].split()[1]
			loOut = list[line].split()[9]
		if device == "eth0:":
			etIn = list[line].split()[1]
			etOut = list[line].split()[9]
		if device == "wlan0:":
			wlIn = list[line].split()[1]
			wlOut = list[line].split()[9]
		if device == "wlan1:":
			wlIn = list[line].split()[1]
			wlOut = list[line].split()[9]

	#outTraffice = '{0}, {1}, {2}, {3}, {4}, {5}'.format(loIn, loOut, etIn, etOut, wlIn, wlOut)
	return '{0}, {1}, {2}, {3}, {4}, {5}'.format(loIn, loOut, etIn, etOut, wlIn, wlOut)

	#return outTraffic

def do_report(result):
	# Get the time and date in human-readable form and UN*X-epoch...
	outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")

	result = ', '.join(map(str, result))
	f = file('/tmp/13-nettraffic.txt', 'a')
	f.write('{0}, {1}\n'.format(outDate, result) )
	f.close()
	return

if __name__ == "__main__":
	daemon = MyDaemon('/tmp/raspdiagd-13.pid')
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