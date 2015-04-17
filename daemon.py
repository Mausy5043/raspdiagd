#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

import sys, time, math, commands
from libdaemon import Daemon

class MyDaemon(Daemon):
	def run(self):
		Tcpu=range(5)
		sampleptr = 0
		sampleTime = 12
		samples = 5
		# sync to whole minute
		waitTime = (60 + sampleTime) - (time.time() % 60)
		time.sleep(waitTime)
		while True:
			startTime=time.time()

			Tcpu[sampleptr] = int(do_work())

			# report sample average
			sampleptr = sampleptr + 1
			if (sampleptr == samples):
				do_report(sum(Tcpu[:]) / samples)
				sampleptr = 0

			waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
			while waitTime <= 0:
				waitTime = waitTime + sampleTime

			time.sleep(waitTime)

def do_work():
	# Read the CPU temperature
	outTemp = commands.getoutput("cat /sys/class/thermal/thermal_zone0/temp")
	if float(outTemp) > 75000:
	  # can't believe my sensors. Probably a glitch. Wait a while then measure again
	  time.sleep(7)
	  outTemp = commands.getoutput("cat /sys/class/thermal/thermal_zone0/temp")
	  outTemp = float(outTemp) + 0.1

	return outTemp

def do_report(Tc):
	# Get the time and date in human-readable form...
	outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")
	# ... and machine-readable form (UNIX-epoch)
	#outUxDate = commands.getoutput("date +%s")

	f = file('/tmp/11-t-cpu.txt', 'a')
	#f.write('{0}, {1}, {2}\n'.format(outDate, outUxDate, float(float(Tc)/1000)) )
	f.write('{0}, {1}\n'.format(outDate, float(float(Tc)/1000)) )
	f.close()
	return


# Function to search for prime numbers
# within number range
def find_primes(upper_limit):
  count = 0
  candidate = 3
  while(candidate <= upper_limit):
    trial_divisor = 2
    prime = 1 # assume it's prime
    while(trial_divisor**2 <= candidate and prime):
      if(candidate%trial_divisor == 0):
        prime = 0 # it isn't prime
      trial_divisor+=1
    if(prime):
      #print_prime(candidate)
      count += 1
    candidate += 2
  return count

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
