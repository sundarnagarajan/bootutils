#!/bin/bash
REQD_PKGS="$*"

MISSING_PKGS=$(dpkg -l $REQD_PKGS 2>/dev/null | sed -e '1,4d'| grep -v '^ii' | awk '{printf("%s ", $2)}')
MISSING_PKGS="$MISSING_PKGS $(dpkg -l $REQD_PKGS 2>&1 1>/dev/null | sed -e 's/^dpkg-query: no packages found matching //')"
if [ -n "${MISSING_PKGS%% }" ]; then
	INSTALL_CMD="sudo apt-get install $MISSING_PKGS"
else
	INSTALL_CMD="All required packages are already installed\nRequired packages: $REQD_PKGS"
fi
echo $INSTALL_CMD
