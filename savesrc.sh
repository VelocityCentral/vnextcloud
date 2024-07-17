#!/bin/bash
tar --exclude "venv" --exclude __pycache__ --exclude ".idea" -cvf /tmp/${PWD##*/}.tar .

echo "Source Saved to " /tmp/${PWD##*/}.tar