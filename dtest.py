#!/usr/bin/env python

import syslog, traceback, commands, timeit
import subprocess as sp

def getuxtime(method):
  if method == 1:
    cmd = ["date", "+'%s'"]
    dt = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
    output, err = dt.communicate()
    output = output.replace("'", "")
  if method == 2:
    output = commands.getoutput("date +'%s'")
  return output

def wrapper(func, *args, **kwargs):
    def wrapped():
        return func(*args, **kwargs)
    return wrapped

def syslog_trace(trace):
  # Log a python stack trace to syslog
  log_lines = trace.split('\n')
  for line in log_lines:
    if line:
      syslog.syslog(syslog.LOG_ALERT,line)

if __name__ == '__main__':
  try:
    ux = getuxtime(1)
    print ux
    ux = getuxtime(2)
    print ux

    wrapped = wrapper(getuxtime, 1)
    tm = timeit.timeit(wrapped, number=1000)
    print tm
    wrapped = wrapper(getuxtime, 2)
    tm = timeit.timeit(wrapped, number=1000)
    print tm
  except Exception as e:
    syslog.syslog(syslog.LOG_ALERT,e.__doc__)
    syslog_trace(traceback.format_exc())
    raise
