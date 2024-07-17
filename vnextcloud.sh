#!/bin/bash

if [[ `hostname` = "fs-01.bathurst.pcms.local" ]] ; then
    export VNXTCLDROOT=/home/velocity/vnextcloud
	export INIFILE=$VNXTCLDROOT/bathurst.ini
else
    export VNXTCLDROOT=/root/PycharmProjects/vnextcloud
	export INIFILE=$VNXTCLDROOT/vnextcloud.ini
fi

OWNER=$1
FILEPATH=$2

# parameters can be referred to via an an array - $@
CREATESHARE=0
for arg in "${@}"
do
  if [[ $arg == --create-share ]] ; then
    CREATESHARE=1
  fi
done
THISLOG=/tmp/vnc_$$.log
# echo -e "$(date)\n$OWNER\n$FILEPATH\n$FILEID" | mail -s "Nextcloud Python Call" ray.burns@velocityglobal.co.nz
echo -e "$(date)\n$OWNER\n$FILEPATH" > $THISLOG
source $VNXTCLDROOT/venv/bin/activate
if [ $? -ne 0 ] ; then
    if type mail >/dev/null 2>/dev/null ; then
      echo "Failed to locate the venv activate script" | mail -s "Nextcloud Python Venv Error" root
    else
      echo "Failed to locate the venv activate script" >> $THISLOG
    fi
    exit 1
fi
echo "$(date +%T) Venv Activated"
if [ $CREATESHARE -eq 1 ]; then
  echo "$(date +%T) Create Share specified"
  $VNXTCLDROOT/venv/bin/python $VNXTCLDROOT/main.py  --configfile $INIFILE --owner $OWNER --file "$FILEPATH" --create-public-share 2>&1 >> $THISLOG
  if [ $? -ne 0 ] ; then
    echo "$(date +%T) Non Zero Exit from python"
    if type mail >/dev/null 2>/dev/null ; then
      echo "A problem occurred when updating the quicklink" | mail -s "Nextcloud Python Call Error" root
    else
      echo "A problem occurred when updating the quicklink" >> $THISLOG
    fi
  fi
else
  $VNXTCLDROOT/venv/bin/python $VNXTCLDROOT/main.py  --configfile $INIFILE --owner $OWNER --file "$FILEPATH"  >> $THISLOG 2>&1
  echo "$(date +%T) Non Zero Exit from python"
  if [ $? -ne 0 ] ; then
    if type mail >/dev/null 2>/dev/null ; then
      echo "A problem occurred when updating the quicklink" | mail -s "Nextcloud Python Call Error" root
    else
      echo "A problem occurred when updating the quicklink" >> $THISLOG
    fi
  fi
fi
if type mail >/dev/null 2>/dev/null ; then
  cat $THISLOG | mail -s "Nextcloud Python Cloud" ray.burns@velocityglobal.co.nz
else
  cat $THISLOG >> $VNXTCLDROOT/shell.log
fi
rm -f $THISLOG
