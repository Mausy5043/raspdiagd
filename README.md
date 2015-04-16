# raspdiagd
**Raspberry Pi Diagnostics Gatherer**

This repository provides a number of python-based daemons that gather some system diagnostics. Although specifically targeted at Raspberry Pi flavours of Debian, most will probably work on any Debian-based Linux distro.
The result of each deamon is a file containing comma-separated-values.

The code used to daemonise python code was borrowed from previous work by:
- Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)
- Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)

and modified for my particular use-case. This includes a couple of bash-scripts that keep the daemons running and upload the data to my NAS. 

NO code is provided for further processing of the data. E.g. adding the data to rrdtool-databases and/or graphing the data. This functionality is offered elsewhere.
