#! /bin/bash

# 00-scriptmanager.sh is run periodically by a private cronjob.
# * It synchronises the local copy of raspdiagd with the current github branch
# * It checks the state of and (re-)starts daemons if they are not (yet) running.

# To suppress git detecting changes by chmod:
# $ git config core.fileMode false
# set the branch
# $ echo master > ~/bin/raspdiagd.branch

branch=$(cat ~/bin/raspdiagd.branch)

# Synchronise local copy with $branch
git fetch origin && \
 # Check which code has changed
 # git diff --name-only
 # git log --graph --oneline --date-order --decorate --color --all

 DIFFlib=$(git --no-pager diff --name-only $branch..origin/$branch -- ./libdaemon.py)
 DIFFd11=$(git --no-pager diff --name-only $branch..origin/$branch -- ./daemon11.py)
 DIFFd12=$(git --no-pager diff --name-only $branch..origin/$branch -- ./daemon12.py)
 DIFFd13=$(git --no-pager diff --name-only $branch..origin/$branch -- ./daemon13.py)
 DIFFd14=$(git --no-pager diff --name-only $branch..origin/$branch -- ./daemon14.py)

 git reset --hard origin/$branch && \
 git clean -f -d

#python -m compileall .
# Set permissions
chmod -R 744 *

if [[ -n "$DIFFd11" ]]; then
  logger -t raspdiagd "daemon11 has changed"
  ./daemon11.py restart
fi
if [[ -n "$DIFFd12" ]]; then
  logger -t raspdiagd "daemon12 has changed"
  ./daemon12.py restart
fi
if [[ -n "$DIFFd13" ]]; then
  logger -t raspdiagd "daemon13 has changed"
  ./daemon13.py restart
fi
if [[ -n "$DIFFd14" ]]; then
  logger -t raspdiagd "daemon14 has changed"
  ./daemon14.py restart
fi

if [[ -n "$DIFFlib" ]]; then
    logger -t raspdiagd "libdaemon has changed"
    # stop all daemons
    ./daemon11.py stop
    ./daemon12.py stop
    ./daemon13.py stop
    ./daemon14.py stop
    sleep 1
    # start all daemons
    ./daemon11.py start
    ./daemon12.py start
    ./daemon13.py start
    ./daemon14.py start
fi
