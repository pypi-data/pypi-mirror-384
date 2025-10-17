#!/usr/bin/bash
# Perform hourly maintenance activities.

# Stop on error.
set -e

# This script is designed to be run by cron.
# Set up the same environemnt variables as for a login shell.
source "$HOME/.bashrc"

kinit_keytab() {
    local principal="$(klist -k "$1" | tail -n 1 | sed 's/.*\s//')"
    kinit "${principal}" -k -t "$1"
}

kinit_keytab "${HOME}/krb5.keytab"
chronic htgettoken -v -a vault.ligo.org -i igwn -r read-cvmfs-${USER} --scopes="read:/virgo gracedb.read" --credkey=read-cvmfs-${USER}/robot/${USER}.ligo.caltech.edu --minsecs 7200 --nooidc

# Rotate log files.
/usr/sbin/logrotate --state ~/.local/state/logrotate.status ~/.config/logrotate.conf
