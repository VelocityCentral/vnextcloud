#!/bin/bash

# This script creates a distribution file to be sent to PHS for installation

SRCDIR=/root/PycharmProjects/vnextcloud
TARFILE=/tmp/vnextcloud.tar

cd $SRCDIR

tar -cvf $TARFILE *.py 
tar -rvf $TARFILE *.sh 
tar -rvf $TARFILE *.ini 
tar -rvf $TARFILE REQUIREMENTS.txt
tar -rvf $TARFILE README.rst
tar -rvf $TARFILE README.pdf

echo "$TARFILE created"
