#! /bin/bash

# `raspbian-ua-netinst` installs `raspboot` and makes sure it is run at the
# very first boot.

# `raspboot` then installs additional packages and modifies the system
# configuration accordingly. Among others `raspdiagd` may be installed
# using `git clone`. Followed by calling this `install.sh` script

# Installing `raspboot` requires:
# 1. Add a cronjob in `/etc/cron.d/` periodically running `00-scriptmanager`
#    to keep the daemons up-to-date
# 2. Add various start-stop scripts to `/etc/init.d/` to start the daemons
#    automagically at re-boot.
# 3. start each of the daemons for the first time.

# To suppress git detecting changes by chmod:
git config core.fileMode false
# set the branch
echo master > ~/.raspdiagd.branch

# set a cronjob
echo "# m h dom mon dow user  command" | sudo tee /etc/cron.d/raspdiagd
echo "42  * *   *   *   pi    /home/pi/raspdiagd/00-scriptmanager.sh 2>/tmp/raspdiagd.err 1>&2" | sudo tee /etc/cron.d/raspdiagd
echo "@reboot           pi    /home/pi/raspdiagd/00-scriptmanager.sh 2>/tmp/raspdiagd.err 1>&2" | sudo tee /etc/cron.d/raspdiagd

if [ ! -e /mnt/share1 ]; then
  echo "Creating mountpoint..."
  sudo mkdir /mnt/share1
fi

exit 0
