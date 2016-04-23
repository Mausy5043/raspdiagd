#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon16.py reports various UPS variables.
# uses moving averages

import syslog, traceback
import os, sys, time, math, subprocess
from libdaemon import Daemon

DEBUG = False
IS_SYSTEMD = os.path.isfile('/bin/journalctl')

class MyDaemon(Daemon):
  def run(self):
    reportTime = 60                                 # time [s] between reports
    cycles = 3                                      # number of cycles to aggregate
    samplesperCycle = 5                             # total number of samples in each cycle
    samples = samplesperCycle * cycles              # total number of samples averaged
    sampleTime = reportTime/samplesperCycle         # time [s] between samples
    cycleTime = samples * sampleTime                # time [s] per cycle

    data = []                                       # array for holding sampledata

    while True:
      try:
        startTime = time.time()

        result = do_work().split(',')
        if DEBUG:print "result:",result

        data.append(map(float, result))
        if (len(data) > samples):data.pop(0)

        # report sample average
        if (startTime % reportTime < sampleTime):
          if DEBUG:print "data:",data
          somma = map(sum,zip(*data))
          averages = [format(s / len(data), '.3f') for s in somma]
          if DEBUG:print "averages:",averages
          do_report(averages)

        waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
        if (waitTime > 0):
          if DEBUG:print "Waiting {0} s".format(waitTime)
          time.sleep(waitTime)
      except Exception as e:
        if DEBUG:
          print "Unexpected error:"
          print e.message
        syslog.syslog(syslog.LOG_ALERT,e.__doc__)
        syslog_trace(traceback.format_exc())
        raise

def syslog_trace(trace):
  # Log a python stack trace to syslog
  log_lines = trace.split('\n')
  for line in log_lines:
    if line:
      syslog.syslog(syslog.LOG_ALERT,line)

def do_work():
  # 5 datapoints gathered here
  try:
    upsc = subprocess.check_output(["upsc", "ups@localhost"]).splitlines()
  except Exception as e:
    if DEBUG:
      print "Unexpected error:"
      print e.message
    syslog.syslog(syslog.LOG_ALERT, e.message)
    syslog_trace(traceback.format_exc())
    time.sleep(60)    # wait 60s to let the driver properly crash
    r = subprocess.check_output(["sudo", "systemctl", "restart",  "nut-driver.service"]).splitlines()
    if DEBUG:
      print r
    time.sleep(10)
    upsc = subprocess.check_output(["upsc", "ups@localhost"]).splitlines()
    pass

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
  outDate = time.strftime('%Y-%m-%dT%H:%M:%S, %s')

  result = ', '.join(map(str, result))
  flock = '/tmp/raspdiagd/16.lock'
  lock(flock)
  with open('/tmp/raspdiagd/16-aux-ups.csv', 'a') as f:
    f.write('{0}, {1}\n'.format(outDate, result) )
  unlock(flock)

def lock(fname):
  open(fname, 'a').close()

def unlock(fname):
  if os.path.isfile(fname):
    os.remove(fname)

if __name__ == "__main__":
  daemon = MyDaemon('/tmp/raspdiagd/16.pid')
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
    print "usage: {0!s} start|stop|restart|foreground".format(sys.argv[0])
    sys.exit(2)
