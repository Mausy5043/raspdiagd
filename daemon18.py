#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon18.py reads data from an Arduino running the cmdMULTIsens sketch from
# https://github.com/Mausy5043/arduino.git.

import sys, time, math, commands
from libdaemon import Daemon
import serial, re

class MyDaemon(Daemon):
	def run(self):
		sampleptr = 0
		samples = 5*5
		datapoints = 11
		data = [[None]*datapoints for _ in range(samples)]

		sampleTime = 12
		cycleTime = samples * sampleTime
		# sync to whole minute
		waitTime = (cycleTime + sampleTime) - (time.time() % cycleTime)
		time.sleep(waitTime)
		while True:
			startTime=time.time()

			result = do_work().split(',')

			data[sampleptr] = map(float, result)
			print data[sampleptr]
			# report sample average
			sampleptr = sampleptr + 1
			if (sampleptr == samples):
				somma = map(sum,zip(*data))
				# not all entries should be float
				# 0.37, 0.18, 0.17, 4, 143, 32147, 3, 4, 93, 0, 0
				averages = [format(s / samples, '.3f') for s in somma]
				#averages[3]=int(data[sampleptr-1][3])
				#averages[4]=int(data[sampleptr-1][4])
				#averages[5]=int(data[sampleptr-1][5])
				do_report(averages)
				sampleptr = 0

			waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
			while waitTime <= 0:
				waitTime = waitTime + sampleTime

			time.sleep(waitTime)

def gettelegram(cmd):
  # flag used to exit the while-loop
  abort = 0
  # countdown counter used to prevent infinite loops
  loops2go = 10
  #
  telegram = "NaN";

  while abort == 0:
    try:
      port.write(cmd)
      line = port.readline()
    except:
      # read error, terminate prematurely
      abort = 2

    if line != "":
      line = line.strip().split()
      if line[0] == cmd:
        if line[-1] == "!":
          telegram = ""
          for item in range(1,len(line)-1):
            telegram = telegram + ' {0}'.format(line[item])
          abort = 1

    loops2go = loops2go - 1
    if loops2go < 0:
      abort = 3

  # Return codes:
  # abort == 1 indicates a successful read
  # abort == 2 means that a serial port read/write error occurred
  # abort == 3 no valid data after several attempts

  return (telegram, abort)

def do_work():
	# 12 datapoints gathered here
	telegram, status = gettelegram("A")
	print telegram
	if (status != 1):
		telegram = -1

	return telegram

def do_report(result):
	# Get the time and date in human-readable form and UN*X-epoch...
	#outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")
	outDate = commands.getoutput("date '+%F %H:%M:%S'")

	result = ', '.join(map(str, result))
	f = file('/tmp/testser.txt', 'a')
	f.write('{0}, {1}\n'.format(outDate, result) )
	f.close()
	return

if __name__ == "__main__":
	port = serial.Serial('/dev/ttyACM0', 9600, timeout=10)
	serial.dsrdtr = False
	time.sleep(0.5)
	daemon = MyDaemon('/tmp/raspdiagd-18.pid')
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
