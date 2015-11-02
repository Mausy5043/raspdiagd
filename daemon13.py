#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon13.py measures the network traffic.
# These are all counters, therefore no averaging is needed.

import syslog, traceback
import os, sys, time, math, commands
from libdaemon import Daemon

DEBUG = False
IS_SYSTEMD = os.path.isfile('/bin/journalctl')

class MyDaemon(Daemon):
  def run(self):
    sampleptr = 0
    samples = 1
    datapoints = 6

    sampleTime = 60
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

        result = do_work().split(',')
        data = map(int, result)

        sampleptr = sampleptr + 1
        if (sampleptr == samples):
          do_report(data)
          if (sampleptr == samples):
            sampleptr = 0

        waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
        if (waitTime > 0):
          if DEBUG:print "Waiting {0} s".format(waitTime)
          time.sleep(waitTime)
      except Exception as e:
        if DEBUG:
          print("Unexpected error:")
          print e.message
        syslog.syslog(syslog.LOG_ALERT,e.__doc__)
        syslog_trace(traceback.format_exc())
        raise

def syslog_trace(trace):
  '''Log a python stack trace to syslog'''
  log_lines = trace.split('\n')
  for line in log_lines:
    if len(line):
      syslog.syslog(syslog.LOG_ALERT,line)

def cat(filename):
  ret = ""
  if os.path.isfile(filename):
    f = file(filename,'r')
    ret = f.read().strip('\n')
    f.close()
  return ret

def do_work():
  # 6 datapoints gathered here
  # Network traffic
  wlIn = 0
  wlOut = 0
  etIn = 0
  etOut = 0
  loIn = 0
  loOut = 0

  list = cat("/proc/net/dev").replace(":"," ").splitlines()
  for line in range(2,len(list)):
    device = list[line].split()[0]
    if device == "lo":
      loIn = int(list[line].split()[1])
      loOut = int(list[line].split()[9])
    if device == "eth0":
      etIn = int(list[line].split()[1])
      etOut = int(list[line].split()[9])
    if device == "wlan0":
      wlIn = int(list[line].split()[1])
      wlOut = int(list[line].split()[9])
    if device == "wlan1":
      wlIn += int(list[line].split()[1])
      wlOut += int(list[line].split()[9])

  return '{0}, {1}, {2}, {3}, {4}, {5}'.format(loIn, loOut, etIn, etOut, wlIn, wlOut)

def do_report(result):
  # Get the time and date in human-readable form and UN*X-epoch...
  outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")

  result = ', '.join(map(str, result))
  flock = '/tmp/raspdiagd/13.lock'
  lock(flock)
  f = file('/tmp/raspdiagd/13-nettraffic.csv', 'a')
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
  daemon = MyDaemon('/tmp/raspdiagd/13.pid')
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
