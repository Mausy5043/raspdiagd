#! /bin/bash

# 00-scriptmanager.sh is run periodically by a private cronjob.
# * It synchronises the local copy of raspdiagd with the current github branch
# * It checks the state of and (re-)starts daemons if they are not (yet) running.

# To suppress git detecting changes by chmod:
# $ git config core.fileMode false
# set the branch
# $ echo master > ~/bin/raspdiagd.branch

branch=$(cat ~/bin/raspdiagd.branch)
clnt=$(hostname)
bindir="~/raspdiagd"

# Synchronise local copy with $branch
git fetch origin && \
 # Check which code has changed
 # git diff --name-only
 # git log --graph --oneline --date-order --decorate --color --all

 DIFFlib=$(git --no-pager diff --name-only $branch..origin/$branch -- $bindir/libdaemon.py)
 DIFFd11=$(git --no-pager diff --name-only $branch..origin/$branch -- $bindir/daemon11.py)
 DIFFd12=$(git --no-pager diff --name-only $branch..origin/$branch -- $bindir/daemon12.py)
 DIFFd13=$(git --no-pager diff --name-only $branch..origin/$branch -- $bindir/daemon13.py)
 DIFFd14=$(git --no-pager diff --name-only $branch..origin/$branch -- $bindir/daemon14.py)
 DIFFd15=$(git --no-pager diff --name-only $branch..origin/$branch -- $bindir/daemon15.py)

 git reset --hard origin/$branch && \
 git clean -f -d

#python -m compileall .
# Set permissions
chmod -R 744 *

######## Stop daemons ######

if [[ -n "$DIFFd11" ]]; then
  logger -t raspdiagd "Source daemon11 has changed."
  $bindir/daemon11.py stop
fi
if [[ -n "$DIFFd12" ]]; then
  logger -t raspdiagd "Source daemon12 has changed."
  $bindir/daemon12.py stop
fi
if [[ -n "$DIFFd13" ]]; then
  logger -t raspdiagd "Source daemon13 has changed."
  $bindir/daemon13.py stop
fi
if [[ -n "$DIFFd14" ]]; then
  logger -t raspdiagd "Source daemon14 has changed."
  $bindir/daemon14.py stop
fi
if [[ -n "$DIFFd15" ]]; then
  logger -t raspdiagd "Source daemon15 has changed."
  $bindir/daemon15.py stop
fi

if [[ -n "$DIFFlib" ]]; then
  logger -t raspdiagd "Source libdaemon has changed."
  # stop all daemons
  $bindir/daemon11.py stop
  $bindir/daemon12.py stop
  $bindir/daemon13.py stop
  $bindir/daemon14.py stop
  $bindir/daemon15.py stop
fi

######## (Re-)start daemons ######

function destale {
  if [ -e /tmp/raspdiagd-$1.pid ]; then
    if ! kill -0 $(cat /tmp/raspdiagd-$1.pid)  > /dev/null 2>&1; then
      logger -t raspdiagd "Stale daemon$1 pid-file found."
      rm /tmp/raspdiagd-$1.pid
      $bindir/daemon$1.py start
    fi
  else
    logger -t raspdiagd "Found daemon$1 not running."
    $bindir/daemon$1.py start
  fi
}

destale 11
destale 12
destale 13
destale 14
destale 15
