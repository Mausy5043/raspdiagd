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
 DIFFdmn=$(git --no-pager diff --name-only $branch..origin/$branch -- ./daemon.py)

 git reset --hard origin/$branch && \
 git clean -f -d

#python -m compileall .
# Set permissions
chmod -R 744 *

if [[ -n "$DIFFdmn" ]]; then
  logger -t raspdiagd "daemon has changed"
#  ./daemon.py restart
fi

if [[ -n "$DIFFlib" ]]; then
    logger -t raspdiagd "libdaemon has changed"
#    ./testdaemon/daemon.py stop
#    sleep 1
#    ./testdaemon/daemon.py start
fi
