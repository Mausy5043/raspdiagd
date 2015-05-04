#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon99.py creates an XML-file and uploads data to the server.

import os, sys, platform, time, math, commands
from libdaemon import Daemon

class MyDaemon(Daemon):
	def run(self):
		sampleptr = 0
		samples = 1
		#datapoints = 1
		#data = range(samples)

		sampleTime = 60
		cycleTime = samples * sampleTime
		# sync to whole minute
		waitTime = (cycleTime + sampleTime) - (time.time() % cycleTime)
		time.sleep(waitTime)
		while True:
			startTime=time.time()

			if os.path.ismount('/mnt/share1'):
				print 'dataspool is mounted'
				do_xml()

			waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
			while waitTime <= 0:
				waitTime = waitTime + sampleTime

			time.sleep(waitTime)

def do_xml():
	#
	uname           = os.uname()
	Tcpu            = float(commands.getoutput("cat /sys/class/thermal/thermal_zone0/temp"))/1000
	fcpu            = float(commands.getoutput("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"))/1000
	raspdiagdbranch = commands.getoutput("cat /home/pi/.raspdiagd.branch")
	gitbinbranch    = commands.getoutput("cat /home/pi/.gitbin.branch")
	uptime          = commands.getoutput("uptime")
	dfh             = commands.getoutput("df -h")
	freeh           = commands.getoutput("free -h")
	psout           = commands.getoutput("ps -e -o pcpu,args | awk 'NR>2' | sort -nr | head -10 | sed 's/&/\&amp;/g' | sed 's/>/\&gt;/g'")
	#
	flock='/tmp/raspdiagd-99.lock'
	lock(flock)
	f = file('/mnt/share1/' + uname[1] + '/status.txt', 'w')

	f.write('<server>\n')

	f.write('<name>\n')
	f.write(uname[1] + '\n')
	f.write('</name>\n')

	f.write('<df>\n')
	f.write(dfh + '\n')
	f.write('</df>\n')

	f.write('<temperature>\n')
	f.write(str(Tcpu) + ' degC @ '+ str(fcpu) +' MHz\n')
	f.write('</temperature>\n')

	f.write('<memusage>\n')
	f.write(freeh + '\n')
	f.write('</memusage>\n')

	f.write(' <uptime>\n')
	f.write(uptime + '\n')
	f.write(uname[0]+ ' ' +uname[1]+ ' ' +uname[2]+ ' ' +uname[3]+ ' ' +uname[4]+ ' ' +platform.platform() +'\n')
	f.write(' - raspdiagd on: '+ raspdiagdbranch +'\n')
	f.write(' - gitbin    on: '+ gitbinbranch +'\n')
	f.write('\nTop 10 processes:\n' + psout +'\n')
	f.write('</uptime>\n')

	f.write('</server>\n')

	f.close()
	unlock(flock)
	return

def lock(fname):
	open(fname, 'a').close()

def unlock(fname):
	if os.path.isfile(fname):
		os.remove(fname)

if __name__ == "__main__":
	daemon = MyDaemon('/tmp/raspdiagd-99.pid')
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
