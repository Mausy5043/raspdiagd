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

if [ "$(hostname)" == 'rbagain' ]; then
  echo "Not installing on $(hostname)"
  exit 0
fi

echo -n "Started installing raspdiagd on "
date

install_package()
{
  # See if packages are installed and install them.
  package=$1
  status=$(dpkg-query -W -f='${Status} ${Version}\n' $package 2>/dev/null | wc -l)
  if [ "$status" -eq 0 ]; then
    sudo apt-get -yuV install $package
  fi
}

install_package "python"
install_package "git"
install_package "nfs-common"

# To suppress git detecting changes by chmod:
git config core.fileMode false
# set the branch
echo master > "$HOME/.raspdiagd.branch"

if [ ! -d /etc/cron.d ]; then
  echo "Creating /etc/cron.d..."
  sudo mkdir /etc/cron.d
fi

# set a cronjob
echo "# m h dom mon dow user  command" | sudo tee /etc/cron.d/raspdiagd
echo "42  * *   *   *   $ME    $HOME/raspdiagd/00-scriptmanager.sh 2>&1 | logger -p info -t raspdiagd" | sudo tee --append /etc/cron.d/raspdiagd
echo "@reboot           $ME    $HOME/raspdiagd/00-scriptmanager.sh 2>&1 | logger -p info -t raspdiagd" | sudo tee --append /etc/cron.d/raspdiagd

if [ ! -e /mnt/share1 ]; then
  echo "Creating mountpoint..."
  sudo mkdir /mnt/share1
fi

./00-scriptmanager.sh

echo -n "Finished installation of raspdiagd on "
date
