#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon17.py communicates with the smart electricity meter.
# This is all singular data, no averaging needed.

import syslog, traceback
import os, sys, time, math, commands
from libdaemon import Daemon
import serial, re

DEBUG = False
IS_SYSTEMD = os.path.isfile('/bin/journalctl')

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
    #data = [[None]*datapoints for _ in range(samples)]

    sampleTime = 10
    cycleTime = samples * sampleTime

    port.open()
    serial.XON
    # sync to whole minute
    waitTime = (cycleTime + sampleTime) - (time.time() % cycleTime)
    if DEBUG:
      print "NOT waiting {0} s.".format(waitTime)
    else:
      time.sleep(waitTime)
    while True:
      try:
        startTime = time.time()

        data = do_work().split(', ')
        if DEBUG: print data

        sampleptr = sampleptr + 1
        if (sampleptr == samples):
          do_report(data)
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

def do_work():
  electra1in = "NaN"
  electra2in = "NaN"
  electra1out = "NaN"
  electra2out = "NaN"
  tarif = "NaN"
  swits = "NaN"
  powerin = "NaN"
  powerout = "NaN"

  telegram, status = gettelegram()

  if status == 1:
    for element in range(0, len(telegram) - 1):
      line =  re.split( '[\(\*\)]', telegram[element] )
      #['1-0:1.8.1', '00175.402', 'kWh', '']  T1 in
      if (line[0] == '1-0:1.8.1'):
        electra1in = int(float(line[1]) * 1000)
      #['1-0:1.8.2', '00136.043', 'kWh', '']  T2 in
      if (line[0] == '1-0:1.8.2'):
        electra2in = int(float(line[1]) * 1000)
      #['1-0:2.8.1', '00000.000', 'kWh', '']  T1 out
      if (line[0] == '1-0:2.8.1'):
        electra1out = int(float(line[1]) * 1000)
      #['1-0:2.8.2', '00000.000', 'kWh', '']  T2 out
      if (line[0] == '1-0:2.8.2'):
        electra2out = int(float(line[1]) * 1000)
      #['0-0:96.14.0', '0002', '']  tarif 1 or 2
      if (line[0] == '0-0:96.14.0'):
        tarif = int(line[1])
      #['1-0:1.7.0', '0000.32', 'kW', '']  power in
      if (line[0] == '1-0:1.7.0'):
        powerin = int(float(line[1]) * 1000)
      #['1-0:2.7.0', '0000.00', 'kW', ''] power out
      if (line[0] == '1-0:2.7.0'):
        powerout = int(float(line[1]) * 1000)
      #['0-0:17.0.0', '999', 'A', '']
         # not recorded
      #['0-0:96.3.10', '1', '']  powerusage (1) or powermanufacturing ()
      if (line[0] == '0-0:96.3.10'):
        swits = int(line[1])
      #['0-0:96.13.1', '', '']
         # not recorded
      #['0-0:96.13.0', '', '']
         # not recorded

  return '{0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}'.format(electra1in, electra2in, powerin, electra1out, electra2out, powerout, tarif, swits)

def gettelegram():
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
      if line == "!":
        abort = 1
      if line != "":
        telegram.append(line)
    except:
      abort = 2
    loops2go = loops2go - 1
    if loops2go < 0:
      abort = 3

  # test for correct start of telegram
  if telegram[0][0] != "/":
    abort = 2

  return telegram, abort

def do_report(result):
  # Get the time and date in human-readable form and UN*X-epoch...
  outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")
  if DEBUG:print result
  result = ', '.join(map(str, result))
  flock = '/tmp/raspdiagd/17.lock'
  lock(flock)
  f = file('/tmp/raspdiagd/17-electra.csv', 'a')
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
  daemon = MyDaemon('/tmp/raspdiagd/17.pid')
  if len(sys.argv) == 2:
    if 'start' == sys.argv[1]:
      daemon.start()
    elif 'stop' == sys.argv[1]:
      serial.XOFF
      port.close()
      daemon.stop()
    elif 'restart' == sys.argv[1]:
      serial.XOFF
      port.close()
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
    print "usage: %s start|stop|foreground" % sys.argv[0]
    sys.exit(2)
