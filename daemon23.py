#!/usr/bin/env python

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon23.py reads data from an Arduino running the cmdMULTIsens sketch from
# https://github.com/Mausy5043/arduino.git.

import syslog, traceback
import os, sys, time, math, commands
from libdaemon import Daemon
import serial, re

from urllib2 import Request, urlopen
from bs4 import BeautifulSoup

DEBUG = False
IS_SYSTEMD = os.path.isfile('/bin/journalctl')

class MyDaemon(Daemon):
  def run(self):
    sampleptr = 0
    cycles = 5
    SamplesPerCycle = 3
    samples = SamplesPerCycle * cycles

    datapoints = 11
    data = []

    sampleTime = 20
    cycleTime = samples * sampleTime

    # Start by getting external data.
    EXTERNAL_DATA_EXPIRY_TIME = 11*60 #seconds
    # This decouples the fetching of external data
    # from the reporting cycle.
    extern_result = do_extern_work().split(',')
    extern_data = map(float, extern_result)
    extern_time = time.time() + EXTERNAL_DATA_EXPIRY_TIME

    # sync to whole cycleTime
    waitTime = (cycleTime + sampleTime) - (time.time() % (cycleTime/cycles))
    if DEBUG:
      logtext = ">>> NOT waiting            : {0:.2f} s.".format(waitTime)
      print logtext
      syslog.syslog(syslog.LOG_DEBUG, logtext)
      waitTime = 0
    else:
      logtext = ">>> Waiting                : {0:.2f} s.".format(waitTime)
      syslog.syslog(syslog.LOG_DEBUG, logtext)

    time.sleep(waitTime)

    while True:
      try:
        startTime = time.time()

        result = do_work().split(',')
        if DEBUG:
          logtext = ":   Result = {0}".format(result)
          print logtext
          #syslog.syslog(syslog.LOG_DEBUG, logtext)

        data.append(map(float, result))
        if (len(data) > samples):data.pop(0)
        sampleptr = sampleptr + 1

        # report sample average
        if (sampleptr % SamplesPerCycle == 0):
          somma = map(sum,zip(*data))
          averages = [format(s / len(data), '.3f') for s in somma]

          # only fetch external data if current data is
          # older than EXTERNAL_DATA_EXPIRY_TIME
          if (extern_time < time.time()):
            extern_result = do_extern_work().split(',')
            extern_data = map(float, extern_result)
            extern_time = time.time() + EXTERNAL_DATA_EXPIRY_TIME

          windchill = calc_windchill(float(averages[1]), extern_data[0])
          avg_ext = [format(s, '.3f') for s in extern_data]
          avg_ext.append(windchill)

          if DEBUG:
            logtext = ":   Reporting sample {0} = {1} + {2}".format(sampleptr, averages, avg_ext)
            print logtext
            syslog.syslog(syslog.LOG_DEBUG, logtext)

          do_report(averages, avg_ext)
          if (sampleptr == samples):
            sampleptr = 0

        waitTime += sampleTime - (time.time() - startTime) - (startTime % sampleTime)
        if (waitTime > 0):
          if DEBUG:
            logtext = ">>> Waiting for next sample: {0:.2f} s".format(waitTime)
            print logtext
            syslog.syslog(syslog.LOG_DEBUG, logtext)
          time.sleep(waitTime)
          waitTime = 0
        else:
          if DEBUG:
            logtext = ">>> NOT waiting            : {0:.2f} s".format(waitTime)
            print logtext
            syslog.syslog(syslog.LOG_DEBUG, logtext)
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

  if DEBUG:
    logtext = ":   [gettelegram] code: {0}; loops: {1}".format(abort, loops2go)
    print logtext
    syslog.syslog(syslog.LOG_DEBUG, logtext)

  # Return codes:
  # abort == 1 indicates a successful read
  # abort == 2 means that a serial port read/write error occurred
  # abort == 3 no valid data after several attempts

  return (telegram, abort)

