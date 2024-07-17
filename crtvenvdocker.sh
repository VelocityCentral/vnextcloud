#/bin/bash

#---------------------------------------------------------------
# key setup items
# The Root of the quicklinks user folder:
export QLROOT=/var/www/html/nextcloud/data/quicklinks/files
QLOCC=$(expr $QLROOT  :  '.*\(/.*/.*\)')
# Full path to the python executable
export PYTHONEXEC=/usr/local/bin/python3.10
# Name  you want to give the virtual environment
export VENVNAME=test_310a
# Place you want to copy the project files from
export VNEXTCLOUDSRC=$QLROOT/test_v10
#---------------------------------------------------------------


export PATH_TO_OCC=`find /var/www/ -name occ | head -n 1` 
export PYTHONVSNEXEC=${PYTHONEXEC##*/}

# should be run as user apache

if [[ `id -un` != 'apache' ]] ; then
	echo "Must be run as apache"
	exit 1
fi

# Check python can be found...
$PYTHONEXEC --version
if [ $? -ne 0 ] ; then
	echo "Cannot execute python"
	exit 1
fi

# Check the quicklinks folder exists:
if [ ! -d $QLROOT ] ; then
	echo "Cannot locate Quicklinks root"
	exit 1
fi

cd $QLROOT

echo "Creating Venv"
$PYTHONEXEC -m venv ./$VENVNAME/venv
ls ./$VENVNAME/venv/bin

# remove sym links because they are not supported in QL.
# take care to ensure the correct version of Python is copied

echo "Replacing Symbolic Links"

cd $QLROOT/$VENVNAME/venv/bin

rm -f python
cp $PYTHONEXEC ./python
rm -f python3
cp $PYTHONEXEC ./python3
rm -f $PYTHONVSNEXEC
cp $PYTHONEXEC ./$PYTHONVSNEXEC


# deal with lib64
cd $QLROOT/$VENVNAME/venv
rm -rf lib64
cp -rp lib ./lib64


echo "Copying source files"
# Copy the files
cd $QLROOT
cp $VNEXTCLOUDSRC/*.py $VENVNAME/.
cp $VNEXTCLOUDSRC/*.sh $VENVNAME/.
cp $VNEXTCLOUDSRC/*.ini $VENVNAME/.
cp $VNEXTCLOUDSRC/REQUIREMENTS.txt $VENVNAME/.

echo "Updating NC database"
# make available to NC
php $PATH_TO_OCC files:scan --path="$QLOCC/$VENVNAME"





