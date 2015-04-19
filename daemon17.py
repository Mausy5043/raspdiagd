#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon17.py communicates with the smart electricity meter.

import sys, time, math, commands
from libdaemon import Daemon

import serial, re

port = serial.Serial()
port.baudrate = 9600
port.bytesize = serial.SEVENBITS
port.parity = serial.PARITY_EVEN
port.stopbits = serial.STOPBITS_ONE
port.xonxoff = 1
port.rtscts = 0
port.dsrdtr = 0
port.timeout = 15
port.port = "/dev/ttyUSB0"

class MyDaemon(Daemon):
	def run(self):
		sampleptr = 0
		samples = 6
		datapoints = 8

		sampleTime = 10
		cycleTime = samples * sampleTime
		# sync to whole minute
		waitTime = (cycleTime + sampleTime) - (time.time() % cycleTime)
		time.sleep(waitTime)

		port.open()
		serial.XON

		while True:
			startTime=time.time()

			result = do_work().split(',')
			data = map(int, result)

			sampleptr = sampleptr + 1
			if (sampleptr == samples):
				do_report(data)
				sampleptr = 0

			waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
			while waitTime <= 0:
				waitTime = waitTime + sampleTime

			time.sleep(waitTime)

def do_work():
	# flag used to exit the while-loop
	abort = 0
	# countdown counter used to prevent infinite loops
	loops2go = 40
	# storage space for the telegram
	telegram = []
	# end of line delimiter
	delim = "\x0a"

	while abort == 0:
		try:
			line = "".join(iter(lambda:port.read(1),delim)).strip()
		except:
			abort = 2
		if line == "!":
			abort = 1
		if line != "":
			telegram.append(line)

		loops2go = loops2go - 1
		if loops2go < 0:
			abort = 3

  # test for correct start of telegram
	if telegram[0][0] != "/":
		abort = 2

	print telegram
	return '{0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}'.format(0, 1, 2, 3, 4, 5, 6, 7)

def do_report(result):
	# Get the time and date in human-readable form and UN*X-epoch...
	outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")

	result = ', '.join(map(str, result))
	f = file('/tmp/17-electra.txt', 'a')
	f.write('{0}, {1}\n'.format(outDate, result) )
	f.close()
	return

if __name__ == "__main__":
	daemon = MyDaemon('/tmp/raspdiagd-17.pid')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'stop' == sys.argv[1]:
			serial.XOFF
			port.close()
			daemon.stop()
		elif 'foreground' == sys.argv[1]:
			# assist with debugging.
			print "Debug-mode started. Use <Ctrl>+C to stop."
			daemon.run()
		else:
			print "Unknown command"
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|foreground" % sys.argv[0]
		sys.exit(2)