def do_work():
  # 12 datapoints gathered here

  ardtime = time.time()
  telegram, status = gettelegram("A")
  ardtime = time.time() - ardtime

  #print telegram
  if (status != 1):
    telegram = -1
    if DEBUG:
      logtext = "*** [do_work] NO TELEGRAM!"
      print logtext
      syslog.syslog(syslog.LOG_DEBUG, logtext)

  if DEBUG:
    logtext = ":   [do_work]              : {0:.2f} s".format(ardtime)
    print logtext
    syslog.syslog(syslog.LOG_DEBUG, logtext)

  return telegram

def do_extern_work():
  #set defaults
  ms = 0
  gr = 270

  ardtime=time.time()
  try:
    req = Request("http://xml.buienradar.nl/")
    response = urlopen(req, timeout=25)
    output = response.read()
    soup = BeautifulSoup(output)
    souptime = time.time()-ardtime

    MSwind = str(soup.buienradarnl.weergegevens.actueel_weer.weerstations.find(id=6350).windsnelheidms)
    GRwind = str(soup.buienradarnl.weergegevens.actueel_weer.weerstations.find(id=6350).windrichtinggr)
    #datum = str(soup.buienradarnl.weergegevens.actueel_weer.weerstations.find(id=6350).datum)
    ms = MSwind.replace("<"," ").replace(">"," ").split()[1]
    gr = GRwind.replace("<"," ").replace(">"," ").split()[1]

    if DEBUG:
      logtext = ":   [do_extern_work]       : {0:.2f} s".format(souptime)
      print logtext
      syslog.syslog(syslog.LOG_DEBUG, logtext)
  except Exception as e:
    logtext = "****** Exception encountered : " + str(e)
    syslog.syslog(syslog.LOG_DEBUG, logtext)
    ardtime = time.time() - ardtime
    logtext = "****** after                 {0:.2f} s".format(ardtime)
    syslog.syslog(syslog.LOG_DEBUG, logtext)

  gilzerijen = '{0}, {1}'.format(ms, gr)
  return gilzerijen

def calc_windchill(T,W):
  # use this data to determine the windchill temperature acc. JAG/TI
  # ref.: http://knmi.nl/bibliotheek/knmipubTR/TR309.pdf
  JagTi = 13.12 + 0.6215 * T - 11.37 * (W * 3.6)**0.16 + 0.3965 * T * (W * 3.6)**0.16
  if (JagTi > T):
    JagTi = T

  return JagTi

def do_report(result, ext_result):
  # Get the time and date in human-readable form and UN*X-epoch...
  #outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")

  outDate = commands.getoutput("date '+%FT%H:%M:%S'")
  ardtime = time.time()
  result = ', '.join(map(str, result))
  ext_result = ', '.join(map(str, ext_result))
  flock = '/tmp/raspdiagd/23.lock'
  lock(flock)
  f = file('/tmp/testser.txt', 'a')
  f.write('{0}, {1}, {2}\n'.format(outDate, result, ext_result) )
  f.close()
  unlock(flock)
  ardtime = time.time() - ardtime
  if DEBUG:
    logtext = ":   [do_report] : {0}, {1}, {2}".format(outDate, result, ext_result)
    print logtext
    #syslog.syslog(syslog.LOG_DEBUG, logtext)
    logtext = ":   [do_report]            : {0:.2f} s".format(ardtime)
    print logtext
    syslog.syslog(syslog.LOG_DEBUG, logtext)
  return

def lock(fname):
  open(fname, 'a').close()

def unlock(fname):
  if os.path.isfile(fname):
    os.remove(fname)

if __name__ == "__main__":
  port = serial.Serial('/dev/ttyACM0', 9600, timeout=10)
  serial.dsrdtr = False
  time.sleep(0.5)
  daemon = MyDaemon('/tmp/raspdiagd/23.pid')
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
