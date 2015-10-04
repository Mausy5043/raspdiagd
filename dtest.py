#!/usr/bin/env python

import syslog, traceback, commands, timeit
import subprocess as sp

def getuxtime(method):
  if method == 1:
    cmd = ["date", "+'%s'"]
    dt = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
    output, err = dt.communicate()
  if method == 2:
    output = commands.getoutput("date '+%F %H:%M:%S, %s'")
  #entries = output.replace("'", "").splitlines()
  return entries

def wrapper(func, *args, **kwargs):
    def wrapped():
        return func(*args, **kwargs)
    return wrapped

if __name__ == '__main__':
  try:
    ux = getuxtime(1)
    print ux
    ux = getuxtime(2)
    print ux

    wrapped = wrapper(getuxtime, 1)
    timeit.timeit(wrapped, number=1000)

    wrapped = wrapper(getuxtime, 2)
    timeit.timeit(wrapped, number=1000)

  except Exception as e:
    syslog.syslog(syslog.LOG_ALERT,e.__doc__)
    syslog_trace(traceback.format_exc())
    raise
