#! /bin/bash

# 00-scriptmanager.sh is run periodically by a private cronjob.
# * It synchronises the local copy of raspdiagd with the current github branch
# * It checks the state of and (re-)starts daemons if they are not (yet) running.

branch=$(cat ~/bin/raspdiagd.branch)

# Synchronise local copy with $branch
git fetch origin && \
 # Check which code has changed
 git diff --name-only
 #DIFFdmn=$(git --no-pager diff --name-only master -- ./testdaemon/daemon.py) && \
 #DIFFdmn=$(git --no-pager diff --name-only dev..origin/dev -- ./testdaemon/daemon.py) && \
 #DIFFlib=$(git --no-pager diff --name-only master -- ./testdaemon/libdaemon.py) && \
 #DIFFlib=$(git --no-pager diff --name-only dev..origin/dev -- ./testdaemon/libdaemon.py) && \
 git reset --hard origin/$branch && \
 git clean -f -d

#python -m compileall .
# Set permissions
chmod -R 744 *

#if [[ -n "$DIFFdmn" ]]; then
#    logger -t 02-update-scripts "daemon has changed"
#    ./testdaemon/daemon.py restart
#fi

#if [[ -n "$DIFFlib" ]]; then
#    logger -t 02-update-scripts "daemonlib has changed"
#    ./testdaemon/daemon.py stop
#    sleep 1
#    ./testdaemon/daemon.py start
#fi
