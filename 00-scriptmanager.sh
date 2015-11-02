#! /bin/bash

# 00-scriptmanager.sh is run periodically by a private cronjob.
# * It synchronises the local copy of raspdiagd with the current github branch
# * It checks the state of and (re-)starts daemons if they are not (yet) running.

CLNT=$(hostname)
ME=$(whoami)
branch=$(cat /home/$ME/.raspdiagd.branch)
pushd /home/$ME/raspdiagd

# force recompilation of libraries
rm *.pyc
# Synchronise local copy with $branch

 git fetch origin
 # Check which code has changed
 # git diff --name-only
 # git log --graph --oneline --date-order --decorate --color --all

 DIFFlib=$(git --no-pager diff --name-only $branch..origin/$branch -- ./libdaemon.py)
 DIFFd11=$(git --no-pager diff --name-only $branch..origin/$branch -- ./daemon11.py)
 DIFFd12=$(git --no-pager diff --name-only $branch..origin/$branch -- ./daemon12.py)
 DIFFd13=$(git --no-pager diff --name-only $branch..origin/$branch -- ./daemon13.py)
 DIFFd14=$(git --no-pager diff --name-only $branch..origin/$branch -- ./daemon14.py)
 DIFFd15=$(git --no-pager diff --name-only $branch..origin/$branch -- ./daemon15.py)
 DIFFd16=$(git --no-pager diff --name-only $branch..origin/$branch -- ./daemon16.py)
 DIFFd17=$(git --no-pager diff --name-only $branch..origin/$branch -- ./daemon17.py)
 DIFFd23=$(git --no-pager diff --name-only $branch..origin/$branch -- ./daemon23.py)
 DIFFd99=$(git --no-pager diff --name-only $branch..origin/$branch -- ./daemon99.py)
 #DIFFdsr=$(git --no-pager diff --name-only $branch..origin/$branch -- ./sqlrand.py)

 git pull
 git fetch origin
 git checkout $branch
 git reset --hard origin/$branch && \
 git clean -f -d

#python -m compileall .
# Set permissions
chmod -R 744 *

if [[ ! -d /tmp/raspdiagd ]]; then
  mkdir /tmp/raspdiagd
fi

######## Stop daemons ######

if [[ -n "$DIFFd11" ]]; then
  logger -p user.notice -t raspdiagd "Source daemon11 has changed."
  ./daemon11.py stop
fi
if [[ -n "$DIFFd12" ]]; then
  logger -p user.notice -t raspdiagd "Source daemon12 has changed."
  ./daemon12.py stop
fi
if [[ -n "$DIFFd13" ]]; then
  logger -p user.notice -t raspdiagd "Source daemon13 has changed."
  ./daemon13.py stop
fi
if [[ -n "$DIFFd14" ]]; then
  logger -p user.notice -t raspdiagd "Source daemon14 has changed."
  ./daemon14.py stop
fi
if [[ -n "$DIFFd15" ]]; then
  logger -p user.notice -t raspdiagd "Source daemon15 has changed."
  ./daemon15.py stop
fi
if [[ -n "$DIFFd16" ]]; then
  logger -p user.notice -t raspdiagd "Source daemon16 has changed."
  ./daemon16.py stop
fi
if [[ -n "$DIFFd17" ]]; then
  logger -p user.notice -t raspdiagd "Source daemon17 has changed."
  ./daemon17.py stop
fi
if [[ -n "$DIFFd23" ]]; then
  logger -p user.notice -t raspdiagd "Source daemon23 has changed."
  ./daemon23.py stop
fi
if [[ -n "$DIFFd99" ]]; then
  logger -p user.notice -t raspdiagd "Source daemon99 has changed."
  ./daemon99.py stop
fi
#if [[ -n "$DIFFdsr" ]]; then
#  logger -p user.notice -t raspdiagd "Source sqlrand has changed."
#  ./sqlrand.py stop
#fi

if [[ -n "$DIFFlib" ]]; then
  logger -p user.notice -t raspdiagd "Source libdaemon has changed."
  # stop all daemons
  ./daemon11.py stop
  ./daemon12.py stop
  ./daemon13.py stop
  ./daemon14.py stop
  ./daemon15.py stop
  ./daemon16.py stop
  ./daemon17.py stop
  ./daemon23.py stop
  ./daemon99.py stop
#  ./sqlrand.py stop
fi

######## (Re-)start daemons ######

function destale {
  if [ -e /tmp/raspdiagd/$1.pid ]; then
    if ! kill -0 $(cat /tmp/raspdiagd/$1.pid)  > /dev/null 2>&1; then
      logger -p user.err -t raspdiagd "Stale daemon$1 pid-file found."
      rm /tmp/raspdiagd/$1.pid
      ./daemon$1.py start
    fi
  else
    logger -p user.warn -t raspdiagd "Found daemon$1 not running."
    ./daemon$1.py start
  fi
}

destale 11
destale 12
destale 13
destale 14
destale 15
destale 99

case "$CLNT" in
  rbups )   echo "UPS monitor"
            destale 16
            ;;
  rbelec )  echo "Electricity monitor"
            destale 17
            ;;
  rbian )   echo "Raspberry testbench"
            destale 23
            #./sqlrand.py restart
            ;;
  rxbmc )   echo "RaspBMC mediacenter"
            ;;
  osmc )    echo "OSMC Media Center"
            ;;
  * )       echo "!! undefined client !!"
            ;;
esac

popd

# the $MOUNTPOINT is in /etc/fstab
# in the unlikely event that the mount was lost,
# remount it here.
MOUNTPOINT=/mnt/share1
MOUNTDRIVE=boson.lan:/srv/array1/dataspool
if grep -qs $MOUNTPOINT /proc/mounts; then
    # It's mounted.
  echo "mounted"
else
    # Mount the share containing the data
    sudo mount $MOUNTDRIVE $MOUNTPOINT
fi
