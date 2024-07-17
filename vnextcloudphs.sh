######!/bin/bash

# This script was written for use in the docker implementation
# which turned out to be useless because there was no way of creating
# the environment that could be sustained when the system was re-booted.
# The main problem was there did not appear to be any way to create a venv
# in a docker environment.


# I made the update of log files via OCC a function
# to that I could call it prior to any "exit 1"
link_log_file() {
	# I changed this to find the occ command because
	# it didn't find it on my machine.
	PATH_TO_OCC=`find /var/www/ -name occ | head -n 1` 
	echo "Running $PATH_TO_OCC" >> $THISLOG
	php $PATH_TO_OCC files:scan --path="$THISLOG"
	if [ $? -ne 0 ] ; then
		eckho "OCC failed to run"
	fi
	php $PATH_TO_OCC files:scan --path="/quicklinks/files/$VENV/logs"
	if [ $? -ne 0 ] ; then
		echo "OCC failed to run"
	fi
}

# I wrote a funciton to check if any call to python is in the venv

check_python_venv() {
python - << ___HEREDOC >> $THISLOG 2>&1

import sys
print('-----------------------------------------------------')
print('Python Venv check routine')
print('sys.prefix set to {}'.format(sys.prefix))
print('sys.base_prefix set to {}'.format(sys.base_prefix))
if sys.prefix == sys.base_prefix:
	print('NOT in a virtual Environment')
	sys.exit(1)
else:
	print('Running in Venv')
print('-----------------------------------------------------')

___HEREDOC

}

OWNER=$1
FILEPATH=$2
if [ -d /var/www/html/data ] ; then
	DATAROOT=/var/www/html/data
fi
if [ -d /var/www/html/nextcloud/data ] ; then
	DATAROOT=/var/www/html/nextcloud/data
fi
# I have set paths here so that is easier to change if the locations change
# This script is called from Flow with a full path name so we can use that to get name of the venv:
VENVROOT=${0%/*}
VENV=${VENVROOT##*/}

if [ ! -d $VENVROOT/logs ] ; then
	mkdir $VENVROOT/logs 
fi
# Use a txt file extension so that it can be opened in nextcloud:
THISLOG=$VENVROOT/logs/vnc_$$.txt
# added the following to the log so that I could see the environment in which it was running.
echo -e "$(date)\nOwner:$OWNER\nFile:$FILEPATH\nUSER:`id`\nPWD:$PWD" 
echo "Current log : $THISLOG"
echo -e "$(date)\nOwner:$OWNER\nFile:$FILEPATH\nUSER:`id`\nPWD:$PWD" > $THISLOG
echo "Venv $VENVROOT" >> $THISLOG
if [[ $(type -P python) ]] ; then
	echo "Current Python Version : `python --version`" >> $THISLOG
else
	echo "Python not found in current path" >> $THISLOG
fi


#check and load requirements:

if [ -r $VENVROOT/venv/bin/python ]
then
		# It would appear this does not correctly load the venv:
        python -m venv $VENVROOT/venv >> $THISLOG 2>&1
		check_python_venv
		# the above sometimes returned an error so the venv is not loaded.
		# So I put in a trap to try and load it from source command
		# I tend to use source /blah/blah/blah/venv/bin/activate.
		if [ $? -ne 0 ] ; then
			source $VENVROOT/venv/bin/activate >> $THISLOG 2>&1
			check_python_venv
			if [ $? -ne 0 ] ; then
				echo "Failed to start Venv" >> $THISLOG
				link_log_file
				exit 1
			else
				echo "Venv successfully started via source command" >> $THISLOG
			fi
		else
			echo "venv started via python" >> $THISLOG
		fi
#        $DATAROOT/quicklinks/files/test_venv/venv/bin/python3 -m pip install -r $DATAROOT/quicklinks/files/test_venv/REQUIREMENTS.txt  >> $THISLOG 2>&1
        pip install -r $VENVROOT/REQUIREMENTS.txt  >> $THISLOG 2>&1
		if [ $? -ne 0 ] ; then
			echo "Pip failed to run " >> $THISLOG
		fi
else
	echo "Failed to load venv"  
	echo "Failed to load venv"  >> $THISLOG
	link_log_file
	exit 1
fi

# What environment are we really in?


check_python_venv
if [ $? -ne 0 ] ; then
	echo "non zero exit" >> $THISLOG
	link_log_file
	exit 1
else
	echo "Venv Check Successful" >> $THISLOG
fi

echo "Current Python Version venv : " >> $THISLOG
python --version >> $THISLOG

echo "Installed Modules in this environment:" >> $THISLOG
pip list --format=columns >> $THISLOG 2>&1
#python3 -m pip list --format=legacy >> $THISLOG 2>&1

# parameters can be referred to via an an array - $@
CREATESHARE=0
for arg in "${@}"
do
  if [[ $arg == --create-share ]] ; then
  	echo "Running with --create-share" >> $THISLOG
    CREATESHARE=1
  fi
done

echo "Running Python:" >> $THISLOG
if [ $CREATESHARE -eq 1 ]; then
# Change this to just call python as the version is determined by the venv.
#  $VENVROOT/venv/bin/python3 $VENVROOT/main.py  --owner $OWNER --file "$FILEPATH" --create-public-share >> $THISLOG 2>&1
  python $VENVROOT/main.py  --owner $OWNER --file "$FILEPATH" --create-public-share >> $THISLOG 2>&1
  if [ $? -ne 0 ] ; then
    echo "A problem occurred when updating the quicklink" >> $THISLOG
  fi
else
  python $VENVROOT/main.py  --owner $OWNER --file "$FILEPATH"  >> $THISLOG 2>&1
  if [ $? -ne 0 ] ; then
    echo "A problem occurred when updating the quicklink" >> $THISLOG
  fi
fi


link_log_file
