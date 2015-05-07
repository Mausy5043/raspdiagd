#! /usr/bin/python

import sys, serial, re, commands, time

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

def gettelegram():
  # flag used to exit the while-loop
  abort = 0
  # countdown counter used to prevent infinite loops
  loops2go = 40
  # storage space for the telegram
  telegram = []
  # end of line delimiter
  delim = "\x0a"

  try:
    port.open()
    serial.XON
  except:
    abort == 4
    # open error terminates immediately
    return telegram, abort

  while abort == 0:
    try:
      # this doesn't seem to work
      #line = str(port.readline()).strip()
      line = "".join(iter(lambda:port.read(1),delim)).strip()
    except:
      # read error, terminate prematurely
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

  try:
    serial.XOFF
    port.flush()
    port.close()
  except:
    abort == 5

  # Return codes:
  # abort == 1 indicates a successful read
  # abort == 2 means that no valid data was read from the serial port
  # abort == 3 indicates a data overrun. More lines were received than expected.
  # abort == 4 indicates a serial port open error.
  # abort == 5 indicates a serial port close error.
  return (telegram, abort)

def getelectrastring ():

  powerin = "NaN"

  telegram, status = gettelegram()

  if status == 1:
    for element in range(0, len(telegram) - 1):
      line =  re.split( '[\(\*\)]', telegram[element] )

      #['1-0:1.7.0', '0000.32', 'kW', '']
      if (line[0] == '1-0:1.7.0'):
        powerin = int(float(line[1]) * 1000)

  out = '{0}, {1}'.format(status, powerin)
  return (out)

if __name__ == "__main__":

  for cnt in range(0, 120):
    time.sleep(8)
    secs = int(commands.getoutput("date +%S"))

    if (secs > 15):
      outElectra = getelectrastring()
      # Get the time and date in human-readable form...
      outDate = commands.getoutput("date '+%F %H:%M:%S'")
      # Print the data
      print '{0}, {1}'.format(outDate, outElectra)
