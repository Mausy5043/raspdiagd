#! /bin/bash

# `raspbian-ua-netinst` installs `raspboot` and makes sure it is run at the
# very first boot.

# `raspboot` then installs additional packages and modifies the system
# configuration accordingly. Among others, `raspdiagd` may be installed
# using `git clone`. Followed by calling this `install.sh` script
ME=$(whoami)
# Installing `raspdiagd` requires:
# 1. Add a cronjob in `/etc/cron.d/` periodically running `00-scriptmanager`
#    to keep the daemons up-to-date
# 2. Add various start-stop scripts to `/etc/init.d/` to start the daemons
#    automagically at re-boot. (currently using a cronjob)

echo -n "Started installing raspdiagd on "
date
# To suppress git detecting changes by chmod:
git config core.fileMode false
# set the branch
echo master > /home/$ME/.raspdiagd.branch

if [ ! -d /etc/cron.d ]; then
  echo "Creating /etc/cron.d..."
  sudo mkdir /etc/cron.d
fi

# set a cronjob
echo "# m h dom mon dow user  command" | sudo tee /etc/cron.d/raspdiagd
echo "42  * *   *   *   $ME    /home/$ME/raspdiagd/00-scriptmanager.sh 2>&1 | logger -p info -t raspdiagd" | sudo tee --append /etc/cron.d/raspdiagd
echo "@reboot           $ME    /home/$ME/raspdiagd/00-scriptmanager.sh 2>&1 | logger -p info -t raspdiagd" | sudo tee --append /etc/cron.d/raspdiagd

if [ ! -e /mnt/share1 ]; then
  echo "Creating mountpoint..."
  sudo mkdir /mnt/share1
fi

./00-scriptmanager.sh

echo -n "Finished installation of raspdiagd on "
date
